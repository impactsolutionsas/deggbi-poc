from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    secret_key: str = "changeme"
    debug: bool = True

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # Redis
    redis_url: str

    # WhatsApp
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_verify_token: str = "deggbi-verify-2026"

    # Telegram
    telegram_bot_token: str = ""

    # HuggingFace
    huggingface_api_key: str = ""

    # Google
    google_factcheck_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
