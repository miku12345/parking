from fastapi import APIRouter, Depends, Request
from services.spot_service import process_spot_update, list_spots, get_one_spot
from device_security import verify_device_signature
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.get("/spots")
def get_spots():
    return list_spots()


@router.get("/spots/{spot_id}")
def get_spot(spot_id: str):
    return get_one_spot(spot_id)


@router.post("/spots/update", dependencies=[Depends(verify_device_signature)])
@limiter.limit("30/minute")
def update_spot(request: Request, payload: dict):
    return process_spot_update(payload)
