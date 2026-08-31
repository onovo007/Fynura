from backend.config import Settings


def test_single_model_default_and_legacy_reader():
    settings = Settings(_env_file=None)
    assert settings.fynura_chat_model == "gemini-3.7-flash"
    assert settings.fynura_model == settings.fynura_chat_model


def test_explicit_model_override_is_shared():
    settings = Settings(_env_file=None, fynura_chat_model="test-model")
    assert settings.fynura_model == "test-model"
