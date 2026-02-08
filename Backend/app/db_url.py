from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def backend_local_db_url() -> str:
    return f"sqlite+pysqlite:///{(PROJECT_ROOT / 'local_dev.db').resolve()}"


def normalize_sqlite_url(database_url: str) -> str:
    if database_url.startswith("sqlite+pysqlite:///./"):
        relative_path = database_url.removeprefix("sqlite+pysqlite:///./")
        absolute_path = (PROJECT_ROOT / relative_path).resolve()
        return f"sqlite+pysqlite:///{absolute_path}"
    if database_url.startswith("sqlite:///./"):
        relative_path = database_url.removeprefix("sqlite:///./")
        absolute_path = (PROJECT_ROOT / relative_path).resolve()
        return f"sqlite:///{absolute_path}"
    return database_url
