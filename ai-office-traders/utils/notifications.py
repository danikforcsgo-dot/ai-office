import time
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "..", "core"))

from config import ALERT_COOLDOWN_SECONDS


class NotificationManager:
    def __init__(self):
        self._last_alerts: dict[str, float] = {}
        self._log: list[dict] = []

    def _should_notify(self, key: str) -> bool:
        now = time.time()
        last = self._last_alerts.get(key, 0)
        return now - last >= ALERT_COOLDOWN_SECONDS

    def notify(self, category: str, pair: str, message: str, severity: str = "info") -> bool:
        key = f"{category}:{pair}"
        if not self._should_notify(key):
            return False

        alert = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "pair": pair,
            "message": message,
            "severity": severity,
        }
        self._last_alerts[key] = time.time()
        self._log.append(alert)

        icon = {"info": "[i]", "warning": "[!]", "critical": "[!!]"}.get(severity, "[*]")
        print(f"  {icon} {alert['time']} | {pair} | {message}")
        return True

    def check_signal_alerts(self, pair_name: str, analysis: dict):
        rec = analysis.get("recommendation", "")
        score = analysis.get("score", 0)
        rsi = analysis.get("rsi", 50)

        if score >= 3:
            self.notify("signal", pair_name, f"СИЛЬНЫЙ ПОКУПАТЕЛЬНЫЙ СИГНАЛ (score={score})", "critical")
        elif score <= -3:
            self.notify("signal", pair_name, f"СИЛЬНЫЙ ПРОДАЖЕВЫЙ СИГНАЛ (score={score})", "critical")

        if rsi > 75:
            self.notify("overbought", pair_name, f"RSI перекуплен: {rsi:.1f}", "warning")
        elif rsi < 25:
            self.notify("oversold", pair_name, f"RSI перепродан: {rsi:.1f}", "warning")

    def get_log(self) -> list[dict]:
        return list(self._log)

    def get_recent(self, n: int = 10) -> list[dict]:
        return self._log[-n:]
