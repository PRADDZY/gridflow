import hashlib
import hmac
import os
import time

from fastapi import HTTPException, Request, status

MAX_INGRESS_AGE_SECONDS = 60


async def require_signed_ingress(request: Request) -> None:
    env = request.scope.get("env")
    secret = _binding_value(env, "INGESTION_HMAC_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingress signing is not configured.",
        )

    sent_at = request.headers.get("x-gridflow-sent-at")
    signature = request.headers.get("x-gridflow-signature")
    if not sent_at or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing ingress signature.")

    try:
        sent_at_seconds = int(sent_at)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingress timestamp.") from exc

    if abs(time.time() - sent_at_seconds) > MAX_INGRESS_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired ingress request.")

    body = await request.body()
    signing_payload = sent_at.encode("ascii") + b"." + body
    expected = hmac.new(secret.encode("utf-8"), signing_payload, hashlib.sha256).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingress signature.")


def _binding_value(env: object | None, name: str) -> str | None:
    if env is None:
        return os.environ.get(name)
    value = getattr(env, name, None)
    return str(value) if value is not None else None
