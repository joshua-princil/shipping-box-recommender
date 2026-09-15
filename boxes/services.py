"""
Box recommendation logic.

The core question: given an order's line items, which shipping box should
the warehouse use?

True 3D bin-packing (deciding whether a specific set of boxes physically
arranges inside a container) is NP-hard and overkill for most ecommerce
catalogs. Instead we use a fast, explainable heuristic that warehouse staff
can reason about, with three independent checks a candidate box must pass:

  1. Weight check — total order weight must not exceed the box's rated
     max weight capacity.
  2. Individual item fit — every single product in the order must fit
     inside the box on its own (comparing sorted dimensions so we don't
     care which way an item is rotated). A box that's big enough in total
     volume but too short for one oversized item is not usable.
  3. Volume check — the summed volume of all items must fit within the
     box's internal volume, discounted by BOX_PACKING_EFFICIENCY to
     account for the fact that real packing never achieves 100% density
     (gaps between items, irregular shapes, padding material, etc).

Any box passing all three checks is a valid candidate. Among valid
candidates we recommend the cheapest one, breaking ties by smallest
internal volume (no reason to ship a bigger box than needed at the same
price).

This approach deliberately errs on the side of "won't recommend a box that
turns out too small" over squeezing out maximum packing efficiency. If you
outgrow this heuristic (e.g. highly irregular or fragile items where
orientation and stacking order matter), swap `_candidate_boxes` /
`recommend_box` for a call into a real 3D bin-packing library such as
`py3dbp`, keeping the same public function signature.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings

from .models import Box, Order


class NoSuitableBoxError(Exception):
    """Raised when no active box can hold the order."""

    def __init__(self, message, total_weight_kg=None, total_volume_cm3=None):
        super().__init__(message)
        self.total_weight_kg = total_weight_kg
        self.total_volume_cm3 = total_volume_cm3


@dataclass
class BoxRecommendation:
    box: Box
    total_weight_kg: Decimal
    total_volume_cm3: Decimal
    weight_utilization_pct: Decimal
    volume_utilization_pct: Decimal


def _packing_efficiency() -> Decimal:
    return Decimal(str(getattr(settings, "BOX_PACKING_EFFICIENCY", 0.85)))


def _item_fits_in_box(product, box) -> bool:
    """Orientation-agnostic check: can this single item physically fit in the box?"""
    return all(
        item_dim <= box_dim
        for item_dim, box_dim in zip(product.dimensions_sorted, box.dimensions_sorted)
    )


def _order_totals(order: Order):
    items = list(order.items.select_related("product").all())
    if not items:
        raise NoSuitableBoxError(f"Order {order.order_number} has no line items.")

    total_weight = sum((item.product.weight_kg * item.quantity for item in items), Decimal("0"))
    total_volume = sum((item.product.volume_cm3 * item.quantity for item in items), Decimal("0"))
    return items, total_weight, total_volume


def get_ranked_candidate_boxes(order: Order) -> list[BoxRecommendation]:
    """
    Return every active box that can hold the order, cheapest first.

    Raises NoSuitableBoxError if none can.
    """
    items, total_weight, total_volume = _order_totals(order)
    efficiency = _packing_efficiency()

    candidates: list[BoxRecommendation] = []
    for box in Box.objects.filter(is_active=True):
        if total_weight > box.max_weight_kg:
            continue
        if not all(_item_fits_in_box(item.product, box) for item in items):
            continue
        usable_volume = box.internal_volume_cm3 * efficiency
        if total_volume > usable_volume:
            continue

        candidates.append(
            BoxRecommendation(
                box=box,
                total_weight_kg=total_weight,
                total_volume_cm3=total_volume,
                weight_utilization_pct=round(total_weight / box.max_weight_kg * 100, 1),
                volume_utilization_pct=round(total_volume / box.internal_volume_cm3 * 100, 1),
            )
        )

    if not candidates:
        raise NoSuitableBoxError(
            f"No active box can hold order {order.order_number} "
            f"(total weight {total_weight} kg, total volume {total_volume} cm3).",
            total_weight_kg=total_weight,
            total_volume_cm3=total_volume,
        )

    # Cheapest first; among equal-cost boxes, prefer the smaller one.
    candidates.sort(key=lambda c: (c.box.cost, c.box.internal_volume_cm3))
    return candidates


def recommend_box(order: Order, persist: bool = True) -> BoxRecommendation:
    """Return the single best recommendation, optionally saving it on the order."""
    best = get_ranked_candidate_boxes(order)[0]
    if persist:
        order.recommended_box = best.box
        order.save(update_fields=["recommended_box"])
    return best
