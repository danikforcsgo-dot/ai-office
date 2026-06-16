import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for d in ["core", "data", "llm", "it", "utils"]:
    sys.path.insert(0, os.path.join(BASE_DIR, d))

from it_errors_IT import check_errors_IT
from it_performance_IT import check_performance_IT
from it_review_IT import code_review_IT
from it_tests_IT import run_tests_IT
from it_notifications_IT import it_notification_manager

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "it_log.md")


def _log_it(entries: list[str]):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    cycle_num = _get_cycle_count()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n## [{timestamp}] Цикл #{cycle_num}\n\n")
        for entry in entries:
            f.write(f"{entry}\n")
        f.write("\n---\n")


def _get_cycle_count() -> int:
    if not os.path.exists(LOG_FILE):
        return 1
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        return content.count("## [") + 1
    except Exception:
        return 1


def run_it_cycle():
    print("[IT] Запуск цикла мониторинга...", flush=True)
    entries = []
    errors_count = 0
    warnings_count = 0

    errors = check_errors_IT()
    entries.append("### Ошибки")
    if errors:
        for e in errors:
            entries.append(f"- {e}")
            if e.startswith("❌"):
                errors_count += 1
                it_notification_manager.send_notification("Критическая ошибка", e, "critical", "errors")
            elif e.startswith("⚠️"):
                warnings_count += 1
                it_notification_manager.send_notification("Предупреждение", e, "warning", "errors")
    else:
        entries.append("- ✅ Критических ошибок нет")

    perf = check_performance_IT()
    entries.append("\n### Производительность")
    for p in perf:
        entries.append(f"- {p}")
        if p.startswith("⚠️"):
            it_notification_manager.send_notification("Производительность", p, "warning", "performance")

    review = code_review_IT()
    entries.append("\n### Код-ревью")
    for r in review:
        entries.append(f"- {r}")

    tests = run_tests_IT()
    entries.append("\n### Тесты")
    tests_pass = sum(1 for t in tests if t.startswith("✅"))
    tests_fail = sum(1 for t in tests if t.startswith("❌"))
    tests_warn = sum(1 for t in tests if t.startswith("⚠️"))
    entries.append(f"- Пройдено: {tests_pass}, Ошибки: {tests_fail}, Предупреждения: {tests_warn}")
    for t in tests:
        entries.append(f"- {t}")

    entries.append(f"\n### Итого")
    entries.append(f"- Ошибки: {errors_count} | Предупреждения: {warnings_count}")
    entries.append(f"- Тесты: {tests_pass} OK / {tests_fail} FAIL / {tests_warn} WARN")

    _log_it(entries)
    print(f"[IT] Цикл завершён. Ошибки: {errors_count}, Предупреждения: {warnings_count}", flush=True)
    return entries


if __name__ == "__main__":
    run_it_cycle()
    print(f"\nЛог: {LOG_FILE}")
