import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class ITNotificationManager:
    def __init__(self):
        self.notifications = []
        self.notification_file = Path(__file__).parent / ".." / "logs" / "it_notifications.json"
        self._load_notifications()

    def _load_notifications(self):
        if self.notification_file.exists():
            try:
                with open(self.notification_file, "r", encoding="utf-8") as f:
                    self.notifications = json.load(f)
            except Exception:
                self.notifications = []

    def _save_notifications(self):
        try:
            with open(self.notification_file, "w", encoding="utf-8") as f:
                json.dump(self.notifications, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def send_notification(self, title, message, severity="info", category="general"):
        notification = {
            "id": len(self.notifications) + 1,
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "severity": severity,
            "category": category,
            "read": False,
        }
        self.notifications.append(notification)
        self._save_notifications()
        self._send_to_main_system(notification)
        return notification

    def _send_to_main_system(self, notification):
        try:
            from notifications import NotificationManager
            notify_mgr = NotificationManager()
            msg = f"[IT] {notification['title']}: {notification['message']}"
            notify_mgr.notify(notification["severity"], msg)
        except Exception:
            pass

    def get_unread(self):
        return [n for n in self.notifications if not n.get("read", True)]

    def get_recent(self, n=10):
        return sorted(self.notifications, key=lambda x: x["timestamp"], reverse=True)[:n]

    def mark_read(self, notification_id):
        for n in self.notifications:
            if n["id"] == notification_id:
                n["read"] = True
                self._save_notifications()
                break

    def clear_old(self, days=30):
        cutoff = datetime.now() - timedelta(days=days)
        self.notifications = [
            n for n in self.notifications
            if datetime.fromisoformat(n["timestamp"]) >= cutoff
        ]
        self._save_notifications()


it_notification_manager = ITNotificationManager()
