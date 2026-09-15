from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """A sellable item with the physical dimensions needed for packing."""

    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    # All dimensions in centimeters, weight in kilograms. Using a single
    # consistent unit system everywhere avoids conversion bugs when
    # comparing products against boxes.
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, validators=[MinValueValidator(0.001)])

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def volume_cm3(self):
        return self.length_cm * self.width_cm * self.height_cm

    @property
    def dimensions_sorted(self):
        """Dimensions sorted ascending — used for orientation-agnostic fit checks."""
        return sorted([self.length_cm, self.width_cm, self.height_cm])


class Box(models.Model):
    """A shipping box the warehouse can pack an order into."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    internal_length_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    internal_width_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    internal_height_cm = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])

    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=3, validators=[MinValueValidator(0.001)])
    cost = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    is_active = models.BooleanField(default=True, help_text="Inactive boxes are excluded from recommendations.")

    class Meta:
        ordering = ["cost"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def internal_volume_cm3(self):
        return self.internal_length_cm * self.internal_width_cm * self.internal_height_cm

    @property
    def dimensions_sorted(self):
        return sorted([self.internal_length_cm, self.internal_width_cm, self.internal_height_cm])


class Order(models.Model):
    order_number = models.CharField(max_length=64, unique=True)
    customer_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Once a recommendation is generated we store it, so the warehouse
    # always sees a stable answer for a given order rather than
    # recomputing (and potentially getting a different answer if box
    # inventory/pricing changes later).
    recommended_box = models.ForeignKey(
        Box, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.sku}"
