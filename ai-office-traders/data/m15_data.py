import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def get_m15_data(symbol: str, period: str = "5d") -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="15m")
        return df
    except Exception as e:
        print(f"[ERROR] M15 {symbol}: {e}")
        return pd.DataFrame()


def get_htf_data(symbol: str, timeframe: str = "4h", period: str = "1mo") -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=timeframe)
        return df
    except Exception as e:
        print(f"[ERROR] HTF {symbol} {timeframe}: {e}")
        return pd.DataFrame()


def _resample_to_h4(df_1h: pd.DataFrame) -> pd.DataFrame:
    if df_1h.empty:
        return df_1h
    agg_dict = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }
    if "Volume" in df_1h.columns:
        agg_dict["Volume"] = "sum"
    return df_1h.resample("4h").agg(agg_dict).dropna()


def get_multi_tf_data(symbol: str) -> dict:
    h1 = get_htf_data(symbol, "1h", period="3mo")
    return {
        "m15": get_m15_data(symbol, period="5d"),
        "h4": _resample_to_h4(h1),
        "d1": get_htf_data(symbol, "1d", period="3mo"),
    }


def detect_htf_bias(d1_df: pd.DataFrame) -> str:
    if d1_df.empty or len(d1_df) < 20:
        return "UNKNOWN"
    close = d1_df["Close"]
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else sma20
    last = float(close.iloc[-1])
    if last > sma20 and sma20 > sma50:
        return "BULLISH"
    elif last < sma20 and sma20 < sma50:
        return "BEARISH"
    return "NEUTRAL"


def detect_bos_choch(m15_df: pd.DataFrame) -> dict:
    if m15_df.empty or len(m15_df) < 10:
        return {"bos": "NO DATA", "choch": "NO DATA"}
    close = m15_df["Close"]
    high = m15_df["High"]
    low = m15_df["Low"]
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    prev2 = float(close.iloc[-3]) if len(close) >= 3 else prev
    swing_high = float(high.iloc[-5:-1].max())
    swing_low = float(low.iloc[-5:-1].min())
    if last > swing_high and prev <= swing_high:
        bos = "BULLISH BOS"
    elif last < swing_low and prev >= swing_low:
        bos = "BEARISH BOS"
    else:
        bos = "NO BOS"
    if last > prev and prev2 > prev and prev < float(close.iloc[-4]) if len(close) >= 4 else False:
        choch = "BULLISH CHoCH"
    elif last < prev and prev2 < prev and prev > float(close.iloc[-4]) if len(close) >= 4 else False:
        choch = "BEARISH CHoCH"
    else:
        choch = "NO CHoCH"
    return {"bos": bos, "choch": choch}


def detect_fvg(m15_df: pd.DataFrame) -> list[dict]:
    if m15_df.empty or len(m15_df) < 3:
        return []
    fvgs = []
    for i in range(2, min(len(m15_df), 20)):
        candle3_high = float(m15_df["High"].iloc[-i-1])
        candle1_low = float(m15_df["Low"].iloc[-i])
        if candle1_low > candle3_high:
            fvgs.append({
                "type": "Bullish FVG",
                "gap_top": round(candle1_low, 5),
                "gap_bottom": round(candle3_high, 5),
                "age_candles": i,
            })
        candle3_low = float(m15_df["Low"].iloc[-i-1])
        candle1_high = float(m15_df["High"].iloc[-i])
        if candle1_high < candle3_low:
            fvgs.append({
                "type": "Bearish FVG",
                "gap_top": round(candle3_low, 5),
                "gap_bottom": round(candle1_high, 5),
                "age_candles": i,
            })
    return fvgs[:3]


def detect_order_blocks(m15_df: pd.DataFrame) -> list[dict]:
    if m15_df.empty or len(m15_df) < 5:
        return []
    obs = []
    for i in range(1, min(len(m15_df) - 1, 20)):
        idx = -i - 1
        candle = m15_df.iloc[idx]
        next_candle = m15_df.iloc[idx + 1]
        body = abs(float(candle["Close"]) - float(candle["Open"]))
        next_body = abs(float(next_candle["Close"]) - float(next_candle["Open"]))
        if next_body > body * 2:
            is_bullish = float(candle["Close"]) < float(candle["Open"])
            if is_bullish:
                obs.append({
                    "type": "Bullish OB",
                    "high": round(float(candle["High"]), 5),
                    "low": round(float(candle["Low"]), 5),
                    "age_candles": i,
                })
            else:
                obs.append({
                    "type": "Bearish OB",
                    "high": round(float(candle["High"]), 5),
                    "low": round(float(candle["Low"]), 5),
                    "age_candles": i,
                })
    return obs[:3]


def detect_liquidity_zones(m15_df: pd.DataFrame) -> dict:
    if m15_df.empty or len(m15_df) < 20:
        return {}
    high = m15_df["High"]
    low = m15_df["Low"]
    recent_high = float(high.iloc[-20:].max())
    recent_low = float(low.iloc[-20:].min())
    current = float(m15_df["Close"].iloc[-1])
    highs_touched = sum(1 for h in high.iloc[-10:] if abs(float(h) - recent_high) / recent_high < 0.001)
    lows_touched = sum(1 for l in low.iloc[-10:] if abs(float(l) - recent_low) / recent_low < 0.001)
    return {
        "bsl_level": round(recent_high, 5),
        "ssl_level": round(recent_low, 5),
        "bsl_touches": highs_touched,
        "ssl_touches": lows_touched,
        "current": round(current, 5),
        "target": "BSL" if (recent_high - current) < (current - recent_low) else "SSL",
    }
