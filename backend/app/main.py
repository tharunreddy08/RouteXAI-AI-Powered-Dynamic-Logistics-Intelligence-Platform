from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401  (registers all models on Base.metadata)
from app.routers import auth, fleet, orders, routes, ml_routes, hardware, riders
from seed.seed_data import seed

# Create tables if they don't exist yet (safe/idempotent — will not drop or
# alter existing tables, so existing data is preserved between restarts).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RouteXAI API",
    description="AI-Powered Dynamic Logistics Intelligence Platform — backend API.",
    version="0.4.0-phase4",
)

# Seed the database on startup if empty
@app.on_event("startup")
def startup_event():
    try:
        seed()
    except Exception as e:
        print(f"Warning: Could not seed database on startup: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(fleet.router)
app.include_router(orders.router)
app.include_router(routes.router)
app.include_router(ml_routes.router)
app.include_router(hardware.router)
app.include_router(riders.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "RouteXAI API",
        "status": "ok",
        "phase": "Phase 4 — Hardware Rerouting",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
