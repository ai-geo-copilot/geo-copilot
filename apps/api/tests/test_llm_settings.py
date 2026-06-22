from apps.api.app.llm.settings import DeepSeekSettings


def test_deepseek_settings_reads_dotenv_when_environment_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "DEEPSEEK_API_KEY=placeholder-key",
                "DEEPSEEK_BASE_URL=https://example.invalid",
                "DEEPSEEK_MODEL=deepseek-test",
            ]
        ),
        encoding="utf-8",
    )

    settings = DeepSeekSettings.from_env()

    assert settings.api_key == "placeholder-key"
    assert settings.base_url == "https://example.invalid"
    assert settings.model == "deepseek-test"


def test_deepseek_settings_environment_overrides_dotenv(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=dotenv-key", encoding="utf-8")

    settings = DeepSeekSettings.from_env()

    assert settings.api_key == "env-key"
