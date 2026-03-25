"""
TruthScan — Module de vérification des faits
- Texte  : NLP multilingue + Fact-check API + détection arnaque
- Image  : OCR (PaddleOCR) + reverse image search
- Audio  : Whisper STT → transcription → analyse NLP
"""
import httpx
import structlog
from app.models.analysis import ContentType, ScoreTruthScan
from app.config import settings

logger = structlog.get_logger()

HF_API_URL = "https://api-inference.huggingface.co/models"


async def analyze_truthscan(
    content: str | None,
    media_url: str | None,
    content_type: ContentType,
) -> ScoreTruthScan:
    """Point d'entrée principal TruthScan."""
    try:
        if content_type == ContentType.TEXT:
            return await _analyze_text(content or "")
        elif content_type == ContentType.IMAGE:
            return await _analyze_image(media_url, content)
        elif content_type == ContentType.AUDIO:
            return await _analyze_audio(media_url)
        else:
            return ScoreTruthScan(score=0, details="Type de contenu non supporté")
    except Exception as e:
        logger.error("Erreur TruthScan", error=str(e))
        return ScoreTruthScan(score=50, details=f"Analyse partielle — {str(e)[:100]}")


async def _analyze_text(text: str) -> ScoreTruthScan:
    """Analyse un texte pour détecter désinformation et arnaques."""
    scores = []
    details = []

    # 1. Détection de patterns d'arnaque (heuristiques rapides)
    arnaque_score = _detect_scam_patterns(text)
    if arnaque_score > 0:
        scores.append(arnaque_score)
        details.append("Patterns d'arnaque détectés")

    # 2. Google Fact Check API
    if settings.google_factcheck_key:
        fc_score = await _google_factcheck(text)
        if fc_score is not None:
            scores.append(fc_score)

    # 3. NLP via HuggingFace (classification fake news)
    nlp_score = await _huggingface_classify(text, "fake-news-detection")
    if nlp_score is not None:
        scores.append(nlp_score)
        details.append("Classification NLP effectuée")

    # Score final = max des scores (worst-case)
    final_score = max(scores) if scores else 30
    sources = []  # TODO: extraire les sources du fact-check

    return ScoreTruthScan(
        score=round(final_score, 1),
        factcheck_score=nlp_score,
        details=" — ".join(details) if details else "Analyse texte complète",
        sources_found=sources,
    )


async def _analyze_image(media_url: str | None, caption: str | None) -> ScoreTruthScan:
    """Analyse une image : OCR + vérification contexte."""
    details = []
    scores = [30]  # Score de base neutre

    # 1. OCR si URL disponible
    ocr_text = ""
    if media_url:
        ocr_text = await _run_ocr(media_url)
        if ocr_text:
            details.append(f"OCR : {ocr_text[:50]}...")
            # Analyser le texte extrait
            text_result = await _analyze_text(ocr_text)
            scores.append(text_result.score * 0.7)  # Pondération plus faible

    # 2. Analyse de la légende si présente
    if caption:
        caption_result = await _analyze_text(caption)
        scores.append(caption_result.score * 0.8)
        details.append("Légende analysée")

    return ScoreTruthScan(
        score=round(max(scores), 1),
        ocr_detected=bool(ocr_text),
        details=" — ".join(details) if details else "Analyse image effectuée",
    )


async def _analyze_audio(media_url: str | None) -> ScoreTruthScan:
    """Transcrit l'audio avec Whisper puis analyse le texte."""
    if not media_url:
        return ScoreTruthScan(score=50, details="Pas d'audio disponible")

    # 1. Transcription Whisper via HuggingFace
    transcription = await _whisper_transcribe(media_url)

    if not transcription:
        return ScoreTruthScan(score=50, details="Transcription échouée")

    # 2. Analyse du texte transcrit
    text_result = await _analyze_text(transcription)

    return ScoreTruthScan(
        score=text_result.score,
        transcription=transcription,
        factcheck_score=text_result.factcheck_score,
        sources_found=text_result.sources_found,
        details=f"Whisper + {text_result.details}",
    )


# ─── Helpers ─────────────────────────────────────────


def _detect_scam_patterns(text: str) -> float:
    """Heuristiques rapides pour détecter les arnaques (Mobile Money, phishing)."""
    text_lower = text.lower()

    high_risk_patterns = [
        "gagné", "gagnez", "félicitations", "congratulations",
        "cliquez ici", "click here", "lien", "link",
        "urgent", "immédiatement", "expires",
        "mobile money", "orange money", "wave", "mtn momo",
        "mot de passe", "password", "code secret", "pin",
        "vérification", "compte bloqué", "account suspended",
    ]

    score = 0
    hits = sum(1 for p in high_risk_patterns if p in text_lower)

    if hits >= 4:
        score = 90
    elif hits >= 2:
        score = 65
    elif hits >= 1:
        score = 40

    return score


async def _google_factcheck(query: str) -> float | None:
    """Interroge Google Fact Check Tools API."""
    if not settings.google_factcheck_key:
        return None
    try:
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {"query": query[:200], "key": settings.google_factcheck_key, "languageCode": "fr"}
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            claims = data.get("claims", [])
            if not claims:
                return 50  # Pas trouvé = neutre
            # Si trouvé avec rating négatif → score élevé
            for claim in claims[:3]:
                rating = claim.get("claimReview", [{}])[0].get("textualRating", "").lower()
                if any(w in rating for w in ["false", "faux", "incorrect", "misleading"]):
                    return 80
            return 20  # Trouvé mais pas marqué faux
    except Exception as e:
        logger.warning("Google Fact Check indisponible", error=str(e))
        return None


async def _huggingface_classify(text: str, task: str) -> float | None:
    """Classification NLP via HuggingFace Inference API."""
    if not settings.huggingface_api_key:
        return None
    try:
        # Modèle de détection fake news multilingue
        model = "mrm8488/bert-tiny-finetuned-fake-news-detection"
        url = f"{HF_API_URL}/{model}"
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={"inputs": text[:512]}, headers=headers)
            results = resp.json()
            if isinstance(results, list) and results:
                for item in results[0] if isinstance(results[0], list) else results:
                    if item.get("label", "").upper() in ("FAKE", "LABEL_1"):
                        return item.get("score", 0.5) * 100
            return 30
    except Exception as e:
        logger.warning("HuggingFace NLP indisponible", error=str(e))
        return None


async def _whisper_transcribe(audio_url: str) -> str:
    """Transcription audio via HuggingFace Whisper Large-v3."""
    if not settings.huggingface_api_key:
        return ""
    try:
        # Télécharger l'audio d'abord
        async with httpx.AsyncClient(timeout=30) as client:
            audio_resp = await client.get(audio_url)
            audio_bytes = audio_resp.content

        model = "openai/whisper-large-v3"
        url = f"{HF_API_URL}/{model}"
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, content=audio_bytes, headers={
                **headers,
                "Content-Type": "audio/ogg",
            })
            result = resp.json()
            return result.get("text", "")
    except Exception as e:
        logger.warning("Whisper indisponible", error=str(e))
        return ""


async def _run_ocr(image_url: str) -> str:
    """OCR sur une image via PaddleOCR ou HuggingFace."""
    # TODO: implémenter PaddleOCR local ou via API
    # Pour le PoC : utiliser TrOCR sur HuggingFace
    return ""
