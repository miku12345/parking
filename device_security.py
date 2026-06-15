import os
import time
import hmac
import hashlib
from fastapi import Request, HTTPException, status
from repositories.device_nonce_repo import reserve_nonce

DEVICE_SECRETS = {
    "pico-001": os.getenv("PICO_001_SECRET", "")
}

ALLOWED_TIME_DRIFT_SECONDS = 60

def build_message(method: str, path: str, timestamp: str, nonce: str, payload: dict) -> str:
    return "\n".join([
        method.upper(),
        path,
        timestamp,
        nonce,
        payload.get("spot_id", ""),
        payload.get("status", ""),
        payload.get("reserved_plate", ""),
        payload.get("current_plate", ""),
    ])

async def verify_device_signature(request: Request):
    device_id = request.headers.get("X-Device-Id")
    timestamp = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")
    signature = request.headers.get("X-Signature")

    if not all([device_id, timestamp, nonce, signature]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing device auth headers"
        )

    secret = DEVICE_SECRETS.get(device_id)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown device"
        )

    try:
        ts = int(timestamp)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid timestamp"
        )

    now = int(time.time())
    if abs(now - ts) > ALLOWED_TIME_DRIFT_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Timestamp expired"
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    message = build_message(
        method=request.method,
        path=request.url.path,
        timestamp=timestamp,
        nonce=nonce,
        payload=payload,
    )

    expected = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    ok = reserve_nonce(device_id=device_id, nonce=nonce, timestamp=ts)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Replay detected"
        )

    return True
