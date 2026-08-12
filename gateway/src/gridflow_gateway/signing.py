import hashlib
import hmac
import json
import time
from typing import Any


def compact_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def signed_headers(body: bytes, secret: str, sent_at: int | None = None) -> dict[str, str]:
    timestamp = sent_at if sent_at is not None else int(time.time())
    payload = str(timestamp).encode("ascii") + b"." + body
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return {
        "content-type": "application/json",
        "x-gridflow-sent-at": str(timestamp),
        "x-gridflow-signature": f"sha256={digest}",
    }
