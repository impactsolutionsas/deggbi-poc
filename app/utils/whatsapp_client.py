"""
Client WhatsApp Business API — envoi de messages texte et médias.
"""
import httpx
import structlog
from app.config import settings

logger = structlog.get_logger()

GRAPH_API_URL = f"https://graph.facebook.com/v20.0/{settings.whatsapp_phone_id}/messages"


async def send_text(to: str, message: str) -> dict:
    """Envoie un message texte WhatsApp."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    return await _send(payload)


async def send_reaction(to: str, message_id: str, emoji: str) -> dict:
    """Envoie une réaction emoji à un message."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "reaction",
        "reaction": {"message_id": message_id, "emoji": emoji},
    }
    return await _send(payload)


async def mark_as_read(message_id: str) -> dict:
    """Marque un message comme lu."""
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    return await _send(payload)


async def _send(payload: dict) -> dict:
    """Envoi générique vers l'API WhatsApp."""
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(GRAPH_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("WhatsApp API error", status=e.response.status_code, body=e.response.text[:200])
        raise
    except Exception as e:
        logger.error("WhatsApp send failed", error=str(e))
        raise
