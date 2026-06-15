import random


_cycle_counter = 0

COUNTER_ARGUMENTS = {
    "BUY": [
        "RSI уже в зоне перекупленности — вход сейчас слишком рискованно!",
        "Фундаментальный фон не подтверждает бычий сценарий.",
        "Корреляция с DXY показывает укрепление доллара.",
        "Волатильность слишком низкая для входа.",
        "HTF структура показывает медвежий bias.",
        "Слишком много бычьих сигналов — это ловушка толпы.",
        "На M15 видна сопротивление — цена может оттолкнуться.",
        "Объёмы падают на росте — признак исчерпания.",
    ],
    "SELL": [
        "Индикаторы показывают перепроданность — возможен отскок!",
        "Геополитический фон поддерживает эту валюту.",
        "Корреляция с товарами показывает рост.",
        "На M15 виден сильный уровень поддержки.",
        "Квантовая модель предсказывает среднесрочный рост.",
        "Слишком много медвежьих сигналов — рынок уже отыграл падение.",
        "OB на часовом показывает зону спроса.",
        "Дивергенция RSI указывает на разворот.",
    ],
}

OPENING_BULLISH = [
    "На {pair} индикаторы дают чёткий бычий сигнал. {evidence} — время покупать!",
    "{pair} формирует восходящий структуру. {evidence} — бычий bias подтверждается.",
    "Анализ {pair} показывает потенциал роста. {evidence}. Готов к long.",
]

OPENING_BEARISH = [
    "На {pair} индикаторы дают чёткий медвежий сигнал. {evidence} — пора продавать!",
    "{pair} формирует нисходящую структуру. {evidence} — медвежий bias подтверждается.",
    "Анализ {pair} показывает потенциал падения. {evidence}. Готов к short.",
]


def run_debate(all_reports: list[dict]) -> list[dict]:
    global _cycle_counter
    _cycle_counter += 1
    messages = []
    bullish = [r for r in all_reports if "BULLISH" in r.get("summary", "")]
    bearish = [r for r in all_reports if "BEARISH" in r.get("summary", "")]

    if not bullish and not bearish:
        messages.append({
            "speaker": "Модератор",
            "text": f"#{_cycle_counter} Все аналитики нейтральны. Спорить не о чем.",
            "type": "moderator",
        })
        return messages

    messages.append({
        "speaker": "Модератор",
        "text": f"#{_cycle_counter} Дебаты: {len(bullish)} бычьих vs {len(bearish)} медвежьих.",
        "type": "moderator",
    })

    if bullish:
        b = random.choice(bullish)
        msg = _build_argument(b, "bullish")
        messages.append(msg)
        if bearish:
            r = random.choice(bearish)
            counter = _build_counter(r, b, "BUY")
            messages.append(counter)

    if bearish:
        b = random.choice(bearish)
        msg = _build_argument(b, "bearish")
        messages.append(msg)
        if bullish:
            r = random.choice(bullish)
            counter = _build_counter(r, b, "SELL")
            messages.append(counter)

    if bullish and bearish:
        swing = random.choice(bullish + bearish)
        agreement = _find_agreement(swing, bullish, bearish)
        if agreement:
            messages.append(agreement)

    bull_score = sum(_report_score(r) for r in bullish)
    bear_score = sum(_report_score(r) for r in bearish)

    if bull_score > bear_score * 1.5:
        conclusion = f"#{_cycle_counter} Итог: бычьи аргументы сильнее ({bull_score:.0f} vs {bear_score:.0f}). Рекомендация: LONG."
    elif bear_score > bull_score * 1.5:
        conclusion = f"#{_cycle_counter} Итог: медвежьи аргументы сильнее ({bear_score:.0f} vs {bull_score:.0f}). Рекомендация: SHORT."
    else:
        conclusion = f"#{_cycle_counter} Итог: мнения разделились ({bull_score:.0f} vs {bear_score:.0f}). Рекомендация: WAIT."

    messages.append({"speaker": "Модератор", "text": conclusion, "type": "moderator"})
    return messages


def _report_score(report: dict) -> float:
    buy = sum(1 for s in report.get("signals", []) if s.get("signal") == "BUY")
    sell = sum(1 for s in report.get("signals", []) if s.get("signal") == "SELL")
    return buy - sell


def _build_argument(analyst: dict, side: str) -> dict:
    pair = ""
    evidence = []
    for f in analyst.get("findings", []):
        if f.get("pair"):
            pair = f["pair"]
        for k, v in f.items():
            if k in ("signal", "pair"):
                continue
            if v and v != "NEUTRAL" and v != "None" and v != "No FVG":
                evidence.append(f"{k}={v}" if not isinstance(v, (list, dict)) else f"{k}")
                break

    evidence_str = ", ".join(evidence[:3]) if evidence else "данные анализа"

    if side == "bullish":
        template = random.choice(OPENING_BULLISH)
    else:
        template = random.choice(OPENING_BEARISH)
    base = template.format(pair=pair, evidence=evidence_str)

    return {
        "speaker": analyst["analyst_name"],
        "department": analyst["department"],
        "text": base,
        "type": "opening",
    }


def _build_counter(responder: dict, original: dict, against_side: str) -> dict:
    counter = random.choice(COUNTER_ARGUMENTS[against_side])
    pair = ""
    for f in responder.get("findings", []):
        if f.get("pair"):
            pair = f["pair"]
            break
    evidence = []
    for f in responder.get("findings", []):
        for k, v in f.items():
            if k in ("signal", "pair"):
                continue
            if v and v != "NEUTRAL" and v != "None":
                evidence.append(f"{k}={v}" if not isinstance(v, (list, dict)) else f"{k}")
                break
        if evidence:
            break
    evidence_str = ", ".join(evidence[:2]) if evidence else ""
    text = f"{original['analyst_name']} возражу: {counter}"
    if evidence_str:
        text += f" Мои данные: {evidence_str}."

    return {
        "speaker": responder["analyst_name"],
        "department": responder["department"],
        "text": text,
        "type": "counter",
    }


def _find_agreement(swing: dict, bullish: list, bearish: list) -> dict | None:
    if swing in bullish and bearish:
        evidence = []
        for f in swing.get("findings", []):
            for k, v in f.items():
                if k not in ("signal", "pair") and v and v != "NEUTRAL":
                    evidence.append(f"{k}={v}" if not isinstance(v, (list, dict)) else k)
                    break
            if evidence:
                break
        ev = ", ".join(evidence[:2]) if evidence else "дополнительные данные"
        return {
            "speaker": swing["analyst_name"],
            "department": swing["department"],
            "text": f"Пересмотрю позицию. {ev} заслуживают внимания.",
            "type": "concession",
        }
    return None


def format_debate(messages: list[dict]) -> str:
    lines = []
    for msg in messages:
        if msg["type"] == "moderator":
            prefix = "[bold blue]МОДЕРАТОР[/]"
        elif msg["type"] == "opening":
            prefix = f"[bold green]{msg['speaker']}[/] ({msg.get('department', '')})"
        elif msg["type"] == "counter":
            prefix = f"[bold red]{msg['speaker']}[/] ({msg.get('department', '')}) [red]ВОЗРАЖЕНИЕ[/]"
        elif msg["type"] == "concession":
            prefix = f"[bold cyan]{msg['speaker']}[/] ({msg.get('department', '')}) [cyan]КОРРЕКТИРОВКА[/]"
        else:
            prefix = msg.get("speaker", "")
        lines.append(f"  {prefix}: {msg['text']}")
    return "\n".join(lines)
