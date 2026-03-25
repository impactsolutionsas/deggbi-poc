from fastapi import APIRouter, Request, HTTPException, Query
from app.config import settings
from app.core.router import detect_content_type
from app.models.analysis import ContentType, Channel
from app.tasks.analysis import run_analysis
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Vérification du webhook Meta (étape d'activation)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook WhatsApp vérifié")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de vérification invalide")


@router.post("/webhook")
async def receive_message(request: Request):
    """Reçoit les messages WhatsApp et lance l'analyse async."""
    body = await request.json()

    try:
        # Extraction du message depuis la structure Meta
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}  # Notification sans message (read receipt, etc.)

        message = messages[0]
        sender_id = message.get("from")
        msg_type = message.get("type", "text")

        logger.info("Message WhatsApp reçu", sender=sender_id, type=msg_type)

        # Mapper le type WhatsApp vers ContentType
        content = None
        mime_type = None
        media_id = None

        if msg_type == "text":
            content = message.get("text", {}).get("body", "")
            content_type = ContentType.TEXT

        elif msg_type == "image":
            media_id = message.get("image", {}).get("id")
            mime_type = message.get("image", {}).get("mime_type", "image/jpeg")
            content_type = ContentType.IMAGE

        elif msg_type in ("audio", "voice"):
            media_id = message.get("audio", {}).get("id") or message.get("voice", {}).get("id")
            mime_type = "audio/ogg"
            content_type = ContentType.AUDIO

        else:
            content_type = ContentType.UNKNOWN

        # Accusé de réception immédiat
        await send_whatsapp_text(
            sender_id,
            "🔍 *DeggBi AI* reçoit votre contenu...\nAnalyse en cours, résultat dans quelques secondes."
        )

        # Lancer l'analyse en arrière-plan via Celery
        run_analysis.delay(
            content=content,
            media_id=media_id,
            content_type=content_type.value,
            channel=Channel.WHATSAPP.value,
            sender_id=sender_id,
            mime_type=mime_type,
        )

        return {"status": "ok"}

    except Exception as e:
        logger.error("Erreur webhook WhatsApp", error=str(e))
        return {"status": "ok"}  # Toujours 200 pour WhatsApp


async def send_whatsapp_text(to: str, message: str) -> dict:
    """Envoie un message texte WhatsApp."""
    import httpx

    url = f"https://graph.facebook.com/v20.0/{settings.whatsapp_phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
