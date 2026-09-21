from django.urls import path

from .views import (
    CreateOrderAPIView,
    ProductDetailAPIView,
    RazorpayWebhookAPIView,
    VerifyPaymentAPIView,
)

urlpatterns = [
    path("products/<int:pk>/", ProductDetailAPIView.as_view()),
    path("create-order/", CreateOrderAPIView.as_view()),
    path("verify-payment/", VerifyPaymentAPIView.as_view()),
    path("webhook/razorpay/", RazorpayWebhookAPIView.as_view()),
]
