from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    google_cloud_project: str = "fynura-public-health"
    google_cloud_location: str = "us-central1"
    google_genai_use_vertexai: bool = True
    fynura_env: str = "development"
    fynura_model: str = "gemini-2.5-flash"
    fynura_use_firestore: bool = False
    fynura_live_fetch: bool = True
    fynura_onboarding_required: bool = False
    fynura_privacy_notice_version: str = "2026-08-29"
    fynura_owner_email: str | None = None
    fynura_firebase_api_key: str | None = None
    fynura_auth_domain: str = "fynura-public-health.firebaseapp.com"
    fynura_session_days: int = 5
    request_timeout_seconds: float = 20.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
