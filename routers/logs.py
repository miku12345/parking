from fastapi import APIRouter
from services.log_service import list_logs

router = APIRouter()

@router.get("/logs")
def get_logs_api(limit: int = 50, spot_id: str | None = None):
    return list_logs(limit=limit, spot_id=spot_id)
