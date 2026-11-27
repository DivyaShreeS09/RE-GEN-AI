"""Launch a loopback-only synthetic facility with ephemeral RS256 identity and SQLite."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, Request
from google.auth import crypt, jwt

BACKEND = Path(__file__).resolve().parents[1]
ORIGINS = {"http://localhost:15173", "http://127.0.0.1:15173"}


def require_local_mode():
    if os.environ.get("REGEN_ENV") != "development" or os.environ.get("REGEN_DEV_IDENTITY") != "1":
        raise RuntimeError("Set REGEN_ENV=development and REGEN_DEV_IDENTITY=1 for this isolated demo.")


def register_session(app, signer):
    require_local_mode()

    @app.post("/dev/session", include_in_schema=False)
    def local_session(request: Request):
        require_local_mode()
        if (not request.client or request.client.host not in {"127.0.0.1", "::1"}
                or request.headers.get("host") not in {"localhost:18000", "127.0.0.1:18000"}
                or request.headers.get("origin") not in ORIGINS
                or request.headers.get("x-regen-local") != "1"):
            raise HTTPException(403, "Local development browser required.")
        issued = int(time.time())
        claims = dict(iss="regen-local-demo", aud="regen-local-demo", sub="synthetic-staff",
                      app_metadata={"tenant_id": "synthetic-local-facility", "regen_role": os.getenv("REGEN_DEMO_ROLE", "staff")},
                      iat=issued, exp=issued + 900)
        from fastapi.responses import JSONResponse
        return JSONResponse({"access_token": jwt.encode(signer, claims).decode(), "expires_in": 900},
                            headers={"Cache-Control": "no-store"})


def main():
    require_local_mode()
    sys.path.insert(0, str(BACKEND))
    with TemporaryDirectory(prefix="regen-demo-", dir=BACKEND.parent) as folder:
        db = Path(folder) / "synthetic.db"
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cert = Path(folder) / "public.pem"
        cert.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                       serialization.PublicFormat.SubjectPublicKeyInfo))
        os.environ.update(REGEN_AI_PROVIDER=os.getenv("REGEN_DEMO_AI_PROVIDER", "offline"), DATABASE_URL=f"sqlite:///{db.as_posix()}",
                          REGEN_AUTH_CERT_FILE=str(cert), REGEN_AUTH_ISSUER="regen-local-demo",
                          REGEN_AUTH_AUDIENCE="regen-local-demo", SLACK_WEBHOOK_URL="",
                          ALLOWED_ORIGINS=",".join(sorted(ORIGINS)))
        import uvicorn
        from main import app
        from core.database import engine
        register_session(app, crypt.RSASigner(key))
        worker = subprocess.Popen([sys.executable, str(BACKEND / "scripts" / "mission_worker.py")])
        try:
            uvicorn.run(app, host="127.0.0.1", port=18000, proxy_headers=False)
        finally:
            worker.terminate()
            worker.wait()
            engine.dispose()


if __name__ == "__main__":
    main()
