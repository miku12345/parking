from fastapi import APIRouter, Depends
from services.reservation_service import create_reservation_request, list_reservation_items
from security import require_api_key

router = APIRouter()

@router.post("/reserve", dependencies=[Depends(require_api_key)])
def reserve_spot(payload: dict):
    return create_reservation_request(payload)

@router.get("/reservations", dependencies=[Depends(require_api_key)])
def get_reservations(limit: int = 50):
    return list_reservation_items(limit=limit)
