from datetime import datetime, timezone

from services.validator import validate_spot_payload
from services.plate_service import normalize_plate_text, recognize_plate_from_base64
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

    status = payload["status"]
    input_plate = normalize_plate_text(payload.get("current_plate", ""))
    image_base64 = payload.get("current_plate_image_base64", "")

    recognized_plate = ""
    raw_ocr_text = ""
    image_received = bool(image_base64)
    recognition_used = False
    plate_mismatch = False

    if image_received:
        try:
            ocr_result = recognize_plate_from_base64(image_base64)
            raw_ocr_text = ocr_result.get("raw_text", "")
            recognized_plate = normalize_plate_text(ocr_result.get("plate_text", ""))
        except Exception as e:
            add_anomaly_event({
                "event_id": f"evt_{int(datetime.now().timestamp())}",
                "spot_id": payload.get("spot_id", ""),
                "anomaly_type": "plate_recognition_failed",
                "timestamp": utc_iso(),
                "detail": str(e),
            })
            return {
                "ok": False,
                "warning": f"plate OCR failed: {e}",
                "saved_to_parking_db": False,
            }

    final_plate = input_plate

    # 只有圖片，沒有文字 -> 用 OCR 結果
    if not final_plate and recognized_plate:
        final_plate = recognized_plate
        recognition_used = True

    # 文字 + 圖片都有，但不同 -> 不擋，只標記 mismatch
    if input_plate and recognized_plate and input_plate != recognized_plate:
        plate_mismatch = True

    # occupied 時最後還是沒有車牌 -> 擋下來
    if status == "occupied" and not final_plate:
        add_anomaly_event({
            "event_id": f"evt_{int(datetime.now().timestamp())}",
            "spot_id": payload.get("spot_id", ""),
            "anomaly_type": "missing_plate_after_recognition",
            "timestamp": utc_iso(),
            "detail": "occupied status requires current_plate text or recognizable plate image",
        })
        return {
            "ok": False,
            "warning": "occupied status requires current_plate text or recognizable plate image",
            "saved_to_parking_db": False,
        }

    # free 時仍照舊清空 current_plate
    if status == "free":
        final_plate = ""

    clean_data = {
        "spot_id": payload["spot_id"],
        "status": status,
        "reserved_plate": payload["reserved_plate"],
        "current_plate": final_plate,
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
        "image_received": image_received,
        "recognition_used": recognition_used,
        "recognized_plate": recognized_plate,
        "raw_ocr_text": raw_ocr_text,
        "plate_mismatch": plate_mismatch,
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
