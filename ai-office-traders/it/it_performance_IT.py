import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for d in ["core", "data", "llm"]:
    sys.path.insert(0, os.path.join(BASE_DIR, d))


def check_performance_IT() -> list[str]:
    metrics = []

    metrics.extend(_check_file_sizes())
    metrics.extend(_check_trade_history())
    metrics.extend(_check_analyst_count())
    metrics.extend(_check_cycle_time())
    metrics.extend(_check_llm_usage())
    metrics.extend(_check_debate_stats())
    metrics.extend(_check_analyst_performance())
    metrics.extend(_check_news_performance())

    return metrics


def _check_file_sizes() -> list[str]:
    metrics = []
    large_files = []
    for f in os.listdir(os.path.dirname(__file__)):
        if f.endswith(".py"):
            size = os.path.getsize(os.path.join(os.path.dirname(__file__), f))
            if size > 10000:
                large_files.append((f, size // 1024))
    if large_files:
        for name, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:3]:
            metrics.append(f"📊 {name}: {size}KB")
    else:
        metrics.append("✅ Все Python файлы < 10KB")
    return metrics


def _check_trade_history() -> list[str]:
    metrics = []
    history_file = Path(__file__).parent / "trade_history.json"
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            trades = data.get("trades", [])
            balance = data.get("balance", 0)
            metrics.append(f"💰 Баланс: ${balance:,.2f}")
            metrics.append(f"📈 Сделок: {len(trades)}")
            if trades:
                wins = sum(1 for t in trades if t.get("result") == "WIN")
                metrics.append(f"✅ Win Rate: {wins/len(trades)*100:.1f}%")
        except Exception:
            metrics.append("⚠️ Не удалось прочитать trade_history.json")
    return metrics


def _check_analyst_count() -> list[str]:
    metrics = []
    try:
        from staff import ANALYSTS, get_all_departments
        depts = get_all_departments()
        metrics.append(f"👥 Сотрудников: {len(ANALYSTS)}")
        metrics.append(f"🏢 Отделов: {len(depts)}")
        heads = sum(1 for a in ANALYSTS if a.is_head)
        metrics.append(f"⭐ Начальников: {heads}")
    except Exception:
        metrics.append("⚠️ Не удалось загрузить staff")
    return metrics


def _check_cycle_time() -> list[str]:
    metrics = []
    log_path = Path(__file__).parent / ".." / "logs" / "it_log.md"
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            time_pattern = r"Цикл завершён за (\d+\.\d+) секунд"
            matches = re.findall(time_pattern, content)
            if matches:
                cycle_times = [float(t) for t in matches[-5:]]
                avg_time = sum(cycle_times) / len(cycle_times)
                metrics.append(f"⏱️ Ср. время цикла: {avg_time:.2f}с")
                if avg_time > 60:
                    metrics.append(f"⚠️ Долгое время цикла")
        except Exception:
            pass
    return metrics if metrics else ["⏱️ Время цикла: данные недоступны"]


def _check_llm_usage() -> list[str]:
    metrics = []
    try:
        from config import LLM_ENABLED
        if LLM_ENABLED:
            metrics.append("🤖 LLM: включён")
        else:
            metrics.append("🤖 LLM: выключен")
    except Exception:
        metrics.append("⚠️ Не удалось проверить LLM")
    return metrics


def _check_debate_stats() -> list[str]:
    metrics = []
    debate_file = Path(__file__).parent / ".." / "logs" / "debate_history.json"
    if debate_file.exists():
        try:
            with open(debate_file, "r", encoding="utf-8") as f:
                debates = json.load(f)
            if debates:
                total = len(debates)
                metrics.append(f"🗣️ Дебатов в истории: {total}")
        except Exception:
            pass
    else:
        metrics.append("🗣️ История дебатов пуста")
    return metrics


def _check_analyst_performance() -> list[str]:
    metrics = []
    try:
        from staff import ANALYSTS
        heads = sum(1 for a in ANALYSTS if a.is_head)
        total = len(ANALYSTS)
        avg_accuracy = sum(getattr(a, 'accuracy', 0.7) for a in ANALYSTS) / total if total else 0
        metrics.append(f"👥 Аналитиков: {total} (начальников: {heads})")
        metrics.append(f"📊 Ср. точность: {avg_accuracy:.1%}")
    except Exception:
        metrics.append("⚠️ Не удалось загрузить аналитиков")
    return metrics


def _check_news_performance() -> list[str]:
    metrics = []
    try:
        from news import fetch_all_news
        news = fetch_all_news()
        metrics.append(f"📰 Новостей загружено: {len(news)}")
    except Exception:
        metrics.append("⚠️ Не удалось загрузить новости")
    return metrics
