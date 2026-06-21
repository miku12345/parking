from datetime import datetime, timedelta, timezone
from uuid import uuid4

from services.validator import validate_reservation_payload
from repositories.firestore_repo import (
    get_spot,
    create_reservation,
    save_parking_spot,
    add_parking_log,
    add_anomaly_event,
    get_reservations,
    get_active_reservations_from_parking_spots,
)

def utc_iso():
    return datetime.now(timezone.utc).isoformat()

def create_reservation_request(payload: dict):
    is_valid, message = validate_reservation_payload(payload)

    if not is_valid:
        add_anomaly_event({
            "event_id": f"evt_{int(datetime.now().timestamp())}",
            "spot_id": payload.get("spot_id", ""),
            "anomaly_type": "invalid_reservation_payload",
            "timestamp": utc_iso(),
            "detail": message,
        })
        return {
            "ok": False,
            "warning": message,
            "saved": False,
        }

    spot = get_spot(payload["spot_id"])
    if not spot:
        return {
            "ok": False,
            "warning": "spot_id not found",
            "saved": False,
        }

    if spot["status"] != "free":
        return {
            "ok": False,
            "warning": "spot is not free",
            "saved": False,
        }

    reservation_id = str(uuid4())[:8]
    created_at = datetime.now(timezone.utc)
    expired_at = created_at + timedelta(days=30)

    reservation = {
        "reservation_id": reservation_id,
        "spot_id": payload["spot_id"],
        "reserved_plate": payload["reserved_plate"],
        "status": "active",
        "created_at": created_at.isoformat(),
        "expired_at": expired_at.isoformat(),
    }

    create_reservation(reservation)

    updated_spot = {
        "spot_id": payload["spot_id"],
        "status": "reserved",
        "reserved_plate": payload["reserved_plate"],
        "current_plate": "",
    }

    save_parking_spot(updated_spot)
    add_parking_log({
        **updated_spot,
        "timestamp": utc_iso(),
    })

    return {
        "ok": True,
        "message": "reservation created",
        "saved": True,
        "reservation": reservation,
        "spot": updated_spot,
    }

def list_reservation_items(limit: int = 50):
    # Admin Active Reservations 改用 parking_spots 目前 reserved_plate 狀態。
    # 這樣 A01 這種 violation / occupied 但仍有 reserved_plate 的車位也會顯示。
    return get_active_reservations_from_parking_spots(limit=limit)

