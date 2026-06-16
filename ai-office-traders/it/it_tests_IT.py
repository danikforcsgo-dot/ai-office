import os
import sys
import unittest
from io import StringIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for d in ["core", "data", "llm"]:
    sys.path.insert(0, os.path.join(BASE_DIR, d))


def run_tests_IT() -> list[str]:
    results = []

    results.extend(_test_imports())
    results.extend(_test_config())
    results.extend(_test_staff())
    results.extend(_test_llm())
    results.extend(_test_functionality())
    results.extend(_test_performance())
    results.extend(_test_security())
    results.extend(_test_integration())
    results.extend(_run_unit_tests())

    return results


def _test_imports() -> list[str]:
    results = []
    modules = [
        "config", "staff", "analyst_engine", "debate",
        "trader", "market_data", "llm_client"
    ]
    for mod in modules:
        try:
            __import__(mod)
            results.append(f"✅ {mod}: OK")
        except ImportError as e:
            results.append(f"❌ {mod}: {e}")
        except Exception as e:
            results.append(f"⚠️ {mod}: {type(e).__name__}")
    return results


def _test_config() -> list[str]:
    results = []
    try:
        from config import INSTRUMENTS, LLM_ENABLED, MISTRAL_API_KEY
        results.append(f"✅ config: {len(INSTRUMENTS)} инструментов, LLM={'ON' if LLM_ENABLED else 'OFF'}")
        if not MISTRAL_API_KEY:
            results.append("⚠️ MISTRAL_API_KEY пустой")
    except Exception as e:
        results.append(f"❌ config: {e}")
    return results


def _test_staff() -> list[str]:
    results = []
    try:
        from staff import ANALYSTS, get_all_departments
        depts = get_all_departments()
        results.append(f"✅ staff: {len(ANALYSTS)} аналитиков, {len(depts)} отделов")
        heads = sum(1 for a in ANALYSTS if a.is_head)
        results.append(f"✅ Начальников: {heads}")
    except Exception as e:
        results.append(f"❌ staff: {e}")
    return results


def _test_llm() -> list[str]:
    results = []
    try:
        from llm_client import get_llm
        llm = get_llm()
        results.append(f"✅ LLM: {llm.provider}/{llm.model}")
    except Exception as e:
        results.append(f"⚠️ LLM: {e}")
    return results


def _test_functionality() -> list[str]:
    results = []

    try:
        from market_data import get_all_prices
        prices = get_all_prices()
        if prices:
            results.append(f"✅ market_data: {len(prices)} пар")
        else:
            results.append("⚠️ market_data: нет данных")
    except Exception as e:
        results.append(f"❌ market_data: {e}")

    try:
        from trader import Trader
        trader = Trader("Test")
        stats = trader.get_stats()
        results.append(f"✅ trader: баланс ${stats['balance']:.2f}")
    except Exception as e:
        results.append(f"❌ trader: {e}")

    return results


def _test_performance() -> list[str]:
    results = []
    import time
    try:
        from market_data import get_all_prices
        start = time.time()
        prices = get_all_prices()
        elapsed = time.time() - start
        if prices:
            results.append(f"✅ Загрузка данных: {elapsed:.2f}с")
            if elapsed > 10:
                results.append(f"⚠️ Медленная загрузка: {elapsed:.2f}с")
    except Exception as e:
        results.append(f"❌ Тест производительности: {e}")
    return results


def _test_security() -> list[str]:
    results = []
    try:
        from config import MISTRAL_API_KEY
        if not MISTRAL_API_KEY:
            results.append("⚠️ MISTRAL_API_KEY пустой")
        else:
            results.append("✅ API ключи заданы")
    except Exception as e:
        results.append(f"❌ Проверка безопасности: {e}")
    return results


def _test_integration() -> list[str]:
    results = []
    try:
        from market_data import get_all_prices
        from analyst_engine import analyst_work
        from debate import run_debate
        from staff import ANALYSTS
        prices = get_all_prices()
        if prices:
            reports = [analyst_work(a, prices) for a in ANALYSTS[:3]]
            debate = run_debate(reports)
            if debate:
                results.append(f"✅ Интеграция: аналитики + дебаты OK")
            else:
                results.append("⚠️ Интеграция: дебаты пусты")
        else:
            results.append("⚠️ Интеграция: нет данных")
    except Exception as e:
        results.append(f"❌ Интеграция: {e}")
    return results


def _run_unit_tests() -> list[str]:
    results = []
    class TestOffice(unittest.TestCase):
        def test_pairs(self):
            from config import INSTRUMENTS
            self.assertGreater(len(INSTRUMENTS), 0)
        def test_staff(self):
            from staff import ANALYSTS
            self.assertGreater(len(ANALYSTS), 0)
        def test_trader(self):
            from trader import Trader
            t = Trader("Test")
            self.assertGreater(t.balance, 0)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestOffice)
    runner = unittest.TextTestRunner(stream=StringIO(), verbosity=0)
    res = runner.run(suite)
    if res.wasSuccessful():
        results.append(f"✅ Unit-тесты: {res.testsRun} пройдено")
    else:
        results.append(f"❌ Unit-тесты: {len(res.failures)} ошибок")
    return results
