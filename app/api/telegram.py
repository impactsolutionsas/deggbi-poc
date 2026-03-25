from fastapi import APIRouter, Request
from app.models.analysis import ContentType, Channel
from app.tasks.analysis import run_analysis
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.post("/webhook")
async def receive_update(request: Request):
    """Reçoit les mises à jour Telegram et lance l'analyse async."""
    body = await request.json()

    try:
        message = body.get("message", {})
        if not message:
            return {"status": "ok"}

        chat_id = str(message.get("chat", {}).get("id"))
        content = None
        media_id = None
        mime_type = None

        if "text" in message:
            content = message["text"]
            content_type = ContentType.TEXT

        elif "photo" in message:
            # Prendre la plus grande photo
            photo = message["photo"][-1]
            media_id = photo["file_id"]
            mime_type = "image/jpeg"
            content_type = ContentType.IMAGE

        elif "voice" in message or "audio" in message:
            audio = message.get("voice") or message.get("audio")
            media_id = audio["file_id"]
            mime_type = audio.get("mime_type", "audio/ogg")
            content_type = ContentType.AUDIO

        else:
            content_type = ContentType.UNKNOWN

        logger.info("Message Telegram reçu", chat_id=chat_id, type=content_type)

        # Accusé de réception
        await send_telegram_message(
            chat_id,
            "🔍 *DeggBi AI* — Analyse en cours...\nRésultat dans quelques secondes."
        )

        run_analysis.delay(
            content=content,
            media_id=media_id,
            content_type=content_type.value,
            channel=Channel.TELEGRAM.value,
            sender_id=chat_id,
            mime_type=mime_type,
        )

        return {"status": "ok"}

    except Exception as e:
        logger.error("Erreur webhook Telegram", error=str(e))
        return {"status": "ok"}


async def send_telegram_message(chat_id: str, text: str) -> None:
    import httpx
    from app.config import settings

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        })
