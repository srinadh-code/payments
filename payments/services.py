import razorpay
from django.conf import settings

client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET,
    )
)
client.set_app_details({"title": "Django-Razorpay-Ecommerce", "version": "1.0.0"})


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verifies the signature returned by Razorpay Checkout after a payment.
    Returns True/False instead of raising, so callers don't need try/except."""

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """Verifies the X-Razorpay-Signature header on an incoming webhook
    request against RAZORPAY_WEBHOOK_SECRET."""

    if not signature or not settings.RAZORPAY_WEBHOOK_SECRET:
        return False

    try:
        client.utility.verify_webhook_signature(
            raw_body.decode("utf-8"),
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
        )
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
