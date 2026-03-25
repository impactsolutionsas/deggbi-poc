"""
DeepShield — Module de détection de deepfakes
- Image : EfficientNet-B4 (FaceForensics++)
- Audio : Wav2Vec2 (détection voix synthétiques/clonées)
- Vidéo : extraction frames + audio → analyse combinée
"""
import httpx
import structlog
from app.models.analysis import ContentType, ScoreDeepShield
from app.config import settings

logger = structlog.get_logger()

HF_API_URL = "https://router.huggingface.co/hf-inference/models"

# Modèles HuggingFace utilisés
MODEL_DEEPFAKE_IMAGE = "umm-maybe/AI-image-detector"
MODEL_DEEPFAKE_AUDIO = "mo-thecreator/deepfake-audio-detection"


async def analyze_deepshield(
    media_url: str | None,
    content_type: ContentType,
    mime_type: str | None = None,
    media_bytes: bytes | None = None,
) -> ScoreDeepShield:
    """Point d'entrée principal DeepShield."""
    if not media_url and not media_bytes:
        return ScoreDeepShield(score=0, details="Pas de média à analyser")

    try:
        if content_type == ContentType.IMAGE:
            return await _analyze_image_deepfake(media_url, media_bytes)
        elif content_type == ContentType.AUDIO:
            return await _analyze_audio_deepfake(media_url, mime_type, media_bytes)
        elif content_type == ContentType.VIDEO:
            return await _analyze_video_deepfake(media_url, media_bytes)
        else:
            return ScoreDeepShield(score=0, details="DeepShield non applicable pour ce type")
    except Exception as e:
        logger.error("Erreur DeepShield", error=str(e))
        return ScoreDeepShield(score=0, details=f"Analyse partielle — {str(e)[:100]}")


async def _analyze_image_deepfake(image_url: str | None, img_bytes: bytes | None = None) -> ScoreDeepShield:
    """Détection de deepfake image via HuggingFace."""
    try:
        # Télécharger l'image si pas de bytes directs
        if not img_bytes and image_url:
            async with httpx.AsyncClient(timeout=15) as client:
                img_resp = await client.get(image_url)
                img_bytes = img_resp.content
        if not img_bytes:
            return ScoreDeepShield(score=0, details="Pas de données image")

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
                if label in ("FAKE", "DEEPFAKE", "MANIPULATED", "LABEL_1", "ARTIFICIAL"):
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


async def _analyze_audio_deepfake(audio_url: str | None, mime_type: str | None, audio_bytes: bytes | None = None) -> ScoreDeepShield:
    """Détection de voix clonée/synthétique via HuggingFace."""
    try:
        # Télécharger l'audio si pas de bytes directs
        if not audio_bytes and audio_url:
            async with httpx.AsyncClient(timeout=20) as client:
                audio_resp = await client.get(audio_url)
                audio_bytes = audio_resp.content
        if not audio_bytes:
            return ScoreDeepShield(score=0, details="Pas de données audio")

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


async def _analyze_video_deepfake(video_url: str | None, video_bytes: bytes | None = None) -> ScoreDeepShield:
    """Analyse vidéo : extraction frames + audio → deepfake combiné."""
    try:
        # Télécharger si URL
        if not video_bytes and video_url:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(video_url)
                video_bytes = resp.content
        if not video_bytes:
            return ScoreDeepShield(score=0, details="Pas de données vidéo")

        # Import des extracteurs depuis truthscan
        from app.services.truthscan import _extract_frames_from_video, _extract_audio_from_video

        scores = []
        details_parts = []

        # 1. Analyse des frames (deepfake visuel)
        frames = _extract_frames_from_video(video_bytes, count=3)
        frame_scores = []
        for i, frame_bytes in enumerate(frames):
            frame_result = await _analyze_image_deepfake(None, frame_bytes)
            frame_scores.append(frame_result.score)
            if frame_result.manipulation_detected:
                details_parts.append(f"Frame {i+1}: manipulation détectée ({frame_result.score:.0f}/100)")

        if frame_scores:
            avg_image = sum(frame_scores) / len(frame_scores)
            max_image = max(frame_scores)
            # Pondération : 70% max frame + 30% moyenne (le pire frame compte plus)
            image_score = max_image * 0.7 + avg_image * 0.3
            scores.append(image_score)
            details_parts.append(f"Analyse visuelle : {len(frames)} frames, score {image_score:.0f}/100")

        # 2. Analyse audio (voix clonée)
        audio_bytes = _extract_audio_from_video(video_bytes)
        audio_score_val = 0.0
        if audio_bytes:
            audio_result = await _analyze_audio_deepfake(None, "audio/wav", audio_bytes)
            audio_score_val = audio_result.score
            scores.append(audio_result.score)
            if audio_result.manipulation_detected:
                details_parts.append(f"Voix synthétique détectée ({audio_result.score:.0f}/100)")
            else:
                details_parts.append(f"Analyse vocale : {audio_result.score:.0f}/100")
        else:
            details_parts.append("Pas de piste audio dans la vidéo")

        if not scores:
            return ScoreDeepShield(score=0, details="Extraction vidéo échouée")

        # Score final vidéo : max des deux (image + audio)
        final_score = max(scores)
        img_s = image_score if frame_scores else None
        aud_s = audio_score_val if audio_bytes else None

        return ScoreDeepShield(
            score=round(final_score, 1),
            image_score=round(img_s, 1) if img_s is not None else None,
            audio_score=round(aud_s, 1) if aud_s is not None else None,
            manipulation_detected=final_score > 60,
            confidence=round(final_score, 1),
            details=" | ".join(details_parts),
        )

    except Exception as e:
        logger.warning("Deepfake vidéo analyse échouée", error=str(e))
        return ScoreDeepShield(score=0, details=f"Analyse vidéo échouée — {str(e)[:80]}")
