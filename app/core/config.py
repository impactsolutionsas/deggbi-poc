from app.models.analysis import ContentType
import structlog

logger = structlog.get_logger()

# Extensions supportées par type
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
AUDIO_EXTENSIONS = {".ogg", ".mp3", ".wav", ".m4a", ".opus", ".aac"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def detect_content_type(
    text: str | None = None,
    mime_type: str | None = None,
    filename: str | None = None,
) -> ContentType:
    """
    Détecte automatiquement le type de contenu.
    Priorité : mime_type > extension fichier > analyse texte
    """
    # Par MIME type (WhatsApp/Telegram envoient ça)
    if mime_type:
        if mime_type.startswith("image/"):
            return ContentType.IMAGE
        if mime_type.startswith("audio/"):
            return ContentType.AUDIO
        if mime_type.startswith("video/"):
            return ContentType.VIDEO
        if mime_type.startswith("text/"):
            return ContentType.TEXT

    # Par extension de fichier
    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext in IMAGE_EXTENSIONS:
            return ContentType.IMAGE
        if ext in AUDIO_EXTENSIONS:
            return ContentType.AUDIO
        if ext in VIDEO_EXTENSIONS:
            return ContentType.VIDEO

    # Par contenu texte (URL d'image ou texte brut)
    if text:
        text_lower = text.lower()
        if any(ext in text_lower for ext in IMAGE_EXTENSIONS):
            return ContentType.IMAGE
        if any(ext in text_lower for ext in AUDIO_EXTENSIONS):
            return ContentType.AUDIO
        # Texte brut par défaut
        if len(text) > 0:
            return ContentType.TEXT

    return ContentType.UNKNOWN


def route_to_pipeline(content_type: ContentType) -> dict:
    """
    Retourne la configuration du pipeline pour un type de contenu.
    """
    pipelines = {
        ContentType.TEXT: {
            "truthscan": ["nlp", "factcheck", "url_analysis"],
            "deepshield": [],
            "description": "NLP + Fact-check + détection arnaque",
        },
        ContentType.IMAGE: {
            "truthscan": ["ocr", "reverse_search", "context_check"],
            "deepshield": ["efficientnet"],
            "description": "OCR + EfficientNet deepfake + reverse image",
        },
        ContentType.AUDIO: {
            "truthscan": ["whisper_stt", "nlp", "factcheck"],
            "deepshield": ["wav2vec2"],
            "description": "Whisper STT + NLP + Wav2Vec2 voix clonée",
        },
        ContentType.VIDEO: {
            "truthscan": ["whisper_stt", "nlp"],
            "deepshield": ["efficientnet_frames", "wav2vec2"],
            "description": "Analyse frame-by-frame + audio (V2)",
        },
    }
    return pipelines.get(content_type, {"truthscan": [], "deepshield": [], "description": "Type inconnu"})
