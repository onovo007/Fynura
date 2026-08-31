from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_voice_requires_explicit_activation_and_keeps_text_pipeline():
    script = (ROOT / "frontend" / "voice.js").read_text(encoding="utf-8")
    assert "mic.addEventListener('click'" in script
    assert "recognition.start()" in script
    assert "contextualAsk(transcript)" not in script
    assert "mic.dataset.ready = 'true'" in script
    assert "Review your question, then select Send" in script
    assert "#chat-q" in script


def test_voice_has_accessible_fallback_and_playback_controls():
    script = (ROOT / "frontend" / "voice.js").read_text(encoding="utf-8")
    for label in (
        "Dictate a question",
        "Stop speaking",
        "Replay spoken response",
        "Mute voice responses",
        "type your question",
    ):
        assert label in script
    assert "More detail and supporting evidence are shown on screen." in script


def test_privacy_notice_matches_transient_browser_voice_implementation():
    notice = (ROOT / "frontend" / "privacy.html").read_text(encoding="utf-8")
    assert "does not record or store raw audio" in notice
    assert "browser speech-recognition service" in notice
    assert "same evidence-grounded Ask Fynura pipeline" in notice
