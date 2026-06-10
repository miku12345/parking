from datetime import datetime, timezone

from services.validator import validate_spot_payload
from repositories.firestore_repo import (
    save_parking_spot,
    add_parking_log,
    add_anomaly_event,
    get_all_spots,
    get_spot,
    get_recent_anomalies,
)

def utc_iso():
    return datetime.now(timezone.utc).isoformat()

def process_spot_update(payload: dict):
    is_valid, message = validate_spot_payload(payload)

    if not is_valid:
        add_anomaly_event({
            "event_id": f"evt_{int(datetime.now().timestamp())}",
            "spot_id": payload.get("spot_id", ""),
            "anomaly_type": "invalid_spot_payload",
            "timestamp": utc_iso(),
            "detail": message,
        })
        return {
            "ok": False,
            "warning": message,
            "saved_to_parking_db": False,
        }

    clean_data = {
        "spot_id": payload["spot_id"],
        "status": payload["status"],
        "reserved_plate": payload["reserved_plate"],
        "current_plate": payload["current_plate"],
    }

    save_parking_spot(clean_data)
    add_parking_log({
        **clean_data,
        "timestamp": utc_iso(),
    })

    return {
        "ok": True,
        "message": "saved to parking_spots",
        "saved_to_parking_db": True,
        "image_received": bool(payload.get("current_plate_image_base64")),
        "data": clean_data,
    }

def list_spots():
    return get_all_spots()

def get_one_spot(spot_id: str):
    data = get_spot(spot_id)
    if data is None:
        return {
            "ok": False,
            "warning": "spot_id not found",
        }
    return {
        "ok": True,
        "data": data,
    }

def list_anomalies(limit: int = 50):
    return get_recent_anomalies(limit=limit)
