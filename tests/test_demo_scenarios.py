"""
Tests des 3 scénarios de démo hackathon iSAFE.
Simulent le pipeline complet : TruthScan + DeepShield → Scoring → Report.
"""
from app.core.scoring import compute_score_final, get_verdict
from app.services.reporter import generate_report
from app.models.analysis import Verdict, ScoreTruthScan, ScoreDeepShield
from app.services.truthscan import _detect_scam_patterns


class TestScenario1_FauxDiscoursPresidentiel:
    """Audio WhatsApp — voix clonée — attendu: ~94/100 DEEPFAKE CONFIRMÉ."""

    def test_scoring(self):
        score = compute_score_final(92, 96)
        assert score == 94.0

    def test_verdict(self):
        verdict = get_verdict(94, "audio")
        assert verdict == Verdict.DEEPFAKE

    def test_report(self):
        ts = ScoreTruthScan(
            score=92,
            transcription="Le président a annoncé la dissolution de l'assemblée nationale...",
            factcheck_score=80,
        )
        ds = ScoreDeepShield(
            score=96,
            audio_score=96,
            manipulation_detected=True,
            confidence=96.2,
            details="Wav2Vec2 — analyse vocale complète",
        )
        report = generate_report(
            verdict=Verdict.DEEPFAKE,
            score_final=94,
            content_type="audio",
            language="fr",
            truthscan=ts,
            deepshield=ds,
            analysis_time_ms=18000,
        )
        assert "DEEPFAKE CONFIRMÉ" in report
        assert "94/100" in report
        assert "Voix synthétique" in report
        assert "96.2%" in report
        assert "Signaler aux autorités" in report


class TestScenario2_PhotoViraleRecyclee:
    """Image WhatsApp — inondation Bangladesh → Sénégal — attendu: ~78/100 PROBABLEMENT FAUX."""

    def test_scoring(self):
        score = compute_score_final(70, 86)
        assert score == 78.0

    def test_verdict(self):
        verdict = get_verdict(78, "image")
        assert verdict == Verdict.PROBABLEMENT_FAUX

    def test_report(self):
        ts = ScoreTruthScan(
            score=70,
            ocr_detected=True,
            factcheck_score=70,
            details="OCR + contexte vérifié",
        )
        ds = ScoreDeepShield(
            score=86,
            image_score=86,
            manipulation_detected=True,
            confidence=88.5,
            details="EfficientNet — analyse visuelle complète",
        )
        report = generate_report(
            verdict=Verdict.PROBABLEMENT_FAUX,
            score_final=78,
            content_type="image",
            language="fr",
            truthscan=ts,
            deepshield=ds,
            analysis_time_ms=22000,
        )
        assert "PROBABLEMENT FAUX" in report
        assert "78/100" in report
        assert "Manipulation visuelle" in report


class TestScenario3_ArnaqueMobileMoney:
    """Texte SMS — faux Orange Money — attendu: ~88/100 ARNAQUE CONFIRMÉE."""

    SCAM_TEXT = (
        "Félicitations! Vous avez gagné 500.000 FCFA sur Orange Money. "
        "Cliquez ici pour réclamer: http://orange-money-sn.xyz/claim "
        "Urgent — votre code secret expire dans 10 minutes!"
    )

    def test_scam_detection_patterns(self):
        score = _detect_scam_patterns(self.SCAM_TEXT)
        assert score >= 65

    def test_scoring(self):
        score = compute_score_final(88, 0)
        assert score == 44.0  # DeepShield=0 car texte pur
        # En réalité le score TruthScan domine pour le texte
        # Le pipeline réel pondère différemment

    def test_verdict_text_high_score(self):
        verdict = get_verdict(88, "text")
        assert verdict == Verdict.ARNAQUE

    def test_report(self):
        ts = ScoreTruthScan(
            score=88,
            factcheck_score=85,
            sources_found=[],
            details="Patterns d'arnaque détectés — Classification NLP effectuée",
        )
        report = generate_report(
            verdict=Verdict.ARNAQUE,
            score_final=88,
            content_type="text",
            language="fr",
            truthscan=ts,
            deepshield=None,
            analysis_time_ms=9000,
        )
        assert "ARNAQUE CONFIRMÉE" in report
        assert "88/100" in report
        assert "Bloquer" in report


class TestScenarioWolof:
    """Vérifie que les 3 scénarios fonctionnent aussi en Wolof."""

    def test_deepfake_wolof(self):
        report = generate_report(
            verdict=Verdict.DEEPFAKE, score_final=94, content_type="audio",
            language="wo",
            truthscan=ScoreTruthScan(score=92),
            deepshield=ScoreDeepShield(score=96, manipulation_detected=True, confidence=96.2),
            analysis_time_ms=18000,
        )
        assert "DEEPFAKE DËGG NA" in report
        assert "Waxal kilifa yi" in report

    def test_arnaque_wolof(self):
        report = generate_report(
            verdict=Verdict.ARNAQUE, score_final=88, content_type="text",
            language="wo",
            truthscan=ScoreTruthScan(score=88),
            deepshield=None,
            analysis_time_ms=9000,
        )
        assert "ARNAQUE DËGG NA" in report
        assert "Dëngal" in report
