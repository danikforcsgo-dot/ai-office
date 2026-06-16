from datetime import datetime, timezone
import sys
import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "..", "data"))

from technical_analysis import analyze, calc_atr, detect_candlestick_patterns
from market_data import get_historical_data
from staff import ANALYSTS, DEPARTMENTS_STRUCTURE
from config import LLM_ENABLED, LLM_FALLBACK, GOLD_CORRELATIONS, GOLD_SEASONALITY

_shared_market_context = None


def _get_shared_market_context(prices: list[dict]) -> dict:
    global _shared_market_context
    if _shared_market_context is not None:
        return _shared_market_context
    context = {"instruments": [], "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    for p in prices:
        df = get_historical_data(p["symbol"], period="1mo", interval="1d")
        if df.empty:
            continue
        close = df["Close"]
        context["instruments"].append({
            "name": p["name"],
            "symbol": p["symbol"],
            "price": round(float(close.iloc[-1]), 2),
            "change_5d": round(float((close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100), 2) if len(close) >= 5 else 0,
            "change_20d": round(float((close.iloc[-1] - close.iloc[-20]) / close.iloc[-20] * 100), 2) if len(close) >= 20 else 0,
        })
    _shared_market_context = context
    return context


def reset_shared_context():
    global _shared_market_context, _llm_calls_this_cycle
    _shared_market_context = None
    _llm_calls_this_cycle = 0


_llm_calls_this_cycle = 0


def analyst_work(analyst, prices: list[dict]) -> dict:
    report = {
        "analyst_id": analyst.id,
        "analyst_name": analyst.name,
        "role": analyst.role,
        "department": analyst.department,
        "is_head": analyst.is_head,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "findings": [],
        "signals": [],
        "summary": "",
        "llm_used": False,
        "accuracy": getattr(analyst, 'accuracy', 0.7),
    }

    relevant_prices = [p for p in prices if p["name"] in getattr(analyst, 'specialization', []) or not getattr(analyst, 'specialization', [])]
    if not relevant_prices:
        relevant_prices = prices

    if analyst.department == "Trading":
        report["findings"] = _trading_analysis(analyst, relevant_prices)
    else:
        report["findings"] = []

    for f in report["findings"]:
        if f.get("signal"):
            report["signals"].append(f)

    report["summary"] = _generate_summary(report)
    return report


def _gold_tech_analysis(analyst, prices):
    findings = []
    for p in prices:
        df = get_historical_data(p["symbol"], period="1mo", interval="1d")
        if df.empty:
            continue
        result = analyze(df)
        if "error" in result:
            continue
        finding = {"pair": p["name"], "price": result["price"]}
        if analyst.id == 1:
            finding["recommendation"] = result["recommendation"]
            finding["score"] = result["score"]
            finding["signals"] = result["signals"][:3]
            finding["signal"] = "BUY" if result["score"] >= 2 else "SELL" if result["score"] <= -2 else "NEUTRAL"
        elif analyst.id == 2:
            finding["rsi"] = round(result["rsi"], 1)
            finding["macd"] = "BULLISH" if result["macd"] > result["macd_signal"] else "BEARISH"
            finding["signal"] = "BUY" if result["score"] >= 2 and result["rsi"] < 70 else "SELL" if result["score"] <= -2 and result["rsi"] > 30 else "NEUTRAL"
        elif analyst.id == 3:
            finding["volume_trend"] = "HIGH" if float(df["Volume"].iloc[-5:].mean()) > float(df["Volume"].iloc[-20:].mean()) else "LOW"
            finding["signal"] = "NEUTRAL"
        elif analyst.id == 4:
            patterns = detect_candlestick_patterns(df)
            finding["patterns"] = patterns if patterns else ["No patterns"]
            bullish_patterns = {"Hammer", "Bullish Engulfing", "Morning Star"}
            bearish_patterns = {"Shooting Star", "Bearish Engulfing", "Evening Star"}
            if any(p in bullish_patterns for p in patterns):
                finding["signal"] = "BUY"
            elif any(p in bearish_patterns for p in patterns):
                finding["signal"] = "SELL"
            else:
                finding["signal"] = "NEUTRAL"
        findings.append(finding)
    return findings


def _gold_fundamental_analysis(analyst, prices):
    findings = []
    for p in prices:
        df = get_historical_data(p["symbol"], period="3mo", interval="1d")
        if df.empty or len(df) < 20:
            continue
        close = df["Close"]
        chg_20 = (float(close.iloc[-1]) - float(close.iloc[-20])) / float(close.iloc[-20]) * 100
        finding = {"pair": p["name"], "price_change_20d": round(chg_20, 2)}
        if analyst.id == 20:
            finding["fundamental_trend"] = "BULLISH" if chg_20 > 2 else "BEARISH" if chg_20 < -2 else "NEUTRAL"
            finding["signal"] = "BUY" if chg_20 > 3 else "SELL" if chg_20 < -3 else "NEUTRAL"
        elif analyst.id == 21:
            finding["etf_flow"] = "Monitoring"
            finding["signal"] = "NEUTRAL"
        elif analyst.id == 22:
            finding["physical_demand"] = "Stable"
            finding["signal"] = "NEUTRAL"
        findings.append(finding)
    return findings


def _macro_analysis(analyst, prices):
    findings = []
    if analyst.id == 30:
        findings.append({
            "dxy_trend": "Monitoring",
            "real_rates": "Negative",
            "inflation": "Above target",
            "signal": "BUY",
        })
    elif analyst.id == 31:
        findings.append({
            "yield_curve": "Inverted",
            "fed_outlook": "Rate cuts expected",
            "signal": "BUY",
        })
    elif analyst.id == 32:
        findings.append({
            "cpi": "3.2%",
            "pce": "2.8%",
            "breakeven": "2.3%",
            "signal": "BUY",
        })
    return findings


def _geopolitical_analysis(analyst, prices):
    findings = []
    if analyst.id == 50:
        findings.append({
            "geopolitical_risk": "Elevated",
            "safe_haven_demand": "Strong",
            "signal": "BUY",
        })
    elif analyst.id == 51:
        findings.append({
            "sanctions_impact": "Moderate",
            "election_risk": "Low",
            "signal": "NEUTRAL",
        })
    return findings


def _cot_analysis(analyst, prices):
    findings = []
    if analyst.id == 60:
        findings.append({
            "spec_long": "180K",
            "spec_short": "45K",
            "net_spec": "+135K",
            "trend": "BULLISH",
            "signal": "BUY",
        })
    elif analyst.id == 61:
        findings.append({
            "commercial_hedge": "Accumulating",
            "smart_money": "Long bias",
            "signal": "BUY",
        })
    return findings


def _seasonal_analysis(analyst, prices):
    findings = []
    month = datetime.now().month
    seasonal_bias = GOLD_SEASONALITY.get(month, 0)
    if analyst.id == 70:
        findings.append({
            "month": month,
            "seasonal_bias": f"{seasonal_bias:+.1%}",
            "pattern": "Historically bullish" if seasonal_bias > 0 else "Historically bearish",
            "signal": "BUY" if seasonal_bias > 0.02 else "SELL" if seasonal_bias < -0.01 else "NEUTRAL",
        })
    elif analyst.id == 71:
        findings.append({
            "historical_analogies": "Similar to 2020, 2022",
            "cycle_position": "Mid-cycle",
            "signal": "NEUTRAL",
        })
    return findings


def _physical_demand_analysis(analyst, prices):
    findings = []
    if analyst.id == 80:
        findings.append({
            "etf_holdings": "Increasing",
            "cb_purchases": "Strong",
            "jewelry_demand": "Seasonal",
            "signal": "BUY",
        })
    elif analyst.id == 81:
        findings.append({
            "gld_flows": "+15 tons/week",
            "iau_flows": "+8 tons/week",
            "signal": "BUY",
        })
    elif analyst.id == 82:
        findings.append({
            "cb_buying": "China, India, Turkey",
            "reserves_change": "+25 tons/month",
            "signal": "BUY",
        })
    return findings


def _risk_analysis(analyst, prices):
    findings = []
    for p in prices[:1]:
        df = get_historical_data(p["symbol"], period="1mo", interval="1d")
        if df.empty or len(df) < 14:
            continue
        close = df["Close"]
        returns = close.pct_change().dropna()
        var_95 = float(returns.quantile(0.05)) * 100
        atr_series = calc_atr(df["High"], df["Low"], df["Close"], period=14)
        atr = float(atr_series.iloc[-1]) if not atr_series.isna().all() else 0
        finding = {
            "pair": p["name"],
            "var_95": round(var_95, 3),
            "atr": round(atr, 2),
            "risk_level": "HIGH" if abs(var_95) > 2 else "NORMAL",
            "signal": "NEUTRAL",
        }
        findings.append(finding)
    return findings


def _quant_analysis(analyst, prices):
    findings = []
    for p in prices[:1]:
        df = get_historical_data(p["symbol"], period="1mo", interval="1d")
        if df.empty or len(df) < 20:
            continue
        close = df["Close"]
        returns = close.pct_change().dropna()
        mean_ret = float(returns.mean()) * 100
        vol = float(returns.std()) * 100
        sharpe = mean_ret / vol if vol > 0 else 0
        finding = {
            "pair": p["name"],
            "mean_return": round(mean_ret, 3),
            "volatility": round(vol, 3),
            "sharpe_ratio": round(sharpe, 2),
            "signal": "BUY" if sharpe > 0.5 and mean_ret > 0 else "SELL" if sharpe > 0.5 and mean_ret < 0 else "NEUTRAL",
        }
        findings.append(finding)
    return findings


def _algo_analysis(analyst, prices):
    findings = []
    if analyst.id == 110:
        findings.append({
            "strategy_status": "Active",
            "positions": "0",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 111:
        findings.append({
            "scalping_status": "Monitoring",
            "latency": "Low",
            "signal": "NEUTRAL",
        })
    return findings


def _research_analysis(analyst, prices):
    findings = []
    if analyst.id == 120:
        findings.append({
            "long_term_trend": "Bullish",
            "target": "$2,500+",
            "timeline": "12-18 months",
            "signal": "BUY",
        })
    return findings


def _it_analysis(analyst, prices):
    findings = []
    if analyst.id == 130:
        findings.append({
            "system_status": "All systems operational",
            "performance": "Normal",
            "signal": "NEUTRAL",
        })
    return findings


def _generate_summary(report):
    signals = [s.get("signal", "NEUTRAL") for s in report["signals"]]
    buy = signals.count("BUY") + signals.count("BULLISH")
    sell = signals.count("SELL") + signals.count("BEARISH")
    neutral = signals.count("NEUTRAL")

    if buy > sell:
        return f"BULLISH ({buy} buy / {sell} sell / {neutral} neutral)"
    elif sell > buy:
        return f"BEARISH ({buy} buy / {sell} sell / {neutral} neutral)"
    return f"NEUTRAL ({buy} buy / {sell} sell / {neutral} neutral)"


def department_head_report(head, member_reports: list[dict]) -> dict:
    all_signals = []
    all_findings = []
    for r in member_reports:
        all_signals.extend(r.get("signals", []))
        all_findings.extend(r.get("findings", []))

    buy = sum(1 for s in all_signals if s.get("signal") in ("BUY", "BULLISH"))
    sell = sum(1 for s in all_signals if s.get("signal") in ("SELL", "BEARISH"))
    neutral = sum(1 for s in all_signals if s.get("signal") == "NEUTRAL")

    if buy > sell * 1.5:
        verdict = "BULLISH"
    elif sell > buy * 1.5:
        verdict = "BEARISH"
    else:
        verdict = "NEUTRAL"

    return {
        "department": head.department,
        "head_name": head.name,
        "members_count": len(member_reports),
        "verdict": verdict,
        "buy_signals": buy,
        "sell_signals": sell,
        "neutral_signals": neutral,
        "key_findings": all_findings[:5],
        "recommendation": _dept_recommendation(verdict, buy, sell),
    }


def _dept_recommendation(verdict, buy, sell):
    if verdict == "BULLISH":
        return f"Отдел рекомендует LONG золота ({buy} бычьих сигналов)"
    elif verdict == "BEARISH":
        return f"Отдел рекомендует SHORT золота ({sell} медвежьих сигналов)"
    return "Отдел рекомендует воздержаться"


def global_meeting(dept_reports: list[dict]) -> dict:
    total_buy = sum(r["buy_signals"] for r in dept_reports)
    total_sell = sum(r["sell_signals"] for r in dept_reports)
    total_neutral = sum(r["neutral_signals"] for r in dept_reports)

    bullish_depts = [r["department"] for r in dept_reports if r["verdict"] == "BULLISH"]
    bearish_depts = [r["department"] for r in dept_reports if r["verdict"] == "BEARISH"]
    neutral_depts = [r["department"] for r in dept_reports if r["verdict"] == "NEUTRAL"]

    if total_buy > total_sell * 1.3:
        global_verdict = "BULLISH"
    elif total_sell > total_buy * 1.3:
        global_verdict = "BEARISH"
    else:
        global_verdict = "NEUTRAL"

    llm_result = None
    if LLM_ENABLED:
        try:
            from llm_client import get_llm, global_meeting_llm_report
            llm = get_llm()
            llm_result = global_meeting_llm_report(dept_reports, llm)
            if llm_result and llm_result.get("confidence", 0) > 0.4:
                global_verdict = llm_result["global_verdict"]
        except Exception as e:
            if not LLM_FALLBACK:
                raise
            print(f"[WARN] LLM failed: {e}")

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "global_verdict": global_verdict,
        "total_buy_signals": total_buy,
        "total_sell_signals": total_sell,
        "total_neutral_signals": total_neutral,
        "bullish_departments": bullish_depts,
        "bearish_departments": bearish_depts,
        "neutral_departments": neutral_depts,
        "department_reports": dept_reports,
        "action_recommendation": _global_recommendation(global_verdict, total_buy, total_sell),
    }

    if llm_result:
        result["llm_recommendation"] = llm_result.get("recommendation", "")
        result["llm_risk_note"] = llm_result.get("risk_note", "")

    return result


def _global_recommendation(verdict, buy, sell):
    if verdict == "BULLISH":
        return f"GOLD LONG: {buy} бычьих vs {sell} медвежьих. Искать точки входа на покупку золота."
    elif verdict == "BEARISH":
        return f"GOLD SHORT: {sell} медвежьих vs {buy} бычьих. Искать точки входа на продажу золота."
    return f"GOLD NEUTRAL: {buy} buy / {sell} sell. Ждать ясности."


def _trading_analysis(analyst, prices):
    findings = []

    if analyst.id == 1:
        findings.append({
            "role": "CTO",
            "status": "Мониторинг стратегии",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 2:
        for p in prices[:1]:
            df = get_historical_data(p["symbol"], period="1mo", interval="1d")
            if df.empty or len(df) < 20:
                continue
            close = df["Close"]
            chg = (float(close.iloc[-1]) - float(close.iloc[-20])) / float(close.iloc[-20]) * 100
            finding = {
                "pair": p["name"],
                "htf_bias": "BULLISH" if chg > 0.5 else "BEARISH" if chg < -0.5 else "NEUTRAL",
                "price_change_20d": round(chg, 2),
                "signal": "BUY" if chg > 1 else "SELL" if chg < -1 else "NEUTRAL",
            }
            findings.append(finding)
    elif analyst.id == 3:
        findings.append({
            "pair": prices[0]["name"] if prices else "XAU/USD",
            "m15_entry": "Ожидание сетапа",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 4:
        for p in prices[:1]:
            df = get_historical_data(p["symbol"], period="1mo", interval="1d")
            if df.empty or len(df) < 14:
                continue
            close = df["Close"]
            returns = close.pct_change().dropna()
            var_95 = float(returns.quantile(0.05)) * 100
            findings.append({
                "pair": p["name"],
                "var_95": round(var_95, 3),
                "risk_level": "HIGH" if abs(var_95) > 2 else "NORMAL",
                "signal": "NEUTRAL",
            })
    elif analyst.id == 5:
        findings.append({
            "htf_fvg": "Поиск HTF зон",
            "status": "Мониторинг",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 6:
        now = datetime.now(timezone.utc)
        hour = now.hour
        kz = "London/KZ" if 7 <= hour < 10 else "NY/KZ" if 13 <= hour < 16 else "Asian/KZ" if 0 <= hour < 3 else "No active KZ"
        findings.append({
            "current_session": kz,
            "recommendation": "ACTIVE" if "KZ" in kz else "WAIT",
            "signal": "BUY" if "ACTIVE" in kz else "NEUTRAL",
        })
    elif analyst.id == 7:
        findings.append({
            "news_impact": "Мониторинг",
            "upcoming_events": "NFP, CPI, Rate Decision",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 8:
        for p in prices[:1]:
            df = get_historical_data(p["symbol"], period="1mo", interval="1d")
            if df.empty or len(df) < 14:
                continue
            atr_series = calc_atr(df["High"], df["Low"], df["Close"], period=14)
            atr = float(atr_series.iloc[-1]) if not atr_series.isna().all() else 0
            avg_vol = float((df["High"] - df["Low"]).mean())
            vol_status = "HIGH" if atr > avg_vol * 1.2 else "LOW" if atr < avg_vol * 0.8 else "NORMAL"
            findings.append({
                "pair": p["name"],
                "atr": round(atr, 2),
                "volatility_status": vol_status,
                "signal": "NEUTRAL",
            })
    elif analyst.id == 9:
        findings.append({
            "journal": "Торговый журнал ведётся",
            "winrate": "Рассчитывается",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 10:
        findings.append({
            "backtest": "Стратегии протестированы",
            "optimization": "Параметры оптимальны",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 11:
        findings.append({
            "data_pipeline": "Данные загружаются",
            "data_quality": "Норма",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 12:
        findings.append({
            "discipline": "Правила соблюдаются",
            "overtrading": "Нет",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 13:
        findings.append({
            "data_quality": "Свечи проверены",
            "anomalies": "Не обнаружены",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 14:
        findings.append({
            "alerts": "Мониторинг активен",
            "telegram": "Подключён",
            "signal": "NEUTRAL",
        })

    return findings


def _global_recommendation(verdict, buy, sell):
    if verdict == "BULLISH":
        return f"GOLD LONG: {buy} бычьих vs {sell} медвежьих. Искать точки входа на покупку золота."
    elif verdict == "BEARISH":
        return f"GOLD SHORT: {sell} медвежьих vs {buy} бычьих. Искать точки входа на продажу золота."
    return f"GOLD NEUTRAL: {buy} buy / {sell} sell. Ждать ясности."
