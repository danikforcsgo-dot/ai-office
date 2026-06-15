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

    # ═══ ОТДЕЛ: КВАНТОВЫЙ АНАЛИЗ ═══
    Analyst(id=8, name="Павел Соколов", role="Нач. отдела / Квантовый аналитик",
            department="Квантовый анализ",
            responsibilities=["Стат. модели", "Распределения", "Оптимизация"],
            tools=["Python", "R", "Backtesting"], is_head=True),
    Analyst(id=9, name="Ирина Морозова", role="ML аналитик",
            department="Квантовый анализ",
            responsibilities=["ML модели", "Нейросети", "Feature engineering"],
            tools=["TensorFlow", "PyTorch", "XGBoost"]),

    # ═══ ОТДЕЛ: УПРАВЛЕНИЕ РИСКАМИ ═══
    Analyst(id=10, name="Никита Лебедев", role="Нач. отдела / Аналитик рисков",
            department="Управление рисками",
            responsibilities=["VaR", "Просадки", "Position sizing"],
            tools=["VaR", "Monte Carlo", "Stress Testing"], is_head=True),
    Analyst(id=11, name="Татьяна Попова", role="Менеджер портфеля",
            department="Управление рисками",
            responsibilities=["Диверсификация", "Корреляции портфеля", "Ребалансировка"],
            tools=["Risk Parity", "Rebalancing"]),

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

    # ═══ ОТДЕЛ: ТЕХНОЛОГИИ ═══
    Analyst(id=20, name="Денис Козлов", role="Нач. отдела / AI/ML инженер",
            department="Технологии",
            responsibilities=["AI модели", "Интеграция", "Мониторинг дрифта"],
            tools=["Python", "MLflow", "Docker"], is_head=True),
    Analyst(id=26, name="Тимур Асанов", role="Инженер данных",
            department="Технологии",
            responsibilities=["ETL", "Данные", "Качество данных"],
            tools=["Airflow", "PostgreSQL", "Redis"]),
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
