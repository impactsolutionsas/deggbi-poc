from supabase import create_client, Client
from app.config import settings
import structlog

logger = structlog.get_logger()

_supabase: Client | None = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
        logger.info("Supabase client initialisé")
    return _supabase


async def save_analysis(result: dict) -> dict:
    """Sauvegarde une analyse dans Supabase."""
    sb = get_supabase()
    response = sb.table("analyses").insert(result).execute()
    return response.data[0] if response.data else {}


async def get_analysis(analysis_id: str) -> dict | None:
    """Récupère une analyse par ID."""
    sb = get_supabase()
    response = (
        sb.table("analyses")
        .select("*")
        .eq("id", analysis_id)
        .single()
        .execute()
    )
    return response.data


async def get_recent_analyses(limit: int = 20) -> list:
    """Récupère les analyses récentes pour le dashboard."""
    sb = get_supabase()
    response = (
        sb.table("analyses")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


async def upload_media(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Upload un média dans Supabase Storage et retourne l'URL publique."""
    sb = get_supabase()
    path = f"inbox/{filename}"
    sb.storage.from_("media-inbox").upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    url = sb.storage.from_("media-inbox").get_public_url(path)
    return url
