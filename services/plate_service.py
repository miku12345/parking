import base64
import re
from google.cloud import vision

PLATE_PATTERNS = [
    re.compile(r"[A-Z]{2,4}-\d{3,4}"),
    re.compile(r"[A-Z]{2,4}\d{3,4}"),
]

_client = None

def get_client():
    global _client
    if _client is None:
        _client = vision.ImageAnnotatorClient()
    return _client

def normalize_plate_text(text: str) -> str:
    text = (text or "").upper().strip()
    text = text.replace(" ", "").replace("_", "-")
    text = re.sub(r"[^A-Z0-9-]", "", text)

    compact = text.replace("-", "")
    if "-" not in text and len(compact) == 7:
        text = compact[:3] + "-" + compact[3:]

    return text

def extract_plate_candidate(text: str) -> str:
    source = (text or "").upper()

    for pattern in PLATE_PATTERNS:
        m = pattern.search(source)
        if m:
            return normalize_plate_text(m.group(0))

    return normalize_plate_text(source)

def decode_base64_image(image_base64: str) -> bytes:
    raw = (image_base64 or "").strip()

    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]

    return base64.b64decode(raw)

def recognize_plate_from_base64(image_base64: str) -> dict:
    image_bytes = decode_base64_image(image_base64)
    image = vision.Image(content=image_bytes)

    response = get_client().text_detection(image=image)

    if response.error.message:
        raise RuntimeError(response.error.message)

    texts = response.text_annotations or []
    raw_text = texts[0].description if texts else ""
    plate_text = extract_plate_candidate(raw_text)

    return {
        "ok": True,
        "raw_text": raw_text,
        "plate_text": plate_text,
    }
