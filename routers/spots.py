from fastapi import APIRouter
from services.spot_service import process_spot_update, list_spots, get_one_spot

router = APIRouter()

@router.get("/spots")
def get_spots():
    return list_spots()

@router.get("/spots/{spot_id}")
def get_spot(spot_id: str):
    return get_one_spot(spot_id)

@router.post("/spots/update")
def update_spot(payload: dict):
    return process_spot_update(payload)
