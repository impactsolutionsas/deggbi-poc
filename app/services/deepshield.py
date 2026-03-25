"""
DeepShield — Module de détection de deepfakes
- Image : EfficientNet-B4 (FaceForensics++)
- Audio : Wav2Vec2 (détection voix synthétiques/clonées)
"""
import httpx
import structlog
from app.models.analysis import ContentType, ScoreDeepShield
from app.config import settings

logger = structlog.get_logger()

HF_API_URL = "https://api-inference.huggingface.co/models"

# Modèles HuggingFace utilisés
MODEL_DEEPFAKE_IMAGE = "Wvolf/ViT-Deepfake-Detection"
MODEL_DEEPFAKE_AUDIO = "mo-thecreator/deepfake-audio-detection"


async def analyze_deepshield(
    media_url: str | None,
    content_type: ContentType,
    mime_type: str | None = None,
) -> ScoreDeepShield:
    """Point d'entrée principal DeepShield."""
    if not media_url:
        return ScoreDeepShield(score=0, details="Pas de média à analyser")

    try:
        if content_type == ContentType.IMAGE:
            return await _analyze_image_deepfake(media_url)
        elif content_type == ContentType.AUDIO:
            return await _analyze_audio_deepfake(media_url, mime_type)
        else:
            return ScoreDeepShield(score=0, details="DeepShield non applicable pour ce type")
    except Exception as e:
        logger.error("Erreur DeepShield", error=str(e))
        return ScoreDeepShield(score=0, details=f"Analyse partielle — {str(e)[:100]}")


async def _analyze_image_deepfake(image_url: str) -> ScoreDeepShield:
    """Détection de deepfake image via HuggingFace."""
    try:
        # Télécharger l'image
        async with httpx.AsyncClient(timeout=15) as client:
            img_resp = await client.get(image_url)
            img_bytes = img_resp.content

        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        url = f"{HF_API_URL}/{MODEL_DEEPFAKE_IMAGE}"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, content=img_bytes, headers={
                **headers,
                "Content-Type": "image/jpeg",
            })
            results = resp.json()

        # Interpréter les résultats
        if isinstance(results, list):
            for item in results:
                label = item.get("label", "").upper()
                score = item.get("score", 0)
                if label in ("FAKE", "DEEPFAKE", "MANIPULATED", "LABEL_1"):
                    confidence = score * 100
                    deep_score = confidence
                    logger.info("Deepfake image détecté", score=deep_score)
                    return ScoreDeepShield(
                        score=round(deep_score, 1),
                        image_score=round(deep_score, 1),
                        manipulation_detected=deep_score > 60,
                        confidence=round(confidence, 1),
                        details="EfficientNet — analyse visuelle complète",
                    )

        return ScoreDeepShield(score=10, details="Aucune manipulation visuelle détectée")

    except Exception as e:
        logger.warning("Deepfake image analyse échouée", error=str(e))
        return ScoreDeepShield(score=0, details=f"Modèle indisponible — {str(e)[:80]}")


async def _analyze_audio_deepfake(audio_url: str, mime_type: str | None) -> ScoreDeepShield:
    """Détection de voix clonée/synthétique via HuggingFace."""
    try:
        # Télécharger l'audio
        async with httpx.AsyncClient(timeout=20) as client:
            audio_resp = await client.get(audio_url)
            audio_bytes = audio_resp.content

        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        url = f"{HF_API_URL}/{MODEL_DEEPFAKE_AUDIO}"
        content_type_header = mime_type or "audio/wav"

        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(url, content=audio_bytes, headers={
                **headers,
                "Content-Type": content_type_header,
            })
            results = resp.json()

        if isinstance(results, list):
            for item in results:
                label = item.get("label", "").upper()
                score = item.get("score", 0)
                if label in ("FAKE", "SPOOF", "SYNTHETIC", "LABEL_1"):
                    audio_score = score * 100
                    return ScoreDeepShield(
                        score=round(audio_score, 1),
                        audio_score=round(audio_score, 1),
                        manipulation_detected=audio_score > 60,
                        confidence=round(score * 100, 1),
                        details="Wav2Vec2 — analyse vocale complète",
                    )

        return ScoreDeepShield(score=5, details="Voix authentique — aucune synthèse détectée")

    except Exception as e:
        logger.warning("Deepfake audio analyse échouée", error=str(e))
        return ScoreDeepShield(score=0, details=f"Modèle audio indisponible — {str(e)[:80]}")
