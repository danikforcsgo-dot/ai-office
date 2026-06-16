# ═══════════════════════════════════════════════════
# AI OFFICE — GOLD TRADING SYSTEM
# ═══════════════════════════════════════════════════

# Инструменты для торговли золотом
INSTRUMENTS = {
    "XAU/USD": "Физическое золото (спот)",
    "XAUUSD": "CFD на золото",
    "GC=F": "Фьючерсы COMEX",
}

# Параметры золота
GOLD_PIP_SIZE = 0.01
GOLD_TICK_SIZE = 0.10
GOLD_POINT_VALUE = 100
GOLD_MIN_LOT = 0.01
GOLD_MAX_LOT = 100.0
PIP_SIZE = {"XAU/USD": 0.01, "XAUUSD": 0.01, "GC=F": 0.10}
DEFAULT_PIP_SIZE = 0.01

# Таймфреймы для анализа
TIMEFRAME = "15m"
ANALYSIS_INTERVAL_MINUTES = 15

# Технические индикаторы
SMA_SHORT = 10
SMA_LONG = 30
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Торговые параметры
ALERT_COOLDOWN_SECONDS = 3600
TRADER_INITIAL_BALANCE = 10000.0
TRADER_RISK_PER_TRADE = 0.02
TRADER_MAX_POSITIONS = 3
TRADER_MAX_DRAWDOWN_PCT = 0.15
TRADER_MIN_SIGNAL_STRENGTH = 3
TRADER_TRAILING_STOP_ACTIVATION = 0.003
TRADER_TRAILING_STOP_DISTANCE = 0.002

# LLM Settings
LLM_ENABLED = True
MISTRAL_API_KEY = "bFeUpGxuKqbph0CDDxyqr8hyXbNI2Bhm"
ZHIPU_API_KEY = "a3ae635f86124712a55039f9c32eeabd.8qWHHNn7NrnG2XuA"
OPENROUTER_API_KEY = ""
LLM_FALLBACK = True

# Корреляции золота
GOLD_CORRELATIONS = {
    "DXY": -0.8,      # Индекс доллара — сильная обратная
    "US10Y": -0.6,     # Доходность облигаций — обратная
    "SPX": 0.3,        # S&P 500 — слабая положительная
    "VIX": 0.5,        # Индекс страха — положительная
    "BTC": 0.2,        # Биткоин — слабая положительная
    "OIL": 0.4,        # Нефть — положительная
}

# Сезонность золота (исторические паттерны по месяцам)
GOLD_SEASONALITY = {
    1: 0.02,    # Январь — обычно рост
    2: 0.01,    # Февраль — слабый рост
    3: -0.01,   # Март — слабое падение
    4: 0.015,   # Апрель — рост
    5: -0.005,  # Май — нейтрально
    6: -0.01,   # Июнь — падение
    7: 0.005,   # Июль — нейтрально
    8: 0.03,    # Август — сильный рост
    9: 0.02,    # Сентябрь — рост
    10: 0.01,   # Октябрь — слабый рост
    11: -0.005,  # Ноябрь — нейтрально
    12: 0.015,  # Декабрь — рост
}

# Веса ролей для голосования
ROLE_WEIGHTS = {
    1: 1.5,   # CTO — финальные решения
    2: 1.4,   # Sr. Market Analyst — HTF bias
    3: 1.2,   # M15 Execution Trader — входы
    4: 1.5,   # Risk Manager — контроль рисков
    5: 1.1,   # HTF FVG Specialist
    6: 1.2,   # Kill Zone Specialist
    7: 1.3,   # News & Event Filter — фильтр новостей
    8: 1.1,   # ATR & Volatility Analyst
    9: 1.0,   # Journal & Statistics Keeper
    10: 1.0,  # Backtester & Optimizer
    11: 1.0,  # Data Engineer
    12: 1.1,  # Psychology & Discipline Officer
    13: 1.0,  # Data Quality Engineer
    14: 1.0,  # Alert & Execution Monitor
}
