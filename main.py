from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.spots import router as spots_router
from routers.anomalies import router as anomalies_router
from routers.reservations import router as reservations_router
from routers.logs import router as logs_router
from routers.prediction import router as prediction_router

app = FastAPI(title="Parking Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spots_router, prefix="/api")
app.include_router(anomalies_router, prefix="/api")
app.include_router(reservations_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(prediction_router, prefix="/api")

@app.get("/")
def root():
    return {"ok": True, "message": "Parking backend is running"}
