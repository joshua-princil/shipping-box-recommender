from django.core.management.base import BaseCommand

from boxes.models import Box, Product


class Command(BaseCommand):
    help = "Populate the database with a handful of demo products and boxes."

    def handle(self, *args, **options):
        products = [
            dict(sku="MUG-001", name="Ceramic Mug", length_cm=12, width_cm=9, height_cm=9, weight_kg=0.35),
            dict(sku="BOOK-014", name="Paperback Novel", length_cm=20, width_cm=13, height_cm=2.5, weight_kg=0.3),
            dict(sku="TSHIRT-M", name="Cotton T-Shirt (M)", length_cm=30, width_cm=25, height_cm=2, weight_kg=0.2),
            dict(sku="LAMP-007", name="Desk Lamp", length_cm=40, width_cm=15, height_cm=15, weight_kg=1.8),
            dict(sku="MONITOR-24", name="24-inch Monitor", length_cm=56, width_cm=20, height_cm=40, weight_kg=4.5),
        ]
        for p in products:
            Product.objects.update_or_create(sku=p["sku"], defaults=p)

        boxes = [
            dict(code="XS", name="Extra Small Box", internal_length_cm=15, internal_width_cm=15,
                 internal_height_cm=10, max_weight_kg=2, cost="1.20"),
            dict(code="SM", name="Small Box", internal_length_cm=25, internal_width_cm=20,
                 internal_height_cm=15, max_weight_kg=5, cost="1.80"),
            dict(code="MD", name="Medium Box", internal_length_cm=35, internal_width_cm=25,
                 internal_height_cm=20, max_weight_kg=10, cost="2.50"),
            dict(code="LG", name="Large Box", internal_length_cm=45, internal_width_cm=35,
                 internal_height_cm=30, max_weight_kg=15, cost="3.75"),
            dict(code="XL", name="Extra Large Box", internal_length_cm=60, internal_width_cm=45,
                 internal_height_cm=45, max_weight_kg=25, cost="5.50"),
        ]
        for b in boxes:
            Box.objects.update_or_create(code=b["code"], defaults=b)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(products)} products and {len(boxes)} boxes."
        ))
