from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from common_gateway_service.core.config import settings


SESSION_COOKIE_NAME = "trinetra_session"
SESSION_TTL_SECONDS = 60 * 60 * 24
JWT_ISSUER = "trinetra"
JWT_TYPE = "JWT"


def _secret_bytes() -> bytes:
    return settings.auth_secret.encode("utf-8")


def _base64_url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _base64_url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _json_b64(value: dict[str, Any]) -> str:
    return _base64_url_encode(json.dumps(value, separators=(",", ":")).encode("utf-8"))


def _sign(signing_input: str) -> str:
    digest = hmac.new(
        _secret_bytes(),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64_url_encode(digest)


def create_session_token(user_id: str) -> str:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required to create a session token.")

    issued_at = int(time.time())
    expires_at = issued_at + SESSION_TTL_SECONDS

    encoded_header = _json_b64({"alg": "HS256", "typ": JWT_TYPE})
    encoded_payload = _json_b64(
        {
            "iss": JWT_ISSUER,
            "sub": normalized_user_id,
            "iat": issued_at,
            "exp": expires_at,
        }
    )
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = _sign(signing_input)
    return f"{signing_input}.{signature}"


def _parse_payload(token: str) -> dict[str, Any] | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        return json.loads(_base64_url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError):
        return None


def verify_session_token(token: str | None) -> bool:
    if not token:
        return False

    parts = token.split(".")
    if len(parts) != 3:
        return False

    encoded_header, encoded_payload, provided_signature = parts

    try:
        header = json.loads(_base64_url_decode(encoded_header))
        payload = json.loads(_base64_url_decode(encoded_payload))
    except (ValueError, json.JSONDecodeError):
        return False

    if header.get("alg") != "HS256" or header.get("typ") != JWT_TYPE:
        return False

    if payload.get("iss") != JWT_ISSUER or not isinstance(payload.get("sub"), str):
        return False

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or int(time.time()) > expires_at:
        return False

    expected_signature = _sign(f"{encoded_header}.{encoded_payload}")
    return hmac.compare_digest(provided_signature, expected_signature)


def get_session_user_id(token: str | None) -> str | None:
    if not verify_session_token(token):
        return None
    payload = _parse_payload(token or "")
    subject = payload.get("sub") if payload else None
    return subject if isinstance(subject, str) else None

