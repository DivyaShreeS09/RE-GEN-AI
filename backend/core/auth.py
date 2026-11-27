"""Validate issuer-signed access tokens against a pinned public signing certificate."""
import os
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, Request
from google.auth import jwt


@dataclass(frozen=True)
class Member:
    tenant: str
    subject: str
    role: str


def validate_production_identity():
    from urllib.parse import urlsplit
    issuer = os.getenv("REGEN_AUTH_ISSUER", "")
    origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",")]
    if (not all(urlsplit(url).scheme == "https" and urlsplit(url).hostname for url in [issuer, *origins])
            or not os.getenv("REGEN_AUTH_AUDIENCE") or not Path(os.getenv("REGEN_AUTH_CERT_FILE", "")).is_file()
            or os.getenv("REGEN_DEV_IDENTITY") == "1"):
        raise RuntimeError("Production requires configured HTTPS origins, issuer, audience and signing certificate.")


async def require_member(request: Request) -> Member:
    if hasattr(request.state, "member"):
        return request.state.member
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not 0 < len(token) <= 16000:
        raise HTTPException(401, "Authentication required.")
    issuer = os.getenv("REGEN_AUTH_ISSUER")
    audience = os.getenv("REGEN_AUTH_AUDIENCE")
    cert_file = os.getenv("REGEN_AUTH_CERT_FILE")
    if not all((issuer, audience, cert_file)):
        raise HTTPException(503, "Identity provider unavailable.")
    try:
        cert = Path(cert_file).read_bytes()
    except OSError:
        raise HTTPException(503, "Signing certificate unavailable.")
    try:
        if jwt.decode_header(token).get("alg") != "RS256":
            raise ValueError()
        claims = jwt.decode(token, certs=cert, audience=audience)
        if claims["iss"] != issuer or claims.get("nbf", 0) > time.time():
            raise ValueError()
        metadata = claims["app_metadata"]
        member = Member(metadata["tenant_id"], claims["sub"], metadata["regen_role"])
        if not all(isinstance(x, str) and 0 < len(x) <= 128 for x in (member.tenant, member.subject)):
            raise ValueError()
    except (TypeError, ValueError, KeyError, AttributeError):
        raise HTTPException(401, "Invalid access token.")
    if member.role not in ("viewer", "staff", "admin"):
        raise HTTPException(403, "Facility membership required.")
    if request.method not in ("GET", "HEAD") and member.role == "viewer":
        raise HTTPException(403, "Facility staff role required.")
    from core.ai_client import _tenant
    request.state.member = member
    _tenant.set(member.tenant)
    return member
