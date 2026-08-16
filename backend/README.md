# RouteXAI — Backend (Phase 1 + 2 + 3 + 4)

AI-Powered Dynamic Logistics Intelligence Platform.

This covers **Phase 1 (Backend Foundation)**, **Phase 2 (Core Logistics)**,
**Phase 3 (AI)**, and **Phase 4 (Hardware)** of the full RouteXAI build. It
is a real, working FastAPI service — not a mock — with a live database, JWT
authentication, role-based authorization, seed data, a genuine
OR-Tools/K-Means/A* optimization engine, a trained XGBoost ETA model with a
working retraining feedback loop, and hardware-triggered single-vehicle
rerouting. Later phases (analytics and the frontend) build on top of this
without breaking anything here.

## What's included so far

**Phase 1 — Foundation**
- FastAPI backend with clean `app/` structure (`models/`, `schemas/`,
  `routers/`, `services/`, `optimization/`, `ml/`, `analytics/`, `hardware/`,
  `utils/` — later phases fill in the still-empty ones)
- SQLAlchemy models for all core tables: `users`, `vehicles`, `orders`,
  `routes`, `rider_performance`, `route_history`, `emission_reports`,
  `hardware_events`
- PostgreSQL support via `DATABASE_URL`, with automatic SQLite fallback for
  local/demo use
- JWT authentication (`/auth/register`, `/auth/login`, `/auth/me`)
- Role-based authorization (Admin / Dispatcher / Rider) via reusable FastAPI
  dependencies (`require_admin`, `require_dispatcher`, `require_rider`)
- Seed script with realistic demo data
- Swagger / OpenAPI docs at `/docs`

**Phase 2 — Core Logistics** (new)
- Manual Order Entry: `POST /orders/manual` — supports "Add Order" and
  "Save & Optimize" (`optimize: true/false`)
- CSV/JSON bulk upload: `POST /orders/upload` — accepts partial-failure
  batches (bad rows are reported, good rows still get created)
- Full order CRUD: `POST/PUT/DELETE /orders/{id}`
- Full vehicle CRUD: `POST/PUT/DELETE /fleet/vehicles/{id}`
- **K-Means clustering** (`app/optimization/clustering.py`) — dynamically
  sized by order volume, vehicle count, and average max-stops, so the
  optimizer scales toward 1000+ orders without one massive VRP solve
- **OR-Tools VRPTW solver** (`app/optimization/vrptw.py`) — respects vehicle
  capacity, max stops, and delivery time windows, with priority-weighted
  drop penalties so Emergency > Express > Normal orders are served first
  when the fleet can't cover everything
- **A\* shortest-path search** (`app/optimization/astar.py`) — real
  priority-queue graph search with a haversine heuristic, with obstacle
  avoidance support (used for hardware rerouting in Phase 4)
- `POST /routes/optimize` — runs the full clustering → VRPTW pipeline,
  persists `Route` rows, and updates order/vehicle state
- `POST /routes/recalculate` — re-optimizes a single vehicle's active orders
- All new endpoints tested with real OR-Tools solves (not mocks) —
  see `tests/test_optimization.py`

**Phase 3 — AI** (new)
- XGBoost regression model for ETA prediction (`app/ml/eta_model.py`),
  trained on `RouteHistory` (distance, traffic mode, hour of day, day of
  week, stop count, per-vehicle historical delay, vehicle mileage)
- `GET /ml/eta` — predicts ETA (minutes), expected delay, and a genuine
  confidence percentage derived from held-out validation error — not a
  hardcoded number
- `POST /route-history` — records a completed delivery's actual outcome
  (predicted vs. actual ETA) and triggers model retraining, implementing
  the feedback loop end to end
- `GET /ml/status` — current model state, sample count, and the ML/
  optimization/shortest-path algorithm names for the (Phase 6) ML Insights
  panel
- Transparent heuristic fallback when too little history exists yet
  (clearly labeled `"model": "heuristic-fallback"` in the response, with a
  lower confidence score, rather than pretending it's a trained prediction)
- Route optimization (`POST /routes/optimize`) now uses the trained ETA
  model for each route's `eta` field once enough data exists
- Verified live: retrained the model via a real `/route-history` POST call
  and confirmed the sample count, MAE, and confidence all updated
- See `tests/test_ml.py` for training/prediction/fallback tests

**Honesty note on "self-learning"**: this is real, verifiable incremental
*batch* retraining — each `POST /route-history` call (or the seed script)
retrains a fresh model on the full accumulated history and the confidence
score is recomputed from actual held-out error. It is **not** continuous/
online learning, and nothing in the API or docs claims otherwise, per spec
section 13.

**Phase 4 — Hardware** (new)
- `POST /hardware/block/{vehicle_id}` — simulates a `BLOCK_DETECTED`
  ultrasonic-sensor signal. Logs a `HardwareEvent`, marks the vehicle
  `Blocked`, then uses the A* module (built in Phase 2) to find a path
  around the obstacle from the vehicle's current position to its next
  stop, splices that detour into the vehicle's existing `Route`, and
  recalculates ETA (via the ML model), fuel, and CO2 — **for that vehicle
  only**
- `POST /hardware/clear/{vehicle_id}` — logs `BLOCK_CLEARED`, resolves the
  open block event, reactivates the vehicle, and re-optimizes its
  remaining stops now that the obstacle is gone
- `GET /hardware/events` — full event log
- **Verified live and in tests that every other vehicle's route is
  byte-for-byte unchanged** when one vehicle is blocked — `tests/test_hardware.py`
  asserts this directly (`route_b.route_points == original_b_points`), and
  a live smoke test confirmed the same: blocking Van-04 changed its route
  and Van-02's route stayed at exactly the same distance
- Original delivery stops are never dropped by a reroute — only detour
  waypoints (flagged `"detour": true`, no `order_id`) are added ahead of
  the untouched stop sequence
- `/routes/recalculate` was also updated to only ever touch the one vehicle
  it's asked about, matching the hardware endpoints' guarantee
- `GET /riders/performance` was added (was missing from Phase 1-4) to
  support the Phase 5 frontend's Rider Performance leaderboard

## What's NOT in yet (coming in later phases)

- Frontend dashboards, fleet map, manual order entry UI (Phase 5)
- Analytics (daily/weekly/monthly/yearly), ML insights panel UI, report export (Phase 6)
- Order status 15-minute auto-sync job

## Project structure

```text
backend/
├── app/
│   ├── main.py               # FastAPI app, router registration
│   ├── config.py             # env-driven settings
│   ├── database.py           # SQLAlchemy engine/session (Postgres or SQLite)
│   ├── models/                # SQLAlchemy models (all 8 core tables)
│   ├── schemas/                # Pydantic request/response schemas
│   ├── routers/                 # auth, fleet, orders, routes
│   ├── services/
│   │   ├── optimization_service.py  # orchestrates clustering -> VRPTW -> persistence
│   │   └── order_ingestion.py       # CSV/JSON parsing for uploads
│   ├── optimization/
│   │   ├── distance.py        # haversine + road-distance estimation
│   │   ├── clustering.py      # K-Means preprocessing
│   │   ├── vrptw.py           # OR-Tools VRPTW solver
│   │   └── astar.py           # A* shortest-path search
│   ├── ml/
│   │   ├── features.py         # shared feature vector definition
│   │   └── eta_model.py        # XGBoost training + prediction + persistence
│   ├── hardware/
│   │   └── rerouting_service.py  # BLOCK_DETECTED/BLOCK_CLEARED -> A* reroute
│   ├── analytics/             # (Phase 6)
│   └── utils/                 # security (hashing/JWT), auth dependencies
├── migrations/
├── seed/
│   └── seed_data.py           # idempotent demo data seeder
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_optimization.py
│   ├── test_ml.py
│   └── test_hardware.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # edit if you want Postgres / a real JWT secret

python -m seed.seed_data         # creates routexai.db (SQLite) and seeds demo data

uvicorn app.main:app --reload --port 8000
```

Then open:
- API root: http://localhost:8000/
- Swagger docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## Using PostgreSQL instead of SQLite

Set `DATABASE_URL` in `.env`, e.g.:

```text
DATABASE_URL=postgresql://routexai:routexai@localhost:5432/routexai
```

No code changes needed — SQLAlchemy handles both.

## Demo credentials (created by the seed script)

| Role       | Email                     | Password      |
|------------|----------------------------|---------------|
| Admin      | admin@routexai.com         | Admin@123     |
| Dispatcher | dispatcher@routexai.com    | Dispatch@123  |
| Rider      | rider1@routexai.com        | Rider@123     |
| Rider      | rider2@routexai.com ... rider5@routexai.com | Rider@123 |

## Sample API requests

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com","password":"SecurePass123","role":"dispatcher"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@routexai.com","password":"Admin@123"}'
```

**Authenticated request:**
```bash
curl http://localhost:8000/orders \
  -H "Authorization: Bearer <access_token>"
```

**Manual order entry (Save & Optimize):**
```bash
curl -X POST http://localhost:8000/orders/manual \
  -H "Authorization: Bearer <dispatcher_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "order": {
          "customer_name": "Jane Doe",
          "address": "MG Road, Bengaluru",
          "latitude": 12.9750,
          "longitude": 77.6050,
          "priority": "Emergency",
          "package_weight": 2.0
        },
        "optimize": true
      }'
```

**CSV/JSON upload:**
```bash
curl -X POST http://localhost:8000/orders/upload \
  -H "Authorization: Bearer <dispatcher_token>" \
  -F "file=@orders.csv"
```

**Trigger route optimization (K-Means -> OR-Tools VRPTW):**
```bash
curl -X POST http://localhost:8000/routes/optimize \
  -H "Authorization: Bearer <dispatcher_token>" \
  -H "Content-Type: application/json" \
  -d '{"traffic_mode": "Normal"}'
```

**Predict ETA (ML):**
```bash
curl "http://localhost:8000/ml/eta?distance_km=12.5&traffic_mode=Heavy&num_stops=4" \
  -H "Authorization: Bearer <token>"
```

**Record a completed delivery (feeds the self-learning feedback loop):**
```bash
curl -X POST http://localhost:8000/route-history \
  -H "Authorization: Bearer <dispatcher_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "vehicle_id": 1,
        "distance": 18.2,
        "eta_predicted": 45.0,
        "eta_actual": 52.0,
        "traffic_mode": "Heavy",
        "fuel_consumption": 1.4,
        "co2_emissions": 3.75
      }'
```

## Running tests

```bash
python -m pytest tests/ -v
```

## Docker

```bash
docker build -t routexai-backend .
docker run -p 8000:8000 --env-file .env routexai-backend
```

(A full `docker-compose.yml` with Postgres + frontend will be added once the
frontend and optimization services exist.)

## Environment variables

See `.env.example`. `JWT_SECRET` must be set explicitly in production — the
app will refuse to start with `ENVIRONMENT=production` and no secret set. In
development it falls back to an insecure default so it boots without setup,
which is clearly not safe for real deployments.

## Security notes (Phase 1)

- Passwords are hashed with bcrypt (via passlib), never stored in plain text.
- JWT tokens carry `sub` (user id) and `role`, expire after
  `ACCESS_TOKEN_EXPIRE_MINUTES` (default 8 hours).
- All non-auth endpoints in this phase require a valid bearer token.
- SQL access goes through the SQLAlchemy ORM (no raw string-built queries).
- No secrets are hardcoded; everything comes from environment variables.

## Notes on the optimization engine

- **Depot location**: fixed at Bengaluru MG Road (12.9716, 77.5946) to match
  the seed data's geography — update `DEPOT` in
  `app/services/optimization_service.py` for a different service area.
- **Road distance estimate**: no live routing API is wired up yet, so travel
  distance is haversine (straight-line) distance scaled by a 1.3x
  road-detour factor — a standard approximation, not literal road distance.
  This is clearly documented in `app/optimization/distance.py`.
- **Priority weighting**: implemented as OR-Tools drop penalties
  (Emergency=100,000, Express=25,000, Normal=5,000) so the solver only
  leaves a high-priority order unserved as an absolute last resort.
- **A\*** is fully implemented and tested now (`app/optimization/astar.py`)
  but isn't wired into a live endpoint yet — that happens in Phase 4 when a
  `BLOCK_DETECTED` hardware event triggers single-vehicle rerouting.

**Trigger a hardware block (single-vehicle reroute):**
```bash
curl -X POST http://localhost:8000/hardware/block/2 \
  -H "Authorization: Bearer <dispatcher_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```
Omit `latitude`/`longitude` to simulate the obstacle at the vehicle's current
position, or pass them to simulate a block further along the route.

**Clear a hardware block:**
```bash
curl -X POST http://localhost:8000/hardware/clear/2 \
  -H "Authorization: Bearer <dispatcher_token>"
```

## Next phase

**Phase 5 — Frontend**: React + Vite + TypeScript + Tailwind + Leaflet
dashboards (Admin/Dispatcher/Rider), the fleet map with animated multi-van
routing, Manual Order Entry UI, and the Hardware Demo page — wired up to
everything built in Phases 1-4.
