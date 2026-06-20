import os
from datetime import datetime, timezone
from google.cloud import firestore
import requests
from dotenv import load_dotenv

PROJECT_ID = os.getenv("FIRESTORE_PROJECT", "project-8f03a674-75e0-47bd-9a3")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE", "parkingspots")
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

parking_spots_col = db.collection("parking_spots")
parking_logs_col = db.collection("parking_logs")
reservations_col = db.collection("reservations")
anomaly_events_col = db.collection("anomaly_events")

def utc_iso():
    return datetime.now(timezone.utc).isoformat()

def get_all_spots():
    return [doc.to_dict() for doc in parking_spots_col.stream()]

def get_spot(spot_id: str):
    doc = parking_spots_col.document(spot_id).get()
    return doc.to_dict() if doc.exists else None

def save_parking_spot(data: dict):
    parking_spots_col.document(data["spot_id"]).set(data)

def add_parking_log(data: dict):
    parking_logs_col.add(data)

def get_logs(limit: int = 50, spot_id: str | None = None):
    docs = parking_logs_col.limit(limit).stream()
    results = [doc.to_dict() for doc in docs]
    if spot_id:
        results = [item for item in results if item.get("spot_id") == spot_id]
    return results

def get_all_logs(limit: int = 10000):
    return [doc.to_dict() for doc in parking_logs_col.limit(limit).stream()]

def add_logs_batch(rows: list[dict]):
    batch = db.batch()
    pending = 0
    written = 0

    for row in rows:
        batch.set(parking_logs_col.document(), row)
        pending += 1

        if pending >= 450:
            batch.commit()
            written += pending
            batch = db.batch()
            pending = 0

    if pending:
        batch.commit()
        written += pending

    return written

def create_reservation(data: dict):
    reservations_col.document(data["reservation_id"]).set(data)

def get_reservations(limit: int = 50, active_only: bool = True):
    """
    Reservation API.

    active_only=True:
      只回傳 status == active，避免 Admin Active Reservations 顯示 cancelled。
    """
    if active_only:
        docs = (
            reservations_col
            .where("status", "==", "active")
            .limit(limit)
            .stream()
        )
    else:
        docs = reservations_col.limit(limit).stream()

    results = []

    for doc in docs:
        data = doc.to_dict()
        data.setdefault("reservation_id", doc.id)
        results.append(data)

    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results


def get_active_reservation_for_spot(spot_id: str):
    """
    回傳指定車位目前 active 的預約。
    若同一車位意外有多筆 active，取 created_at 最新的一筆。
    """
    docs = (
        reservations_col
        .where("spot_id", "==", spot_id)
        .where("status", "==", "active")
        .limit(20)
        .stream()
    )

    items = []

    for doc in docs:
        data = doc.to_dict()
        data.setdefault("reservation_id", doc.id)
        items.append(data)

    if not items:
        return None

    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[0]

def cancel_reservation(reservation_id: str, reason: str = "vehicle_left_after_valid_reservation"):
    """
    不刪除 reservation 文件，而是把 status 改成 cancelled，保留紀錄。
    """
    if not reservation_id:
        return None

    update_data = {
        "status": "cancelled",
        "cancel_reason": reason,
        "cancelled_at": utc_iso(),
    }

    reservations_col.document(reservation_id).set(update_data, merge=True)

    return {
        "reservation_id": reservation_id,
        **update_data,
    }

def cancel_active_reservations_for_spot(
    spot_id: str,
    reason: str = "vehicle_left_after_valid_reservation"
):
    docs = (
        reservations_col
        .where("spot_id", "==", spot_id)
        .where("status", "==", "active")
        .limit(20)
        .stream()
    )

    cancelled = []

    for doc in docs:
        cancelled_item = cancel_reservation(doc.id, reason=reason)
        if cancelled_item:
            cancelled.append(cancelled_item)

    return cancelled

def add_anomaly_event(data: dict):
    anomaly_events_col.add(data)

    if DISCORD_WEBHOOK_URL:
        try:
            msg = (
                f"⚠️ **停車場系統異常警報** ⚠️\n"
                f"**車位**: {data.get('spot_id', 'N/A')}\n"
                f"**類型**: {data.get('anomaly_type')}\n"
                f"**詳情**: {data.get('detail')}"
            )

            requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=3)

        except Exception as e:
            print(f"Failed to send webhook: {e}")

def get_recent_anomalies(limit: int = 50):
    return [doc.to_dict() for doc in anomaly_events_col.limit(limit).stream()]

def get_active_reservations_from_parking_spots(limit: int = 50):
    """
    Admin Active Reservations 改看 parking_spots 的目前狀態。

    只要車位還有 reserved_plate，就代表這個預約仍然有效。
    即使 status 是 occupied / violation，也要顯示，
    因為像 A01 這種違規佔用仍然有 active reservation。
    """
    docs = parking_spots_col.limit(500).stream()

    results = []

    for doc in docs:
        data = doc.to_dict() or {}

        spot_id = data.get("spot_id") or doc.id
        status = str(data.get("status") or "free").lower()
        reserved_plate = str(data.get("reserved_plate") or "").strip()
        current_plate = str(data.get("current_plate") or "").strip()

        if not reserved_plate:
            continue

        if status == "free":
            continue

        results.append({
            "reservation_id": data.get("active_reservation_id", ""),
            "spot_id": spot_id,
            "reserved_plate": reserved_plate,
            "current_plate": current_plate,
            "spot_status": status,
            "status": "active",
            "created_at": data.get("created_at", ""),
            "expired_at": data.get("expired_at", ""),
        })

    results.sort(key=lambda x: x.get("spot_id", ""))
    return results[:limit]
