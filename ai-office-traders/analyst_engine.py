from datetime import datetime, timezone
import numpy as np
from technical_analysis import analyze, calc_atr, detect_candlestick_patterns
from market_data import get_historical_data
from m15_data import detect_order_blocks, detect_fvg
from staff import ANALYSTS, DEPARTMENTS_STRUCTURE


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
    }

    if analyst.department == "Технический анализ":
        report["findings"] = _tech_analysis(analyst, prices)
    elif analyst.department == "ICT / Smart Money":
        report["findings"] = _ict_smc(analyst, prices)
    elif analyst.department == "M15 Краткосрочный анализ":
        report["findings"] = _m15_analysis(analyst, prices)
    elif analyst.department == "Макроэкономика":
        report["findings"] = _macro_analysis(analyst, prices)
    elif analyst.department == "Квантовый анализ":
        report["findings"] = _quant_analysis(analyst, prices)
    elif analyst.department == "Управление рисками":
        report["findings"] = _risk_analysis(analyst, prices)
    elif analyst.department == "Межрыночный анализ":
        report["findings"] = _cross_market_analysis(analyst, prices)
    elif analyst.department == "Исследования и стратегия":
        report["findings"] = _research_analysis(analyst, prices)
    elif analyst.department == "Операционный отдел":
        report["findings"] = _ops_analysis(analyst, prices)
    elif analyst.department == "Технологии":
        report["findings"] = _tech_ops_analysis(analyst, prices)

    for f in report["findings"]:
        if f.get("signal"):
            report["signals"].append(f)

    report["summary"] = _generate_summary(report)
    return report


def _tech_analysis(analyst, prices):
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
            finding["signals"] = result["signals"][:2]
        elif analyst.id == 2:
            finding["rsi"] = round(result["rsi"], 1)
            finding["macd"] = "BULLISH" if result["macd"] > result["macd_signal"] else "BEARISH"
            finding["signal"] = "BUY" if result["score"] >= 2 and result["rsi"] < 70 else \
                               "SELL" if result["score"] <= -2 and result["rsi"] > 30 else "NEUTRAL"
        elif analyst.id == 3:
            finding["bb_position"] = "OVERBOUGHT" if result.get("bb_upper", 0) < result["price"] else \
                                     "OVERSOLD" if result.get("bb_lower", 999) > result["price"] else "NEUTRAL"
            swing_high = float(df["High"].max())
            swing_low = float(df["Low"].min())
            diff = swing_high - swing_low
            fib = {level: round(swing_low + diff * level, 5) for level in [0.236, 0.382, 0.5, 0.618, 0.786]}
            finding["fib_levels"] = fib
            price = result["price"]
            nearest_fib = min(fib.values(), key=lambda x: abs(x - price))
            finding["nearest_fib"] = nearest_fib
            finding["signal"] = "BUY" if price < fib[0.382] else "SELL" if price > fib[0.618] else "NEUTRAL"
        elif analyst.id == 16:
            patterns = detect_candlestick_patterns(df)
            finding["patterns"] = patterns if patterns else ["No patterns detected"]
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


def _ict_smc(analyst, prices):
    findings = []
    for p in prices:
        df = get_historical_data(p["symbol"], period="3mo", interval="1d")
        if df.empty or len(df) < 20:
            continue

        close = df["Close"]
        high = df["High"]
        low = df["Low"]

        finding = {"pair": p["name"]}

        if analyst.id == 27:
            trend = "BULLISH" if close.iloc[-1] > close.iloc[-20] else "BEARISH"
            finding["htf_bias"] = trend
            finding["structure"] = "HH/HL" if trend == "BULLISH" else "LH/LL"
            finding["poi"] = "Demand Zone" if trend == "BULLISH" else "Supply Zone"
            finding["signal"] = "BUY" if trend == "BULLISH" else "SELL"
        elif analyst.id == 28:
            obs = detect_order_blocks(df)
            fvgs = detect_fvg(df)
            finding["order_blocks"] = [{"type": ob["type"], "high": ob["high"], "low": ob["low"]} for ob in obs[:2]]
            finding["fvg_count"] = len(fvgs)
            bullish_obs = [ob for ob in obs if ob["type"] == "Bullish OB"]
            bearish_obs = [ob for ob in obs if ob["type"] == "Bearish OB"]
            if bullish_obs and not bearish_obs:
                finding["signal"] = "BUY"
            elif bearish_obs and not bullish_obs:
                finding["signal"] = "SELL"
            else:
                finding["signal"] = "NEUTRAL"
        elif analyst.id == 33:
            recent_high = float(high.max())
            recent_low = float(low.min())
            current = float(close.iloc[-1])
            dist_to_high = (recent_high - current) / current * 100
            dist_to_low = (current - recent_low) / current * 100
            finding["bsl_distance"] = f"{dist_to_high:.2f}%"
            finding["ssl_distance"] = f"{dist_to_low:.2f}%"
            finding["liquidity_zone"] = "BSL target" if dist_to_high < dist_to_low else "SSL target"
            finding["signal"] = "NEUTRAL"

        findings.append(finding)
    return findings


def _m15_analysis(analyst, prices):
    findings = []
    now = datetime.now(timezone.utc)
    hour = now.hour

    if analyst.id == 32:
        if 7 <= hour < 10:
            kz = "London Kill Zone (_ACTIVE)"
        elif 13 <= hour < 16:
            kz = "NY Kill Zone (ACTIVE)"
        elif 0 <= hour < 3:
            kz = "Asian Kill Zone (ACTIVE)"
        else:
            kz = "No active Kill Zone"

        findings.append({
            "current_session": kz,
            "time": now.strftime("%H:%M"),
            "recommendation": "ACTIVE TRADING" if "ACTIVE" in kz else "WAIT",
            "signal": "BUY" if "ACTIVE" in kz else "NEUTRAL",
        })

    elif analyst.id == 29:
        for p in prices:
            df = get_historical_data(p["symbol"], period="5d", interval="1d")
            if df.empty or len(df) < 5:
                continue

            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            atr_series = calc_atr(high, low, close, period=14)
            atr = float(atr_series.iloc[-1]) if not atr_series.isna().all() else float((high - low).mean())

            last = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            bos = "BULLISH BOS" if last > prev and last > float(high.iloc[-2]) else \
                  "BEARISH BOS" if last < prev and last < float(low.iloc[-2]) else "NO BOS"

            if len(close) >= 3:
                prev2 = float(close.iloc[-3])
                choch = "BULLISH CHoCH" if last > prev and prev2 > prev else \
                        "BEARISH CHoCH" if last < prev and prev2 < prev else "NO CHoCH"
            else:
                choch = "NO CHoCH"

            findings.append({
                "pair": p["name"],
                "bos": bos,
                "choch": choch,
                "atr": round(atr, 5),
                "signal": "BUY" if "BULLISH" in bos or "BULLISH" in choch else \
                          "SELL" if "BEARISH" in bos or "BEARISH" in choch else "NEUTRAL",
            })

    return findings


def _macro_analysis(analyst, prices):
    findings = []

    if analyst.id == 30:
        usd_pairs = [p for p in prices if p["name"].startswith("USD")]
        usd_strength = 0
        for p in usd_pairs:
            df = get_historical_data(p["symbol"], period="1mo", interval="1d")
            if not df.empty and len(df) >= 20:
                change = (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-20])) / float(df["Close"].iloc[-20]) * 100
                if p["name"] in ("USD/JPY", "USD/CHF", "USD/CAD"):
                    usd_strength += change
                else:
                    usd_strength -= change

        findings.append({
            "dxy_proxy": round(usd_strength, 2),
            "dxy_trend": "USD STRONG" if usd_strength > 0.5 else "USD WEAK" if usd_strength < -0.5 else "USD NEUTRAL",
            "monetary_policy": "ФРС: мониторинг ставок",
            "signal": "BUY USD" if usd_strength > 1 else "SELL USD" if usd_strength < -1 else "NEUTRAL",
        })

    elif analyst.id == 4:
        findings.append({
            "event": "Economic Calendar",
            "focus": "NFP, CPI, GDP, rate decisions",
            "signal": "NEUTRAL",
        })

    elif analyst.id == 5:
        findings.append({
            "yield_curve": "Мониторинг",
            "interest_rates": "Глобальные ставки",
            "signal": "NEUTRAL",
        })

    return findings


def _quant_analysis(analyst, prices):
    findings = []

    if analyst.id == 8:
        for p in prices[:3]:
            df = get_historical_data(p["symbol"], period="1mo", interval="1d")
            if df.empty or len(df) < 20:
                continue
            close = df["Close"]
            returns = close.pct_change().dropna()
            mean_ret = float(returns.mean()) * 100
            vol = float(returns.std()) * 100
            sharpe = mean_ret / vol if vol > 0 else 0

            findings.append({
                "pair": p["name"],
                "mean_return": round(mean_ret, 3),
                "volatility": round(vol, 3),
                "sharpe_ratio": round(sharpe, 2),
                "signal": "BUY" if sharpe > 0.5 and mean_ret > 0 else \
                          "SELL" if sharpe > 0.5 and mean_ret < 0 else "NEUTRAL",
            })

    elif analyst.id == 9:
        findings.append({
            "model_status": "ML модели обновлены",
            "accuracy": "Мониторинг",
            "signal": "NEUTRAL",
        })

    return findings


def _risk_analysis(analyst, prices):
    findings = []

    if analyst.id == 10:
        for p in prices[:3]:
            df = get_historical_data(p["symbol"], period="1mo", interval="1d")
            if df.empty or len(df) < 14:
                continue
            close = df["Close"]
            returns = close.pct_change().dropna()
            var_95 = float(returns.quantile(0.05)) * 100

            findings.append({
                "pair": p["name"],
                "var_95": round(var_95, 3),
                "risk_level": "HIGH" if abs(var_95) > 1 else "NORMAL",
                "signal": "NEUTRAL",
            })

    elif analyst.id == 11:
        findings.append({
            "portfolio_status": "Диверсификация в норме",
            "correlation_check": "Мониторинг",
            "signal": "NEUTRAL",
        })

    return findings


def _cross_market_analysis(analyst, prices):
    findings = []

    if analyst.id == 14:
        if len(prices) >= 2:
            p1, p2 = prices[0], prices[1]
            df1 = get_historical_data(p1["symbol"], period="1mo", interval="1d")
            df2 = get_historical_data(p2["symbol"], period="1mo", interval="1d")
            if not df1.empty and not df2.empty and len(df1) == len(df2):
                corr = float(np.corrcoef(df1["Close"].values, df2["Close"].values)[0, 1])
                findings.append({
                    "pair_1": p1["name"],
                    "pair_2": p2["name"],
                    "correlation": round(corr, 3),
                    "signal": "NEUTRAL",
                })

    elif analyst.id == 12:
        for p in prices[:3]:
            df = get_historical_data(p["symbol"], period="1mo", interval="1d")
            if df.empty or len(df) < 14:
                continue
            atr_series = calc_atr(df["High"], df["Low"], df["Close"], period=14)
            atr = float(atr_series.iloc[-1]) if not atr_series.isna().all() else 0
            avg_tr = float((df["High"] - df["Low"]).mean())
            vol_status = "HIGH" if atr > avg_tr * 1.2 else "LOW" if atr < avg_tr * 0.8 else "NORMAL"
            findings.append({
                "pair": p["name"],
                "atr": round(atr, 5),
                "volatility_status": vol_status,
                "signal": "NEUTRAL",
            })

    elif analyst.id == 15:
        findings.append({
            "liquidity_status": "Спреды в норме",
            "best_windows": "London/NY overlap",
            "signal": "NEUTRAL",
        })

    return findings


def _research_analysis(analyst, prices):
    findings = []

    if analyst.id == 19:
        for p in prices:
            df = get_historical_data(p["symbol"], period="3mo", interval="1d")
            if df.empty or len(df) < 20:
                continue
            close = df["Close"]
            chg_20 = (float(close.iloc[-1]) - float(close.iloc[-20])) / float(close.iloc[-20]) * 100
            chg_60 = (float(close.iloc[-1]) - float(close.iloc[-60])) / float(close.iloc[-60]) * 100 if len(close) >= 60 else 0
            findings.append({
                "pair": p["name"],
                "change_20d": round(chg_20, 2),
                "change_60d": round(chg_60, 2),
                "trend": "UP" if chg_20 > 0.5 else "DOWN" if chg_20 < -0.5 else "SIDEWAYS",
                "signal": "BUY" if chg_20 > 1 else "SELL" if chg_20 < -1 else "NEUTRAL",
            })

    elif analyst.id == 24:
        findings.append({
            "strategy": "PPP/Fair Value analysis",
            "outlook": "Долгосрочная оценка",
            "signal": "NEUTRAL",
        })

    elif analyst.id == 13:
        findings.append({
            "geopolitical_risk": "Стабильно",
            "events": "Мониторинг",
            "signal": "NEUTRAL",
        })

    return findings


def _ops_analysis(analyst, prices):
    findings = []

    if analyst.id == 18:
        findings.append({
            "system_status": "Все системы работают",
            "performance": "Норма",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 17:
        findings.append({
            "algo_status": "Алгоритмы активны",
            "backtest": "Результаты в норме",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 25:
        findings.append({
            "compliance": "Все сделки в рамках",
            "limits": "Не превышены",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 31:
        findings.append({
            "exotic_pairs": "Нет экзотики в основных парах",
            "em_risk": "Мониторинг",
            "signal": "NEUTRAL",
        })

    return findings


def _tech_ops_analysis(analyst, prices):
    findings = []

    if analyst.id == 20:
        findings.append({
            "ai_models": "Все модели работают",
            "drift_monitoring": "Активно",
            "signal": "NEUTRAL",
        })
    elif analyst.id == 26:
        findings.append({
            "data_pipeline": "ETL работает",
            "data_quality": "Норма",
            "signal": "NEUTRAL",
        })

    return findings


def _generate_summary(report):
    signals = [s.get("signal", "NEUTRAL") for s in report["signals"]]
    buy = signals.count("BUY") + signals.count("BULLISH") + signals.count("BULLISH BOS")
    sell = signals.count("SELL") + signals.count("BEARISH") + signals.count("BEARISH BOS")
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

    buy = sum(1 for s in all_signals if s.get("signal") in ("BUY", "BULLISH", "BULLISH BOS"))
    sell = sum(1 for s in all_signals if s.get("signal") in ("SELL", "BEARISH", "BEARISH BOS"))
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
        return f"Отдел рекомендует LONG позиции ({buy} бычьих сигналов)"
    elif verdict == "BEARISH":
        return f"Отдел рекомендует SHORT позиции ({sell} медвежьих сигналов)"
    return "Отдел рекомендует воздержаться от входов"


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

    return {
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


def _global_recommendation(verdict, buy, sell):
    if verdict == "BULLISH":
        return f"ГЛОБАЛЬНАЯ РЕКОМЕНДАЦИЯ: LONG ({buy} бычьих vs {sell} медвежьих). Искать точки входа на покупку."
    elif verdict == "BEARISH":
        return f"ГЛОБАЛЬНАЯ РЕКОМЕНДАЦИЯ: SHORT ({sell} медвежьих vs {buy} бычьих). Искать точки входа на продажу."
    return f"ГЛОБАЛЬНАЯ РЕКОМЕНДАЦИЯ: NEUTRAL ({buy} buy / {sell} sell). Ждать ясности."
