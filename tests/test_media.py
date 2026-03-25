from app.utils.media import _guess_mime, _mime_to_ext


def test_guess_mime_jpg():
    assert _guess_mime("photos/image.jpg") == "image/jpeg"


def test_guess_mime_ogg():
    assert _guess_mime("voice/audio.ogg") == "audio/ogg"


def test_guess_mime_png():
    assert _guess_mime("file.png") == "image/png"


def test_guess_mime_unknown():
    assert _guess_mime("file.xyz") == "application/octet-stream"


def test_mime_to_ext_jpeg():
    assert _mime_to_ext("image/jpeg") == "jpg"


def test_mime_to_ext_ogg():
    assert _mime_to_ext("audio/ogg") == "ogg"


def test_mime_to_ext_unknown():
    assert _mime_to_ext("application/pdf") == "bin"
