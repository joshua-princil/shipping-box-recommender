# Shipping Box Recommender

A small Django + Django REST Framework service that recommends the cheapest
shipping box that can physically hold a given order.

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # optional, for the admin UI
python manage.py seed_demo_data   # optional, loads sample products & boxes
python manage.py runserver
```

Run the test suite:

```bash
python manage.py test
```

> Note: this project was written and syntax-checked in an offline sandbox
> without network access to install Django, so `manage.py test` has not
> been executed live — but every file passed `py_compile`, the models/
> migration are hand-verified to match, and the test suite below covers
> the recommendation logic's key branches. Run it locally to confirm.

**Want to just click around and try it out?** See [TESTING.md](TESTING.md)
for a no-code-required walkthrough — good for sharing with anyone who
wants to test the app manually without reading the source.

## Data model

- **Product** — SKU, name, `length_cm` / `width_cm` / `height_cm`, `weight_kg`.
- **Box** — code, name, internal dimensions, `max_weight_kg`, `cost`, `is_active`.
- **Order** — order number, customer name, `recommended_box` (filled in once
  a recommendation is generated and persisted).
- **OrderItem** — order + product + quantity.

All dimensions are centimeters, all weights are kilograms — one consistent
unit system everywhere to avoid conversion bugs.

## The recommendation algorithm (`boxes/services.py`)

True 3D bin-packing — figuring out whether a specific set of items can be
physically arranged inside a container — is NP-hard and unnecessary
complexity for most ecommerce catalogs. Instead, a candidate box must pass
three fast, explainable checks:

1. **Weight** — total order weight ≤ the box's `max_weight_kg`.
2. **Individual item fit** — *every single product* must fit inside the box
   on its own, comparing each item's dimensions sorted ascending against the
   box's dimensions sorted ascending (so a 40×10×10 item still fits a
   15×15×45 box — rotation is allowed, but nothing assumes clever stacking).
   This stops the algorithm from approving a box that's big enough in total
   volume but too short for one oversized item.
3. **Volume** — total item volume ≤ the box's internal volume × a
   configurable `BOX_PACKING_EFFICIENCY` (default `0.85`, set in
   `settings.py`). Real packing never hits 100% density — there are always
   gaps between items, irregular shapes, and padding — so this discount
   keeps the system from recommending boxes that look fine on paper but
   don't work in practice.

Among all boxes that pass, the **cheapest** is recommended; ties are broken
by the smallest box (no reason to ship bigger than necessary for the same
price). `get_ranked_candidate_boxes()` returns the full ranked list, which
the API exposes via `?all=true` so warehouse staff can see alternatives —
useful if, say, the recommended box size is temporarily out of stock.

If you outgrow this heuristic — e.g. irregular/fragile items where stacking
order and orientation genuinely matter — swap the internals of
`get_ranked_candidate_boxes` for a call into a real bin-packing library like
`py3dbp`, keeping the same function signature so nothing else has to change.

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Redirects to `/api/` |
| GET | `/api/` | Browsable API root — links to every resource below |
| GET/POST | `/api/products/` | List / create products |
| GET/POST | `/api/boxes/` | List / create boxes |
| GET/POST | `/api/orders/` | List / create orders |
| GET | `/api/orders/<id>/` | Order detail |
| GET | `/api/orders/<id>/recommend-box/` | Best box recommendation (saved on the order) |
| GET | `/api/orders/<id>/recommend-box/?all=true` | Every viable box, cheapest first |

Open `http://127.0.0.1:8000/` in a browser (not curl) and you land on DRF's
**browsable API**: an interactive HTML page with clickable links into each
resource, forms for POSTing new products/boxes/orders, and — on each order
in `/api/orders/` — a link straight to that order's `recommend-box`
endpoint. curl/Postman/etc. still get plain JSON back; the HTML rendering
only kicks in for requests a browser makes.

### Create an order

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
        "order_number": "ORD-1001",
        "customer_name": "Priya Rao",
        "item_inputs": [
          {"sku": "MUG-001", "quantity": 2},
          {"sku": "BOOK-014", "quantity": 1}
        ]
      }'
```

### Get a recommendation

```bash
curl http://localhost:8000/api/orders/1/recommend-box/
```

```json
{
  "order": "ORD-1001",
  "recommendation": {
    "box": {"id": 2, "code": "SM", "name": "Small Box", "cost": "1.80", ...},
    "total_weight_kg": "1.000",
    "total_volume_cm3": "2598.00",
    "weight_utilization_pct": "20.0",
    "volume_utilization_pct": "34.6"
  }
}
```

If nothing fits (e.g. an oversized or overweight item), the endpoint returns
HTTP 422 with an explanatory message and the computed totals, rather than
silently guessing.

## Extending this

- **Multiple boxes per order** — currently the system assumes one order
  ships in one box. Splitting an order across multiple boxes (a proper
  multi-container bin-packing problem) would need a different algorithm —
  a good next step if average order size grows.
- **Per-warehouse box inventory** — add a `Warehouse` FK to `Box` and filter
  candidates by warehouse stock on hand.
- **Fragility / stacking rules** — add a `max_stack_weight_kg` or
  `is_fragile` flag on `Product` and factor it into the fit check.
