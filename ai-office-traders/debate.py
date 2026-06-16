import random
import json
import os
from datetime import datetime
from config import LLM_ENABLED

_cycle_counter = 0
DEBATES_FILE = os.path.join(os.path.dirname(__file__), "debate_history.json")


def run_debate(all_reports: list[dict], dept_reports: list[dict] = None) -> list[dict]:
    global _cycle_counter
    _cycle_counter += 1
    messages = []

    bullish_heads = [r for r in all_reports if r.get("is_head") and "BULLISH" in r.get("summary", "")]
    bearish_heads = [r for r in all_reports if r.get("is_head") and "BEARISH" in r.get("summary", "")]

    if not bullish_heads and not bearish_heads:
        messages.append({
            "speaker": "Модератор",
            "text": f"#{_cycle_counter} Все аналитики нейтральны. Дебаты не проводятся.",
            "type": "moderator",
        })
        return messages

    pair = _select_pair_llm(all_reports) if LLM_ENABLED else _select_pair_random(all_reports)

    bull = _select_strongest(bullish_heads, "BUY")
    bear = _select_strongest(bearish_heads, "SELL")

    judge = None
    expert = None
    if dept_reports:
        for r in dept_reports:
            if "Управление рисками" in r.get("department", ""):
                judge = r
        if bull and bear:
            other_heads = [r for r in dept_reports
                          if r.get("department") not in (bull.get("department"), bear.get("department"),
                                                          judge.get("department") if judge else "")]
            if other_heads:
                expert = random.choice(other_heads)

    messages.append({
        "speaker": "Модератор",
        "text": f"#{_cycle_counter} ДЕБАТЫ: {pair}",
        "type": "moderator",
    })

    if bull:
        messages.append({
            "speaker": "Модератор",
            "text": f"Бычий лагерь: {bull['analyst_name']} ({bull['department']})",
            "type": "moderator",
        })
    if bear:
        messages.append({
            "speaker": "Модератор",
            "text": f"Медвежий лагерь: {bear['analyst_name']} ({bear['department']})",
            "type": "moderator",
        })
    if judge:
        messages.append({
            "speaker": "Модератор",
            "text": f"Судья: {judge['head_name']} ({judge['department']})",
            "type": "moderator",
        })
    if expert:
        messages.append({
            "speaker": "Модератор",
            "text": f"Эксперт: {expert['head_name']} ({expert['department']})",
            "type": "moderator",
        })

    bull_arg = ""
    bear_arg = ""

    if LLM_ENABLED and bull and bear:
        bull_arg = _llm_opening(bull, pair, "BUY")
        bear_arg = _llm_opening(bear, pair, "SELL")
    else:
        bull_arg = _template_opening(bull, pair, "BUY") if bull else ""
        bear_arg = _template_opening(bear, pair, "SELL") if bear else ""

    if bull_arg:
        messages.append({
            "speaker": bull["analyst_name"],
            "department": bull["department"],
            "text": bull_arg,
            "type": "opening",
            "side": "BUY",
            "round": 1,
        })
    if bear_arg:
        messages.append({
            "speaker": bear["analyst_name"],
            "department": bear["department"],
            "text": bear_arg,
            "type": "opening",
            "side": "SELL",
            "round": 1,
        })

    bull_counter = ""
    bear_counter = ""

    if LLM_ENABLED and bull and bear_arg:
        bull_counter = _llm_counter(bull, bear_arg, pair, "BUY")
        bear_counter = _llm_counter(bear, bull_arg, pair, "SELL") if bull_arg else ""
    else:
        bull_counter = _template_counter(bull, bear_arg, pair, "BUY") if bull else ""
        bear_counter = _template_counter(bear, bull_arg, pair, "SELL") if bear else ""

    if bull_counter:
        messages.append({
            "speaker": bull["analyst_name"],
            "department": bull["department"],
            "text": bull_counter,
            "type": "counter",
            "side": "BUY",
            "round": 2,
        })
    if bear_counter:
        messages.append({
            "speaker": bear["analyst_name"],
            "department": bear["department"],
            "text": bear_counter,
            "type": "counter",
            "side": "SELL",
            "round": 2,
        })

    bull_rebuttal = ""
    bear_rebuttal = ""

    if LLM_ENABLED and bull and bear_counter:
        bull_rebuttal = _llm_rebuttal(bull, bear_counter, pair, "BUY")
        bear_rebuttal = _llm_rebuttal(bear, bull_counter, pair, "SELL") if bull_counter else ""
    else:
        bull_rebuttal = _template_rebuttal(bull, bear_counter, pair, "BUY") if bull else ""
        bear_rebuttal = _template_rebuttal(bear, bull_counter, pair, "SELL") if bear else ""

    if bull_rebuttal:
        messages.append({
            "speaker": bull["analyst_name"],
            "department": bull["department"],
            "text": bull_rebuttal,
            "type": "rebuttal",
            "side": "BUY",
            "round": 3,
        })
    if bear_rebuttal:
        messages.append({
            "speaker": bear["analyst_name"],
            "department": bear["department"],
            "text": bear_rebuttal,
            "type": "rebuttal",
            "side": "SELL",
            "round": 3,
        })

    if expert:
        expert_text = _template_expert(expert, bull_arg, bear_arg, pair)
        messages.append({
            "speaker": expert["head_name"],
            "department": expert["department"],
            "text": expert_text,
            "type": "expert",
        })

    if judge:
        judge_text = _llm_judge(judge, messages, dept_reports, pair) if LLM_ENABLED else _template_judge(judge)
        messages.append({
            "speaker": judge["head_name"],
            "department": judge["department"],
            "text": judge_text,
            "type": "judge",
            "llm": LLM_ENABLED,
        })

    vote_result = _vote(all_reports, dept_reports)
    messages.append({
        "speaker": "Модератор",
        "text": f"ГОЛОСОВАНИЕ: {vote_result['text']}",
        "type": "vote",
    })

    conclusion = _conclusion(vote_result, pair)
    messages.append({
        "speaker": "Модератор",
        "text": f"#{_cycle_counter} ИТОГ: {conclusion}",
        "type": "moderator",
    })

    _save_debate(messages, pair)
    return messages


def _select_strongest(heads: list[dict], side: str) -> dict:
    if not heads:
        return None
    best = None
    best_signals = 0
    for h in heads:
        count = sum(1 for s in h.get("signals", []) if s.get("signal") == side)
        if count > best_signals:
            best_signals = count
            best = h
    return best or random.choice(heads)


def _select_pair_llm(all_reports: list[dict]) -> str:
    from llm_client import get_llm
    try:
        llm = get_llm()
        signals_summary = []
        for r in all_reports:
            for sig in r.get("signals", []):
                if sig.get("pair"):
                    signals_summary.append(f"{sig['pair']}: {sig.get('signal', '?')}")
        prompt = f"""Сигналы аналитиков:
{chr(10).join(signals_summary[:20])}

Выбери самую спорную валютную пару для дебатов (где больше расхождений).
Ответь ТОЛЬКО одним названием пары (например: EUR/USD)."""
        messages = [
            {"role": "system", "content": "Ты модератор Forex дебатов. Выбери пару."},
            {"role": "user", "content": prompt},
        ]
        result = llm.chat(messages, temperature=0.3, max_tokens=20)
        pair = result.strip().strip('"').strip("'")
        valid_pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "USD/CAD", "NZD/USD"]
        for vp in valid_pairs:
            if vp in pair:
                return vp
        return random.choice(valid_pairs)
    except Exception:
        return _select_pair_random(all_reports)


def _select_pair_random(all_reports: list[dict]) -> str:
    pairs = set()
    for r in all_reports:
        for sig in r.get("signals", []):
            if sig.get("pair"):
                pairs.add(sig["pair"])
    return random.choice(list(pairs)) if pairs else "EUR/USD"


def _llm_judge(judge: dict, messages: list, dept_reports: list, pair: str) -> str:
    from llm_client import get_llm
    try:
        llm = get_llm()
        debate_text = "\n".join([
            f"[{m.get('type', '?')}] {m['speaker']}: {m['text'][:200]}"
            for m in messages if m.get("type") in ("opening", "counter", "rebuttal", "expert")
        ])
        votes_text = ""
        if dept_reports:
            votes = [f"{r['department']}: {r['verdict']}" for r in dept_reports]
            votes_text = "\n".join(votes)
        prompt = f"""Ты — {judge['head_name']}, начальник "{judge['department']}".
Дебаты по {pair}. 3 раунда + эксперт.

{debate_text}

Голоса отделов:
{votes_text}

Оцени каждый аргумент по 1-10 и дай финальный вердикт.
Формат:
Оценка бычьего аргумента: X/10
Оценка медвежьего аргумента: X/10
Вердикт: BULLISH/BEARISH/NEUTRAL
Обоснование: (2-3 предложения)"""
        messages_llm = [
            {"role": "system", "content": "Ты судья в дебатах аналитиков. Будь объективен, оценивай аргументы по фактам."},
            {"role": "user", "content": prompt},
        ]
        return llm.chat(messages_llm, temperature=0.3, max_tokens=400)
    except Exception:
        return _template_judge(judge)


def _format_findings(analyst: dict) -> str:
    lines = []
    for f in analyst.get("findings", []):
        parts = []
        for k, v in f.items():
            if k == "signal":
                parts.append(f"Сигнал: {v}")
            elif k == "pair":
                parts.append(f"Пара: {v}")
            elif isinstance(v, dict):
                parts.append(f"{k}: {json.dumps(v, ensure_ascii=False)[:80]}")
            elif isinstance(v, list):
                parts.append(f"{k}: {', '.join(str(x) for x in v[:3])}")
            elif v and str(v) not in ("NEUTRAL", "None", "No FVG", "NO DATA"):
                parts.append(f"{k}: {v}")
        if parts:
            lines.append(" | ".join(parts[:4]))
    return "\n".join(lines[:5]) if lines else "Нет данных"


def _llm_opening(analyst: dict, pair: str, side: str) -> str:
    from llm_client import get_llm
    try:
        llm = get_llm()
        findings = _format_findings(analyst)
        side_ru = "LONG (покупка)" if side == "BUY" else "SHORT (продажа)"
        prompt = f"""Ты — {analyst['analyst_name']}, {analyst.get('role', '')}, отдел "{analyst['department']}".
Пара: {pair}. Твоя позиция: {side_ru}.

Твои данные:
{findings}

Напиши сильное открывающее заявление (4-6 предложений):
- Назови ключевые уровни, индикаторы или данные
- Объясни логику
- Будь уверенным и профессиональным"""
        messages = [
            {"role": "system", "content": "Ты опытный Forex-трейдер. Говори конкретно, с уровнями и фактами."},
            {"role": "user", "content": prompt},
        ]
        return llm.chat(messages, temperature=0.75, max_tokens=450)
    except Exception:
        return _template_opening(analyst, pair, side)


def _llm_counter(analyst: dict, opponent_text: str, pair: str, side: str) -> str:
    from llm_client import get_llm
    try:
        llm = get_llm()
        findings = _format_findings(analyst)
        side_ru = "LONG" if side == "BUY" else "SHORT"
        prompt = f"""Ты — {analyst['analyst_name']}, отдел "{analyst['department']}".
Оппонент сказал по {pair}:
"{opponent_text[:400]}"

Твои данные:
{findings}

Напиши контраргумент (3-5 предложений). Опровергни оппонента и приведи свои доказательства."""
        messages = [
            {"role": "system", "content": f"Ты агрессивно, но профессионально защищаешь свою позицию {side_ru}."},
            {"role": "user", "content": prompt},
        ]
        return llm.chat(messages, temperature=0.7, max_tokens=400)
    except Exception:
        return _template_counter(analyst, opponent_text, pair, side)


def _llm_rebuttal(analyst: dict, opponent_counter: str, pair: str, side: str) -> str:
    from llm_client import get_llm
    try:
        llm = get_llm()
        findings = _format_findings(analyst)
        prompt = f"""Ты — {analyst['analyst_name']}, отдел "{analyst['department']}".
Оппонент возразил:
"{opponent_counter[:400]}"

Твои данные:
{findings}

Напиши финальный ответ (rebuttal). Укрепи свою позицию и закрой вопрос."""
        messages = [
            {"role": "system", "content": "Ты подводишь итог своей позиции уверенно и убедительно."},
            {"role": "user", "content": prompt},
        ]
        return llm.chat(messages, temperature=0.65, max_tokens=350)
    except Exception:
        return _template_rebuttal(analyst, opponent_counter, pair, side)


def _template_opening(analyst: dict, pair: str, side: str) -> str:
    if not analyst:
        return ""
    evidence = []
    for f in analyst.get("findings", []):
        for k, v in f.items():
            if k not in ("signal", "pair") and v and v != "NEUTRAL":
                evidence.append(f"{k}={v}" if not isinstance(v, (list, dict)) else k)
                break
        if evidence:
            break
    ev = ", ".join(evidence[:3]) if evidence else "данные анализа"
    dept = analyst.get("department", "анализ")
    if side == "BUY":
        return f"На {pair} вижу бычий потенциал. По данным отдела «{dept}»: {ev}. Рекомендую LONG."
    else:
        return f"На {pair} вижу медвежий потенциал. По данным отдела «{dept}»: {ev}. Рекомендую SHORT."


def _template_counter(analyst: dict, opponent_text: str, pair: str, side: str) -> str:
    if not analyst:
        return ""
    dept = analyst.get("department", "анализ")
    return f"Возражаю — данные отдела «{dept}» указывают на другое направление. Аргументы оппонента не учитывают ключевые факторы. Рекомендую пересмотреть позицию по {pair}."


def _template_rebuttal(analyst: dict, counter_text: str, pair: str, side: str) -> str:
    if not analyst:
        return ""
    dept = analyst.get("department", "анализ")
    return f"Настаиваю на своей позиции. Отдел «{dept}» подтверждает {side} по {pair}. Контраргументы не опровергают ключевые данные."


def _template_expert(expert: dict, bull_arg: str, bear_arg: str, pair: str) -> str:
    if not expert:
        return ""
    dept = expert.get("department", "экспертиза")
    return f"Как эксперт из отдела «{dept}»: оба аргумента имеют место быть. По {pair} рекомендую взвешенный подход с учётом рисков."


def _template_judge(judge: dict) -> str:
    if not judge:
        return "Дебаты завершены. Рекомендую воздержаться."
    return f"Учитывая аргументы сторон и голоса отделов, рекомендую {judge.get('verdict', 'NEUTRAL')}."


def _vote(all_reports: list[dict], dept_reports: list[dict] = None) -> dict:
    buy = 0
    sell = 0
    neutral = 0
    voters = []

    if dept_reports:
        for r in dept_reports:
            v = r.get("verdict", "NEUTRAL")
            voters.append(f"{r['department']} [{v}]")
            if v == "BULLISH":
                buy += 1
            elif v == "BEARISH":
                sell += 1
            else:
                neutral += 1
    else:
        for r in all_reports:
            if r.get("is_head"):
                s = r.get("summary", "")
                if "BULLISH" in s:
                    buy += 1
                    voters.append(f"{r['department']} [BULLISH]")
                elif "BEARISH" in s:
                    sell += 1
                    voters.append(f"{r['department']} [BEARISH]")
                else:
                    neutral += 1
                    voters.append(f"{r['department']} [NEUTRAL]")

    total = buy + sell + neutral
    if buy > sell:
        result = "BULLISH"
    elif sell > buy:
        result = "BEARISH"
    else:
        result = "NEUTRAL"

    return {
        "result": result,
        "buy": buy,
        "sell": sell,
        "neutral": neutral,
        "total": total,
        "text": f"{buy} BUY vs {sell} SELL vs {neutral} NEUTRAL ({total} голосов) -> {result}",
        "voters": voters,
    }


def _conclusion(vote_result: dict, pair: str) -> str:
    r = vote_result["result"]
    if r == "BULLISH":
        return f"По {pair}: бычьи аргументы победили ({vote_result['buy']}/{vote_result['sell']}). Рекомендация: LONG."
    elif r == "BEARISH":
        return f"По {pair}: медвежьи аргументы победили ({vote_result['sell']}/{vote_result['buy']}). Рекомендация: SHORT."
    return f"По {pair}: мнения разделились ({vote_result['buy']}/{vote_result['sell']}/{vote_result['neutral']}). Рекомендация: WAIT."


def _save_debate(messages: list, pair: str):
    try:
        history = []
        if os.path.exists(DEBATES_FILE):
            with open(DEBATES_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        entry = {
            "cycle": _cycle_counter,
            "pair": pair,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": [{
                "speaker": m.get("speaker", ""),
                "department": m.get("department", ""),
                "type": m.get("type", ""),
                "side": m.get("side", ""),
                "round": m.get("round", 0),
                "text": m.get("text", "")[:300],
            } for m in messages],
        }
        history.append(entry)
        history = history[-50:]
        with open(DEBATES_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def format_debate(messages: list[dict]) -> str:
    lines = []
    current_round = 0
    for msg in messages:
        t = msg.get("type", "")
        rnd = msg.get("round", 0)

        if rnd and rnd != current_round:
            current_round = rnd
            round_names = {1: "РАУНД 1: ОТКРЫТИЕ", 2: "РАУНД 2: ВОЗРАЖЕНИЯ", 3: "РАУНД 3: ЗАКЛЮЧЕНИЯ"}
            lines.append(f"\n  [bold white]═══ {round_names.get(rnd, f'РАУНД {rnd}')} ═══[/]")

        llm_tag = " [LLM]" if msg.get("llm") else ""

        if t == "moderator":
            prefix = "[bold blue]МОДЕРАТОР[/]"
        elif t == "opening":
            side = msg.get("side", "")
            color = "green" if side == "BUY" else "red"
            prefix = f"[bold {color}]{msg['speaker']}[/] ({msg.get('department', '')}){llm_tag}"
        elif t == "counter":
            side = msg.get("side", "")
            color = "green" if side == "BUY" else "red"
            prefix = f"[bold {color}]{msg['speaker']}[/] ({msg.get('department', '')}) [yellow]ВОЗРАЖЕНИЕ[/]{llm_tag}"
        elif t == "rebuttal":
            side = msg.get("side", "")
            color = "green" if side == "BUY" else "red"
            prefix = f"[bold {color}]{msg['speaker']}[/] ({msg.get('department', '')}) [cyan]ОТВЕТ[/]{llm_tag}"
        elif t == "expert":
            prefix = f"[bold white]{msg['speaker']}[/] ({msg.get('department', '')}) [white]ЭКСПЕРТ[/]"
        elif t == "judge":
            prefix = f"[bold magenta]{msg['speaker']}[/] ({msg.get('department', '')}) [bold magenta]СУДЬЯ[/]{llm_tag}"
        elif t == "vote":
            prefix = "[bold yellow]ГОЛОСОВАНИЕ[/]"
        else:
            prefix = msg.get("speaker", "")

        lines.append(f"  {prefix}: {msg.get('text', '')}")
    return "\n".join(lines)
