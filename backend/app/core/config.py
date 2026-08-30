import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Financial Risk Manager for UPI-like Digital Payments"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "murali-super-secret-risk-manager-jwt-key-2026-secure-random")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./financial_risk.db")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*"
    ]

    # Fund Manager / Escrow Cooling Period Rules
    COOLING_PERIOD_MINUTES: int = 30
    RELEASE_RISK_THRESHOLD: float = 40.0   # risk <= 40 -> auto release
    REFUND_RISK_THRESHOLD: float = 75.0    # risk >= 75 -> auto refund
    PERSONAL_RISK_HIGH_THRESHOLD: float = 70.0
    PAYEE_RISK_HIGH_THRESHOLD: float = 65.0
    OVERALL_RISK_HOLD_THRESHOLD: float = 70.0

    # Rate Limiting Baseline
    RATE_LIMIT_PER_MINUTE: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
