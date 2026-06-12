"""
AI parking availability prediction.

Reads historical rows from `parking_logs`, where each row is one observation
of (timestamp, status). We turn each row into a training sample:

    features = [hour_of_day, weekday]      # weekday: Monday=0 .. Sunday=6
    label    = 1 if the spot was taken (occupied/reserved) else 0

and train a small RandomForest classifier. At predict time the model returns
the probability a spot is free for a given (weekday, hour), which we scale by
the number of spots to estimate how many will be free.

The model is tiny and CPU-only. It is trained lazily on first use and cached
in memory; call POST /predict/train to retrain after seeding more data.
"""

from datetime import datetime

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from repositories.firestore_repo import get_all_logs, get_all_spots

OCCUPIED_STATES = {"occupied", "reserved"}

_MODEL = None
_MODEL_INFO: dict = {}


def _build_dataset(logs):
    features, labels = [], []
    for log in logs:
        timestamp = log.get("timestamp")
        status = log.get("status")
        if not timestamp or not status:
            continue
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            continue
        features.append([dt.hour, dt.weekday()])
        labels.append(1 if status in OCCUPIED_STATES else 0)
    return np.array(features), np.array(labels)


def train_model():
    global _MODEL, _MODEL_INFO

    logs = get_all_logs(limit=20000)
    X, y = _build_dataset(logs)

    if len(X) < 50 or len(set(y.tolist())) < 2:
        _MODEL = None
        _MODEL_INFO = {
            "trained": False,
            "samples": int(len(X)),
            "reason": "not enough varied data — seed logs first (POST /predict/seed)",
        }
        return _MODEL_INFO

    model = RandomForestClassifier(n_estimators=60, max_depth=6, random_state=42)
    model.fit(X, y)

    _MODEL = model
    _MODEL_INFO = {
        "trained": True,
        "samples": int(len(X)),
        "occupied_rate": round(float(y.mean()), 3),
    }
    return _MODEL_INFO


def _get_model():
    # lazy train on first request
    if _MODEL is None and not _MODEL_INFO.get("trained"):
        train_model()
    return _MODEL


def _total_spots():
    spots = get_all_spots()
    return len(spots) if spots else 0


def _p_occupied(model, weekday: int, hour: int) -> float:
    # column 1 is the probability of class "occupied"
    return float(model.predict_proba([[hour, weekday]])[0][1])


def _not_trained_response():
    return {
        "ok": False,
        "warning": "model not trained — call POST /predict/seed then POST /predict/train",
        "info": _MODEL_INFO,
    }


def predict_point(weekday: int, hour: int):
    model = _get_model()
    if model is None:
        return _not_trained_response()

    total = _total_spots()
    p_occupied = _p_occupied(model, weekday, hour)
    p_free = 1 - p_occupied

    return {
        "ok": True,
        "weekday": weekday,
        "hour": hour,
        "p_free": round(p_free, 3),
        "p_occupied": round(p_occupied, 3),
        "total_spots": total,
        "estimated_free_spots": round(p_free * total) if total else None,
    }


def forecast_day(weekday: int):
    model = _get_model()
    if model is None:
        return _not_trained_response()

    total = _total_spots()
    forecast = []
    for hour in range(24):
        p_free = 1 - _p_occupied(model, weekday, hour)
        forecast.append({
            "hour": hour,
            "p_free": round(p_free, 3),
            "estimated_free_spots": round(p_free * total) if total else None,
        })

    return {
        "ok": True,
        "weekday": weekday,
        "total_spots": total,
        "forecast": forecast,
    }
