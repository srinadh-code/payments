from decimal import Decimal

from django.db import migrations


def seed_product(apps, schema_editor):
    Product = apps.get_model("payments", "Product")
    Product.objects.get_or_create(
        name="Premium Shirt",
        defaults={"price": Decimal("1.00"), "stock": 10},
    )


def remove_product(apps, schema_editor):
    Product = apps.get_model("payments", "Product")
    Product.objects.filter(name="Premium Shirt").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_product, remove_product),
    ]
