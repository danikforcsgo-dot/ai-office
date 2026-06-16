import random
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import LLM_ENABLED

_cycle_counter = 0
DEBATES_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "debate_history.json")
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "debate_memory.json")
_used_arguments = set()
MAX_ARGUMENT_CACHE = 100


def _get_dept_weights() -> dict:
    try:
        from staff import staff_manager
        return {dept: data.weight for dept, data in staff_manager.departments.items()}
    except Exception:
        return {
            "Управление рисками": 1.5,
            "Макроэкономика": 1.3,
            "Технический анализ": 1.2,
            "ICT / Smart Money": 1.2,
            "Исследования и стратегия": 1.1,
            "Квантовый анализ": 1.1,
            "Межрыночный анализ": 1.1,
        }


def _load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_memory(memory: dict):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _calculate_max_rounds(bullish_heads: list, bearish_heads: list) -> int:
    total = len(bullish_heads) + len(bearish_heads)
    if total < 2:
        return 1
    disagreement = abs(len(bullish_heads) - len(bearish_heads)) / max(total, 1)
    if disagreement > 0.6:
        return 1
    elif disagreement > 0.3:
        return 2
    return 3


def run_debate(all_reports: list[dict], dept_reports: list[dict] = None) -> list[dict]:
    global _cycle_counter
    _cycle_counter += 1
    messages = []

    bullish_heads = [r for r in all_reports if r.get("is_head") and "BULLISH" in r.get("summary", "") and r.get("department") != "IT отдел"]
    bearish_heads = [r for r in all_reports if r.get("is_head") and "BEARISH" in r.get("summary", "") and r.get("department") != "IT отдел"]

    if not bullish_heads and not bearish_heads:
        messages.append({
            "speaker": "Модератор",
            "text": f"#{_cycle_counter} Все аналитики нейтральны. Дебаты не проводятся.",
            "type": "moderator",
        })
        return messages

    pair = _select_pair_llm(all_reports) if LLM_ENABLED else _select_pair_random(all_reports)

    bull_team = _select_team(bullish_heads, "BUY", 2)
    bear_team = _select_team(bearish_heads, "SELL", 2)

    judge = None
    expert = None
    if dept_reports:
        for r in dept_reports:
            if "Управление рисками" in r.get("department", ""):
                judge = r
        if bull_team and bear_team:
            bull_depts = {a.get("department") for a in bull_team}
            bear_depts = {a.get("department") for a in bear_team}
            judge_dept = judge.get("department") if judge else ""
            other_heads = [r for r in dept_reports
                          if r.get("department") not in bull_depts | bear_depts | {judge_dept}]
            if other_heads:
                expert = random.choice(other_heads)

    max_rounds = _calculate_max_rounds(bullish_heads, bearish_heads)

    messages.append({
        "speaker": "Модератор",
        "text": f"#{_cycle_counter} ДЕБАТЫ: {pair} ({max_rounds} раундов)",
        "type": "moderator",
    })

    if bull_team:
        names = ", ".join([a["analyst_name"] for a in bull_team])
        messages.append({
            "speaker": "Модератор",
            "text": f"Бычий лагерь: {names}",
            "type": "moderator",
        })
    if bear_team:
        names = ", ".join([a["analyst_name"] for a in bear_team])
        messages.append({
            "speaker": "Модератор",
            "text": f"Медвежий лагерь: {names}",
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

    bull_args = []
    bear_args = []

    bull_speaker = random.choice(bull_team) if bull_team else None
    bear_speaker = random.choice(bear_team) if bear_team else None

    if bull_speaker:
        bull_arg = _llm_opening(bull_speaker, pair, "BUY") if LLM_ENABLED else _template_opening(bull_speaker, pair, "BUY")
        bull_args.append(bull_arg)
        messages.append({
            "speaker": bull_speaker["analyst_name"],
            "department": bull_speaker["department"],
            "text": bull_arg,
            "type": "opening",
            "side": "BUY",
            "round": 1,
        })
    if bear_speaker:
        bear_arg = _llm_opening(bear_speaker, pair, "SELL") if LLM_ENABLED else _template_opening(bear_speaker, pair, "SELL")
        bear_args.append(bear_arg)
        messages.append({
            "speaker": bear_speaker["analyst_name"],
            "department": bear_speaker["department"],
            "text": bear_arg,
            "type": "opening",
            "side": "SELL",
            "round": 1,
        })

    for round_num in range(2, max_rounds + 1):
        bull_speaker = random.choice(bull_team) if bull_team else None
        bear_speaker = random.choice(bear_team) if bear_team else None

        if bull_speaker and bear_args:
            bull_counter = _llm_counter(bull_speaker, bear_args[-1], pair, "BUY") if LLM_ENABLED else _template_counter(bull_speaker, bear_args[-1], pair, "BUY")
            bull_args.append(bull_counter)
            messages.append({
                "speaker": bull_speaker["analyst_name"],
                "department": bull_speaker["department"],
                "text": bull_counter,
                "type": "counter" if round_num == 2 else "rebuttal",
                "side": "BUY",
                "round": round_num,
            })
        if bear_speaker and bull_args:
            bear_counter = _llm_counter(bear_speaker, bull_args[-1], pair, "SELL") if LLM_ENABLED else _template_counter(bear_speaker, bull_args[-1], pair, "SELL")
            bear_args.append(bear_counter)
            messages.append({
                "speaker": bear_speaker["analyst_name"],
                "department": bear_speaker["department"],
                "text": bear_counter,
                "type": "counter" if round_num == 2 else "rebuttal",
                "side": "SELL",
                "round": round_num,
            })

    if expert:
        expert_text = _template_expert(expert, bull_args[-1] if bull_args else "", bear_args[-1] if bear_args else "", pair)
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
    _update_memory(pair, vote_result)
    return messages


def _select_team(heads: list[dict], side: str, max_members: int = 2) -> list[dict]:
    if not heads:
        return []
    scored = []
    for h in heads:
        count = sum(1 for s in h.get("signals", []) if s.get("signal") == side)
        scored.append((count, h))
    scored.sort(key=lambda x: x[0], reverse=True)
    seen_depts = set()
    team = []
    for _, h in scored:
        if len(team) >= max_members:
            break
        dept = h.get("department", "")
        if dept not in seen_depts or len(team) < 2:
            team.append(h)
            seen_depts.add(dept)
    return team if team else random.sample(heads, min(max_members, len(heads)))


def _select_pair_llm(all_reports: list[dict]) -> str:
    from llm_client import get_llm
    memory = _load_memory()
    controversial = [p for p, d in memory.items() if d.get("confidence", 1.0) < 0.6 and d.get("debates", 0) > 0]
    if controversial and random.random() < 0.5:
        return random.choice(controversial)
    try:
        llm = get_llm()
        signals_summary = []
        for r in all_reports:
            for sig in r.get("signals", []):
                if sig.get("pair"):
                    signals_summary.append(f"{sig['pair']}: {sig.get('signal', '?')}")
        prompt = f"""Сигналы аналитиков по золоту:
{chr(10).join(signals_summary[:20])}

Выбери инструмент для дебатов (где больше расхождений).
Ответь ТОЛЬКО одним названием (например: XAU/USD)."""
        messages = [
            {"role": "system", "content": "Ты модератор дебатов по золоту. Выбери инструмент."},
            {"role": "user", "content": prompt},
        ]
        result = llm.chat(messages, temperature=0.3, max_tokens=20)
        pair = result.strip().strip('"').strip("'")
        valid_pairs = ["XAU/USD", "XAUUSD", "GC=F"]
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
    return random.choice(list(pairs)) if pairs else "XAU/USD"


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
    dept_weights = _get_dept_weights()

    if dept_reports:
        for r in dept_reports:
            v = r.get("verdict", "NEUTRAL")
            weight = dept_weights.get(r["department"], 1.0)
            voters.append(f"{r['department']} [{v}] x{weight}")
            if v == "BULLISH":
                buy += weight
            elif v == "BEARISH":
                sell += weight
            else:
                neutral += weight
    else:
        for r in all_reports:
            if r.get("is_head"):
                s = r.get("summary", "")
                weight = dept_weights.get(r["department"], 1.0)
                if "BULLISH" in s:
                    buy += weight
                    voters.append(f"{r['department']} [BULLISH] x{weight}")
                elif "BEARISH" in s:
                    sell += weight
                    voters.append(f"{r['department']} [BEARISH] x{weight}")
                else:
                    neutral += weight
                    voters.append(f"{r['department']} [NEUTRAL] x{weight}")

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


def _update_memory(pair: str, vote_result: dict):
    memory = _load_memory()
    if pair not in memory:
        memory[pair] = {"debates": 0, "bullish": 0, "bearish": 0, "neutral": 0}
    memory[pair]["debates"] += 1
    result = vote_result["result"]
    if result == "BULLISH":
        memory[pair]["bullish"] += 1
    elif result == "BEARISH":
        memory[pair]["bearish"] += 1
    else:
        memory[pair]["neutral"] += 1
    total = memory[pair]["debates"]
    memory[pair]["confidence"] = max(memory[pair].get("bullish", 0), memory[pair].get("bearish", 0)) / max(total, 1)
    _save_memory(memory)


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
