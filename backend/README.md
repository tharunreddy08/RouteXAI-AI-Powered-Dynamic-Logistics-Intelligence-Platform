# RouteXAI — Backend 

AI-Powered Dynamic Logistics Intelligence Platform.

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
