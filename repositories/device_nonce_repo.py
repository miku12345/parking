import os
import hashlib
from google.cloud import firestore
from google.api_core.exceptions import AlreadyExists

PROJECT_ID = os.getenv("FIRESTORE_PROJECT", "project-8f03a674-75e0-47bd-9a3")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE", "parkingspots")

db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)
nonce_col = db.collection("device_nonces")

def reserve_nonce(device_id: str, nonce: str, timestamp: int) -> bool:
    raw = f"{device_id}:{nonce}".encode("utf-8")
    doc_id = hashlib.sha256(raw).hexdigest()

    try:
        nonce_col.document(doc_id).create({
            "device_id": device_id,
            "nonce": nonce,
            "timestamp": timestamp,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        return True
    except AlreadyExists:
        return False
