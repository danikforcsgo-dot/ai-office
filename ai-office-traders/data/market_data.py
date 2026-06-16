import yfinance as yf
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "..", "core"))

from config import INSTRUMENTS, GOLD_PIP_SIZE

_historical_cache = {}
_CACHE_TTL = 300


def get_pip_size(symbol: str = None) -> float:
    return GOLD_PIP_SIZE


def get_current_price(symbol: str) -> dict | None:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m")
        if hist.empty:
            hist = ticker.history(period="5d", interval="1h")
        if hist.empty:
            return None
        last = hist.iloc[-1]
        price = float(last["Close"])
        open_price = float(hist.iloc[0]["Open"])
        high_price = float(hist["High"].max())
        low_price = float(hist["Low"].min())
        return {
            "symbol": symbol,
            "name": INSTRUMENTS.get(symbol, symbol),
            "price": price,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "volume": int(hist["Volume"].sum()) if "Volume" in hist.columns else 0,
            "timestamp": datetime.now().isoformat(),
            "pip_size": GOLD_PIP_SIZE,
            "price_change": round((price - open_price) / GOLD_PIP_SIZE, 1),
        }
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}")
        return None


def get_historical_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    cache_key = f"{symbol}:{period}:{interval}"
    now = datetime.now().timestamp()
    cached = _historical_cache.get(cache_key)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        _historical_cache[cache_key] = (now, df)
        return df
    except Exception as e:
        print(f"[ERROR] Historical {symbol}: {e}")
        return pd.DataFrame()


def get_all_prices() -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(get_current_price, sym): sym for sym in INSTRUMENTS}
        for future in as_completed(futures):
            data = future.result()
            if data:
                results.append(data)
    return results


def get_gold_correlations() -> dict:
    try:
        xau = get_historical_data("XAU/USD", period="3mo", interval="1d")
        if xau.empty:
            return {}
        correlations = {}
        tickers = {"DXY": "DX-Y.NYB", "US10Y": "^TNX", "SPX": "^GSPC", "VIX": "^VIX"}
        for name, ticker in tickers.items():
            try:
                data = get_historical_data(ticker, period="3mo", interval="1d")
                if not data.empty and len(data) == len(xau):
                    corr = float(pd.Series(xau["Close"]).corr(pd.Series(data["Close"])))
                    correlations[name] = round(corr, 3)
            except Exception:
                pass
        return correlations
    except Exception:
        return {}
