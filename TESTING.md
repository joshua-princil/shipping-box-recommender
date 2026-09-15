# Trying it out manually

This is a walkthrough for anyone who wants to click through the app without
reading the code first. No prior Django knowledge needed — everything here
happens in a web browser.

## 1. Get it running

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo_data   # loads sample products & boxes
python manage.py runserver
```

Leave that running, then open **http://127.0.0.1:8000/** in a browser.

## 2. Start at the root

You'll land on a page titled "Api Root" with a JSON-looking body and three
links: `products`, `boxes`, `orders`. This is DRF's **browsable API** —
every page from here on is both a normal webpage *and* the raw API
response, so clicking around is a legitimate way to explore the whole
system.

Click **`orders`**.

## 3. Look at what's already there

`/api/orders/` starts empty (the seed command only loads products and
boxes, not orders — that's the thing you're about to test). Click
**`products`** in the top nav instead and you'll see the 5 seeded items
with their dimensions and weight. Click **`boxes`** to see the 5 box
sizes, their capacity, and cost. This is the raw material the
recommendation engine works from.

## 4. Create an order

Go back to `/api/orders/`. Scroll to the bottom — there's an HTML form
titled "OrderSerializer" with fields for `order_number`, `customer_name`,
and `item_inputs`.

Fill it in:
- **order_number**: `TEST-001`
- **customer_name**: your name (optional)
- **item_inputs**: paste this exactly, including the brackets:
  ```json
  [{"sku": "MUG-001", "quantity": 2}, {"sku": "BOOK-014", "quantity": 1}]
  ```

Click **POST**. You should get redirected to the new order's detail page,
showing the two line items you just added.

## 5. Get a box recommendation

On that order's detail page (or back on the `/api/orders/` list) you'll
see a `recommend_box_url` link. Click it.

You'll get back the recommended box, its cost, and two utilization
percentages — how much of the box's weight and volume capacity this order
actually uses. Add `?all=true` to the end of that URL to see *every* box
that could have worked, cheapest first, instead of just the top pick.

## 6. Try to break it

The interesting part isn't the happy path — it's watching the system
correctly refuse or upgrade:

| Try this order... | ...and you should see |
|---|---|
| Just `MONITOR-24` x1 | A large box gets recommended — it's too big for the small/medium boxes even though it's light |
| `LAMP-007` x10 | Either a much bigger box, or (if you seed enough of them) a "no box fits" error — total weight/volume outgrows even the XL box |
| An order with `item_inputs: []` | A 422 error: "Order has no line items" |
| A SKU that doesn't exist, e.g. `sku: "FAKE-999"` | A validation error when you try to POST, before an order is even created |

Each of these is intentional — the point of the recommend-box endpoint is
to tell the warehouse team *no* clearly when nothing fits, rather than
silently picking something too small.

## 7. Optional: the admin UI

If you'd rather add/edit products and boxes with a spreadsheet-like grid
instead of JSON forms:

```bash
python manage.py createsuperuser
```

Then visit **http://127.0.0.1:8000/admin/** and log in. You can add
products, boxes, and orders (with inline order-item rows) there too — it's
the same underlying data as the API.

## 8. If something looks wrong

Run the automated test suite to check whether it's your data/setup or an
actual bug in the recommendation logic:

```bash
python manage.py test
```

If tests pass but a specific order still looks off, the most useful thing
to report is: the order's line items (SKU + quantity), which box got
recommended, and which box you expected instead.
