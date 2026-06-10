from fastapi import APIRouter
from services.spot_service import list_anomalies

router = APIRouter()

@router.get("/anomalies")
def get_anomalies(limit: int = 50):
    return list_anomalies(limit=limit)
