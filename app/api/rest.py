from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.models.analysis import AnalysisRequest, AnalysisResult, ContentType, Channel
from app.tasks.analysis import run_analysis
from app.models.database import get_analysis, get_recent_analyses
import structlog
import uuid

router = APIRouter()
logger = structlog.get_logger()


@router.post("/analyze/text", response_model=dict)
async def analyze_text(request: AnalysisRequest):
    """Analyse un contenu texte (SMS, message, URL)."""
    task = run_analysis.delay(
        content=request.content,
        content_type=ContentType.TEXT.value,
        channel=Channel.API.value,
        sender_id=request.sender_id or "api",
    )
    return {"task_id": task.id, "status": "queued"}


@router.post("/analyze/media", response_model=dict)
async def analyze_media(
    file: UploadFile = File(...),
    channel: str = Form(default="api"),
):
    """Analyse un fichier média (image, audio)."""
    file_bytes = await file.read()
    task_id = str(uuid.uuid4())

    # Détermination du type
    content_type = ContentType.UNKNOWN
    mime = file.content_type or ""
    if mime.startswith("image/"):
        content_type = ContentType.IMAGE
    elif mime.startswith("audio/"):
        content_type = ContentType.AUDIO

    run_analysis.delay(
        content=None,
        media_bytes=file_bytes,
        mime_type=mime,
        content_type=content_type.value,
        channel=channel,
        sender_id="api",
        filename=file.filename,
    )

    return {"task_id": task_id, "status": "queued"}


@router.get("/analysis/{analysis_id}", response_model=dict)
async def get_analysis_result(analysis_id: str):
    """Récupère le résultat d'une analyse par ID."""
    result = await get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return result


@router.get("/analyses", response_model=list)
async def list_analyses(limit: int = 20):
    """Liste les analyses récentes (dashboard B2B)."""
    return await get_recent_analyses(limit=limit)
