from app.models.analysis import (
    ContentType, Channel, Verdict, Language,
    ScoreTruthScan, ScoreDeepShield, AnalysisResult, AnalysisRequest,
)


def test_content_type_values():
    assert ContentType.TEXT.value == "text"
    assert ContentType.IMAGE.value == "image"
    assert ContentType.AUDIO.value == "audio"


def test_verdict_values():
    assert Verdict.FIABLE.value == "CONTENU FIABLE"
    assert Verdict.DEEPFAKE.value == "DEEPFAKE CONFIRMÉ"


def test_score_truthscan_defaults():
    s = ScoreTruthScan(score=50)
    assert s.ocr_detected is False
    assert s.sources_found == []


def test_score_deepshield_defaults():
    s = ScoreDeepShield(score=80)
    assert s.manipulation_detected is False
    assert s.confidence == 0.0


def test_analysis_request():
    req = AnalysisRequest(content="test", content_type=ContentType.TEXT)
    assert req.channel == Channel.API
    assert req.language == Language.FR


def test_analysis_result_has_id():
    r = AnalysisResult(
        content_type=ContentType.TEXT,
        channel=Channel.WHATSAPP,
        score_truthscan=50,
        score_deepshield=30,
        score_final=40,
        verdict=Verdict.DOUTEUX,
    )
    assert r.id is not None
    assert len(r.id) == 36  # UUID format
