import os
import sys
import re
import json
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for d in ["core", "data", "llm"]:
    sys.path.insert(0, os.path.join(BASE_DIR, d))


def check_errors_IT() -> list[str]:
    errors = []

    errors.extend(_check_rate_limits())
    errors.extend(_check_missing_files())
    errors.extend(_check_api_keys())
    errors.extend(_check_data_integrity())
    errors.extend(_check_exceptions_in_logs())
    errors.extend(_check_external_services())
    errors.extend(_check_disk_space())
    errors.extend(_check_system_resources())
    errors.extend(_check_library_versions())
    errors.extend(_check_config_validation())

    return errors


def _check_rate_limits() -> list[str]:
    issues = []
    log_file = Path(__file__).parent / "it_log.md"
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            recent = content[-2000:] if len(content) > 2000 else content
            rate_count = recent.lower().count("rate limit") + recent.lower().count("429")
            if rate_count > 3:
                issues.append(f"⚠️ Частые rate limits ({rate_count} за последние циклы)")
        except Exception:
            pass
    return issues


def _check_missing_files() -> list[str]:
    issues = []
    required_files = [
        "config.py", "staff.py", "analyst_engine.py", "debate.py",
        "trader.py", "market_data.py", "llm_client.py", "main.py",
        "it_monitor_IT.py", "it_errors_IT.py", "it_performance_IT.py",
        "it_review_IT.py", "it_tests_IT.py"
    ]
    for f in required_files:
        path = Path(__file__).parent / f
        if not path.exists():
            issues.append(f"❌ Отсутствует файл: {f}")
    return issues


def _check_api_keys() -> list[str]:
    issues = []
    config_path = Path(__file__).parent / "config.py"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "MISTRAL_API_KEY" not in content:
                issues.append("⚠️ MISTRAL_API_KEY не найден в config.py")
            if LLM_ENABLED and not MISTRAL_API_KEY:
                issues.append("❌ LLM включён, но ключ пустой")
        except Exception:
            pass
    return issues


def _check_data_integrity() -> list[str]:
    issues = []
    history_file = Path(__file__).parent / "trade_history.json"
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "balance" not in data:
                issues.append("⚠️ trade_history.json: нет поля balance")
            if "trades" not in data:
                issues.append("⚠️ trade_history.json: нет поля trades")
        except json.JSONDecodeError:
            issues.append("❌ trade_history.json повреждён")
        except Exception:
            pass
    return issues


def _check_exceptions_in_logs() -> list[str]:
    issues = []
    log_file = os.path.join(BASE_DIR, "..", "logs", "it_log.md")

    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            exception_patterns = [
                r"Traceback", r"Exception:", r"Error:",
                r"\[ERROR\]", r"\[CRITICAL\]",
                r"KeyError:", r"ValueError:", r"TypeError:",
                r"ConnectionError:", r"Timeout:",
            ]
            for pattern in exception_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    issues.append(f"⚠️ Найдено {len(matches)} исключений типа '{pattern}' в it_log.md")
        except Exception:
            pass
    return issues


def _check_external_services() -> list[str]:
    issues = []
    import requests
    services = {
        "Yahoo Finance": "https://query1.finance.yahoo.com",
        "Mistral API": "https://api.mistral.ai",
    }
    for name, url in services.items():
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                issues.append(f"⚠️ Сервис {name} недоступен (HTTP {resp.status_code})")
        except requests.RequestException:
            issues.append(f"⚠️ Сервис {name} недоступен")
    return issues


def _check_disk_space() -> list[str]:
    issues = []
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024 ** 3)
        if free_gb < 1:
            issues.append(f"❌ Мало места: {free_gb:.2f} GB свободно")
        elif free_gb < 5:
            issues.append(f"⚠️ Мало места: {free_gb:.2f} GB свободно")
    except Exception:
        pass
    return issues


def _check_system_resources() -> list[str]:
    issues = []
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            issues.append(f"❌ Высокое использование памяти: {mem.percent}%")
        elif mem.percent > 80:
            issues.append(f"⚠️ Высокое использование памяти: {mem.percent}%")
        cpu = psutil.cpu_percent(interval=1)
        if cpu > 90:
            issues.append(f"❌ Высокое использование CPU: {cpu}%")
        elif cpu > 80:
            issues.append(f"⚠️ Высокое использование CPU: {cpu}%")
    except ImportError:
        pass
    except Exception as e:
        issues.append(f"⚠️ Ошибка проверки ресурсов: {e}")
    return issues


def _check_library_versions() -> list[str]:
    issues = []
    try:
        import pkg_resources
        required = {"yfinance": "0.2.31", "pandas": "2.0.0", "numpy": "1.24.0"}
        for lib, min_ver in required.items():
            try:
                installed = pkg_resources.get_distribution(lib).version
                if installed < min_ver:
                    issues.append(f"⚠️ Устаревшая библиотека: {lib} {installed}")
            except pkg_resources.DistributionNotFound:
                issues.append(f"❌ Отсутствует: {lib}")
    except ImportError:
        pass
    return issues


def _check_config_validation() -> list[str]:
    issues = []
    try:
        from config import INSTRUMENTS, TIMEFRAME, ANALYSIS_INTERVAL_MINUTES, TRADER_RISK_PER_TRADE, LLM_ENABLED, MISTRAL_API_KEY
        if not INSTRUMENTS:
            issues.append("❌ Нет инструментов для торговли")
        if TIMEFRAME not in ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]:
            issues.append(f"⚠️ Некорректный таймфрейм: {TIMEFRAME}")
        if not (0 < TRADER_RISK_PER_TRADE <= 1):
            issues.append(f"❌ Некорректный риск: {TRADER_RISK_PER_TRADE}")
        if LLM_ENABLED and not MISTRAL_API_KEY:
            issues.append("❌ LLM включён, но ключ пустой")
    except Exception as e:
        issues.append(f"❌ Ошибка конфигурации: {e}")
    return issues
