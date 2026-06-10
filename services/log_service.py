from repositories.firestore_repo import get_logs

def list_logs(limit: int = 50, spot_id: str | None = None):
    return get_logs(limit=limit, spot_id=spot_id)
