from decimal import Decimal

from django.test import TestCase

from .models import Box, Order, OrderItem, Product
from .services import NoSuitableBoxError, get_ranked_candidate_boxes, recommend_box


class BoxRecommendationTests(TestCase):
    def setUp(self):
        self.small_box = Box.objects.create(
            code="SM", name="Small", internal_length_cm=20, internal_width_cm=15,
            internal_height_cm=10, max_weight_kg=3, cost="1.00",
        )
        self.medium_box = Box.objects.create(
            code="MD", name="Medium", internal_length_cm=35, internal_width_cm=25,
            internal_height_cm=20, max_weight_kg=10, cost="2.00",
        )
        self.large_box = Box.objects.create(
            code="LG", name="Large", internal_length_cm=60, internal_width_cm=40,
            internal_height_cm=35, max_weight_kg=20, cost="3.50",
        )

        self.mug = Product.objects.create(
            sku="MUG", name="Mug", length_cm=12, width_cm=9, height_cm=9, weight_kg="0.35",
        )
        self.book = Product.objects.create(
            sku="BOOK", name="Book", length_cm=20, width_cm=13, height_cm=2.5, weight_kg="0.3",
        )
        self.monitor = Product.objects.create(
            sku="MONITOR", name="Monitor", length_cm=56, width_cm=20, height_cm=40, weight_kg="4.5",
        )

    def make_order(self, order_number, items):
        order = Order.objects.create(order_number=order_number)
        for product, qty in items:
            OrderItem.objects.create(order=order, product=product, quantity=qty)
        return order

    def test_picks_cheapest_box_that_fits(self):
        order = self.make_order("ORD-1", [(self.mug, 1)])
        result = recommend_box(order, persist=False)
        self.assertEqual(result.box, self.small_box)

    def test_upgrades_box_when_small_one_overflows_on_volume(self):
        # Enough books that total volume no longer fits the small box,
        # even though each individual book does.
        order = self.make_order("ORD-2", [(self.book, 15)])
        result = recommend_box(order, persist=False)
        self.assertNotEqual(result.box, self.small_box)

    def test_oversized_single_item_forces_larger_box_even_if_light(self):
        # The monitor is light enough for the small box's weight limit,
        # but physically too big to fit inside it.
        order = self.make_order("ORD-3", [(self.monitor, 1)])
        result = recommend_box(order, persist=False)
        self.assertEqual(result.box, self.large_box)

    def test_weight_limit_forces_bigger_box(self):
        heavy_item = Product.objects.create(
            sku="WEIGHT", name="Heavy but small", length_cm=10, width_cm=10, height_cm=10, weight_kg="12.0",
        )
        order = self.make_order("ORD-4", [(heavy_item, 1)])
        result = recommend_box(order, persist=False)
        # Fits inside the small AND medium box's dimensions easily, but
        # exceeds both of their weight limits (3kg, 10kg) — needs the
        # large box (20kg limit).
        self.assertEqual(result.box, self.large_box)

    def test_no_suitable_box_raises(self):
        giant = Product.objects.create(
            sku="GIANT", name="Giant", length_cm=200, width_cm=200, height_cm=200, weight_kg="1",
        )
        order = self.make_order("ORD-5", [(giant, 1)])
        with self.assertRaises(NoSuitableBoxError):
            recommend_box(order, persist=False)

    def test_inactive_box_excluded(self):
        self.small_box.is_active = False
        self.small_box.save()
        order = self.make_order("ORD-6", [(self.mug, 1)])
        result = recommend_box(order, persist=False)
        self.assertNotEqual(result.box, self.small_box)

    def test_ranked_candidates_sorted_by_cost_then_size(self):
        order = self.make_order("ORD-7", [(self.mug, 1)])
        candidates = get_ranked_candidate_boxes(order)
        costs = [c.box.cost for c in candidates]
        self.assertEqual(costs, sorted(costs))

    def test_recommendation_persists_on_order_by_default(self):
        order = self.make_order("ORD-8", [(self.mug, 1)])
        recommend_box(order)  # persist=True by default
        order.refresh_from_db()
        self.assertEqual(order.recommended_box, self.small_box)

    def test_empty_order_raises(self):
        order = Order.objects.create(order_number="ORD-9")
        with self.assertRaises(NoSuitableBoxError):
            recommend_box(order, persist=False)

    def test_utilization_percentages_are_reasonable(self):
        order = self.make_order("ORD-10", [(self.mug, 1)])
        result = recommend_box(order, persist=False)
        self.assertGreater(result.weight_utilization_pct, Decimal("0"))
        self.assertLessEqual(result.weight_utilization_pct, Decimal("100"))
        self.assertGreater(result.volume_utilization_pct, Decimal("0"))
