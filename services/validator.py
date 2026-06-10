VALID_SPOT_STATUS = {"free", "reserved", "occupied"}

def validate_spot_payload(payload: dict):
    required_fields = ["spot_id", "status", "reserved_plate", "current_plate"]

    for field in required_fields:
        if field not in payload:
            return False, f"missing field: {field}"

    if not isinstance(payload["spot_id"], str) or not payload["spot_id"].strip():
        return False, "spot_id must be a non-empty string"

    if payload["status"] not in VALID_SPOT_STATUS:
        return False, "status must be one of: free, reserved, occupied"

    if not isinstance(payload["reserved_plate"], str):
        return False, "reserved_plate must be a string"

    if not isinstance(payload["current_plate"], str):
        return False, "current_plate must be a string"

    # 先預留圖片欄位，現在收但不存
    if "current_plate_image_base64" in payload:
        if not isinstance(payload["current_plate_image_base64"], str):
            return False, "current_plate_image_base64 must be a string"

    return True, "ok"

def validate_reservation_payload(payload: dict):
    required_fields = ["spot_id", "reserved_plate"]

    for field in required_fields:
        if field not in payload:
            return False, f"missing field: {field}"

    if not isinstance(payload["spot_id"], str) or not payload["spot_id"].strip():
        return False, "spot_id must be a non-empty string"

    if not isinstance(payload["reserved_plate"], str) or not payload["reserved_plate"].strip():
        return False, "reserved_plate must be a non-empty string"

    return True, "ok"
