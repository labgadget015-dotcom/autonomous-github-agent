# Configuration Management
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration with environment variable support"""

    # Core
    APP_NAME: str = "Revenue Autonomy Engine"
    DEBUG: bool = False
    ENV: str = "production"

    # Database
    DATABASE_URL: str = "sqlite:///revenue.db"
    DATABASE_ECHO: bool = False

    # Stripe
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or standard
    LOG_FILE: Optional[str] = "logs/revenue_engine.log"

    # API Configuration
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 2.0

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    REVENUE_SYNC_INTERVAL_MINUTES: int = 5
    RECONCILIATION_INTERVAL_HOURS: int = 1
    FORECAST_INTERVAL_HOURS: int = 24

    # Analytics
    ANOMALY_THRESHOLD_SIGMA: float = 3.0
    MIN_HISTORICAL_DAYS: int = 30
    FORECAST_DAYS_AHEAD: int = 90

    # Webhook
    WEBHOOK_PORT: int = 8000
    WEBHOOK_HOST: str = "0.0.0.0"

    # Alerts
    ENABLE_ALERTS: bool = True
    ALERT_EMAIL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


if __name__ == "__main__":
    settings = get_settings()
    print(f"Configuration: {settings.model_dump()}")
