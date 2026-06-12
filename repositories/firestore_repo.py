import os
from google.cloud import firestore

PROJECT_ID = os.getenv("FIRESTORE_PROJECT", "project-8f03a674-75e0-47bd-9a3")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE", "parkingspots")

db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

parking_spots_col = db.collection("parking_spots")
parking_logs_col = db.collection("parking_logs")
reservations_col = db.collection("reservations")
anomaly_events_col = db.collection("anomaly_events")

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
    # used by the AI prediction module as training data
    return [doc.to_dict() for doc in parking_logs_col.limit(limit).stream()]

def add_logs_batch(rows: list[dict]):
    # batched writes so seeding thousands of synthetic logs stays fast/cheap
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

def get_reservations(limit: int = 50):
    return [doc.to_dict() for doc in reservations_col.limit(limit).stream()]

def add_anomaly_event(data: dict):
    anomaly_events_col.add(data)

def get_recent_anomalies(limit: int = 50):
    return [doc.to_dict() for doc in anomaly_events_col.limit(limit).stream()]
