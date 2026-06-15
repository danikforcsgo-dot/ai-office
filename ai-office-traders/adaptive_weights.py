import json
import os
from datetime import datetime


WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "analyst_weights.json")

DEFAULT_WEIGHT = 1.0
MIN_WEIGHT = 0.2
MAX_WEIGHT = 1.5
DECAY = 0.95


def load_weights() -> dict:
    if os.path.exists(WEIGHTS_FILE):
        try:
            with open(WEIGHTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_weights(weights: dict):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f, indent=2, ensure_ascii=False)


def get_weight(analyst_id: int) -> float:
    weights = load_weights()
    return weights.get(str(analyst_id), DEFAULT_WEIGHT)


def record_signal(analyst_id: int, predicted: str, actual: str):
    weights = load_weights()
    key = str(analyst_id)
    current = weights.get(key, DEFAULT_WEIGHT)
    if predicted == actual:
        current = min(current + 0.05, MAX_WEIGHT)
    elif predicted in ("BUY", "SELL") and actual == "NEUTRAL":
        current = max(current - 0.1, MIN_WEIGHT)
    elif predicted != "NEUTRAL" and actual in ("BUY", "SELL") and predicted != actual:
        current = max(current - 0.15, MIN_WEIGHT)
    else:
        current = max(current * DECAY, MIN_WEIGHT)
    weights[key] = round(current, 3)
    save_weights(weights)


def get_all_weights() -> dict:
    return load_weights()


def get_weighted_verdict(dept_reports: list[dict]) -> dict:
    from staff import ANALYSTS
    weights = load_weights()
    total_weighted_buy = 0
    total_weighted_sell = 0
    total_weighted_neutral = 0
    for r in dept_reports:
        dept_members = [a for a in ANALYSTS if a.department == r["department"]]
        dept_weight = sum(weights.get(str(a.id), DEFAULT_WEIGHT) for a in dept_members) / len(dept_members) if dept_members else 1.0
        total_weighted_buy += r["buy_signals"] * dept_weight
        total_weighted_sell += r["sell_signals"] * dept_weight
        total_weighted_neutral += r["neutral_signals"] * dept_weight
    if total_weighted_buy > total_weighted_sell * 1.3:
        verdict = "BULLISH"
    elif total_weighted_sell > total_weighted_buy * 1.3:
        verdict = "BEARISH"
    else:
        verdict = "NEUTRAL"
    return {
        "verdict": verdict,
        "weighted_buy": round(total_weighted_buy, 2),
        "weighted_sell": round(total_weighted_sell, 2),
        "weighted_neutral": round(total_weighted_neutral, 2),
        "weights": {str(a.id): weights.get(str(a.id), DEFAULT_WEIGHT) for a in ANALYSTS},
    }


def reset_weights():
    save_weights({})
