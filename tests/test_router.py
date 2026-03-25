from app.core.config import detect_content_type, route_to_pipeline
from app.models.analysis import ContentType


def test_detect_by_mime_image():
    assert detect_content_type(mime_type="image/jpeg") == ContentType.IMAGE


def test_detect_by_mime_audio():
    assert detect_content_type(mime_type="audio/ogg") == ContentType.AUDIO


def test_detect_by_mime_video():
    assert detect_content_type(mime_type="video/mp4") == ContentType.VIDEO


def test_detect_by_filename():
    assert detect_content_type(filename="photo.png") == ContentType.IMAGE


def test_detect_by_filename_audio():
    assert detect_content_type(filename="voice.ogg") == ContentType.AUDIO


def test_detect_text_fallback():
    assert detect_content_type(text="Bonjour le monde") == ContentType.TEXT


def test_detect_unknown():
    assert detect_content_type() == ContentType.UNKNOWN


def test_route_text_pipeline():
    p = route_to_pipeline(ContentType.TEXT)
    assert "nlp" in p["truthscan"]
    assert p["deepshield"] == []


def test_route_image_pipeline():
    p = route_to_pipeline(ContentType.IMAGE)
    assert "ocr" in p["truthscan"]
    assert "efficientnet" in p["deepshield"]


def test_route_audio_pipeline():
    p = route_to_pipeline(ContentType.AUDIO)
    assert "whisper_stt" in p["truthscan"]
    assert "wav2vec2" in p["deepshield"]
