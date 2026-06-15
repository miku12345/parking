from fastapi import APIRouter, Depends
from services.log_service import list_logs
from security import require_api_key

router = APIRouter()

@router.get("/logs", dependencies=[Depends(require_api_key)])
def get_logs_api(limit: int = 50, spot_id: str | None = None):
    return list_logs(limit=limit, spot_id=spot_id)
