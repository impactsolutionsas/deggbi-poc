from app.models.analysis import Verdict, ScoreTruthScan, ScoreDeepShield
import structlog

logger = structlog.get_logger()

# Poids du scoring (ajustable)
WEIGHT_TRUTHSCAN = 0.5
WEIGHT_DEEPSHIELD = 0.5

# Seuils des verdicts
THRESHOLD_FIABLE = 30
THRESHOLD_DOUTEUX = 60
THRESHOLD_PROBFAUX = 85


def compute_score_final(
    score_truthscan: float,
    score_deepshield: float,
) -> float:
    """Calcule le score final DeggBi (0–100)."""
    score = (score_truthscan * WEIGHT_TRUTHSCAN) + (score_deepshield * WEIGHT_DEEPSHIELD)
    return round(min(max(score, 0), 100), 1)


def get_verdict(score: float, content_type: str = "unknown") -> Verdict:
    """Détermine le verdict à partir du score final."""
    if score <= THRESHOLD_FIABLE:
        return Verdict.FIABLE
    elif score <= THRESHOLD_DOUTEUX:
        return Verdict.DOUTEUX
    elif score <= THRESHOLD_PROBFAUX:
        return Verdict.PROBABLEMENT_FAUX
    else:
        # Distinction arnaque vs deepfake selon le type de contenu
        if content_type == "text":
            return Verdict.ARNAQUE
        return Verdict.DEEPFAKE


def get_verdict_emoji(verdict: Verdict) -> str:
    emojis = {
        Verdict.FIABLE: "✅",
        Verdict.DOUTEUX: "⚠️",
        Verdict.PROBABLEMENT_FAUX: "🔴",
        Verdict.DEEPFAKE: "🚨",
        Verdict.ARNAQUE: "🚫",
    }
    return emojis.get(verdict, "❓")


def build_report(
    verdict: Verdict,
    score_final: float,
    content_type: str,
    language: str,
    truthscan: ScoreTruthScan | None,
    deepshield: ScoreDeepShield | None,
    analysis_time_ms: int,
) -> str:
    """Génère le rapport texte formaté pour WhatsApp."""

    emoji = get_verdict_emoji(verdict)

    # Détails selon les modules
    details_lines = []
    if truthscan:
        if truthscan.transcription:
            details_lines.append(f"• Transcription : *{truthscan.transcription[:80]}...*")
        if truthscan.sources_found:
            details_lines.append(f"• Sources : {', '.join(truthscan.sources_found[:2])}")
        elif truthscan.factcheck_score and truthscan.factcheck_score > 50:
            details_lines.append("• Aucune source officielle correspondante")
    if deepshield:
        if deepshield.manipulation_detected:
            if content_type == "audio":
                details_lines.append(f"• Voix synthétique détectée (Wav2Vec2)")
            else:
                details_lines.append(f"• Manipulation visuelle détectée (EfficientNet)")
            details_lines.append(f"• Confiance : {deepshield.confidence:.1f}%")

    details_text = "\n".join(details_lines) if details_lines else "• Analyse complète effectuée"

    # Actions recommandées
    actions = {
        Verdict.FIABLE: "✔ Ce contenu semble authentique. Restez vigilant.",
        Verdict.DOUTEUX: "⚠ Vérifiez les sources avant de partager.",
        Verdict.PROBABLEMENT_FAUX: "🔴 Ne pas partager — signaler à votre entourage.",
        Verdict.DEEPFAKE: "🚨 Ne pas partager — Signaler aux autorités.",
        Verdict.ARNAQUE: "🚫 Ne pas cliquer ni répondre — Bloquer l'expéditeur.",
    }

    time_sec = analysis_time_ms / 1000

    report = f"""🔍 *Analyse DeggBi AI*

{emoji} *{verdict.value}*
Score : {score_final}/100

📊 *Détails :*
{details_text}

⏱ Analysé en {time_sec:.0f} secondes

➡️ {actions.get(verdict, "")}

_DeggBi AI — La Vérité à Portée de Main_"""

    return report
