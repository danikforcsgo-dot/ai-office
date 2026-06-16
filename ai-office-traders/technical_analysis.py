import numpy as np
import pandas as pd
from config import SMA_SHORT, SMA_LONG, RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, PIP_SIZE, DEFAULT_PIP_SIZE


def get_pip_size(symbol: str = None) -> float:
    return PIP_SIZE.get(symbol, DEFAULT_PIP_SIZE) if symbol else DEFAULT_PIP_SIZE


def calc_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_rsi(series: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_macd(series: pd.Series) -> dict:
    ema12 = calc_ema(series, 12)
    ema26 = calc_ema(series, 26)
    macd_line = ema12 - ema26
    signal_line = calc_ema(macd_line, 9)
    histogram = macd_line - signal_line
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    }


def calc_bollinger_bands(series: pd.Series, period: int = 20) -> dict:
    sma = calc_sma(series, period)
    std = series.rolling(window=period).std()
    return {
        "upper": sma + 2 * std,
        "middle": sma,
        "lower": sma - 2 * std,
    }


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calc_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> dict:
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    return {"k": k, "d": d}


def calc_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    tp = (high + low + close) / 3
    sma = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma) / (0.015 * mad)


def detect_candlestick_patterns(df: pd.DataFrame) -> list[str]:
    if df.empty or len(df) < 3:
        return []
    patterns = []
    o = df["Open"].iloc[-1]
    h = df["High"].iloc[-1]
    l = df["Low"].iloc[-1]
    c = df["Close"].iloc[-1]
    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    total_range = h - l if h != l else 0.0001

    if body < total_range * 0.1:
        patterns.append("Doji")
    if lower_wick > body * 2 and upper_wick < body * 0.5 and c > o:
        patterns.append("Hammer")
    if upper_wick > body * 2 and lower_wick < body * 0.5 and c < o:
        patterns.append("Shooting Star")

    o2 = df["Open"].iloc[-2]
    c2 = df["Close"].iloc[-2]
    if c2 < o2 and c > o and o < c2 and c > o2:
        patterns.append("Bullish Engulfing")
    elif c2 > o2 and c < o and o > c2 and c < o2:
        patterns.append("Bearish Engulfing")

    o3 = df["Open"].iloc[-3]
    c3 = df["Close"].iloc[-3]
    if c3 > o3 and abs(c2 - o2) < abs(c3 - o3) * 0.3 and c > o and c > max(c3, c2):
        patterns.append("Morning Star")
    elif c3 < o3 and abs(c2 - o2) < abs(c3 - o3) * 0.3 and c < o and c < min(c3, c2):
        patterns.append("Evening Star")

    return patterns


def analyze(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < SMA_LONG + 5:
        return {"error": "Недостаточно данных для анализа"}

    close = df["Close"]
    last_price = float(close.iloc[-1])

    sma_short = calc_sma(close, SMA_SHORT)
    sma_long = calc_sma(close, SMA_LONG)
    rsi = calc_rsi(close)
    macd = calc_macd(close)
    bb = calc_bollinger_bands(close)

    last_sma_short = float(sma_short.iloc[-1])
    last_sma_long = float(sma_long.iloc[-1])
    last_rsi = float(rsi.iloc[-1])
    last_macd = float(macd["macd"].iloc[-1])
    last_signal = float(macd["signal"].iloc[-1])
    last_bb_upper = float(bb["upper"].iloc[-1])
    last_bb_lower = float(bb["lower"].iloc[-1])
    last_bb_middle = float(bb["middle"].iloc[-1])

    signals = []
    score = 0

    if last_sma_short > last_sma_long:
        signals.append("SMA: бычий тренд (короткая SMA выше длинной)")
        score += 1
    else:
        signals.append("SMA: медвежий тренд")
        score -= 1

    prev_sma_short = float(sma_short.iloc[-2])
    prev_sma_long = float(sma_long.iloc[-2])
    if prev_sma_short <= prev_sma_long and last_sma_short > last_sma_long:
        signals.append("Golden Cross! Сильный бычий сигнал")
        score += 2
    elif prev_sma_short >= prev_sma_long and last_sma_short < last_sma_long:
        signals.append("Death Cross! Сильный медвежий сигнал")
        score -= 2

    if last_rsi > RSI_OVERBOUGHT:
        signals.append(f"RSI перекуплен ({last_rsi:.1f}) - возможен разворот вниз")
        score -= 1
    elif last_rsi < RSI_OVERSOLD:
        signals.append(f"RSI перепродан ({last_rsi:.1f}) - возможен разворот вверх")
        score += 1
    else:
        signals.append(f"RSI нейтрален ({last_rsi:.1f})")

    if last_macd > last_signal:
        signals.append("MACD: бычий (MACD выше signal)")
        score += 1
    else:
        signals.append("MACD: медвежий")
        score -= 1

    bb_position = (last_price - last_bb_lower) / (last_bb_upper - last_bb_lower) if last_bb_upper != last_bb_lower else 0.5
    if bb_position > 0.9:
        signals.append("Цена у верхней полосы Боллинджера - возможна коррекция")
        score -= 1
    elif bb_position < 0.1:
        signals.append("Цена у нижней полосы Боллинджера - возможен отскок")
        score += 1

    last_hist = float(macd["histogram"].iloc[-1])
    prev_hist = float(macd["histogram"].iloc[-2])
    if last_hist > 0 and prev_hist <= 0:
        signals.append("MACD Histogram: бычий разворот")
        score += 1
    elif last_hist < 0 and prev_hist >= 0:
        signals.append("MACD Histogram: медвежий разворот")
        score -= 1

    stoch = calc_stochastic(df["High"], df["Low"], close)
    last_k = float(stoch["k"].iloc[-1]) if not stoch["k"].isna().all() else 50
    last_d = float(stoch["d"].iloc[-1]) if not stoch["d"].isna().all() else 50
    if last_k < 20 and last_k > last_d:
        signals.append(f"Stochastic: перепродан (K={last_k:.1f}), бычий кроссовер")
        score += 1
    elif last_k > 80 and last_k < last_d:
        signals.append(f"Stochastic: перекуплен (K={last_k:.1f}), медвежий кроссовер")
        score -= 1

    cci = calc_cci(df["High"], df["Low"], close)
    last_cci = float(cci.iloc[-1]) if not cci.isna().all() else 0
    if last_cci < -100:
        signals.append(f"CCI: перепродан ({last_cci:.0f})")
        score += 1
    elif last_cci > 100:
        signals.append(f"CCI: перекуплен ({last_cci:.0f})")
        score -= 1

    if score >= 3:
        recommendation = "СИЛЬНАЯ ПОКУПКА"
    elif score >= 1:
        recommendation = "ПОКУПКА"
    elif score <= -3:
        recommendation = "СИЛЬНАЯ ПРОДАЖА"
    elif score <= -1:
        recommendation = "ПРОДАЖА"
    else:
        recommendation = "ДЕРЖАТЬ"

    return {
        "price": last_price,
        "sma_short": last_sma_short,
        "sma_long": last_sma_long,
        "rsi": last_rsi,
        "macd": last_macd,
        "macd_signal": last_signal,
        "bb_upper": last_bb_upper,
        "bb_lower": last_bb_lower,
        "bb_middle": last_bb_middle,
        "score": score,
        "recommendation": recommendation,
        "signals": signals,
        "pip_size": get_pip_size(),
        "price_change_pips": round((last_price - float(close.iloc[-2])) / get_pip_size(), 1) if len(close) >= 2 else 0,
    }
