from dataclasses import dataclass


@dataclass
class Analyst:
    id: int
    name: str
    role: str
    department: str
    responsibilities: list[str]
    tools: list[str]
    is_head: bool = False


DEPARTMENTS_STRUCTURE = {
    "Технический анализ": {
        "head_id": 1,
        "description": "Классический технический анализ: индикаторы, паттерны, уровни",
    },
    "ICT / Smart Money": {
        "head_id": 27,
        "description": "Smart Money Concepts: Order Blocks, FVG, ликвидность, HTF структура",
    },
    "M15 Краткосрочный анализ": {
        "head_id": 32,
        "description": "Анализ на M15: Kill Zones, волатильность, быстрые сигналы",
    },
    "Макроэкономика": {
        "head_id": 30,
        "description": "DXY, монетарная политика, фундаментальный анализ",
    },
    "Квантовый анализ": {
        "head_id": 8,
        "description": "Статистические модели, ML, бэктестинг",
    },
    "Управление рисками": {
        "head_id": 10,
        "description": "VaR, просадки, размер позиций, портфель",
    },
    "Межрыночный анализ": {
        "head_id": 14,
        "description": "Корреляции, связь с товарами, ликвидность",
    },
    "Исследования и стратегия": {
        "head_id": 19,
        "description": "Долгосрочные тенденции, сезонность, стратегии",
    },
    "Операционный отдел": {
        "head_id": 18,
        "description": "Производительность, комплаенс, сессии, экзотика",
    },
    "Технологии": {
        "head_id": 20,
        "description": "AI/ML, данные, инфраструктура",
    },
    "Сентимент и Новостной анализ": {
        "head_id": 50,
        "description": "COT, соцсети, новостной тон, розничные настроения",
    },
    "Прогнозирование": {
        "head_id": 56,
        "description": "LSTM, Transformer, модели временных рядов",
    },
    "Алгоритмическая торговля": {
        "head_id": 57,
        "description": "RL-агенты, HFT, скальпинг",
    },
    "Управление портфелем": {
        "head_id": 58,
        "description": "Аллокация капитала, ребалансировка",
    },
    "Тестирование стратегий": {
        "head_id": 60,
        "description": "Бэктестинг, Monte Carlo, Walk-Forward Analysis",
    },
    "Поведенческие финансы": {
        "head_id": 62,
        "description": "Психология участников рынка",
    },
    "Волатильность": {
        "head_id": 63,
        "description": "VIX, опционы на валюты",
    },
    "Фундаментальный анализ": {
        "head_id": 70,
        "description": "Глубокий фундаментальный анализ валют",
    },
}


ANALYSTS = [
    # ═══ ОТДЕЛ: ТЕХНИЧЕСКИЙ АНАЛИЗ ═══
    Analyst(id=1, name="Артём Волков", role="Нач. отдела / Технический аналитик",
            department="Технический анализ",
            responsibilities=["Паттерны", "S/R уровни", "Трендовые линии", "Финальная валидация"],
            tools=["Chart patterns", "S/R", "Trend lines"], is_head=True),
    Analyst(id=2, name="Дмитрий Орлов", role="Тех. аналитик (индикаторы)",
            department="Технический анализ",
            responsibilities=["RSI", "MACD", "Stochastic", "Дивергенции"],
            tools=["RSI", "MACD", "Stochastic", "CCI"]),
    Analyst(id=3, name="Елена Смирнова", role="Аналитик уровней",
            department="Технический анализ",
            responsibilities=["Фибоначчи", "Pivot Points", "Volume Profile"],
            tools=["Fibonacci", "Pivot Points", "Volume Profile"]),
    Analyst(id=16, name="Роман Егоров", role="Специалист по паттернам",
            department="Технический анализ",
            responsibilities=["Свечные паттерны", "Harmonic", "Elliott Wave"],
            tools=["Candlestick", "Harmonic", "Elliott Wave"]),

    # ═══ ОТДЕЛ: ICT / SMART MONEY ═══
    Analyst(id=27, name="Матвей Жуков", role="Нач. отдела / HTF Bias & Structure",
            department="ICT / Smart Money",
            responsibilities=["HTF Bias", "Market Structure", "POI"],
            tools=["HTF Bias", "Structure Map", "POI Scanner"], is_head=True),
    Analyst(id=28, name="Степан Крылов", role="ICT+SMC (Order Blocks / FVG)",
            department="ICT / Smart Money",
            responsibilities=["Order Blocks", "FVG", "Mitigation"],
            tools=["OB Detector", "FVG Scanner", "Mitigation Tracker"]),
    Analyst(id=33, name="Пётр Зимин", role="Аналитик ликвидности",
            department="ICT / Smart Money",
            responsibilities=["BSL/SSL", "Liquidity Grab", "Stop Hunt"],
            tools=["Liquidity Map", "Stop Hunt Detector"]),
    Analyst(id=65, name="Анастасия Морозова", role="Order Flow & Liquidity Analyst",
            department="ICT / Smart Money",
            responsibilities=["Ордерфлоу", "Ликвидность", "Зоны накопления"],
            tools=["Order Flow", "Volume Profile", "Footprint"]),

    # ═══ ОТДЕЛ: M15 КРАТКОСРОЧНЫЙ АНАЛИЗ ═══
    Analyst(id=32, name="Кирилл Пономарёв", role="Нач. отдела / M15 Kill Zones",
            department="M15 Краткосрочный анализ",
            responsibilities=["Kill Zones", "Сессии", "M15 сигналы"],
            tools=["Session Heatmap", "Kill Zone Timer"], is_head=True),
    Analyst(id=29, name="Олег Баранов", role="BOS/CHoCH/ATR аналитик",
            department="M15 Краткосрочный анализ",
            responsibilities=["BOS", "CHoCH", "ATR", "Структура M15"],
            tools=["BOS Detector", "CHoCH Scanner", "ATR"]),

    # ═══ ОТДЕЛ: МАКРОЭКОНОМИКА ═══
    Analyst(id=30, name="Анна Григорьева", role="Нач. отдела / DXY & Монетарная политика",
            department="Макроэкономика",
            responsibilities=["DXY", "Корреляции", "Монетарная политика"],
            tools=["DXY Monitor", "Rate Tracker", "Correlation Matrix"], is_head=True),
    Analyst(id=4, name="Андрей Козлов", role="Фундаментальный аналитик",
            department="Макроэкономика",
            responsibilities=["ВВП", "CPI", "NFP", "Решения центробанков"],
            tools=["Economic Calendar", "CPI", "GDP"]),
    Analyst(id=5, name="Мария Петрова", role="Аналитик ставок",
            department="Макроэкономика",
            responsibilities=["Yield curve", "Процентные ставки", "Торговый баланс"],
            tools=["Interest Rates", "Yield Curve"]),
    Analyst(id=53, name="Даниил Морозов", role="Forex Macro Analyst",
            department="Макроэкономика",
            responsibilities=["Макроэкономические данные", "ВВП", "Инфляция", "Торговый баланс"],
            tools=["Bloomberg", "Reuters", "Macro Calendar"]),
    Analyst(id=64, name="Максим Ковалёв", role="Central Banks & Monetary Policy Analyst",
            department="Макроэкономика",
            responsibilities=["Политика центробанков", "ФРС", "ЕЦБ", "Банк Англии"],
            tools=["Central Bank Tracker", "Rate Monitor"]),

    # ═══ ОТДЕЛ: КВАНТОВЫЙ АНАЛИЗ ═══
    Analyst(id=8, name="Павел Соколов", role="Нач. отдела / Квантовый аналитик",
            department="Квантовый анализ",
            responsibilities=["Стат. модели", "Распределения", "Оптимизация"],
            tools=["Python", "R", "Backtesting"], is_head=True),
    Analyst(id=9, name="Ирина Морозова", role="ML аналитик",
            department="Квантовый анализ",
            responsibilities=["ML модели", "Нейросети", "Feature engineering"],
            tools=["TensorFlow", "PyTorch", "XGBoost"]),
    Analyst(id=67, name="Роман Сидоров", role="Quantitative Forex Strategist",
            department="Квантовый анализ",
            responsibilities=["Количественные модели", "Статистические стратегии"],
            tools=["Python", "R", "MATLAB"]),

    # ═══ ОТДЕЛ: УПРАВЛЕНИЕ РИСКАМИ ═══
    Analyst(id=10, name="Никита Лебедев", role="Нач. отдела / Аналитик рисков",
            department="Управление рисками",
            responsibilities=["VaR", "Просадки", "Position sizing"],
            tools=["VaR", "Monte Carlo", "Stress Testing"], is_head=True),
    Analyst(id=11, name="Татьяна Попова", role="Менеджер портфеля",
            department="Управление рисками",
            responsibilities=["Диверсификация", "Корреляции портфеля", "Ребалансировка"],
            tools=["Risk Parity", "Rebalancing"]),
    Analyst(id=76, name="Елена Кузнецова", role="Risk & Position Sizing Manager",
            department="Управление рисками",
            responsibilities=["Расчёт рисков", "Позиционирование", "Управление просадками"],
            tools=["VaR Models", "Stress Testing", "Risk Dashboard"]),

    # ═══ ОТДЕЛ: МЕЖРЫНОЧНЫЙ АНАЛИЗ ═══
    Analyst(id=14, name="Алексей Михайлов", role="Нач. отдела / Корреляционный аналитик",
            department="Межрыночный анализ",
            responsibilities=["Корреляции", "Связь с товарами", "Spread trading"],
            tools=["Correlation Matrix", "Cointegration"], is_head=True),
    Analyst(id=12, name="Виктор Сидоров", role="Аналитик волатильности",
            department="Межрыночный анализ",
            responsibilities=["ATR", "Implied vs Realized vol", "Волатильность"],
            tools=["ATR", "Bollinger Width"]),
    Analyst(id=15, name="Юлия Волкова", role="Аналитик ликвидности рынка",
            department="Межрыночный анализ",
            responsibilities=["Order book", "Спреды", "Объёмы"],
            tools=["Order Book", "Volume Analysis"]),
    Analyst(id=54, name="Анна Беляева", role="Cross-Currency & Correlation Analyst",
            department="Межрыночный анализ",
            responsibilities=["Корреляции между парами", "Связь с активами"],
            tools=["Correlation Matrix", "Cointegration", "Spread Charts"]),
    Analyst(id=71, name="Арсений Павлов", role="Statistical Arbitrage Specialist",
            department="Межрыночный анализ",
            responsibilities=["Парный трейдинг", "Статистический арбитраж"],
            tools=["Python", "R", "Spread Trading"]),

    # ═══ ОТДЕЛ: ИССЛЕДОВАНИЯ И СТРАТЕГИЯ ═══
    Analyst(id=19, name="Екатерина Новикова", role="Нач. отдела / Исследователь рынка",
            department="Исследования и стратегия",
            responsibilities=["Тенденции", "Сезонность", "Исторические аналогии"],
            tools=["Historical Data", "Seasonal Analysis"], is_head=True),
    Analyst(id=24, name="Анна Григорьева", role="Валютный стратег",
            department="Исследования и стратегия",
            responsibilities=["PPP", "Fair value", "Долгосрочные прогнозы"],
            tools=["PPP Model", "REER"]),
    Analyst(id=13, name="Наталья Фёдорова", role="Геополитический аналитик",
            department="Исследования и стратегия",
            responsibilities=["Геополитика", "Санкции", "Выборы"],
            tools=["Political Risk Index", "News Monitoring"]),
    Analyst(id=74, name="София Новикова", role="Alternative Data Analyst",
            department="Исследования и стратегия",
            responsibilities=["Альтернативные данные", "Спутники", "Геолокация"],
            tools=["Python", "GIS", "Satellite Data"]),
    Analyst(id=75, name="Владимир Орлов", role="Global Forex Strategy Director",
            department="Исследования и стратегия",
            responsibilities=["Глобальная стратегия", "Долгосрочные тренды"],
            tools=["Macro Models", "Strategy Framework"]),

    # ═══ ОТДЕЛ: ОПЕРАЦИОННЫЙ ОТДЕЛ ═══
    Analyst(id=18, name="Максим Зайцев", role="Нач. отдела / Аналитик производительности",
            department="Операционный отдел",
            responsibilities=["ROI", "CAGR", "Max DD", "Отчёты"],
            tools=["Excel", "SQL", "Performance Attribution"], is_head=True),
    Analyst(id=17, name="Ксения Белова", role="Аналитик алгоритмов",
            department="Операционный отдел",
            responsibilities=["Алгоритмы", "Backtesting", "Оптимизация"],
            tools=["Backtesting Engine", "Sharpe Ratio"]),
    Analyst(id=25, name="Игорь Мещеряков", role="Комплаенс",
            department="Операционный отдел",
            responsibilities=["Проверка сделок", "Лимиты", "Аудит"],
            tools=["Compliance Engine", "Audit Trail"]),
    Analyst(id=31, name="Денис Яковлев", role="Аналитик экзотики",
            department="Операционный отдел",
            responsibilities=["Экзотические пары", "EM валюты"],
            tools=["EM Currency Index", "Sovereign CDS"]),
    Analyst(id=73, name="Иван Козлов", role="Execution & Slippage Specialist",
            department="Операционный отдел",
            responsibilities=["Качество исполнения ордеров", "Slippage"],
            tools=["Execution Analytics", "Latency Monitor"]),

    # ═══ ОТДЕЛ: ТЕХНОЛОГИИ ═══
    Analyst(id=20, name="Денис Козлов", role="Нач. отдела / AI/ML инженер",
            department="Технологии",
            responsibilities=["AI модели", "Интеграция", "Мониторинг дрифта"],
            tools=["Python", "MLflow", "Docker"], is_head=True),
    Analyst(id=26, name="Тимур Асанов", role="Инженер данных",
            department="Технологии",
            responsibilities=["ETL", "Данные", "Качество данных"],
            tools=["Airflow", "PostgreSQL", "Redis"]),
    Analyst(id=55, name="Евгений Соколов", role="Forex ML Engineer",
            department="Технологии",
            responsibilities=["Разработка ML моделей", "Прогнозирование"],
            tools=["TensorFlow", "PyTorch", "Scikit-learn"]),
    Analyst(id=68, name="Ксения Лебедева", role="Dashboard & Visualization Specialist",
            department="Технологии",
            responsibilities=["Дашборды", "Визуализация данных"],
            tools=["Plotly", "D3.js", "Tableau"]),

    # ═══ ОТДЕЛ: СЕНТИМЕНТ И НОВОСНОЙ АНАЛИЗ ═══
    Analyst(id=50, name="Артём Власов", role="Нач. отдела / Chief Sentiment Analyst",
            department="Сентимент и Новостной анализ",
            responsibilities=["Розничные настроения", "COT", "Соцсети", "Telegram", "Новостной тон"],
            tools=["COT Report", "Sentiment API", "NLP"], is_head=True),
    Analyst(id=51, name="Виктория Смирнова", role="Major Pairs News Trader",
            department="Сентимент и Новостной анализ",
            responsibilities=["Торговля на новостях", "NFP", "Ставки ЦБ", "Прогнозирование реакции"],
            tools=["Economic Calendar", "News Feed", "Reaction Model"]),
    Analyst(id=72, name="Мария Волкова", role="Retail Sentiment & COT Analyst",
            department="Сентимент и Новостной анализ",
            responsibilities=["Отчёты COT", "Анализ розничных трейдеров"],
            tools=["COT Report", "Commitment of Traders"]),

    # ═══ ОТДЕЛ: ПРОГНОЗИРОВАНИЕ ═══
    Analyst(id=56, name="Полина Орлова", role="Нач. отдела / Time Series Forecaster",
            department="Прогнозирование",
            responsibilities=["LSTM", "Transformer", "Модели временных рядов"],
            tools=["TensorFlow", "PyTorch", "Prophet"], is_head=True),

    # ═══ ОТДЕЛ: АЛГОРИТМИЧЕСКАЯ ТОРГОВЛЯ ═══
    Analyst(id=57, name="Илья Романов", role="Нач. отдела / RL Forex Trader",
            department="Алгоритмическая торговля",
            responsibilities=["RL-агенты", "Торговые решения", "Автоматизация"],
            tools=["Stable-Baselines", "OpenAI Gym", "Python"], is_head=True),
    Analyst(id=69, name="Дмитрий Соколов", role="High-Frequency Forex Trader",
            department="Алгоритмическая торговля",
            responsibilities=["HFT-стратегии", "Скальпинг", "Микроструктура"],
            tools=["C++", "Low Latency", "FIX Protocol"]),

    # ═══ ОТДЕЛ: УПРАВЛЕНИЕ ПОРТФЕЛЕМ ═══
    Analyst(id=58, name="Сергей Волков", role="Нач. отдела / Chief Portfolio Manager",
            department="Управление портфелем",
            responsibilities=["Управление портфелем", "Аллокация капитала"],
            tools=["Portfolio Analytics", "Risk Parity"], is_head=True),
    Analyst(id=59, name="Ольга Морозова", role="Currency Allocation Specialist",
            department="Управление портфелем",
            responsibilities=["Оптимальное распределение капитала", "Ребалансировка"],
            tools=["Mean-Variance", "Black-Litterman"]),

    # ═══ ОТДЕЛ: ТЕСТИРОВАНИЕ СТРАТЕГИЙ ═══
    Analyst(id=60, name="Никита Воронин", role="Нач. отдела / Head of Backtesting",
            department="Тестирование стратегий",
            responsibilities=["Глубокий бэктестинг", "Оптимизация стратегий"],
            tools=["Python", "Backtrader", "VectorBT"], is_head=True),
    Analyst(id=61, name="Дарья Киселёва", role="Monte Carlo & Walk-Forward Specialist",
            department="Тестирование стратегий",
            responsibilities=["Стресс-тестирование", "Monte Carlo", "Walk-Forward Analysis"],
            tools=["Python", "R", "Monte Carlo Simulation"]),

    # ═══ ОТДЕЛ: ПОВЕДЕНЧЕСКИЕ ФИНАНСЫ ═══
    Analyst(id=62, name="Александр Петров", role="Нач. отдела / Behavioral Forex Psychology",
            department="Поведенческие финансы",
            responsibilities=["Психологические факторы", "Поведение участников рынка"],
            tools=["Sentiment Analysis", "Behavioral Models"], is_head=True),

    # ═══ ОТДЕЛ: ВОЛАТИЛЬНОСТЬ ═══
    Analyst(id=63, name="Константин Фёдоров", role="Нач. отдела / Volatility & Options on FX",
            department="Волатильность",
            responsibilities=["Анализ волатильности", "VIX", "Опционы на валюты"],
            tools=["Volatility Surface", "Options Pricer", "VIX Monitor"], is_head=True),

    # ═══ ОТДЕЛ: ФУНДАМЕНТАЛЬНЫЙ АНАЛИЗ ═══
    Analyst(id=70, name="Екатерина Романова", role="Нач. отдела / Fundamental Forex Sector",
            department="Фундаментальный анализ",
            responsibilities=["Глубокий фундаментальный анализ валют"],
            tools=["Economic Data", "Fundamental Models"], is_head=True),
]


def get_department_heads() -> dict[str, Analyst]:
    heads = {}
    for dept, cfg in DEPARTMENTS_STRUCTURE.items():
        head_id = cfg["head_id"]
        for a in ANALYSTS:
            if a.id == head_id and a.department == dept:
                heads[dept] = a
                break
    return heads


def get_department_members(dept: str) -> list[Analyst]:
    return [a for a in ANALYSTS if a.department == dept]


def get_all_departments() -> dict[str, dict]:
    result = {}
    for dept, cfg in DEPARTMENTS_STRUCTURE.items():
        members = get_department_members(dept)
        result[dept] = {
            "description": cfg["description"],
            "head": next((a.name for a in members if a.is_head), "N/A"),
            "members": [a.name for a in members],
            "count": len(members),
        }
    return result
