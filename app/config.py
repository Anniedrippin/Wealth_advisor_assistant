import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY", None)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    CRM_BASE_URL: str = "http://localhost:8001"
    DATABASE_URL: str = "sqlite:///./wealth_advisor.db"

    MEMORY_ENABLED: bool = True
    ANOMALY_ZSCORE_THRESHOLD: float = 2.5
    SPENDING_SPIKE_THRESHOLD: float = 1.5
    CATEGORY_CONCENTRATION_THRESHOLD: float = 0.40

    HITL_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
