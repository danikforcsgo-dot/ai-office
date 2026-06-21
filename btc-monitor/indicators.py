import numpy as np
from typing import Optional


def ema(closes: list[float], period: int) -> list[Optional[float]]:
    result = [None] * len(closes)
    if len(closes) < period:
        return result
    k = 2 / (period + 1)
    result[period - 1] = sum(closes[:period]) / period
    for i in range(period, len(closes)):
        if result[i - 1] is None:
            result[i] = closes[i]
        else:
            result[i] = closes[i] * k + result[i - 1] * (1 - k)
    return result


def sma(closes: list[float], period: int) -> list[Optional[float]]:
    result = [None] * len(closes)
    if len(closes) < period:
        return result
    for i in range(period - 1, len(closes)):
        result[i] = sum(closes[i - period + 1 : i + 1]) / period
    return result


def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[Optional[float]]:
    n = len(closes)
    tr_list = [0.0] * n
    tr_list[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr_list[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
    result = [None] * n
    if n < period:
        return result
    result[period - 1] = sum(tr_list[:period]) / period
    for i in range(period, n):
        if result[i - 1] is None:
            result[i] = tr_list[i]
        else:
            result[i] = (result[i - 1] * (period - 1) + tr_list[i]) / period
    return result


def rsi(closes: list[float], period: int = 14) -> list[Optional[float]]:
    n = len(closes)
    result = [None] * n
    if n < period + 1:
        return result
    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        if diff > 0:
            gains[i] = diff
        else:
            losses[i] = -diff
    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    if avg_loss == 0:
        result[period] = 100.0
    else:
        result[period] = 100.0 - 100.0 / (1 + avg_gain / avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result[i] = 100.0
        else:
            result[i] = 100.0 - 100.0 / (1 + avg_gain / avg_loss) if avg_loss > 0 else 50.0
    return result


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[list[Optional[float]], list[Optional[float]], list[Optional[float]]]:
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    n = len(closes)
    macd_line = [None] * n
    for i in range(n):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]
    macd_vals = [v for v in macd_line if v is not None]
    if len(macd_vals) < signal:
        return macd_line, [None] * n, [None] * n
    signal_line_raw = ema(macd_vals, signal)
    signal_line = [None] * n
    offset = n - len(signal_line_raw)
    for i, v in enumerate(signal_line_raw):
        signal_line[offset + i] = v
    histogram = [None] * n
    for i in range(n):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram[i] = macd_line[i] - signal_line[i]
    return macd_line, signal_line, histogram


def supertrend(highs: list[float], lows: list[float], closes: list[float], atr_period: int = 10, multiplier: float = 3.0) -> tuple[list[Optional[float]], list[Optional[str]]]:
    n = len(closes)
    atr_vals = atr(highs, lows, closes, atr_period)
    upper_band = [None] * n
    lower_band = [None] * n
    st_line = [None] * n
    direction = [None] * n

    for i in range(n):
        if atr_vals[i] is None:
            continue
        hl2 = (highs[i] + lows[i]) / 2
        ub = hl2 + multiplier * atr_vals[i]
        lb = hl2 - multiplier * atr_vals[i]
        if i > 0 and upper_band[i - 1] is not None:
            if ub < upper_band[i - 1] or closes[i - 1] > upper_band[i - 1]:
                upper_band[i] = ub
            else:
                upper_band[i] = upper_band[i - 1]
        else:
            upper_band[i] = ub
        if i > 0 and lower_band[i - 1] is not None:
            if lb > lower_band[i - 1] or closes[i - 1] < lower_band[i - 1]:
                lower_band[i] = lb
            else:
                lower_band[i] = lower_band[i - 1]
        else:
            lower_band[i] = lb

    for i in range(n):
        if upper_band[i] is None or lower_band[i] is None:
            continue
        if i == 0:
            direction[i] = "BUY"
            st_line[i] = lower_band[i]
            continue
        prev_dir = direction[i - 1]
        if prev_dir == "BUY":
            if closes[i] < lower_band[i]:
                direction[i] = "SELL"
                st_line[i] = upper_band[i]
            else:
                direction[i] = "BUY"
                st_line[i] = lower_band[i]
        else:
            if closes[i] > upper_band[i]:
                direction[i] = "BUY"
                st_line[i] = lower_band[i]
            else:
                direction[i] = "SELL"
                st_line[i] = upper_band[i]

    return st_line, direction


def bollinger(closes: list[float], period: int = 20, std_mult: float = 2.0) -> tuple[list[Optional[float]], list[Optional[float]], list[Optional[float]]]:
    n = len(closes)
    middle = sma(closes, period)
    upper = [None] * n
    lower = [None] * n
    for i in range(period - 1, n):
        window = closes[i - period + 1 : i + 1]
        std = float(np.std(window, ddof=0))
        if middle[i] is not None:
            upper[i] = middle[i] + std_mult * std
            lower[i] = middle[i] - std_mult * std
    return upper, middle, lower


def swing_highs_lows(highs: list[float], lows: list[float], left: int = 5, right: int = 5) -> list[Optional[str]]:
    n = len(highs)
    result = [None] * n
    for i in range(left, n - right):
        is_high = True
        is_low = True
        for j in range(i - left, i + right + 1):
            if j == i:
                continue
            if highs[j] >= highs[i]:
                is_high = False
            if lows[j] <= lows[i]:
                is_low = False
        if is_high:
            result[i] = "HIGH"
        elif is_low:
            result[i] = "LOW"
    return result


def detect_fvg(candles: list[dict]) -> list[dict]:
    fvgs = []
    for i in range(2, len(candles)):
        c1, c2, c3 = candles[i - 2], candles[i - 1], candles[i]
        if c3["low"] > c1["high"]:
            fvgs.append({
                "index": i,
                "type": "bullish",
                "top": c3["low"],
                "bottom": c1["high"],
                "time": c3["time"],
            })
        elif c3["high"] < c1["low"]:
            fvgs.append({
                "index": i,
                "type": "bearish",
                "top": c1["low"],
                "bottom": c3["high"],
                "time": c3["time"],
            })
    return fvgs


def detect_ob(candles: list[dict], lookback: int = 20) -> list[dict]:
    obs = []
    n = len(candles)
    for i in range(max(1, n - lookback), n):
        c = candles[i]
        prev_c = candles[i - 1]
        if c["close"] > c["open"] and prev_c["close"] < prev_c["open"]:
            body_size = abs(c["close"] - c["open"])
            is_bullish_impulse = False
            for j in range(i + 1, min(i + 5, n)):
                if candles[j]["close"] - candles[j]["open"] > body_size * 1.5:
                    is_bullish_impulse = True
                    break
            if is_bullish_impulse:
                obs.append({
                    "index": i,
                    "type": "bullish_ob",
                    "high": c["high"],
                    "low": c["low"],
                    "time": c["time"],
                })
        elif c["close"] < c["open"] and prev_c["close"] > prev_c["open"]:
            body_size = abs(c["close"] - c["open"])
            is_bearish_impulse = False
            for j in range(i + 1, min(i + 5, n)):
                if candles[j]["open"] - candles[j]["close"] > body_size * 1.5:
                    is_bearish_impulse = True
                    break
            if is_bearish_impulse:
                obs.append({
                    "index": i,
                    "type": "bearish_ob",
                    "high": c["high"],
                    "low": c["low"],
                    "time": c["time"],
                })
    return obs


def detect_structure_break(candles: list[dict], lookback: int = 5) -> list[dict]:
    breaks = []
    n = len(candles)
    for i in range(lookback, n):
        swing_highs = []
        swing_lows = []
        for j in range(i - lookback, i):
            if candles[j]["high"] > candles[j - 1]["high"] and candles[j]["high"] > candles[j + 1]["high"]:
                swing_highs.append(candles[j]["high"])
            if candles[j]["low"] < candles[j - 1]["low"] and candles[j]["low"] < candles[j + 1]["low"]:
                swing_lows.append(candles[j]["low"])
        if swing_highs and candles[i]["close"] > max(swing_highs):
            breaks.append({
                "index": i,
                "type": "BOS_bullish",
                "level": max(swing_highs),
                "time": candles[i]["time"],
            })
        if swing_lows and candles[i]["close"] < min(swing_lows):
            breaks.append({
                "index": i,
                "type": "BOS_bearish",
                "level": min(swing_lows),
                "time": candles[i]["time"],
            })
    return breaks


def volume_sma(candles: list[dict], period: int = 20) -> list[Optional[float]]:
    volumes = [c["volume"] for c in candles]
    return sma(volumes, period)


def adx(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[Optional[float]]:
    n = len(closes)
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr_list = [0.0] * n
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        if up > down and up > 0:
            plus_dm[i] = up
        if down > up and down > 0:
            minus_dm[i] = down
        tr_list[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
    atr14 = atr(highs, lows, closes, period)
    result = [None] * n
    smooth_plus = [0.0] * n
    smooth_minus = [0.0] * n
    smooth_tr = [0.0] * n
    if n < period + 1:
        return result
    smooth_plus[period] = sum(plus_dm[1 : period + 1])
    smooth_minus[period] = sum(minus_dm[1 : period + 1])
    smooth_tr[period] = sum(tr_list[1 : period + 1])
    for i in range(period + 1, n):
        smooth_plus[i] = smooth_plus[i - 1] - smooth_plus[i - 1] / period + plus_dm[i] if smooth_plus[i - 1] is not None else plus_dm[i]
        smooth_minus[i] = smooth_minus[i - 1] - smooth_minus[i - 1] / period + minus_dm[i] if smooth_minus[i - 1] is not None else minus_dm[i]
        smooth_tr[i] = smooth_tr[i - 1] - smooth_tr[i - 1] / period + tr_list[i] if smooth_tr[i - 1] is not None else tr_list[i]
    dx_list = []
    for i in range(period, n):
        if smooth_tr[i] == 0:
            dx_list.append(0)
            continue
        pdi = 100 * smooth_plus[i] / smooth_tr[i]
        mdi = 100 * smooth_minus[i] / smooth_tr[i]
        if pdi + mdi == 0:
            dx_list.append(0)
        else:
            dx_list.append(100 * abs(pdi - mdi) / (pdi + mdi))
    if len(dx_list) >= period:
        adx_val = sum(dx_list[:period]) / period
        if period + period - 1 < n:
            result[period + period - 1] = adx_val
        for i in range(period, len(dx_list)):
            adx_val = (adx_val * (period - 1) + dx_list[i]) / period
            idx = period + i
            if idx < n:
                result[idx] = adx_val
    return result


def stoch_rsi(closes: list[float], rsi_period: int = 14, stoch_period: int = 14, k_smooth: int = 3, d_smooth: int = 3) -> tuple[list[Optional[float]], list[Optional[float]]]:
    rsi_vals = rsi(closes, rsi_period)
    n = len(rsi_vals)
    raw_k = [None] * n
    for i in range(stoch_period - 1, n):
        window = [v for v in rsi_vals[i - stoch_period + 1 : i + 1] if v is not None]
        if len(window) < stoch_period:
            continue
        min_rsi = min(window)
        max_rsi = max(window)
        if max_rsi - min_rsi == 0:
            raw_k[i] = 50.0
        else:
            raw_k[i] = 100 * (rsi_vals[i] - min_rsi) / (max_rsi - min_rsi) if rsi_vals[i] is not None else 50.0
    k_vals = [v for v in raw_k if v is not None]
    k_result = [None] * n
    d_result = [None] * n
    if len(k_vals) < k_smooth:
        return k_result, d_result
    k_smoothed = ema(k_vals, k_smooth)
    d_smoothed = ema([v for v in k_smoothed if v is not None], d_smooth) if k_smoothed else []
    k_offset = n - len(k_smoothed)
    for i, v in enumerate(k_smoothed):
        if k_offset + i < n:
            k_result[k_offset + i] = v
    d_offset = n - len(d_smoothed)
    for i, v in enumerate(d_smoothed):
        if d_offset + i < n:
            d_result[d_offset + i] = v
    return k_result, d_result
