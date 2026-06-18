#!/usr/bin/env bash
set -euo pipefail

echo "== Parking backend body-hash signature patch =="

BACKEND_DIR="$HOME/parking_backend"

BACKEND_API_KEY="Iv_CWa6Eud79TNmOKY832GVLE7hx_SKSlX7n956cZxA"
PICO_001_SECRET="uNKToGkxB9ezLupzj-_iVEMk5QxWKLlqEF565yISVGg"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "ERROR: 找不到 Cloud Run backend 資料夾：$BACKEND_DIR"
  echo "請先用 ls ~ 確認資料夾名稱。"
  exit 1
fi

cd "$BACKEND_DIR"

echo "目前目錄：$(pwd)"

if [ ! -f "main.py" ]; then
  echo "ERROR: 找不到 main.py，這不像 backend 根目錄。"
  exit 1
fi

if [ ! -d "repositories" ]; then
  echo "ERROR: 找不到 repositories/，這可能不是你的 Cloud Run backend 專案。"
  exit 1
fi

if [ ! -f "repositories/device_nonce_repo.py" ]; then
  echo "ERROR: 找不到 repositories/device_nonce_repo.py"
  echo "你的 nonce 防重送檔案可能位置不同，先停止避免亂改。"
  exit 1
fi

BACKUP_DIR="backup_body_hash_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "device_security.py" ]; then
  cp device_security.py "$BACKUP_DIR/device_security.py.bak"
  echo "已備份 device_security.py -> $BACKUP_DIR/device_security.py.bak"
fi

cat > device_security.py <<'PY'
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


def build_message(method: str, path: str, timestamp: str, nonce: str, body_hash: str) -> str:
    """
    版本 B：簽整包 JSON body hash。

    message =
      METHOD
      PATH
      TIMESTAMP
      NONCE
      SHA256(JSON_BODY_BYTES)
    """
    return "\n".join([
        method.upper(),
        path,
        timestamp,
        nonce,
        body_hash,
    ])


async def verify_device_signature(request: Request):
    device_id = request.headers.get("X-Device-Id")
    timestamp = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")
    body_hash = request.headers.get("X-Body-SHA256")
    signature = request.headers.get("X-Signature")

    if not all([device_id, timestamp, nonce, body_hash, signature]):
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

    body_bytes = await request.body()
    actual_body_hash = hashlib.sha256(body_bytes).hexdigest()

    if not hmac.compare_digest(actual_body_hash, body_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid body hash"
        )

    message = build_message(
        method=request.method,
        path=request.url.path,
        timestamp=timestamp,
        nonce=nonce,
        body_hash=body_hash,
    )

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    ok = reserve_nonce(
        device_id=device_id,
        nonce=nonce,
        timestamp=ts,
    )

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Replay detected"
        )

    return True
PY

echo
echo "已寫入新版 device_security.py"
echo

echo "檢查後端目前是否有引用 verify_device_signature："
grep -R "verify_device_signature" . || true

echo
echo "開始 deploy Cloud Run..."
gcloud run deploy parking-backend \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated \
  --update-env-vars BACKEND_API_KEY="$BACKEND_API_KEY",PICO_001_SECRET="$PICO_001_SECRET"

echo
echo "完成。Cloud Run backend 已改成版本 B：body-hash 簽章。"
echo
echo "之後 Pico / Windows CLI 必須送這些 headers："
echo "  X-Device-Id"
echo "  X-Timestamp"
echo "  X-Nonce"
echo "  X-Body-SHA256"
echo "  X-Signature"
echo
echo "注意：這個 apply_body_hash_backend.sh 內含 key，不要 push 到 GitHub。"
