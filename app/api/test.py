"""
Route de test synchrone — exécute le pipeline complet sans Celery/Redis.
À utiliser en dev uniquement.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.truthscan import analyze_truthscan
from app.services.deepshield import analyze_deepshield
from app.services.reporter import generate_report
from app.core.scoring import compute_score_final, get_verdict
from app.core.config import detect_content_type
from app.models.analysis import ContentType
from app.models.database import save_analysis
import structlog
import time
import uuid

router = APIRouter()
logger = structlog.get_logger()


@router.post("/analyze")
async def test_analyze_sync(
    text: str = Form(default=None),
    language: str = Form(default="fr"),
    file: UploadFile | None = File(default=None),
):
    """
    Analyse synchrone — pas besoin de Celery/Redis.
    Accepte du texte et/ou un fichier (image, audio).
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())

    file_bytes = None
    mime_type = None

    if file and file.filename:
        file_bytes = await file.read()
        mime_type = file.content_type or ""
        content_type = detect_content_type(mime_type=mime_type, filename=file.filename)
    elif text:
        content_type = ContentType.TEXT
    else:
        raise HTTPException(status_code=400, detail="Envoyez du texte ou un fichier")

    logger.info("Test sync", id=analysis_id, type=content_type.value)

    # TruthScan — passe les bytes directs
    ts_result = await analyze_truthscan(
        content=text,
        media_url=None,
        content_type=content_type,
        media_bytes=file_bytes,
    )

    # DeepShield — passe les bytes directs
    ds_result = await analyze_deepshield(
        media_url=None,
        content_type=content_type,
        mime_type=mime_type,
        media_bytes=file_bytes,
    )

    # Scoring
    score_final = compute_score_final(ts_result.score, ds_result.score)
    verdict = get_verdict(score_final, content_type.value)
    analysis_time_ms = int((time.time() - start_time) * 1000)

    # Rapport
    report = generate_report(
        verdict=verdict,
        score_final=score_final,
        content_type=content_type.value,
        language=language,
        truthscan=ts_result,
        deepshield=ds_result,
        analysis_time_ms=analysis_time_ms,
    )

    # Sauvegarder en base Supabase
    try:
        await save_analysis({
            "id": analysis_id,
            "content_type": content_type.value,
            "channel": "web",
            "score_truthscan": ts_result.score,
            "score_deepshield": ds_result.score,
            "score_final": score_final,
            "verdict": verdict.value,
            "report_text": report,
            "analysis_time_ms": analysis_time_ms,
            "language": language,
        })
        logger.info("Analyse sauvegardée", id=analysis_id)
    except Exception as e:
        logger.warning("Sauvegarde échouée", error=str(e))

    return {
        "id": analysis_id,
        "content_type": content_type.value,
        "score_truthscan": ts_result.score,
        "score_deepshield": ds_result.score,
        "score_final": score_final,
        "verdict": verdict.value,
        "report": report,
        "analysis_time_ms": analysis_time_ms,
        "truthscan_details": ts_result.model_dump(),
        "deepshield_details": ds_result.model_dump(),
    }
