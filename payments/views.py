import json
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, Product
from .serializers import (
    CreateOrderSerializer,
    ProductSerializer,
    VerifyPaymentSerializer,
)
from .services import client, verify_payment_signature, verify_webhook_signature

logger = logging.getLogger(__name__)


class ProductDetailAPIView(APIView):
    """Returns a single product, used by the product page to show live stock."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data)


class CreateOrderAPIView(APIView):
    """Creates a Razorpay order for a product.

    The charge amount is always computed from Product.price on the server —
    the client only ever sends a product_id. Never trust an amount field
    coming from the browser.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            product = get_object_or_404(
                Product.objects.select_for_update(), pk=data["product_id"]
            )

            if product.stock <= 0:
                return Response(
                    {"success": False, "message": "Product is out of stock"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            amount_paise = int(product.price * 100)

            razorpay_order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": f"product_{product.id}",
                    "notes": {"product_id": str(product.id)},
                }
            )

            payment = Payment.objects.create(
                product=product,
                customer_name=data["customer_name"],
                email=data["email"],
                amount=product.price,
                razorpay_order_id=razorpay_order["id"],
                status=Payment.STATUS_PENDING,
            )

        return Response(
            {
                "success": True,
                "payment_id": payment.id,
                "order_id": razorpay_order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "product_name": product.name,
                "customer_name": payment.customer_name,
                "email": payment.email,
            }
        )


def _mark_payment_success(payment: Payment, product: Product) -> None:
    """Flips a payment to SUCCESS and decrements stock exactly once.

    Caller must pass `payment` and `product` fetched with select_for_update()
    inside the same transaction, so concurrent callers (the browser verify
    call and the async webhook) can't double-decrement the same payment.
    """

    if payment.status == Payment.STATUS_SUCCESS and payment.stock_reduced:
        return

    payment.status = Payment.STATUS_SUCCESS

    if not payment.stock_reduced:
        if product.stock > 0:
            product.stock -= 1
            product.save(update_fields=["stock"])
        else:
            logger.warning(
                "Payment %s verified SUCCESS but product %s has no stock left",
                payment.id,
                product.id,
            )
        payment.stock_reduced = True

    payment.save(update_fields=["status", "stock_reduced"])


class VerifyPaymentAPIView(APIView):
    """Called by the frontend right after Razorpay Checkout closes with a
    successful payment. Verifies the signature before trusting anything."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payment = get_object_or_404(
            Payment, razorpay_order_id=data["razorpay_order_id"]
        )

        is_valid = verify_payment_signature(
            data["razorpay_order_id"],
            data["razorpay_payment_id"],
            data["razorpay_signature"],
        )

        if not is_valid:
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=["status"])
            return Response(
                {"success": False, "message": "Signature verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(pk=payment.pk)
            product = Product.objects.select_for_update().get(pk=payment.product_id)

            payment.razorpay_payment_id = data["razorpay_payment_id"]
            payment.razorpay_signature = data["razorpay_signature"]
            _mark_payment_success(payment, product)

        return Response({"success": True, "message": "Payment verified"})


class RazorpayWebhookAPIView(APIView):
    """Server-to-server webhook. This is the source of truth for payment
    status — the browser can close/crash/lose network right after paying,
    so stock must also be reconciled here, not only in VerifyPaymentAPIView.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_body = request.body
        signature = request.headers.get("X-Razorpay-Signature", "")

        if not verify_webhook_signature(raw_body, signature):
            logger.warning("Rejected webhook with invalid signature")
            return Response(
                {"success": False, "message": "Invalid webhook signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = json.loads(raw_body)
        event = payload.get("event")

        if event != "payment.captured":
            return Response({"success": True, "message": "Event ignored"})

        payment_entity = payload["payload"]["payment"]["entity"]
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        try:
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(
                    razorpay_order_id=order_id
                )
                product = Product.objects.select_for_update().get(
                    pk=payment.product_id
                )

                if not payment.razorpay_payment_id:
                    payment.razorpay_payment_id = payment_id

                _mark_payment_success(payment, product)
        except Payment.DoesNotExist:
            logger.warning("Webhook for unknown order_id=%s", order_id)
            return Response(
                {"success": False, "message": "Unknown order"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"success": True, "message": "Webhook processed"})
