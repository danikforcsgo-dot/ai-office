import json
import time
import os
import sys
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "..", "core"))

_last_request_time = 0


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 2.0:
        time.sleep(2.0 - elapsed)
    _last_request_time = time.time()


class LLMClient:
    def __init__(self, model="mistral-small-latest", api_key=""):
        self.provider = "mistral"
        self.model = model
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"
        self._broken = False
        self._broken_at = 0

    def chat(self, messages, temperature=0.7, max_tokens=2000, timeout=10):
        if self._broken and (time.time() - self._broken_at) < 60:
            raise Exception("Mistral rate limited — пропускаю")
        self._broken = False
        _rate_limit()
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            timeout=timeout,
        )
        if resp.status_code == 429:
            self._broken = True
            self._broken_at = time.time()
            raise Exception("Rate limit 429 — Mistral заблокировал на время")
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:100]}")
        return resp.json()["choices"][0]["message"]["content"]

    def chat_json(self, messages, temperature=0.3, max_tokens=2000):
        raw = self.chat(messages, temperature, max_tokens)
        for char in ["{", "["]:
            start = raw.find(char)
            end = raw.rfind("}" if char == "{" else "]") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(raw[start:end])
                except json.JSONDecodeError:
                    pass
        return {"raw_response": raw}


_llm_instance = None


def get_llm():
    global _llm_instance
    if _llm_instance is None:
        from config import MISTRAL_API_KEY
        _llm_instance = LLMClient(api_key=MISTRAL_API_KEY)
    return _llm_instance


def reset_llm():
    global _llm_instance
    _llm_instance = None


def analyst_llm_analysis(analyst, market_data, llm=None):
    llm = llm or get_llm()
    prompt = f"""Ты — аналитик на Forex рынке. Имя: {analyst['name']}, Роль: {analyst['role']}.
Отдел: {analyst['department']}. Обязанности: {', '.join(analyst['responsibilities'])}.

Данные по рынку:
{json.dumps(market_data, ensure_ascii=False, indent=2)}

Дай КРАТКОЕ заключение (2-4 предложения) по своей специализации.
Верни JSON: {{"signal": "BUY/SELL/NEUTRAL", "confidence": 0.0-1.0, "summary": "текст заключения", "key_levels": ["уровень1", "уровень2"]}}"""

    messages = [
        {"role": "system", "content": "Ты профессиональный Forex аналитик. Отвечай кратко и по делу. Всегда возвращай JSON."},
        {"role": "user", "content": prompt},
    ]
    try:
        result = llm.chat_json(messages, temperature=0.3)
        return {"signal": result.get("signal", "NEUTRAL"), "confidence": result.get("confidence", 0.5),
                "summary": result.get("summary", ""), "key_levels": result.get("key_levels", []), "llm_model": llm.model}
    except Exception as e:
        return {"signal": "NEUTRAL", "confidence": 0.0, "summary": f"LLM error: {e}", "key_levels": [], "llm_model": llm.model}


def debate_llm(messages_history, analyst_a, analyst_b, topic, llm=None):
    llm = llm or get_llm()
    history = "\n".join([f"{m['speaker']}: {m['text']}" for m in messages_history[-4:]])
    prompt = f"""Ты участвуешь в дебатах аналитиков на Forex рынке.
Тема: {topic}
Участники: {analyst_a['name']} ({analyst_a['role']}) vs {analyst_b['name']} ({analyst_b['role']})
Предыдущие аргументы:
{history}
Напиши аргументированный ответ (2-3 предложения) от имени {analyst_a['name']}."""
    messages = [
        {"role": "system", "content": "Ты опытный Forex аналитик в дебатах."},
        {"role": "user", "content": prompt},
    ]
    try:
        return llm.chat(messages, temperature=0.7, max_tokens=500)
    except Exception as e:
        return f"[LLM недоступен: {e}]"


def news_llm_analysis(news_items, pair, llm=None):
    llm = llm or get_llm()
    news_text = "\n".join([f"- {n.get('title', '')}" for n in news_items[:10]])
    prompt = f"""Проанализируй новости для {pair}:
{news_text}
Верни JSON: {{"sentiment": "POSITIVE/NEGATIVE/NEUTRAL", "impact": "high/medium/low", "summary": "текст", "signal": "BUY/SELL/NEUTRAL"}}"""
    messages = [
        {"role": "system", "content": "Ты новостной аналитик Forex. Возвращай JSON."},
        {"role": "user", "content": prompt},
    ]
    try:
        result = llm.chat_json(messages, temperature=0.3)
        return {"sentiment": result.get("sentiment", "NEUTRAL"), "impact": result.get("impact", "low"),
                "summary": result.get("summary", ""), "signal": result.get("signal", "NEUTRAL")}
    except Exception as e:
        return {"sentiment": "NEUTRAL", "impact": "low", "summary": f"LLM error: {e}", "signal": "NEUTRAL"}


def department_head_llm_summary(head, member_reports, llm=None):
    llm = llm or get_llm()
    reports_text = json.dumps([{"name": r.get("analyst_name"), "summary": r.get("summary", "")[:200]} for r in member_reports], ensure_ascii=False)
    prompt = f"""Начальник "{head['department']}" ({head['name']}). Отчёты: {reports_text}
Дай вердикт: BULLISH/BEARISH/NEUTRAL. JSON: {{"verdict": "...", "summary": "текст", "confidence": 0.0-1.0, "key_finding": "вывод"}}"""
    messages = [{"role": "system", "content": "Ты руководитель отдела аналитиков."}, {"role": "user", "content": prompt}]
    try:
        result = llm.chat_json(messages, temperature=0.3)
        return {"verdict": result.get("verdict", "NEUTRAL"), "summary": result.get("summary", ""),
                "confidence": result.get("confidence", 0.5), "key_finding": result.get("key_finding", "")}
    except Exception as e:
        return {"verdict": "NEUTRAL", "summary": f"LLM error: {e}", "confidence": 0.0, "key_finding": ""}


def global_meeting_llm_report(dept_reports, llm=None):
    llm = llm or get_llm()
    depts_text = json.dumps([{"dept": r.get("department"), "verdict": r.get("verdict")} for r in dept_reports], ensure_ascii=False)
    prompt = f"""CEO hedge fund. Отчёты: {depts_text}
Дай глобальную рекомендацию. JSON: {{"global_verdict": "BULLISH/BEARISH/NEUTRAL", "recommendation": "текст", "risk_note": "риски", "confidence": 0.0-1.0}}"""
    messages = [{"role": "system", "content": "Ты CEO hedge fund."}, {"role": "user", "content": prompt}]
    try:
        result = llm.chat_json(messages, temperature=0.3)
        return {"global_verdict": result.get("global_verdict", "NEUTRAL"), "recommendation": result.get("recommendation", ""),
                "risk_note": result.get("risk_note", ""), "confidence": result.get("confidence", 0.5)}
    except Exception as e:
        return {"global_verdict": "NEUTRAL", "recommendation": f"LLM error: {e}", "risk_note": "", "confidence": 0.0}
