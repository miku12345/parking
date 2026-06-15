from fastapi import APIRouter, Depends
from services.spot_service import list_anomalies
from security import require_api_key

router = APIRouter()

@router.get("/anomalies", dependencies=[Depends(require_api_key)])
def get_anomalies(limit: int = 50):
    return list_anomalies(limit=limit)
