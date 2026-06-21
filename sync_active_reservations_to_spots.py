from repositories.firestore_repo import (
    reservations_col,
    parking_spots_col,
)

def norm(x):
    return str(x or "").strip()

active_docs = (
    reservations_col
    .where("status", "==", "active")
    .limit(500)
    .stream()
)

count = 0

for doc in active_docs:
    res = doc.to_dict()
    reservation_id = res.get("reservation_id") or doc.id
    spot_id = norm(res.get("spot_id"))
    reserved_plate = norm(res.get("reserved_plate"))

    if not spot_id or not reserved_plate:
        continue

    spot_ref = parking_spots_col.document(spot_id)
    spot_doc = spot_ref.get()
    spot = spot_doc.to_dict() if spot_doc.exists else {}

    current_status = spot.get("status", "free")
    current_plate = norm(spot.get("current_plate"))

    update_data = {
        "spot_id": spot_id,
        "reserved_plate": reserved_plate,
        "active_reservation_id": reservation_id,
    }

    # 如果車位目前是 occupied / violation，不強制改成 reserved，
    # 只補上 reservation 關聯。
    if current_status in ["occupied", "violation"]:
        if current_status == "occupied" and current_plate == reserved_plate:
            update_data["reservation_matched"] = True
        else:
            update_data["reservation_matched"] = False

    # 如果車位目前是 free / reserved / 缺狀態，
    # 則以 active reservation 為準，改成 reserved。
    else:
        update_data.update({
            "status": "reserved",
            "current_plate": "",
            "reservation_matched": False,
        })

    spot_ref.set(update_data, merge=True)
    count += 1

print(f"synced active reservations to parking_spots: {count}")
