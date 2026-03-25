from app.services.reporter import generate_report
from app.models.analysis import Verdict, ScoreTruthScan, ScoreDeepShield


def _make_report(lang="fr", verdict=Verdict.DEEPFAKE, score=94, content_type="audio"):
    return generate_report(
        verdict=verdict,
        score_final=score,
        content_type=content_type,
        language=lang,
        truthscan=ScoreTruthScan(
            score=90,
            transcription="Le président a déclaré que...",
            factcheck_score=80,
        ),
        deepshield=ScoreDeepShield(
            score=98,
            manipulation_detected=True,
            confidence=96.2,
        ),
        analysis_time_ms=18000,
    )


def test_report_fr_contains_verdict():
    report = _make_report("fr")
    assert "DEEPFAKE CONFIRMÉ" in report
    assert "94/100" in report
    assert "DeggBi AI" in report


def test_report_fr_contains_details():
    report = _make_report("fr")
    assert "Voix synthétique" in report
    assert "Confiance" in report
    assert "96.2%" in report


def test_report_en():
    report = _make_report("en")
    assert "CONFIRMED DEEPFAKE" in report
    assert "DeggBi AI Analysis" in report
    assert "Synthetic voice" in report
    assert "Confidence" in report


def test_report_wolof():
    report = _make_report("wo")
    assert "DEEPFAKE DËGG NA" in report
    assert "DeggBi AI" in report
    assert "Cëru" in report


def test_report_fiable_fr():
    report = _make_report("fr", verdict=Verdict.FIABLE, score=15)
    assert "CONTENU FIABLE" in report
    assert "authentique" in report


def test_report_arnaque_fr():
    report = generate_report(
        verdict=Verdict.ARNAQUE,
        score_final=88,
        content_type="text",
        language="fr",
        truthscan=ScoreTruthScan(score=88, factcheck_score=85),
        deepshield=None,
        analysis_time_ms=9000,
    )
    assert "ARNAQUE CONFIRMÉE" in report
    assert "Bloquer" in report


def test_report_unknown_lang_falls_back_to_fr():
    report = generate_report(
        verdict=Verdict.DOUTEUX,
        score_final=45,
        content_type="text",
        language="xx",
        truthscan=None,
        deepshield=None,
        analysis_time_ms=5000,
    )
    assert "Analyse DeggBi AI" in report
