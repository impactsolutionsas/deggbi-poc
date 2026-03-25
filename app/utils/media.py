"""
Utilitaires média — téléchargement depuis WhatsApp/Telegram et upload vers Supabase Storage.
"""
import httpx
import structlog
from app.config import settings
from app.models.database import upload_media

logger = structlog.get_logger()

WHATSAPP_GRAPH_URL = "https://graph.facebook.com/v20.0"
TELEGRAM_API_URL = "https://api.telegram.org"


async def download_whatsapp_media(media_id: str) -> tuple[bytes, str]:
    """
    Télécharge un média WhatsApp en deux étapes :
    1. Récupère l'URL du média via l'API Graph
    2. Télécharge le fichier binaire

    Returns:
        (file_bytes, mime_type)

    Raises:
        httpx.HTTPStatusError si l'API échoue
    """
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        # Étape 1 : obtenir l'URL de téléchargement
        meta_resp = await client.get(
            f"{WHATSAPP_GRAPH_URL}/{media_id}",
            headers=headers,
        )
        meta_resp.raise_for_status()
        meta = meta_resp.json()
        download_url = meta["url"]
        mime_type = meta.get("mime_type", "application/octet-stream")

        # Étape 2 : télécharger le fichier
        file_resp = await client.get(download_url, headers=headers)
        file_resp.raise_for_status()

    logger.info("Média WhatsApp téléchargé", media_id=media_id, size=len(file_resp.content))
    return file_resp.content, mime_type


async def download_telegram_media(file_id: str) -> tuple[bytes, str]:
    """
    Télécharge un média Telegram en deux étapes :
    1. getFile pour obtenir le file_path
    2. Téléchargement via le CDN Telegram

    Returns:
        (file_bytes, mime_type)
    """
    token = settings.telegram_bot_token

    async with httpx.AsyncClient(timeout=30) as client:
        # Étape 1 : obtenir le file_path
        info_resp = await client.get(
            f"{TELEGRAM_API_URL}/bot{token}/getFile",
            params={"file_id": file_id},
        )
        info_resp.raise_for_status()
        result = info_resp.json().get("result", {})
        file_path = result.get("file_path", "")

        if not file_path:
            raise ValueError(f"Telegram n'a pas retourné de file_path pour {file_id}")

        # Étape 2 : télécharger
        file_resp = await client.get(
            f"{TELEGRAM_API_URL}/file/bot{token}/{file_path}",
        )
        file_resp.raise_for_status()

    # Deviner le mime_type à partir de l'extension
    mime_type = _guess_mime(file_path)
    logger.info("Média Telegram téléchargé", file_id=file_id, size=len(file_resp.content))
    return file_resp.content, mime_type


async def download_and_store(
    media_id: str,
    channel: str,
    analysis_id: str,
    mime_type: str | None = None,
) -> str:
    """
    Télécharge un média depuis le canal source et l'upload dans Supabase Storage.

    Returns:
        URL publique du fichier dans Supabase Storage
    """
    if channel == "whatsapp":
        file_bytes, detected_mime = await download_whatsapp_media(media_id)
    elif channel == "telegram":
        file_bytes, detected_mime = await download_telegram_media(media_id)
    else:
        raise ValueError(f"Canal non supporté pour le téléchargement : {channel}")

    final_mime = mime_type or detected_mime
    ext = _mime_to_ext(final_mime)
    filename = f"{analysis_id}.{ext}"

    url = await upload_media(file_bytes, filename, final_mime)
    logger.info("Média stocké dans Supabase", analysis_id=analysis_id, url=url)
    return url


def _guess_mime(file_path: str) -> str:
    ext_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".ogg": "audio/ogg",
        ".oga": "audio/ogg",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".mp4": "video/mp4",
    }
    for ext, mime in ext_map.items():
        if file_path.lower().endswith(ext):
            return mime
    return "application/octet-stream"


def _mime_to_ext(mime_type: str) -> str:
    mime_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "audio/ogg": "ogg",
        "audio/mpeg": "mp3",
        "audio/wav": "wav",
        "audio/mp4": "m4a",
        "video/mp4": "mp4",
    }
    return mime_map.get(mime_type, "bin")
