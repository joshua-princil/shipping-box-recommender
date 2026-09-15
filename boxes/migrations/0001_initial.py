import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Box",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("internal_length_cm", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ("internal_width_cm", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ("internal_height_cm", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ("max_weight_kg", models.DecimalField(decimal_places=3, max_digits=8, validators=[django.core.validators.MinValueValidator(0.001)])),
                ("cost", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0)])),
                ("is_active", models.BooleanField(default=True, help_text="Inactive boxes are excluded from recommendations.")),
            ],
            options={"ordering": ["cost"]},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sku", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("length_cm", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ("width_cm", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ("height_cm", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0.01)])),
                ("weight_kg", models.DecimalField(decimal_places=3, max_digits=8, validators=[django.core.validators.MinValueValidator(0.001)])),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_number", models.CharField(max_length=64, unique=True)),
                ("customer_name", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("recommended_box", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="boxes.box")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="boxes.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="boxes.product")),
            ],
            options={"unique_together": {("order", "product")}},
        ),
    ]
