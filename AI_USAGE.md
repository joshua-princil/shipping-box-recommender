# AI Usage Log

This document records how AI assistance was used to build the Shipping Box
Recommender, for transparency with anyone reviewing or extending this
codebase.

## Tool used

- **Claude** (Anthropic), used conversationally through a chat interface
  with access to a sandboxed Linux environment (for writing files, running
  `py_compile`, and packaging the project as a zip). No network/internet
  access was available in that sandbox — this matters for verification,
  see below.

## Workflow, prompt by prompt

1. **Initial prompt**: "Design and build a small Django-based system that
   recommends the most suitable box for an order" (ecommerce context:
   products have dimensions/weight, boxes have internal dimensions/max
   weight/cost).
   → AI produced the full project from scratch: `Product`/`Box`/`Order`/
   `OrderItem` models, a `services.py` recommendation algorithm, DRF
   serializers/views/urls, Django admin registration, a hand-written
   initial migration, a seed-data management command, a test suite, a
   `requirements.txt`, and a `README.md` explaining the algorithm's
   design rationale and limitations.

2. **"http://127.0.0.1:8000/ gives 404 error why?"** (with screenshot)
   → AI explained the root cause (no URL pattern registered for `/`,
   only `admin/` and `api/`) and offered a redirect fix, asking for
   confirmation before applying it.

3. **"why is this happening now then"** (screenshot of `/api/` also
   404ing)
   → AI identified this as the same root cause one level down — `/api/`
   itself wasn't registered, only paths under it (`/api/products/`,
   etc.) — and proposed two fixes (redirect to a real endpoint, or add
   a real root view), asking which was wanted.

4. **"i want the user to be able to navigate through the different urls
   when using http://127.0.0.1:8000/. Is your option B the apt one for
   that"**
   → AI confirmed Option B was appropriate and implemented it: a
   `boxes.views.api_root` view rendering DRF's browsable API, a `/`
   redirect to `/api/`, and hyperlinked `url` / `recommend_box_url`
   fields added to `OrderSerializer` so order records are clickable
   from the list view, not just the root.

5. **"do i have to reinstall shipping box recommender zip?"**
   → AI clarified only 4 files had changed and no dependency/database
   changes were needed — just overwrite those files and restart the
   dev server.

6. **"help me enter some sample data(inputs)"**
   → AI walked through running the existing `seed_demo_data` command,
   then creating a test order via the browsable API form and via curl,
   including a reference table of the seeded product SKUs/dimensions.

7. **"i want this program to be tested by anyone interested, so then how
   would one navigate through this program to try it out manually"**
   → AI added `TESTING.md`: a no-code walkthrough (setup → browse
   root → browse products/boxes → create an order → get a
   recommendation → a table of edge cases to try that should
   deliberately fail or upgrade the box choice → admin UI → what to do
   if something looks wrong), linked from the top of `README.md`.

8. **This prompt** — writing this log.

## Accepted outputs

All AI-authored code was accepted into the project as delivered, across
every round: models, service/recommendation logic, serializers, views,
urls, admin config, migration, seed command, tests, and both docs
(`README.md`, `TESTING.md`). Nothing was rewritten by hand outside of this
conversation.

## Rejected / revised outputs

Nothing the AI proposed was rejected outright, but two design choices were
narrowed down through back-and-forth rather than accepted on the first
suggestion:

- When `/` 404'd, the AI's first fix (a bare redirect to `api/`) was a
  reasonable patch but didn't solve the underlying want — it only moved
  the 404 one level down. The user's follow-up ("I want to navigate
  through different URLs") surfaced that a *real* browsable root, not
  just a redirect target, was the actual requirement — this led to
  Option B (an `api_root` view) being built instead of the simpler
  fix.

## Mistakes found (and how)

- **Two hand-written test cases initially had inconsistent fixture
  numbers.** While building the test suite, the AI's first draft of
  `test_weight_limit_forces_bigger_box` used an 8.0kg item, but the
  medium box's stated 10kg capacity meant that item actually *would*
  fit the medium box — contradicting the test's assertion that a large
  box was required. Similarly, `test_oversized_single_item_forces_larger_box_even_if_light`
  originally gave the "large" box a 50cm internal length, which was
  too short for the 56cm monitor used in the test, meaning *no* box
  would have satisfied the test as originally written. Both were
  **caught by the AI itself** during a self-review pass (manually
  tracing each test's expected outcome against the actual algorithm)
  before the project was ever handed over, and fixed by adjusting the
  fixture values (8.0kg → 12.0kg; large box length 50cm → 60cm).
- **Two 404 errors were caught by the user**, not the AI: the missing
  `/` and `/api/` root routes. The original project only exposed
  concrete resource paths (`/api/products/`, `/api/boxes/`, etc.) with
  nothing registered at the parent paths. This wasn't tested up front
  because the AI's own verification (see below) was limited to static
  checks, not a running server — a real gap in coverage that manual
  testing caught immediately.

## Verification steps taken

- **`python3 -m py_compile`** was run against every `.py` file in the
  project after each round of changes, catching syntax errors.
- **Manual trace-through** of each automated test case against the
  recommendation algorithm's logic (sorted-dimension fit check, weight
  check, volume × packing-efficiency check) to confirm the asserted
  box was actually the one the algorithm would pick, given the fixture
  data — this is how the two fixture mistakes above were caught.
- **What was *not* done**: the sandbox this was built in has no network
  access, so `pip install django djangorestframework` could not be run,
  and `python manage.py migrate` / `python manage.py test` /
  `python manage.py runserver` were never executed live. The project
  was verified statically only. This was disclosed in `README.md` from
  the first delivery, with an explicit ask for the user to run
  `python manage.py test` locally to confirm.
- **User-side verification**: running the actual dev server surfaced the
  two 404 routing gaps above, which static checks couldn't have caught
  and which the AI would not otherwise have found.

## Known limitations carried forward

- No live `manage.py test` run — recommended as the next verification
  step for anyone extending this project.
- The recommendation algorithm is a heuristic (weight + per-item fit +
  discounted volume), not true 3D bin-packing — documented in
  `README.md` along with a pointer to `py3dbp` if a future need
  requires genuine geometric packing verification.
