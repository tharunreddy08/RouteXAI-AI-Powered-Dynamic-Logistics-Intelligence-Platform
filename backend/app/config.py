"""
RouteXAI backend configuration.

All secrets/config are read from environment variables (see .env.example).
Nothing is hardcoded. If DATABASE_URL is not set, the app falls back to a
local SQLite database so the project can run immediately in demo mode.
"""
import os
from functools import lru_cache


class Settings:
    # --- General ---
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PROJECT_NAME: str = "RouteXAI"

    # --- Database ---
    # Preferred: PostgreSQL, e.g. postgresql://user:pass@localhost:5432/routexai
    # Fallback: SQLite file, used automatically if DATABASE_URL is unset.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./routexai.db")

    # --- Auth ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")
    )

    # --- Optional external services (app must work without these) ---
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    MAP_API_KEY: str = os.getenv("MAP_API_KEY", "")

    # --- CORS ---
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    def __init__(self) -> None:
        if not self.JWT_SECRET:
            if self.ENVIRONMENT == "production":
                raise RuntimeError(
                    "JWT_SECRET must be set via environment variable in production."
                )
            # Dev/demo-only fallback so the app boots without a .env file.
            # This is NEVER safe for production and is clearly labeled as such.
            self.JWT_SECRET = "dev-only-insecure-secret-change-me"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
