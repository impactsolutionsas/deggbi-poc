from celery import Celery
from app.config import settings
import structlog
import time

logger = structlog.get_logger()

# Initialisation Celery
celery_app = Celery(
    "deggbi",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={"app.tasks.analysis.*": {"queue": "analysis"}},
    task_track_started=True,
    task_time_limit=120,        # 2 min max par analyse
    task_soft_time_limit=90,
)


@celery_app.task(bind=True, name="app.tasks.analysis.run_analysis", max_retries=2)
def run_analysis(
    self,
    content: str | None = None,
    media_id: str | None = None,
    media_bytes: bytes | None = None,
    mime_type: str | None = None,
    content_type: str = "unknown",
    channel: str = "api",
    sender_id: str | None = None,
    filename: str | None = None,
):
    """
    Task principale : orchestre l'analyse complète d'un contenu.
    1. Télécharge le média si nécessaire
    2. Lance TruthScan + DeepShield en parallèle
    3. Calcule le score final
    4. Sauvegarde en base
    5. Envoie la réponse au canal d'origine
    """
    import asyncio
    from app.services.truthscan import analyze_truthscan
    from app.services.deepshield import analyze_deepshield
    from app.core.scoring import compute_score_final, get_verdict, build_report
    from app.models.analysis import (
        ContentType, Channel, Language,
        ScoreTruthScan, ScoreDeepShield
    )
    from app.models.database import save_analysis, upload_media
    import uuid

    start_time = time.time()
    analysis_id = str(uuid.uuid4())

    logger.info("Analyse démarrée", id=analysis_id, type=content_type, channel=channel)

    try:
        ct = ContentType(content_type)
        ch = Channel(channel)

        # 1. Téléchargement média si nécessaire
        media_url = None
        if media_id and channel in ("whatsapp", "telegram"):
            # TODO: implémenter download_whatsapp_media / download_telegram_media
            pass
        elif media_bytes:
            ext = (filename or "file").rsplit(".", 1)[-1] if filename else "bin"
            fname = f"{analysis_id}.{ext}"
            media_url = asyncio.run(upload_media(media_bytes, fname, mime_type or "application/octet-stream"))

        # 2. TruthScan
        ts_result: ScoreTruthScan = asyncio.run(
            analyze_truthscan(
                content=content,
                media_url=media_url or media_id,
                content_type=ct,
            )
        )

        # 3. DeepShield
        ds_result: ScoreDeepShield = asyncio.run(
            analyze_deepshield(
                media_url=media_url or media_id,
                content_type=ct,
                mime_type=mime_type,
            )
        )

        # 4. Scoring
        score_final = compute_score_final(ts_result.score, ds_result.score)
        verdict = get_verdict(score_final, content_type)
        analysis_time_ms = int((time.time() - start_time) * 1000)

        report = build_report(
            verdict=verdict,
            score_final=score_final,
            content_type=content_type,
            language="fr",
            truthscan=ts_result,
            deepshield=ds_result,
            analysis_time_ms=analysis_time_ms,
        )

        # 5. Sauvegarde Supabase
        asyncio.run(save_analysis({
            "id": analysis_id,
            "content_type": content_type,
            "channel": channel,
            "sender_id": sender_id,
            "score_truthscan": ts_result.score,
            "score_deepshield": ds_result.score,
            "score_final": score_final,
            "verdict": verdict.value,
            "report_text": report,
            "analysis_time_ms": analysis_time_ms,
        }))

        # 6. Envoi de la réponse
        if sender_id and channel == "whatsapp":
            from app.api.whatsapp import send_whatsapp_text
            asyncio.run(send_whatsapp_text(sender_id, report))
        elif sender_id and channel == "telegram":
            from app.api.telegram import send_telegram_message
            asyncio.run(send_telegram_message(sender_id, report))

        logger.info("Analyse terminée", id=analysis_id, score=score_final, verdict=verdict.value, ms=analysis_time_ms)
        return {"analysis_id": analysis_id, "score_final": score_final, "verdict": verdict.value}

    except Exception as exc:
        logger.error("Erreur analyse", id=analysis_id, error=str(exc))
        # Notification d'erreur à l'utilisateur
        error_msg = "⚠️ *DeggBi AI* — Analyse impossible pour le moment. Réessayez dans quelques instants."
        if sender_id and channel == "whatsapp":
            from app.api.whatsapp import send_whatsapp_text
            import asyncio
            asyncio.run(send_whatsapp_text(sender_id, error_msg))
        raise self.retry(exc=exc, countdown=10)
