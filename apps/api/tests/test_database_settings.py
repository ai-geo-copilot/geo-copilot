from apps.api.app.main import _load_database_url


def test_load_database_url_prefers_process_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql://from-file\n", encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", "postgresql://from-env")

    assert _load_database_url() == "postgresql://from-env"


def test_load_database_url_reads_dotenv_fallback(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GEO_DISABLE_DOTENV_DATABASE", raising=False)
    (tmp_path / ".env").write_text(
        "\n# comment\nDATABASE_URL='postgresql://geo:geo@localhost:5432/geo'\n",
        encoding="utf-8",
    )

    assert _load_database_url() == "postgresql://geo:geo@localhost:5432/geo"


def test_load_database_url_can_disable_dotenv_fallback(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("GEO_DISABLE_DOTENV_DATABASE", "1")
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql://from-file\n", encoding="utf-8")

    assert _load_database_url() is None
