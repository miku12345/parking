"""
Generates synthetic historical parking logs.

The real system only writes a log on a state change, and with a single Pico
there is almost no real history to train on. For this simulation we seed
`parking_logs` with realistic data so the AI prediction module has something
to learn from. Each row is a normal log entry, so it doubles as demo data.

The occupancy pattern follows a typical daily rhythm: quiet at night, busy
in the morning and evening, calmer on weekends.
"""

import random
from datetime import datetime, timedelta, timezone

from repositories.firestore_repo import (
    add_logs_batch,
    get_all_spots,
    save_parking_spot,
)

# Probability that a spot is occupied, indexed by hour 0..23.
WEEKDAY_CURVE = [
    0.10, 0.08, 0.07, 0.07, 0.08, 0.12,   # 00-05 night
    0.25, 0.45, 0.70, 0.78, 0.72, 0.68,   # 06-11 morning rush -> midday
    0.70, 0.72, 0.70, 0.68, 0.72, 0.85,   # 12-17 afternoon -> evening rush
    0.88, 0.80, 0.60, 0.45, 0.30, 0.18,   # 18-23 evening wind-down
]

WEEKEND_CURVE = [
    0.12, 0.10, 0.08, 0.08, 0.08, 0.10,   # 00-05
    0.15, 0.20, 0.30, 0.40, 0.50, 0.58,   # 06-11
    0.62, 0.65, 0.63, 0.60, 0.58, 0.55,   # 12-17
    0.55, 0.50, 0.45, 0.38, 0.28, 0.18,   # 18-23
]


def _occupancy_prob(hour: int, weekday: int) -> float:
    # weekday(): Monday=0 .. Sunday=6
    curve = WEEKEND_CURVE if weekday >= 5 else WEEKDAY_CURVE
    # small noise so the data isn't perfectly clean
    return min(0.97, max(0.02, curve[hour] + random.uniform(-0.05, 0.05)))


def _ensure_spots(lot_size: int):
    spots = get_all_spots()
    if spots:
        return [s["spot_id"] for s in spots]
    spot_ids = [f"A{i:02d}" for i in range(1, lot_size + 1)]
    for spot_id in spot_ids:
        save_parking_spot({
            "spot_id": spot_id,
            "status": "free",
            "reserved_plate": "",
            "current_plate": "",
        })
    return spot_ids


def generate_synthetic_logs(days: int = 14, lot_size: int = 10):
    spot_ids = _ensure_spots(lot_size)
    now = datetime.now(timezone.utc)

    rows = []
    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        weekday = day.weekday()
        for hour in range(24):
            timestamp = day.replace(
                hour=hour, minute=0, second=0, microsecond=0
            ).isoformat()
            for spot_id in spot_ids:
                occupied = random.random() < _occupancy_prob(hour, weekday)
                rows.append({
                    "spot_id": spot_id,
                    "status": "occupied" if occupied else "free",
                    "reserved_plate": "",
                    "current_plate": f"SIM-{random.randint(1000, 9999)}" if occupied else "",
                    "timestamp": timestamp,
                })

    written = add_logs_batch(rows)
    return {
        "days": days,
        "lot_size": len(spot_ids),
        "rows_written": written,
    }
