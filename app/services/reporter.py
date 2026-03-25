"""
Reporter multilingue — génère le rapport d'analyse en FR, EN et Wolof.
Rapports détaillés et naturels, sans jargon technique visible.
"""
from app.models.analysis import Verdict, ScoreTruthScan, ScoreDeepShield, Language
from app.core.scoring import get_verdict_emoji


# ─── Textes par langue ──────────────────────────────

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


def _score_bar(score: float) -> str:
    """Barre visuelle ████░░░░░░ 42/100."""
    filled = round(score / 10)
    empty = 10 - filled
    return f"{'█' * filled}{'░' * empty} {score:.0f}/100"


def _risk_label_fr(score: float) -> str:
    if score <= 20:
        return "très faible"
    if score <= 40:
        return "faible"
    if score <= 60:
        return "modéré"
    if score <= 80:
        return "élevé"
    return "très élevé"


def _risk_label_en(score: float) -> str:
    if score <= 20:
        return "very low"
    if score <= 40:
        return "low"
    if score <= 60:
        return "moderate"
    if score <= 80:
        return "high"
    return "very high"


def _risk_label_wo(score: float) -> str:
    if score <= 20:
        return "ndaw lool"
    if score <= 40:
        return "ndaw"
    if score <= 60:
        return "diggante"
    if score <= 80:
        return "kawe"
    return "kawe lool"


def generate_report(
    verdict: Verdict,
    score_final: float,
    content_type: str,
    language: str,
    truthscan: ScoreTruthScan | None,
    deepshield: ScoreDeepShield | None,
    analysis_time_ms: int,
) -> str:
    """Génère le rapport formaté dans la langue demandée."""

    lang = Language(language) if language in [l.value for l in Language] else Language.FR

    if lang == Language.EN:
        return _report_en(verdict, score_final, content_type, truthscan, deepshield, analysis_time_ms)
    if lang == Language.WO:
        return _report_wo(verdict, score_final, content_type, truthscan, deepshield, analysis_time_ms)
    return _report_fr(verdict, score_final, content_type, truthscan, deepshield, analysis_time_ms)


# ═══════════════════════════════════════════════════════
#  FRANÇAIS
# ═══════════════════════════════════════════════════════

def _report_fr(
    verdict: Verdict, score: float, content_type: str,
    ts: ScoreTruthScan | None, ds: ScoreDeepShield | None,
    time_ms: int,
) -> str:
    emoji = get_verdict_emoji(verdict)
    verdict_text = VERDICT_TRANSLATIONS[Language.FR].get(verdict, verdict.value)
    risk = _risk_label_fr(score)
    bar = _score_bar(score)
    time_sec = time_ms / 1000

    # Type de contenu en français
    type_labels = {"text": "texte", "image": "image", "audio": "audio", "video": "vidéo"}
    type_fr = type_labels.get(content_type, content_type)

    lines = [
        f"{'─' * 32}",
        f"  {emoji}  *{verdict_text}*",
        f"{'─' * 32}",
        "",
        f"  Risque : {risk}",
        f"  {bar}",
        f"  Type analysé : {type_fr}",
        "",
    ]

    # ── Section TruthScan ──
    if ts:
        lines.append("📝 *Vérification du contenu*")
        ts_risk = _risk_label_fr(ts.score)
        lines.append(f"  Score : {ts.score:.0f}/100 ({ts_risk})")

        if ts.transcription:
            preview = ts.transcription[:120].strip()
            lines.append(f"  Transcription audio :")
            lines.append(f"  « {preview} »")

        if ts.ocr_detected:
            lines.append(f"  Du texte a été extrait de l'image par reconnaissance optique.")

        if ts.sources_found:
            lines.append(f"  Sources trouvées :")
            for src in ts.sources_found[:3]:
                lines.append(f"    - {src}")
        elif ts.factcheck_score is not None and ts.factcheck_score > 50:
            lines.append(f"  Aucune source officielle ne confirme cette information.")

        if ts.nlp_score is not None:
            nlp_risk = _risk_label_fr(ts.nlp_score)
            lines.append(f"  Analyse linguistique : risque {nlp_risk} ({ts.nlp_score:.0f}/100)")

        if ts.details and ts.details not in ("Analyse texte complète", "Analyse image effectuée"):
            # Afficher les détails pertinents du pipeline
            for part in ts.details.split(" — "):
                part = part.strip()
                if part and part not in ("Classification NLP effectuée",):
                    lines.append(f"  {part}")

        lines.append("")

    # ── Section DeepShield ──
    if ds and ds.score > 0:
        lines.append("🛡️ *Détection de manipulation*")
        ds_risk = _risk_label_fr(ds.score)
        lines.append(f"  Score : {ds.score:.0f}/100 ({ds_risk})")

        if ds.manipulation_detected:
            if content_type == "audio":
                lines.append(f"  La voix présente des caractéristiques de synthèse artificielle.")
            else:
                lines.append(f"  Des signes de manipulation visuelle ont été détectés.")
            lines.append(f"  Niveau de certitude : {ds.confidence:.1f}%")
        else:
            if content_type == "audio":
                lines.append(f"  La voix semble naturelle, pas de synthèse détectée.")
            elif content_type == "image":
                lines.append(f"  Pas de manipulation visuelle évidente.")

        if ds.image_score is not None and ds.image_score > 0:
            lines.append(f"  Analyse image : {ds.image_score:.0f}/100")
        if ds.audio_score is not None and ds.audio_score > 0:
            lines.append(f"  Analyse audio : {ds.audio_score:.0f}/100")

        if ds.details and ds.details not in ("Pas de média à analyser", "DeepShield non applicable pour ce type"):
            lines.append(f"  {ds.details}")

        lines.append("")

    # ── Recommandation ──
    lines.append("💡 *Que faire ?*")
    actions = {
        Verdict.FIABLE: "Ce contenu ne présente pas de signe de falsification.\nRestez tout de même vigilant : vérifiez la source avant de partager.",
        Verdict.DOUTEUX: "Nous ne pouvons pas confirmer l'authenticité de ce contenu.\nRecoupez avec d'autres sources fiables avant de le relayer.",
        Verdict.PROBABLEMENT_FAUX: "Ce contenu présente plusieurs indicateurs de fausseté.\nNe le partagez pas et informez votre entourage.",
        Verdict.DEEPFAKE: "Ce contenu a de fortes chances d'avoir été généré ou manipulé.\nNe le partagez pas. Signalez-le à la plateforme et aux autorités.",
        Verdict.ARNAQUE: "Ce message correspond à un schéma d'arnaque connu.\nNe cliquez sur aucun lien, ne répondez pas, bloquez l'expéditeur.",
    }
    action_text = actions.get(verdict, "")
    for line in action_text.split("\n"):
        lines.append(f"  {line}")

    lines.append("")
    lines.append(f"⏱ Analyse effectuée en {time_sec:.1f}s")
    lines.append(f"_DeggBi AI — La Vérité à Portée de Main_")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
#  ENGLISH
# ═══════════════════════════════════════════════════════

def _report_en(
    verdict: Verdict, score: float, content_type: str,
    ts: ScoreTruthScan | None, ds: ScoreDeepShield | None,
    time_ms: int,
) -> str:
    emoji = get_verdict_emoji(verdict)
    verdict_text = VERDICT_TRANSLATIONS[Language.EN].get(verdict, verdict.value)
    risk = _risk_label_en(score)
    bar = _score_bar(score)
    time_sec = time_ms / 1000

    lines = [
        f"{'─' * 32}",
        f"  {emoji}  *{verdict_text}*",
        f"{'─' * 32}",
        "",
        f"  Risk level: {risk}",
        f"  {bar}",
        f"  Content type: {content_type}",
        "",
    ]

    if ts:
        lines.append("📝 *Content verification*")
        ts_risk = _risk_label_en(ts.score)
        lines.append(f"  Score: {ts.score:.0f}/100 ({ts_risk})")

        if ts.transcription:
            preview = ts.transcription[:120].strip()
            lines.append(f"  Audio transcript:")
            lines.append(f"  \"{preview}\"")

        if ts.ocr_detected:
            lines.append(f"  Text was extracted from the image using optical recognition.")

        if ts.sources_found:
            lines.append(f"  Sources found:")
            for src in ts.sources_found[:3]:
                lines.append(f"    - {src}")
        elif ts.factcheck_score is not None and ts.factcheck_score > 50:
            lines.append(f"  No official source confirms this information.")

        if ts.nlp_score is not None:
            nlp_risk = _risk_label_en(ts.nlp_score)
            lines.append(f"  Linguistic analysis: {nlp_risk} risk ({ts.nlp_score:.0f}/100)")

        lines.append("")

    if ds and ds.score > 0:
        lines.append("🛡️ *Manipulation detection*")
        ds_risk = _risk_label_en(ds.score)
        lines.append(f"  Score: {ds.score:.0f}/100 ({ds_risk})")

        if ds.manipulation_detected:
            if content_type == "audio":
                lines.append(f"  The voice shows characteristics of artificial synthesis.")
            else:
                lines.append(f"  Signs of visual manipulation were detected.")
            lines.append(f"  Confidence: {ds.confidence:.1f}%")
        else:
            if content_type == "audio":
                lines.append(f"  The voice sounds natural, no synthesis detected.")
            elif content_type == "image":
                lines.append(f"  No obvious visual manipulation found.")

        if ds.details and ds.details not in ("Pas de média à analyser", "DeepShield non applicable pour ce type"):
            lines.append(f"  {ds.details}")

        lines.append("")

    lines.append("💡 *What should you do?*")
    actions = {
        Verdict.FIABLE: "This content shows no signs of falsification.\nStill, verify the source before sharing.",
        Verdict.DOUTEUX: "We cannot confirm the authenticity of this content.\nCross-check with other reliable sources before sharing.",
        Verdict.PROBABLEMENT_FAUX: "This content shows multiple indicators of being false.\nDo not share it and warn people around you.",
        Verdict.DEEPFAKE: "This content was very likely generated or manipulated.\nDo not share. Report it to the platform and authorities.",
        Verdict.ARNAQUE: "This message matches a known scam pattern.\nDo not click any links, do not reply, block the sender.",
    }
    action_text = actions.get(verdict, "")
    for line in action_text.split("\n"):
        lines.append(f"  {line}")

    lines.append("")
    lines.append(f"⏱ Analyzed in {time_sec:.1f}s")
    lines.append(f"_DeggBi AI — Truth at Your Fingertips_")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
#  WOLOF
# ═══════════════════════════════════════════════════════

def _report_wo(
    verdict: Verdict, score: float, content_type: str,
    ts: ScoreTruthScan | None, ds: ScoreDeepShield | None,
    time_ms: int,
) -> str:
    emoji = get_verdict_emoji(verdict)
    verdict_text = VERDICT_TRANSLATIONS[Language.WO].get(verdict, verdict.value)
    risk = _risk_label_wo(score)
    bar = _score_bar(score)
    time_sec = time_ms / 1000

    type_labels = {"text": "mbind", "image": "nataal", "audio": "baat", "video": "vidéo"}
    type_wo = type_labels.get(content_type, content_type)

    lines = [
        f"{'─' * 32}",
        f"  {emoji}  *{verdict_text}*",
        f"{'─' * 32}",
        "",
        f"  Tollu : {risk}",
        f"  {bar}",
        f"  Lu ñu topp : {type_wo}",
        "",
    ]

    if ts:
        lines.append("📝 *Saytug mbind mi*")
        ts_risk = _risk_label_wo(ts.score)
        lines.append(f"  Tollu : {ts.score:.0f}/100 ({ts_risk})")

        if ts.transcription:
            preview = ts.transcription[:120].strip()
            lines.append(f"  Li mu wax :")
            lines.append(f"  « {preview} »")

        if ts.ocr_detected:
            lines.append(f"  Mbind bu ci nataal bi ñu ko jële.")

        if ts.sources_found:
            lines.append(f"  Fu mu jóge :")
            for src in ts.sources_found[:3]:
                lines.append(f"    - {src}")
        elif ts.factcheck_score is not None and ts.factcheck_score > 50:
            lines.append(f"  Amul source bu wóor bu ko dëgge.")

        lines.append("")

    if ds and ds.score > 0:
        lines.append("🛡️ *Saytug nataal/baat*")
        ds_risk = _risk_label_wo(ds.score)
        lines.append(f"  Tollu : {ds.score:.0f}/100 ({ds_risk})")

        if ds.manipulation_detected:
            if content_type == "audio":
                lines.append(f"  Baat bi mel na ni ordinatër moo ko def.")
            else:
                lines.append(f"  Nataal bi dañu ko soppi, du dëgg.")
            lines.append(f"  Ngëm : {ds.confidence:.1f}%")
        else:
            if content_type == "audio":
                lines.append(f"  Baat bi mel na ni dëgg la.")
            elif content_type == "image":
                lines.append(f"  Nataal bi amul lu ko soppi.")

        lines.append("")

    lines.append("💡 *Lan lañu wara def ?*")
    actions = {
        Verdict.FIABLE: "Li mel na ni dëgg la.\nWànte saytul fu mu jóge balaa nga ko yóbbu.",
        Verdict.DOUTEUX: "Mënuwuñu wax ni li dëgg walla fenn.\nSaytul ci yeneen fu mu jóge balaa nga ko yóbbu.",
        Verdict.PROBABLEMENT_FAUX: "Li am na lu ñu xam ni fenn la.\nBul ko yóbbu, waxal sa wàllu kër.",
        Verdict.DEEPFAKE: "Li mel na ni dañu ko febal ci ordinatër.\nBul ko yóbbu. Waxal kilifa yi.",
        Verdict.ARNAQUE: "Baat bii mel na ni arnaque la.\nBul tëral ci lien, bul tontu, dëngal kiy yónne.",
    }
    action_text = actions.get(verdict, "")
    for line in action_text.split("\n"):
        lines.append(f"  {line}")

    lines.append("")
    lines.append(f"⏱ Topp nañu ko ci {time_sec:.1f} saa")
    lines.append(f"_DeggBi AI — Dëgg Bi Ci Sa Loxo_")

    return "\n".join(lines)
