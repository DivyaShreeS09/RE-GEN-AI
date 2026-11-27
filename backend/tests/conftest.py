import os
import socket
import tempfile
import sys
from pathlib import Path

import pytest

# Configure before collection imports main or SQLAlchemy.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_test_dir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2], prefix=".regen-test-", ignore_cleanup_errors=True)
os.environ.update(RATELIMIT_ENABLED="false", REGEN_ENV="test", REGEN_AI_PROVIDER="offline", GEMINI_API_KEY="", GROQ_API_KEY="", GEMINI_MODEL="fixture-model",
                  SLACK_WEBHOOK_URL="", DATABASE_URL=f"sqlite:///{Path(_test_dir.name).as_posix()}/runs.db")
_pg_schema = None

if os.environ.get("REGEN_TEST_POSTGRES") == "1":
    import psycopg
    from uuid import uuid4
    from sqlalchemy.engine import make_url

    _pg_dsn = os.environ.get("REGEN_TEST_POSTGRES_DSN")

    if not _pg_dsn:
        raise RuntimeError(
            "REGEN_TEST_POSTGRES_DSN is required "
            "for PostgreSQL integration tests."
        )

    _pg_url = make_url(_pg_dsn)

    if (
        _pg_url.get_backend_name() != "postgresql"
        or _pg_url.host != "127.0.0.1"
        or _pg_url.database != "regen_test"
        or _pg_url.port != 5433
        or set(_pg_url.query) - {"connect_timeout", "sslmode"}
    ):
        raise RuntimeError(
            "PostgreSQL tests require the dedicated "
            "local regen_test database."
        )

    _pg_schema = "fixture_" + uuid4().hex

    with psycopg.connect(
        _pg_dsn, connect_timeout=5
    ) as conn:
        _pg_version = conn.execute("SHOW server_version").fetchone()[0]
        conn.execute(
            psycopg.sql.SQL("CREATE SCHEMA {}").format(
                psycopg.sql.Identifier(_pg_schema)
            )
        )

    _test_url = _pg_url.set(
        drivername="postgresql+psycopg"
    ).update_query_dict({
        "connect_timeout": "5",
        "options": f"-csearch_path={_pg_schema}",
    })

    os.environ["DATABASE_URL"] = (
        _test_url.render_as_string(hide_password=False)
    )

_original_connect = socket.socket.connect


def _offline_connect(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in ("127.0.0.1", "::1"):
        raise AssertionError("Outbound network disabled in tests")
    return _original_connect(sock, address)


_original_resolve = socket.getaddrinfo
_original_connect_ex = socket.socket.connect_ex


def _offline_resolve(host, *args, **kwargs):
    if host not in (None, "127.0.0.1", "::1", "localhost"):
        raise AssertionError("External name resolution disabled in tests")
    return _original_resolve(host, *args, **kwargs)


def _offline_connect_ex(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in ("127.0.0.1", "::1"):
        raise AssertionError("Outbound network disabled in tests")
    return _original_connect_ex(sock, address)


def pytest_configure(config):
    from sqlalchemy.engine import make_url
    test_url = make_url(os.environ["DATABASE_URL"])
    print("\nTest database engine:", test_url.get_backend_name())
    if _pg_schema:
        print("PostgreSQL server version:", _pg_version)
    if config.option.basetemp is None:
        config.option.basetemp = str(Path(_test_dir.name) / "pytest")
    socket.socket.connect = _offline_connect
    socket.socket.connect_ex = _offline_connect_ex
    socket.getaddrinfo = _offline_resolve


def pytest_unconfigure(config):
    database = sys.modules.get("core.database")
    if database is not None:
        database.engine.dispose()
    if _pg_schema:
        with psycopg.connect(_pg_dsn) as conn:
            conn.execute(psycopg.sql.SQL("DROP SCHEMA {} CASCADE").format(psycopg.sql.Identifier(_pg_schema)))
            remaining, = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname = %s", (_pg_schema,)).fetchone()
            assert remaining == 0
        print("Current PostgreSQL fixture schemas remaining:", remaining)
    socket.socket.connect = _original_connect
    socket.socket.connect_ex = _original_connect_ex
    socket.getaddrinfo = _original_resolve


@pytest.fixture(autouse=True)
def reset_ai_state(monkeypatch):
    from core import ai_client
    monkeypatch.setattr(ai_client, "_retry_after", 0.0)
    usage = ai_client._usage.set(0)
    yield
    ai_client._usage.reset(usage)


@pytest.fixture(scope="session")
def signing_key():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path = Path(_test_dir.name) / "fixture-public.pem"
    path.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    os.environ.update(REGEN_AUTH_ISSUER="fixture-issuer", REGEN_AUTH_AUDIENCE="fixture-audience", REGEN_AUTH_CERT_FILE=str(path))
    return key


@pytest.fixture
def token_for(signing_key):
    from google.auth import jwt, crypt
    import time
    def issue(tenant="fixture", role="staff", subject="fixture-user"):
        now = int(time.time())
        payload = dict(iss="fixture-issuer", aud="fixture-audience", sub=subject, exp=now+600, iat=now,
                       app_metadata={"tenant_id": tenant, "regen_role": role})
        return "Bearer " + jwt.encode(crypt.RSASigner(signing_key), payload).decode()
    return issue
