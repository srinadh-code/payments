from rest_framework import serializers

from .models import Payment, Product


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ["id", "name", "price", "stock", "image", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = [
            "id",
            "amount",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
            "status",
            "stock_reduced",
            "created_at",
        ]


class CreateOrderSerializer(serializers.Serializer):
    """Input for creating a Razorpay order. Amount is NEVER accepted from the
    client — it is always derived server-side from Product.price."""

    product_id = serializers.IntegerField()
    customer_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()


class VerifyPaymentSerializer(serializers.Serializer):

    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
