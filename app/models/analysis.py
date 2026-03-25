from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"


class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    API = "api"
    WEB = "web"


class Verdict(str, Enum):
    FIABLE = "CONTENU FIABLE"
    DOUTEUX = "CONTENU DOUTEUX"
    PROBABLEMENT_FAUX = "PROBABLEMENT FAUX"
    DEEPFAKE = "DEEPFAKE CONFIRMÉ"
    ARNAQUE = "ARNAQUE CONFIRMÉE"


class Language(str, Enum):
    FR = "fr"
    EN = "en"
    WO = "wo"   # Wolof
    HA = "ha"   # Haoussa


class ScoreTruthScan(BaseModel):
    score: float = Field(ge=0, le=100)
    nlp_score: Optional[float] = None
    factcheck_score: Optional[float] = None
    ocr_detected: bool = False
    transcription: Optional[str] = None
    sources_found: list[str] = []
    details: str = ""


class ScoreDeepShield(BaseModel):
    score: float = Field(ge=0, le=100)
    image_score: Optional[float] = None
    audio_score: Optional[float] = None
    manipulation_detected: bool = False
    confidence: float = 0.0
    details: str = ""


class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_type: ContentType
    channel: Channel
    language: Language = Language.FR
    score_truthscan: float = Field(ge=0, le=100)
    score_deepshield: float = Field(ge=0, le=100)
    score_final: float = Field(ge=0, le=100)
    verdict: Verdict
    truthscan_details: Optional[ScoreTruthScan] = None
    deepshield_details: Optional[ScoreDeepShield] = None
    report_text: str = ""
    analysis_time_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisRequest(BaseModel):
    content: Optional[str] = None       # texte ou URL du média
    content_type: ContentType = ContentType.UNKNOWN
    channel: Channel = Channel.API
    sender_id: Optional[str] = None
    language: Language = Language.FR
