from fastapi import APIRouter
from services.reservation_service import create_reservation_request, list_reservation_items

router = APIRouter()

@router.post("/reserve")
def reserve_spot(payload: dict):
    return create_reservation_request(payload)

@router.get("/reservations")
def get_reservations(limit: int = 50):
    return list_reservation_items(limit=limit)
