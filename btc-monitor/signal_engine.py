import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from indicators import (
    ema, atr, rsi, macd, supertrend, bollinger,
    swing_highs_lows, detect_fvg, detect_ob, detect_structure_break,
    volume_sma, adx, stoch_rsi,
)


@dataclass
class Signal:
    script_name: str
    author: str
    category: str
    direction: str
    confidence: float
    rules_matched: list[str]
    timestamp: datetime
    price: float
    url: str = ""


@dataclass
class ConfluenceSignal:
    direction: str
    confluence_score: float
    total_scripts: int
    total_loaded: int
    buy_scripts: list[str]
    sell_scripts: list[str]
    categories: dict[str, int]
    timestamp: datetime
    price: float
    individual_signals: list[Signal]


class SignalEngine:
    def __init__(self, scripts_dir: str):
        self.scripts = []
        self.scripts_dir = scripts_dir
        self._load_scripts()

    def _load_scripts(self):
        for fname in os.listdir(self.scripts_dir):
            if fname.endswith(".json"):
                with open(os.path.join(self.scripts_dir, fname), "r", encoding="utf-8") as f:
                    self.scripts.append(json.load(f))

    def analyze(self, candles: list[dict]) -> dict:
        if len(candles) < 50:
            return {"individual": [], "confluence": None}

        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        opens = [c["open"] for c in candles]
        volumes = [c["volume"] for c in candles]

        indicators = self._compute_indicators(closes, highs, lows, candles, volumes)
        signals = []

        for script in self.scripts:
            signal = self._check_script(script, candles, closes, highs, lows, opens, volumes, indicators)
            if signal:
                signals.append(signal)

        signals.sort(key=lambda s: s.confidence, reverse=True)
        confluence = self._compute_confluence(signals, closes[-1], len(self.scripts))
        return {"individual": signals, "confluence": confluence}

    def _compute_confluence(self, signals: list[Signal], price: float, total_loaded: int = 0) -> Optional[ConfluenceSignal]:
        if not signals:
            return None

        buy_signals = [s for s in signals if s.direction == "BUY"]
        sell_signals = [s for s in signals if s.direction == "SELL"]

        total = max(len(signals), total_loaded)
        buy_count = len(buy_signals)
        sell_count = len(sell_signals)

        categories = {}
        for s in signals:
            categories[s.category] = categories.get(s.category, 0) + 1

        if buy_count > sell_count and buy_count >= 2:
            confluence = buy_count / total
            return ConfluenceSignal(
                direction="BUY",
                confluence_score=round(confluence, 2),
                total_scripts=total,
                total_loaded=total_loaded,
                buy_scripts=[s.script_name for s in buy_signals],
                sell_scripts=[s.script_name for s in sell_signals],
                categories=categories,
                timestamp=datetime.now(timezone.utc),
                price=price,
                individual_signals=signals,
            )
        elif sell_count > buy_count and sell_count >= 2:
            confluence = sell_count / total
            return ConfluenceSignal(
                direction="SELL",
                confluence_score=round(confluence, 2),
                total_scripts=total,
                total_loaded=total_loaded,
                buy_scripts=[s.script_name for s in buy_signals],
                sell_scripts=[s.script_name for s in sell_signals],
                categories=categories,
                timestamp=datetime.now(timezone.utc),
                price=price,
                individual_signals=signals,
            )
        return None

    def _compute_indicators(self, closes, highs, lows, candles, volumes) -> dict:
        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        ema50 = ema(closes, 50)
        ema200 = ema(closes, 200)
        atr14 = atr(highs, lows, closes, 14)
        rsi14 = rsi(closes, 14)
        macd_line, macd_signal, macd_hist = macd(closes)
        st_line, st_dir = supertrend(highs, lows, closes)
        bb_upper, bb_middle, bb_lower = bollinger(closes)
        swings = swing_highs_lows(highs, lows)
        fvgs = detect_fvg(candles)
        obs = detect_ob(candles)
        bos = detect_structure_break(candles)
        vol_avg = volume_sma(candles)
        adx14 = adx(highs, lows, closes)
        stoch_k, stoch_d = stoch_rsi(closes)

        return {
            "ema9": ema9, "ema21": ema21, "ema50": ema50, "ema200": ema200,
            "atr": atr14, "rsi": rsi14,
            "macd_line": macd_line, "macd_signal": macd_signal, "macd_hist": macd_hist,
            "supertrend_line": st_line, "supertrend_dir": st_dir,
            "bb_upper": bb_upper, "bb_middle": bb_middle, "bb_lower": bb_lower,
            "swings": swings, "fvgs": fvgs, "obs": obs, "bos": bos,
            "vol_avg": vol_avg, "adx": adx14,
            "stoch_k": stoch_k, "stoch_d": stoch_d,
        }

    def _check_script(self, script, candles, closes, highs, lows, opens, volumes, ind) -> Optional[Signal]:
        cat = script.get("category", "")
        rules = script.get("rules", {})
        buy_rules = rules.get("entry_buy", [])
        sell_rules = rules.get("entry_sell", [])

        if not buy_rules and not sell_rules:
            return None

        i = len(closes) - 1
        price = closes[i]

        buy_score, buy_matched = self._score_rules(buy_rules, cat, i, candles, closes, highs, lows, opens, volumes, ind)
        sell_score, sell_matched = self._score_rules(sell_rules, cat, i, candles, closes, highs, lows, opens, volumes, ind)

        total_rules = max(len(buy_rules), len(sell_rules), 1)

        if buy_score > sell_score and buy_score > 0:
            return Signal(
                script_name=script["name"],
                author=script.get("author", "Unknown"),
                category=cat,
                direction="BUY",
                confidence=min(buy_score / total_rules, 1.0),
                rules_matched=buy_matched,
                timestamp=datetime.now(timezone.utc),
                price=price,
                url=script.get("url", ""),
            )
        elif sell_score > buy_score and sell_score > 0:
            return Signal(
                script_name=script["name"],
                author=script.get("author", "Unknown"),
                category=cat,
                direction="SELL",
                confidence=min(sell_score / total_rules, 1.0),
                rules_matched=sell_matched,
                timestamp=datetime.now(timezone.utc),
                price=price,
                url=script.get("url", ""),
            )
        return None

    def _score_rules(self, rules, category, i, candles, closes, highs, lows, opens, volumes, ind) -> tuple[int, list[str]]:
        score = 0
        matched = []
        for rule in rules:
            if self._check_single_rule(rule, category, i, candles, closes, highs, lows, opens, volumes, ind):
                score += 1
                matched.append(rule)
        return score, matched

    def _check_single_rule(self, rule: str, category: str, i: int, candles, closes, highs, lows, opens, volumes, ind) -> bool:
        rule_lower = rule.lower()

        if "supertrend" in rule_lower:
            return self._check_supertrend_rule(rule_lower, i, ind)
        if "ema" in rule_lower and ("alignment" in rule_lower or "fast" in rule_lower or "structure" in rule_lower):
            return self._check_ema_rule(rule_lower, i, ind)
        if "rsi" in rule_lower:
            return self._check_rsi_rule(rule_lower, i, ind)
        if "macd" in rule_lower:
            return self._check_macd_rule(rule_lower, i, ind)
        if "order block" in rule_lower or "ob " in rule_lower or "область блока" in rule_lower:
            return self._check_ob_rule(rule_lower, i, ind, candles)
        if "fvg" in rule_lower or "fair value gap" in rule_lower:
            return self._check_fvg_rule(rule_lower, i, ind)
        if "bos" in rule_lower or "structure break" in rule_lower or "choch" in rule_lower or "mss" in rule_lower:
            return self._check_bos_rule(rule_lower, i, ind)
        if "volume" in rule_lower:
            return self._check_volume_rule(rule_lower, i, ind, volumes)
        if "atr" in rule_lower:
            return self._check_atr_rule(rule_lower, i, ind)
        if "bollinger" in rule_lower or "bb" in rule_lower:
            return self._check_bb_rule(rule_lower, i, ind, candles)
        if "premium" in rule_lower or "discount" in rule_lower:
            return self._check_premium_discount_rule(rule_lower, i, ind, highs, lows)
        if "swing" in rule_lower:
            return self._check_swing_rule(rule_lower, i, ind)
        if "adx" in rule_lower:
            return self._check_adx_rule(rule_lower, i, ind)
        if "stochastic" in rule_lower or "stoch" in rule_lower:
            return self._check_stoch_rule(rule_lower, i, ind)
        if "pin bar" in rule_lower or "engulfing" in rule_lower or "candle" in rule_lower:
            return self._check_candle_pattern(rule_lower, i, candles)
        if "divergence" in rule_lower:
            return self._check_divergence_rule(rule_lower, i, ind)
        if "session" in rule_lower or "killzone" in rule_lower or "kill zone" in rule_lower:
            return self._check_session_rule(rule_lower, i, candles)
        if "trailing stop" in rule_lower or "trail" in rule_lower:
            return self._check_trailing_stop_rule(rule_lower, i, ind, candles)
        if "momentum" in rule_lower:
            return self._check_momentum_rule(rule_lower, i, ind)
        if "breakout" in rule_lower or "consolidation" in rule_lower:
            return self._check_breakout_rule(rule_lower, i, ind, candles)
        if "liquidation" in rule_lower or "liquidity" in rule_lower or "liquidity grab" in rule_lower or "sweep" in rule_lower:
            return self._check_liquidity_rule(rule_lower, i, ind, highs, lows)
        if "supply" in rule_lower and "demand" in rule_lower:
            return self._check_supply_demand_rule(rule_lower, i, ind, candles)
        if "magnet" in rule_lower:
            return self._check_magnet_rule(rule_lower, i, ind)
        if "ghost trend" in rule_lower:
            return self._check_ghost_trend_rule(rule_lower, i, ind)
        if "fibonacci" in rule_lower or "fib" in rule_lower:
            return self._check_fibonacci_rule(rule_lower, i, ind)
        if "amd" in rule_lower or "power of 3" in rule_lower:
            return self._check_amd_rule(rule_lower, i, candles)
        if "timing" in rule_lower or "cycle" in rule_lower:
            return self._check_timing_rule(rule_lower, i, ind)
        if "confidence" in rule_lower and "score" in rule_lower:
            return self._check_confidence_rule(rule_lower, i, ind)
        if "projection" in rule_lower or "ml" in rule_lower:
            return self._check_ml_projection_rule(rule_lower, i, ind)
        if "pressure" in rule_lower:
            return self._check_pressure_rule(rule_lower, i, ind)
        if "quality" in rule_lower and "score" in rule_lower:
            return self._check_quality_score_rule(rule_lower, i, ind)
        if "rejection" in rule_lower:
            return self._check_rejection_rule(rule_lower, i, candles)
        return False

    def _check_supertrend_rule(self, rule, i, ind):
        st_dir = ind["supertrend_dir"]
        if st_dir[i] is None:
            return False
        if "buy" in rule and "flip" in rule:
            return st_dir[i] == "BUY" and (i == 0 or st_dir[i - 1] != "BUY")
        if "sell" in rule and "flip" in rule:
            return st_dir[i] == "SELL" and (i == 0 or st_dir[i - 1] != "SELL")
        if "buy" in rule:
            return st_dir[i] == "BUY"
        if "sell" in rule:
            return st_dir[i] == "SELL"
        return False

    def _check_ema_rule(self, rule, i, ind):
        e9, e21, e50 = ind["ema9"][i], ind["ema21"][i], ind["ema50"][i]
        if None in (e9, e21, e50):
            return False
        if "bullish" in rule or ("fast" in rule and "slow" in rule) or "structure" in rule:
            if "bearish" in rule:
                return e9 < e21 < e50
            return e9 > e21 > e50
        if "bearish" in rule:
            return e9 < e21 < e50
        return False

    def _check_rsi_rule(self, rule, i, ind):
        r = ind["rsi"][i]
        if r is None:
            return False
        if "oversold" in rule:
            return r < 30
        if "overbought" in rule:
            return r > 70
        if "< 30" in rule or "<30" in rule:
            return r < 30
        if "> 70" in rule or ">70" in rule:
            return r > 70
        if "below 40" in rule:
            return r < 40
        if "above 60" in rule:
            return r > 60
        return False

    def _check_macd_rule(self, rule, i, ind):
        h = ind["macd_hist"][i]
        if h is None:
            return False
        if "cross" in rule and "above" in rule:
            prev_h = ind["macd_hist"][i - 1] if i > 0 else None
            if prev_h is None:
                return False
            return prev_h <= 0 and h > 0
        if "cross" in rule and "below" in rule:
            prev_h = ind["macd_hist"][i - 1] if i > 0 else None
            if prev_h is None:
                return False
            return prev_h >= 0 and h < 0
        if "positive" in rule or "above zero" in rule:
            return h > 0
        if "negative" in rule or "below zero" in rule:
            return h < 0
        return False

    def _check_ob_rule(self, rule, i, ind, candles):
        obs = ind["obs"]
        if not obs:
            return False
        price = candles[i]["close"]
        for ob in reversed(obs):
            if i - ob["index"] > 30:
                break
            if "bullish" in rule and ob["type"] == "bullish_ob":
                if ob["low"] <= price <= ob["high"]:
                    return True
            if "bearish" in rule and ob["type"] == "bearish_ob":
                if ob["low"] <= price <= ob["high"]:
                    return True
        return False

    def _check_fvg_rule(self, rule, i, ind):
        fvgs = ind["fvgs"]
        if not fvgs:
            return False
        for fvg in reversed(fvgs):
            if i - fvg["index"] > 20:
                break
            if "bullish" in rule and fvg["type"] == "bullish":
                return True
            if "bearish" in rule and fvg["type"] == "bearish":
                return True
        return False

    def _check_bos_rule(self, rule, i, ind):
        bos = ind["bos"]
        if not bos:
            return False
        for b in reversed(bos):
            if i - b["index"] > 10:
                break
            if "bullish" in rule and b["type"] == "BOS_bullish":
                return True
            if "bearish" in rule and b["type"] == "BOS_bearish":
                return True
        return False

    def _check_volume_rule(self, rule, i, ind, volumes):
        vol_avg = ind["vol_avg"][i]
        if vol_avg is None:
            return False
        vol = volumes[i]
        if "above" in rule or "high" in rule or "spike" in rule or "expansion" in rule:
            return vol > vol_avg * 1.2
        if "below" in rule or "low" in rule:
            return vol < vol_avg * 0.8
        return vol > vol_avg

    def _check_atr_rule(self, rule, i, ind):
        a = ind["atr"][i]
        if a is None:
            return False
        if "expansion" in rule or "increase" in rule or "rising" in rule:
            prev_a = ind["atr"][i - 1] if i > 0 else None
            if prev_a is None:
                return False
            return a > prev_a
        if "contraction" in rule or "decrease" in rule or "falling" in rule:
            prev_a = ind["atr"][i - 1] if i > 0 else None
            if prev_a is None:
                return False
            return a < prev_a
        return False

    def _check_bb_rule(self, rule, i, ind, candles=None):
        upper = ind["bb_upper"][i]
        lower = ind["bb_lower"][i]
        middle = ind["bb_middle"][i]
        if upper is None or lower is None or middle is None:
            return False
        if candles and i < len(candles):
            price = candles[i]["close"]
            if "touch" in rule or "bounce" in rule:
                return abs(price - upper) < (upper - lower) * 0.05 or abs(price - lower) < (upper - lower) * 0.05
            if "squeeze" in rule:
                return (upper - lower) < (upper - lower) * 0.5
        return False

    def _check_premium_discount_rule(self, rule, i, ind, highs, lows):
        lookback = min(50, i + 1)
        h_slice = [h for h in highs[i - lookback + 1 : i + 1] if h is not None]
        l_slice = [l for l in lows[i - lookback + 1 : i + 1] if l is not None]
        if not h_slice or not l_slice:
            return False
        high_max = max(h_slice)
        low_min = min(l_slice)
        rng = high_max - low_min
        if rng == 0:
            return False
        pos = (highs[i] - low_min) / rng if highs[i] is not None else 0.5
        if "premium" in rule:
            return pos > 0.75
        if "discount" in rule:
            return pos < 0.5
        return False

    def _check_swing_rule(self, rule, i, ind):
        swings = ind["swings"]
        if swings[i] is None:
            return False
        if "high" in rule:
            return swings[i] == "HIGH"
        if "low" in rule:
            return swings[i] == "LOW"
        return False

    def _check_adx_rule(self, rule, i, ind):
        a = ind["adx"][i]
        if a is None:
            return False
        if "strong" in rule or "> 25" in rule or ">25" in rule:
            return a > 25
        if "weak" in rule or "< 20" in rule or "<20" in rule:
            return a < 20
        return a > 25

    def _check_stoch_rule(self, rule, i, ind):
        k = ind["stoch_k"][i]
        if k is None:
            return False
        if "oversold" in rule or "< 20" in rule:
            return k < 20
        if "overbought" in rule or "> 80" in rule:
            return k > 80
        return False

    def _check_candle_pattern(self, rule, i, candles):
        if i < 1:
            return False
        c = candles[i]
        p = candles[i - 1]
        body = abs(c["close"] - c["open"])
        upper_wick = c["high"] - max(c["close"], c["open"])
        lower_wick = min(c["close"], c["open"]) - c["low"]
        total_range = c["high"] - c["low"]
        if total_range == 0:
            return False
        if "pin bar" in rule or "hammer" in rule:
            if c["close"] > c["open"]:
                return lower_wick > body * 2 and upper_wick < body * 0.5
            else:
                return upper_wick > body * 2 and lower_wick < body * 0.5
        if "engulfing" in rule:
            if c["close"] > c["open"] and p["close"] < p["open"]:
                return c["close"] > p["open"] and c["open"] < p["close"]
            if c["close"] < c["open"] and p["close"] > p["open"]:
                return c["close"] < p["open"] and c["open"] > p["close"]
            return False
        if "doji" in rule:
            return body < total_range * 0.1
        if "inside bar" in rule:
            return c["high"] < p["high"] and c["low"] > p["low"]
        return False

    def _check_divergence_rule(self, rule, i, ind):
        if i < 20:
            return False
        rsi_vals = ind["rsi"]
        if rsi_vals is None or i >= len(rsi_vals) or i - 10 < 0:
            return False
        r1 = rsi_vals[i]
        r2 = rsi_vals[i - 10]
        if r1 is None or r2 is None:
            return False
        if "bullish" in rule:
            return r1 > r2
        if "bearish" in rule:
            return r1 < r2
        return False

    def _check_session_rule(self, rule, i, candles):
        return False

    def _check_trailing_stop_rule(self, rule, i, ind, candles=None):
        st = ind["supertrend_line"][i]
        if st is None:
            return False
        if candles and i < len(candles):
            price = candles[i]["close"]
            if "above" in rule:
                return price > st
            if "below" in rule:
                return price < st
        return False

    def _check_momentum_rule(self, rule, i, ind):
        r = ind["rsi"][i]
        if r is None:
            return False
        if "strong" in rule:
            return r > 60 or r < 40
        return abs(r - 50) > 10

    def _check_breakout_rule(self, rule, i, ind, candles):
        if i < 20:
            return False
        closes = [c["close"] for c in candles[:i + 1] if c.get("close") is not None]
        if len(closes) < 20:
            return False
        recent_high = max(closes[-20:])
        recent_low = min(closes[-20:])
        price = closes[-1]
        if "above" in rule or "breakout up" in rule:
            return price > recent_high * 0.99
        if "below" in rule or "breakout down" in rule:
            return price < recent_low * 1.01
        return False

    def _check_liquidity_rule(self, rule, i, ind, highs, lows):
        if i < 20:
            return False
        lookback = min(50, i)
        h_slice = [h for h in highs[i - lookback:i] if h is not None]
        l_slice = [l for l in lows[i - lookback:i] if l is not None]
        if not h_slice or not l_slice:
            return False
        recent_high = max(h_slice)
        recent_low = min(l_slice)
        price = highs[i]
        if price is None:
            return False
        if "sweep" in rule and "high" in rule:
            return price > recent_high
        if "sweep" in rule and "low" in rule:
            return lows[i] is not None and lows[i] < recent_low
        if "grab" in rule and "bullish" in rule:
            low = lows[i]
            if low is None:
                return False
            close = ind["ema9"][i] if ind["ema9"][i] is not None else 0
            return low < recent_low and close > recent_low
        if "grab" in rule and "bearish" in rule:
            high = highs[i]
            close = ind["ema9"][i] if ind["ema9"][i] is not None else 0
            return high > recent_high and close < recent_high
        return False

    def _check_supply_demand_rule(self, rule, i, ind, candles):
        if i < 10:
            return False
        obs = ind.get("obs", [])
        if not obs:
            return False
        price = candles[i]["close"]
        for ob in reversed(obs):
            if i - ob["index"] > 20:
                break
            if "buy" in rule and ob["type"] == "bullish_ob":
                if ob["low"] <= price <= ob["high"]:
                    return True
            if "sell" in rule and ob["type"] == "bearish_ob":
                if ob["low"] <= price <= ob["high"]:
                    return True
        return False

    def _check_magnet_rule(self, rule, i, ind):
        return False

    def _check_ghost_trend_rule(self, rule, i, ind):
        return False

    def _check_fibonacci_rule(self, rule, i, ind):
        return False

    def _check_amd_rule(self, rule, i, candles):
        if i < 3:
            return False
        c = candles[i]
        body = abs(c["close"] - c["open"])
        total_range = c["high"] - c["low"]
        if total_range == 0:
            return False
        if "accumulation" in rule:
            return body < total_range * 0.3
        if "manipulation" in rule:
            return body < total_range * 0.3
        if "distribution" in rule:
            return body > total_range * 0.5
        return False

    def _check_timing_rule(self, rule, i, ind):
        return False

    def _check_confidence_rule(self, rule, i, ind):
        rsi_vals = ind.get("rsi")
        if rsi_vals is None or i >= len(rsi_vals) or rsi_vals[i] is None:
            return False
        rsi_val = rsi_vals[i]
        if "> 60" in rule or ">60" in rule:
            return rsi_val > 60 or rsi_val < 40
        return True

    def _check_ml_projection_rule(self, rule, i, ind):
        return False

    def _check_pressure_rule(self, rule, i, ind):
        e9_vals = ind.get("ema9")
        e21_vals = ind.get("ema21")
        if e9_vals is None or e21_vals is None:
            return False
        if i >= len(e9_vals) or i >= len(e21_vals):
            return False
        e9 = e9_vals[i]
        e21 = e21_vals[i]
        if e9 is None or e21 is None:
            return False
        if "bullish" in rule:
            return e9 > e21
        if "bearish" in rule:
            return e9 < e21
        return False

    def _check_quality_score_rule(self, rule, i, ind):
        return False

    def _check_rejection_rule(self, rule, i, candles):
        if i < 1:
            return False
        c = candles[i]
        body = abs(c["close"] - c["open"])
        lower_wick = min(c["close"], c["open"]) - c["low"]
        upper_wick = c["high"] - max(c["close"], c["open"])
        if body == 0:
            return False
        if "bullish" in rule:
            return lower_wick > body * 1.5
        if "bearish" in rule:
            return upper_wick > body * 1.5
        return False
