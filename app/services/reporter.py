"""
Reporter multilingue — génère le rapport d'analyse en FR, EN et Wolof.
"""
from app.models.analysis import Verdict, ScoreTruthScan, ScoreDeepShield, Language
from app.core.scoring import get_verdict_emoji


# ─── Traductions ─────────────────────────────────────

TRANSLATIONS = {
    Language.FR: {
        "title": "Analyse DeggBi AI",
        "verdict": "Verdict",
        "score": "Score",
        "details": "Détails",
        "analyzed_in": "Analysé en",
        "seconds": "secondes",
        "tagline": "DeggBi AI — La Vérité à Portée de Main",
        "synthetic_voice": "Voix synthétique détectée (Wav2Vec2)",
        "visual_manip": "Manipulation visuelle détectée (EfficientNet)",
        "confidence": "Confiance",
        "no_source": "Aucune source officielle correspondante",
        "transcription": "Transcription",
        "sources": "Sources",
        "analysis_complete": "Analyse complète effectuée",
        "ocr": "Texte extrait de l'image (OCR)",
        "actions": {
            Verdict.FIABLE: "Ce contenu semble authentique. Restez vigilant.",
            Verdict.DOUTEUX: "Vérifiez les sources avant de partager.",
            Verdict.PROBABLEMENT_FAUX: "Ne pas partager — signaler à votre entourage.",
            Verdict.DEEPFAKE: "Ne pas partager — Signaler aux autorités.",
            Verdict.ARNAQUE: "Ne pas cliquer ni répondre — Bloquer l'expéditeur.",
        },
    },
    Language.EN: {
        "title": "DeggBi AI Analysis",
        "verdict": "Verdict",
        "score": "Score",
        "details": "Details",
        "analyzed_in": "Analyzed in",
        "seconds": "seconds",
        "tagline": "DeggBi AI — Truth at Your Fingertips",
        "synthetic_voice": "Synthetic voice detected (Wav2Vec2)",
        "visual_manip": "Visual manipulation detected (EfficientNet)",
        "confidence": "Confidence",
        "no_source": "No matching official source found",
        "transcription": "Transcription",
        "sources": "Sources",
        "analysis_complete": "Full analysis completed",
        "ocr": "Text extracted from image (OCR)",
        "actions": {
            Verdict.FIABLE: "This content appears authentic. Stay vigilant.",
            Verdict.DOUTEUX: "Verify sources before sharing.",
            Verdict.PROBABLEMENT_FAUX: "Do not share — report to your community.",
            Verdict.DEEPFAKE: "Do not share — Report to authorities.",
            Verdict.ARNAQUE: "Do not click or reply — Block the sender.",
        },
    },
    Language.WO: {
        "title": "Cëru DeggBi AI",
        "verdict": "Xellu",
        "score": "Tollu",
        "details": "Ngir xam",
        "analyzed_in": "Topp nañu ko ci",
        "seconds": "saa",
        "tagline": "DeggBi AI — Dëgg Bi Ci Sa Loxo",
        "synthetic_voice": "Baat bu ëmb ci ordinatër lañu ko def (Wav2Vec2)",
        "visual_manip": "Nataal bi dañu ko soppi (EfficientNet)",
        "confidence": "Ngëm",
        "no_source": "Amul source bu woorul bu ko dëgge",
        "transcription": "Bind",
        "sources": "Fu mu jóge",
        "analysis_complete": "Topp bi jeexna",
        "ocr": "Mbind mu ci nataal bi (OCR)",
        "actions": {
            Verdict.FIABLE: "Li dëgg la. Wàcc xam-xam.",
            Verdict.DOUTEUX: "Saytul lu mu jóge balaa nga ko yóbbu.",
            Verdict.PROBABLEMENT_FAUX: "Buleen ko yóbbu — waxal sa wàllu kër.",
            Verdict.DEEPFAKE: "Buleen ko yóbbu — Waxal kilifa yi.",
            Verdict.ARNAQUE: "Bul tëral ci — Dëngal kiy yónne.",
        },
    },
}

# Verdicts traduits
VERDICT_TRANSLATIONS = {
    Language.FR: {
        Verdict.FIABLE: "CONTENU FIABLE",
        Verdict.DOUTEUX: "CONTENU DOUTEUX",
        Verdict.PROBABLEMENT_FAUX: "PROBABLEMENT FAUX",
        Verdict.DEEPFAKE: "DEEPFAKE CONFIRMÉ",
        Verdict.ARNAQUE: "ARNAQUE CONFIRMÉE",
    },
    Language.EN: {
        Verdict.FIABLE: "RELIABLE CONTENT",
        Verdict.DOUTEUX: "DOUBTFUL CONTENT",
        Verdict.PROBABLEMENT_FAUX: "LIKELY FALSE",
        Verdict.DEEPFAKE: "CONFIRMED DEEPFAKE",
        Verdict.ARNAQUE: "CONFIRMED SCAM",
    },
    Language.WO: {
        Verdict.FIABLE: "LI DËGG LA",
        Verdict.DOUTEUX: "LI DAFAY SIKK",
        Verdict.PROBABLEMENT_FAUX: "LI FENN LA",
        Verdict.DEEPFAKE: "DEEPFAKE DËGG NA",
        Verdict.ARNAQUE: "ARNAQUE DËGG NA",
    },
}


def generate_report(
    verdict: Verdict,
    score_final: float,
    content_type: str,
    language: str,
    truthscan: ScoreTruthScan | None,
    deepshield: ScoreDeepShield | None,
    analysis_time_ms: int,
) -> str:
    """Génère le rapport formaté WhatsApp dans la langue demandée."""

    lang = Language(language) if language in [l.value for l in Language] else Language.FR
    t = TRANSLATIONS.get(lang, TRANSLATIONS[Language.FR])
    verdict_text = VERDICT_TRANSLATIONS.get(lang, VERDICT_TRANSLATIONS[Language.FR]).get(
        verdict, verdict.value
    )
    emoji = get_verdict_emoji(verdict)

    # Détails
    details_lines = []
    if truthscan:
        if truthscan.transcription:
            details_lines.append(f"• {t['transcription']} : *{truthscan.transcription[:80]}...*")
        if truthscan.ocr_detected:
            details_lines.append(f"• {t['ocr']}")
        if truthscan.sources_found:
            details_lines.append(f"• {t['sources']} : {', '.join(truthscan.sources_found[:2])}")
        elif truthscan.factcheck_score and truthscan.factcheck_score > 50:
            details_lines.append(f"• {t['no_source']}")
    if deepshield:
        if deepshield.manipulation_detected:
            if content_type == "audio":
                details_lines.append(f"• {t['synthetic_voice']}")
            else:
                details_lines.append(f"• {t['visual_manip']}")
            details_lines.append(f"• {t['confidence']} : {deepshield.confidence:.1f}%")

    details_text = "\n".join(details_lines) if details_lines else f"• {t['analysis_complete']}"
    time_sec = analysis_time_ms / 1000
    action = t["actions"].get(verdict, "")

    return f"""🔍 *{t['title']}*

{emoji} *{verdict_text}*
{t['score']} : {score_final}/100

📊 *{t['details']} :*
{details_text}

⏱ {t['analyzed_in']} {time_sec:.0f} {t['seconds']}

➡️ {action}

_{t['tagline']}_"""
