from fastapi import APIRouter, Query

from services.prediction_service import predict_point, forecast_day, train_model
from services.data_generator import generate_synthetic_logs

# weekday follows Python convention: Monday=0 .. Sunday=6
router = APIRouter(prefix="/predict", tags=["prediction"])


@router.get("")
def predict(
    weekday: int = Query(..., ge=0, le=6),
    hour: int = Query(..., ge=0, le=23),
):
    return predict_point(weekday=weekday, hour=hour)


@router.get("/forecast")
def forecast(weekday: int = Query(..., ge=0, le=6)):
    return forecast_day(weekday=weekday)


@router.post("/train")
def train():
    return train_model()


@router.post("/seed")
def seed(
    days: int = Query(14, ge=1, le=60),
    lot_size: int = Query(10, ge=1, le=50),
):
    result = generate_synthetic_logs(days=days, lot_size=lot_size)
    info = train_model()
    return {"seeded": result, "training": info}
