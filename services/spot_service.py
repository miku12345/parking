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
    get_active_reservation_for_spot,
    cancel_reservation,
    cancel_active_reservations_for_spot,
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

    spot_id = payload["spot_id"]
    status = payload["status"]

    existing_spot = get_spot(spot_id) or {}
    active_reservation = get_active_reservation_for_spot(spot_id)

    input_plate = normalize_plate_text(payload.get("current_plate", ""))
    image_base64 = payload.get("current_plate_image_base64", "")

    payload_reserved_plate = normalize_plate_text(payload.get("reserved_plate", ""))
    spot_reserved_plate = normalize_plate_text(existing_spot.get("reserved_plate", ""))

    reservation_reserved_plate = ""
    if active_reservation:
        reservation_reserved_plate = normalize_plate_text(
            active_reservation.get("reserved_plate", "")
        )

    effective_reserved_plate = (
        payload_reserved_plate
        or spot_reserved_plate
        or reservation_reserved_plate
    )

    recognized_plate = ""
    raw_ocr_text = ""
    image_received = bool(image_base64)
    recognition_used = False
    plate_mismatch = False
    reservation_plate_mismatch = False
    reservation_matched = False
    cancelled_reservations = []

    if image_received:
        try:
            ocr_result = recognize_plate_from_base64(image_base64)
            raw_ocr_text = ocr_result.get("raw_text", "")
            recognized_plate = normalize_plate_text(ocr_result.get("plate_text", ""))

        except Exception as e:
            add_anomaly_event({
                "event_id": f"evt_{int(datetime.now().timestamp())}",
                "spot_id": spot_id,
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

    if not final_plate and recognized_plate:
        final_plate = recognized_plate
        recognition_used = True

    if input_plate and recognized_plate and input_plate != recognized_plate:
        plate_mismatch = True

    if status == "occupied" and not final_plate:
        add_anomaly_event({
            "event_id": f"evt_{int(datetime.now().timestamp())}",
            "spot_id": spot_id,
            "anomaly_type": "missing_plate_after_recognition",
            "timestamp": utc_iso(),
            "detail": "occupied status requires current_plate text or recognizable plate image",
        })
        return {
            "ok": False,
            "warning": "occupied status requires current_plate text or recognizable plate image",
            "saved_to_parking_db": False,
        }

    # 預設最後狀態等於輸入狀態
    final_status = status

    # 核心新增：
    # 如果車位有預約車牌，但停入車牌不等於預約車牌，
    # 後端直接把狀態改成 violation。
    if status == "occupied" and effective_reserved_plate:
        if final_plate == effective_reserved_plate:
            reservation_matched = True
            reservation_plate_mismatch = False
            final_status = "occupied"
        else:
            reservation_matched = False
            reservation_plate_mismatch = True
            final_status = "violation"

            add_anomaly_event({
                "event_id": f"evt_{int(datetime.now().timestamp())}",
                "spot_id": spot_id,
                "anomaly_type": "plate_mismatch_with_reservation",
                "timestamp": utc_iso(),
                "detail": f"The reserved plate {effective_reserved_plate} does not match the actual parked plate {final_plate}",
            })

    # 釋放車位邏輯：
    # 1. 原本只是 reserved：釋放不取消預約，維持 reserved
    # 2. 原本 violation：錯車離開，回到 reserved，預約保留
    # 3. 原本 occupied 且 reservation_matched=true：正確預約車離開，取消預約，變 free
    # 4. 原本 occupied 但不是正確預約車：如果還有 reserved_plate，回到 reserved
    # 5. 普通車位：變 free
    if status == "free":
        final_plate = ""

        existing_status = existing_spot.get("status", "free")
        existing_current_plate = normalize_plate_text(existing_spot.get("current_plate", ""))
        existing_reserved_plate = normalize_plate_text(existing_spot.get("reserved_plate", ""))

        was_valid_reservation_vehicle = bool(existing_spot.get("reservation_matched"))

        # 相容舊資料：
        # 若舊資料沒有 reservation_matched，
        # 但離場前 current_plate 剛好等於 reserved_plate，也視為正確預約車。
        if not was_valid_reservation_vehicle:
            if (
                existing_status == "occupied"
                and existing_reserved_plate
                and existing_current_plate == existing_reserved_plate
            ):
                was_valid_reservation_vehicle = True

        # 原本只是預約，沒有車停進來：保持 reserved
        if existing_status == "reserved":
            clean_data = {
                "spot_id": spot_id,
                "status": "reserved",
                "reserved_plate": existing_reserved_plate or effective_reserved_plate,
                "current_plate": "",
                "reservation_matched": False,
                "active_reservation_id": existing_spot.get("active_reservation_id", ""),
            }

        # 原本是違規佔用：錯車離開，預約仍保留，回到 reserved
        elif existing_status == "violation":
            clean_data = {
                "spot_id": spot_id,
                "status": "reserved",
                "reserved_plate": existing_reserved_plate or effective_reserved_plate,
                "current_plate": "",
                "reservation_matched": False,
                "active_reservation_id": existing_spot.get("active_reservation_id", ""),
            }

        # 正確預約車離開：取消預約，變 free
        elif was_valid_reservation_vehicle:
            active_reservation_id = existing_spot.get("active_reservation_id", "")

            if active_reservation_id:
                cancelled = cancel_reservation(
                    active_reservation_id,
                    reason="vehicle_left_after_valid_reservation",
                )
                if cancelled:
                    cancelled_reservations.append(cancelled)
            else:
                cancelled_reservations = cancel_active_reservations_for_spot(
                    spot_id,
                    reason="vehicle_left_after_valid_reservation",
                )

            clean_data = {
                "spot_id": spot_id,
                "status": "free",
                "reserved_plate": "",
                "current_plate": "",
                "reservation_matched": False,
                "active_reservation_id": "",
            }

        # 有預約，但不是正確預約車離開：預約保留
        elif existing_reserved_plate or effective_reserved_plate:
            clean_data = {
                "spot_id": spot_id,
                "status": "reserved",
                "reserved_plate": existing_reserved_plate or effective_reserved_plate,
                "current_plate": "",
                "reservation_matched": False,
                "active_reservation_id": existing_spot.get("active_reservation_id", ""),
            }

        # 普通車位釋放
        else:
            clean_data = {
                "spot_id": spot_id,
                "status": "free",
                "reserved_plate": "",
                "current_plate": "",
                "reservation_matched": False,
                "active_reservation_id": "",
            }

        save_parking_spot(clean_data)

        add_parking_log({
            **clean_data,
            "timestamp": utc_iso(),
            "cancelled_reservations": cancelled_reservations,
        })

        return {
            "ok": True,
            "message": "spot released",
            "saved_to_parking_db": True,
            "image_received": image_received,
            "recognition_used": recognition_used,
            "recognized_plate": recognized_plate,
            "raw_ocr_text": raw_ocr_text,
            "plate_mismatch": plate_mismatch,
            "reservation_plate_mismatch": reservation_plate_mismatch,
            "reservation_matched": clean_data.get("reservation_matched", False),
            "cancelled_reservations": cancelled_reservations,
            "data": clean_data,
        }

    active_reservation_id = ""

    if final_status in ["occupied", "violation"] and active_reservation:
        active_reservation_id = active_reservation.get("reservation_id", "")

    clean_data = {
        "spot_id": spot_id,
        "status": final_status,
        "reserved_plate": effective_reserved_plate if final_status != "free" else "",
        "current_plate": final_plate,
        "reservation_matched": reservation_matched,
        "active_reservation_id": active_reservation_id,
    }

    save_parking_spot(clean_data)

    add_parking_log({
        **clean_data,
        "timestamp": utc_iso(),
        "recognized_plate": recognized_plate,
        "plate_mismatch": plate_mismatch,
        "reservation_plate_mismatch": reservation_plate_mismatch,
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
        "reservation_plate_mismatch": reservation_plate_mismatch,
        "reservation_matched": reservation_matched,
        "cancelled_reservations": cancelled_reservations,
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
