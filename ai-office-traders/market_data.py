import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import FOREX_PAIRS, PIP_SIZE, DEFAULT_PIP_SIZE

_historical_cache: dict[str, tuple[float, pd.DataFrame]] = {}
_CACHE_TTL = 300


def get_pip_size(symbol: str) -> float:
    return PIP_SIZE.get(symbol, DEFAULT_PIP_SIZE)


def get_current_price(symbol: str) -> dict | None:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m")
        if hist.empty:
            return None
        last = hist.iloc[-1]
        pip_size = get_pip_size(symbol)
        price = float(last["Close"])
        open_price = float(hist.iloc[0]["Open"])
        high_price = float(hist["High"].max())
        low_price = float(hist["Low"].min())
        return {
            "symbol": symbol,
            "name": FOREX_PAIRS.get(symbol, symbol),
            "price": price,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "volume": int(hist["Volume"].sum()),
            "timestamp": datetime.now().isoformat(),
            "pip_size": pip_size,
            "price_change": round((price - open_price) / pip_size, 1),
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
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {pool.submit(get_current_price, sym): sym for sym in FOREX_PAIRS}
        for future in as_completed(futures):
            data = future.result()
            if data:
                results.append(data)
    results.sort(key=lambda x: list(FOREX_PAIRS.values()).index(x["name"]))
    return results
