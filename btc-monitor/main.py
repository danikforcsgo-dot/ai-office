import asyncio
import json
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from signal_engine import SignalEngine, Signal, ConfluenceSignal

BINANCE_REST = "https://api.binance.com/api/v3"
BINANCE_WS_BASE = "wss://stream.binance.com:9443/ws"

DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "4h"
CANDLE_LIMIT = 1000

SUPPORTED_INTERVALS = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]

connected_clients: set[WebSocket] = set()
ticker_cache: dict = {}
ticker_last_update: float = 0
TICKER_CACHE_TTL = 2.0


class BinanceClient:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self._rate_limit_remaining = 1200
        self._rate_limit_reset = 0

    async def init(self):
        self.client = httpx.AsyncClient(
            base_url=BINANCE_REST,
            timeout=10.0,
            headers={"User-Agent": "BTC-Monitor/1.0"},
        )

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def _request(self, method: str, path: str, params: dict = None) -> dict | list:
        now = time.time()
        if self._rate_limit_remaining < 10 and now < self._rate_limit_reset:
            wait = self._rate_limit_reset - now
            if wait > 0:
                await asyncio.sleep(wait)

        resp = await self.client.request(method, path, params=params)

        self._rate_limit_remaining = int(resp.headers.get("X-MBX-USED-WEIGHT-1M", 1200))
        self._rate_limit_reset = now + 60

        resp.raise_for_status()
        return resp.json()

    async def get_klines(self, symbol: str, interval: str, limit: int = 1000, start_time: int = None, end_time: int = None) -> list[dict]:
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        data = await self._request("GET", "/klines", params)
        return [self._parse_candle(k) for k in data]

    async def get_ticker_24h(self, symbol: str) -> dict:
        global ticker_cache, ticker_last_update
        now = time.time()
        cache_key = f"ticker_{symbol}"
        if cache_key in ticker_cache and (now - ticker_last_update) < TICKER_CACHE_TTL:
            return ticker_cache[cache_key]

        data = await self._request("GET", "/ticker/24hr", {"symbol": symbol})
        ticker = {
            "symbol": data["symbol"],
            "price": float(data["lastPrice"]),
            "change": float(data["priceChange"]),
            "changePercent": float(data["priceChangePercent"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"]),
            "volume": float(data["volume"]),
            "quoteVolume": float(data["quoteVolume"]),
            "weightedAvgPrice": float(data["weightedAvgPrice"]),
            "openPrice": float(data["openPrice"]),
            "prevClosePrice": float(data["prevClosePrice"]),
        }
        ticker_cache[cache_key] = ticker
        ticker_last_update = now
        return ticker

    async def get_order_book(self, symbol: str, limit: int = 20) -> dict:
        data = await self._request("GET", "/depth", {"symbol": symbol, "limit": limit})
        return {
            "bids": [[float(p), float(q)] for p, q in data["bids"]],
            "asks": [[float(p), float(q)] for p, q in data["asks"]],
            "lastUpdateId": data["lastUpdateId"],
        }

    async def get_recent_trades(self, symbol: str, limit: int = 50) -> list[dict]:
        data = await self._request("GET", "/trades", {"symbol": symbol, "limit": limit})
        return [
            {
                "id": t["id"],
                "price": float(t["price"]),
                "qty": float(t["qty"]),
                "time": t["time"],
                "isBuyerMaker": t["isBuyerMaker"],
            }
            for t in data
        ]

    async def get_exchange_info(self, symbol: str = None) -> dict:
        data = await self._request("GET", "/exchangeInfo")
        if symbol:
            for s in data["symbols"]:
                if s["symbol"] == symbol:
                    return s
        return data

    async def get_price(self, symbol: str) -> float:
        data = await self._request("GET", "/ticker/price", {"symbol": symbol})
        return float(data["price"])

    async def get_all_tickers(self) -> list[dict]:
        data = await self._request("GET", "/ticker/price")
        return [{"symbol": t["symbol"], "price": float(t["price"])} for t in data]

    def _parse_candle(self, raw: list) -> dict:
        return {
            "time": int(raw[0]) // 1000,
            "open": float(raw[1]),
            "high": float(raw[2]),
            "low": float(raw[3]),
            "close": float(raw[4]),
            "volume": float(raw[5]),
            "close_time": int(raw[6]) // 1000,
            "quote_volume": float(raw[7]),
            "trades": int(raw[8]),
            "taker_buy_volume": float(raw[9]),
            "taker_buy_quote_volume": float(raw[10]),
        }


binance = BinanceClient()

latest_candle: dict | None = None
candle_history: list[dict] = []
signal_engine: SignalEngine | None = None
current_data: dict = {"individual": [], "confluence": None}
current_symbol: str = DEFAULT_SYMBOL
current_interval: str = DEFAULT_INTERVAL


def signal_to_dict(s: Signal) -> dict:
    return {
        "script_name": s.script_name,
        "author": s.author,
        "category": s.category,
        "direction": s.direction,
        "confidence": round(s.confidence, 2),
        "rules_matched": s.rules_matched,
        "timestamp": s.timestamp.isoformat(),
        "price": s.price,
        "url": s.url,
    }


def confluence_to_dict(c: ConfluenceSignal) -> dict:
    return {
        "direction": c.direction,
        "confluence_score": c.confluence_score,
        "total_scripts": c.total_scripts,
        "total_loaded": c.total_loaded,
        "buy_count": len(c.buy_scripts),
        "sell_count": len(c.sell_scripts),
        "buy_scripts": c.buy_scripts,
        "sell_scripts": c.sell_scripts,
        "categories": c.categories,
        "timestamp": c.timestamp.isoformat(),
        "price": c.price,
    }


async def broadcast(message: str):
    stale = set()
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            stale.add(ws)
    connected_clients.difference_update(stale)


async def signal_analysis_loop():
    global current_data
    while True:
        try:
            if candle_history and signal_engine:
                result = signal_engine.analyze(candle_history)
                current_data = {
                    "individual": [signal_to_dict(s) for s in result["individual"]],
                    "confluence": confluence_to_dict(result["confluence"]) if result["confluence"] else None,
                }
                msg = json.dumps({"type": "signals", "data": current_data})
                await broadcast(msg)
            await asyncio.sleep(5)
        except Exception as e:
            import traceback
            print(f"Signal analysis error: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)


async def ticker_loop():
    while True:
        try:
            ticker = await binance.get_ticker_24h(current_symbol)
            msg = json.dumps({"type": "ticker", "data": ticker})
            await broadcast(msg)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Ticker error: {e}")
            await asyncio.sleep(3)


async def binance_ws_loop():
    global latest_candle, candle_history
    import websockets

    while True:
        ws_url = f"{BINANCE_WS_BASE}/{current_symbol.lower()}@kline_{current_interval}"
        try:
            async with websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
            ) as ws:
                async for raw in ws:
                    data = json.loads(raw)
                    if "k" in data:
                        k = data["k"]
                        candle = {
                            "time": int(k["t"]) // 1000,
                            "open": float(k["o"]),
                            "high": float(k["h"]),
                            "low": float(k["l"]),
                            "close": float(k["c"]),
                            "volume": float(k["v"]),
                            "close_time": int(k["T"]) // 1000,
                            "quote_volume": float(k["q"]),
                            "trades": int(k["n"]),
                            "taker_buy_volume": float(k["V"]),
                            "taker_buy_quote_volume": float(k["Q"]),
                            "is_closed": k["x"],
                        }
                        latest_candle = candle
                        if candle_history:
                            last = candle_history[-1]
                            if last["time"] == candle["time"]:
                                candle_history[-1] = candle
                            else:
                                candle_history.append(candle)
                                if len(candle_history) > CANDLE_LIMIT + 100:
                                    candle_history = candle_history[-CANDLE_LIMIT:]
                        msg = json.dumps({"type": "kline", "data": candle})
                        await broadcast(msg)
        except websockets.ConnectionClosed:
            print("WebSocket closed, reconnecting...")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"WebSocket error: {e}")
            await asyncio.sleep(3)


async def depth_ws_loop():
    import websockets
    while True:
        ws_url = f"{BINANCE_WS_BASE}/{current_symbol.lower()}@depth20@100ms"
        try:
            async with websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10,
            ) as ws:
                async for raw in ws:
                    data = json.loads(raw)
                    depth = {
                        "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
                        "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
                    }
                    msg = json.dumps({"type": "depth", "data": depth})
                    await broadcast(msg)
        except Exception:
            await asyncio.sleep(3)


async def trades_ws_loop():
    import websockets
    while True:
        ws_url = f"{BINANCE_WS_BASE}/{current_symbol.lower()}@aggTrade"
        try:
            async with websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10,
            ) as ws:
                async for raw in ws:
                    data = json.loads(raw)
                    trade = {
                        "price": float(data["p"]),
                        "qty": float(data["q"]),
                        "time": data["T"],
                        "is_buyer_maker": data["m"],
                    }
                    msg = json.dumps({"type": "trade", "data": trade})
                    await broadcast(msg)
        except Exception:
            await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global candle_history, signal_engine
    await binance.init()

    candle_history = await binance.get_klines(current_symbol, current_interval, CANDLE_LIMIT)
    if candle_history:
        latest = candle_history[-1]
        global latest_candle
        latest_candle = latest

    signal_engine = SignalEngine("scripts")

    tasks = [
        asyncio.create_task(binance_ws_loop()),
        asyncio.create_task(signal_analysis_loop()),
        asyncio.create_task(ticker_loop()),
        asyncio.create_task(depth_ws_loop()),
        asyncio.create_task(trades_ws_loop()),
    ]

    yield

    for task in tasks:
        task.cancel()
    await binance.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/ticker")
async def get_ticker(symbol: str = Query(default=DEFAULT_SYMBOL)):
    return await binance.get_ticker_24h(symbol)


@app.get("/api/orderbook")
async def get_orderbook(symbol: str = Query(default=DEFAULT_SYMBOL), limit: int = Query(default=20)):
    return await binance.get_order_book(symbol, limit)


@app.get("/api/trades")
async def get_trades(symbol: str = Query(default=DEFAULT_SYMBOL), limit: int = Query(default=50)):
    return await binance.get_recent_trades(symbol, limit)


@app.get("/api/klines")
async def get_klines(
    symbol: str = Query(default=DEFAULT_SYMBOL),
    interval: str = Query(default=DEFAULT_INTERVAL),
    limit: int = Query(default=1000),
    start_time: int = Query(default=None),
    end_time: int = Query(default=None),
):
    return await binance.get_klines(symbol, interval, limit, start_time, end_time)


@app.get("/api/signals")
async def get_signals():
    return current_data


@app.get("/api/scripts")
async def get_scripts():
    import os
    scripts = []
    for fname in sorted(os.listdir("scripts")):
        if fname.endswith(".json"):
            with open(os.path.join("scripts", fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                scripts.append({
                    "name": data.get("name"),
                    "author": data.get("author"),
                    "category": data.get("category"),
                    "url": data.get("url"),
                })
    return {"scripts": scripts}


@app.get("/api/symbols")
async def get_symbols():
    info = await binance.get_exchange_info()
    return {"symbols": SUPPORTED_INTERVALS, "intervals": SUPPORTED_INTERVALS}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, interval: str = Query(default=DEFAULT_INTERVAL)):
    global current_interval
    if interval in SUPPORTED_INTERVALS:
        current_interval = interval
    await ws.accept()
    connected_clients.add(ws)
    try:
        if candle_history:
            await ws.send_text(json.dumps({"type": "history", "data": candle_history}))
        if latest_candle:
            await ws.send_text(json.dumps({"type": "kline", "data": latest_candle}))
        if current_data["individual"]:
            await ws.send_text(json.dumps({"type": "signals", "data": current_data}))

        try:
            ticker = await binance.get_ticker_24h(current_symbol)
            await ws.send_text(json.dumps({"type": "ticker", "data": ticker}))
        except Exception:
            pass

        while True:
            try:
                msg = await ws.receive_text()
                try:
                    cmd = json.loads(msg)
                    if cmd.get("type") == "subscribe":
                        pass
                except json.JSONDecodeError:
                    pass
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        connected_clients.discard(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
