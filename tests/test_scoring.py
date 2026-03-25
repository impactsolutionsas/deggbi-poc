from app.core.scoring import compute_score_final, get_verdict, get_verdict_emoji, build_report
from app.models.analysis import Verdict, ScoreTruthScan, ScoreDeepShield


def test_compute_score_final_balanced():
    assert compute_score_final(80, 60) == 70.0


def test_compute_score_final_zero():
    assert compute_score_final(0, 0) == 0.0


def test_compute_score_final_max():
    assert compute_score_final(100, 100) == 100.0


def test_compute_score_final_clamped():
    assert compute_score_final(200, 200) == 100.0


def test_verdict_fiable():
    assert get_verdict(10) == Verdict.FIABLE


def test_verdict_douteux():
    assert get_verdict(45) == Verdict.DOUTEUX


def test_verdict_probablement_faux():
    assert get_verdict(75) == Verdict.PROBABLEMENT_FAUX


def test_verdict_deepfake():
    assert get_verdict(90, "audio") == Verdict.DEEPFAKE


def test_verdict_arnaque_text():
    assert get_verdict(90, "text") == Verdict.ARNAQUE


def test_verdict_emoji():
    assert get_verdict_emoji(Verdict.FIABLE) == "✅"
    assert get_verdict_emoji(Verdict.DEEPFAKE) == "🚨"


def test_build_report_contains_verdict():
    report = build_report(
        verdict=Verdict.DEEPFAKE,
        score_final=94,
        content_type="audio",
        language="fr",
        truthscan=ScoreTruthScan(score=90, transcription="Test audio"),
        deepshield=ScoreDeepShield(
            score=98, manipulation_detected=True, confidence=96.2
        ),
        analysis_time_ms=18000,
    )
    assert "DEEPFAKE CONFIRMÉ" in report
    assert "94/100" in report
    assert "DeggBi AI" in report
