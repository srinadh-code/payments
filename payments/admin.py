from django.contrib import admin

from .models import Payment, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "price", "stock", "created_at"]
    search_fields = ["name"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "product",
        "customer_name",
        "email",
        "amount",
        "status",
        "razorpay_order_id",
        "razorpay_payment_id",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["customer_name", "email", "razorpay_order_id", "razorpay_payment_id"]
    readonly_fields = [
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "stock_reduced",
    ]
