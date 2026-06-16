import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from technical_analysis import calc_atr
from market_data import get_historical_data, get_pip_size
from config import (
    TRADER_INITIAL_BALANCE, TRADER_RISK_PER_TRADE, TRADER_MAX_POSITIONS,
    TRADER_MAX_DRAWDOWN_PCT, TRADER_MIN_SIGNAL_STRENGTH,
    TRADER_TRAILING_STOP_ACTIVATION, TRADER_TRAILING_STOP_DISTANCE,
)


TRADES_FILE = os.path.join(os.path.dirname(__file__), "trade_history.json")


@dataclass
class Position:
    pair: str
    side: str
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: str = field(default_factory=lambda: datetime.now().isoformat())
    trailing_stop: float = 0.0
    highest_pnl: float = 0.0
    atr_at_entry: float = 0.0
    signal_strength: int = 0
    confluence: list = field(default_factory=list)
    pnl: float = 0.0


@dataclass
class TradeHistory:
    pair: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    entry_time: str
    exit_time: str
    pnl: float
    result: str
    signal_strength: int = 0
    confluence: list = field(default_factory=list)
    exit_reason: str = ""


class Trader:
    def __init__(self, name: str):
        self.name = name
        self.balance = TRADER_INITIAL_BALANCE
        self.initial_balance = TRADER_INITIAL_BALANCE
        self.positions: list[Position] = []
        self.history: list[TradeHistory] = []
        self.max_positions = TRADER_MAX_POSITIONS
        self.risk_per_trade = TRADER_RISK_PER_TRADE
        self.max_drawdown_pct = TRADER_MAX_DRAWDOWN_PCT
        self.min_signal_strength = TRADER_MIN_SIGNAL_STRENGTH
        self.trailing_stop_activation = TRADER_TRAILING_STOP_ACTIVATION
        self.trailing_stop_distance = TRADER_TRAILING_STOP_DISTANCE
        self._cooldowns: dict[str, datetime] = {}
        self._load_history()

    def _load_history(self):
        if os.path.exists(TRADES_FILE):
            try:
                with open(TRADES_FILE, "r") as f:
                    data = json.load(f)
                self.balance = data.get("balance", self.initial_balance)
                self.history = [TradeHistory(**t) for t in data.get("trades", [])]
            except Exception:
                pass

    def _save_history(self):
        data = {
            "balance": round(self.balance, 2),
            "trades": [asdict(t) for t in self.history[-200:]],
        }
        with open(TRADES_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _check_drawdown(self) -> bool:
        equity = self.balance + sum(p.pnl for p in self.positions)
        drawdown = (self.initial_balance - equity) / self.initial_balance
        return drawdown < self.max_drawdown_pct

    def _get_atr_pips(self, symbol: str) -> float:
        df = get_historical_data(symbol, period="3mo", interval="1d")
        if df.empty or len(df) < 14:
            return 20.0
        atr_series = calc_atr(df["High"], df["Low"], df["Close"], period=14)
        atr_val = float(atr_series.iloc[-1]) if not atr_series.isna().all() else 20.0
        pip = get_pip_size(symbol)
        return max(atr_val / pip, 5.0)

    def evaluate_signals(self, all_reports: list[dict], global_report: dict,
                         dept_reports: list[dict], news_results: list[dict],
                         multi_tf_results: list[dict]) -> list[dict]:
        pair_signals = {}
        for r in all_reports:
            for sig in r.get("signals", []):
                pair = sig.get("pair", "")
                signal = sig.get("signal", "NEUTRAL")
                if not pair:
                    continue
                if pair not in pair_signals:
                    pair_signals[pair] = {"BUY": 0, "SELL": 0, "NEUTRAL": 0, "details": []}
                pair_signals[pair][signal] = pair_signals[pair].get(signal, 0) + 1
                pair_signals[pair]["details"].append({
                    "analyst": r["analyst_name"],
                    "dept": r["department"],
                    "signal": signal,
                })

        news_map = {}
        for n in news_results:
            news_map[n["pair"]] = n

        tf_map = {}
        for tf in multi_tf_results:
            tf_map[tf["pair"]] = tf

        decisions = []
        for pair_name, sigs in pair_signals.items():
            buy_count = sigs["BUY"]
            sell_count = sigs["SELL"]
            total = buy_count + sell_count + sigs["NEUTRAL"]

            if total == 0:
                continue

            strength = 0
            direction = "NEUTRAL"
            confluence = []

            if buy_count > sell_count and buy_count >= 2:
                direction = "BUY"
                strength = buy_count
                confluence.append(f"{buy_count} BUY signals")
            elif sell_count > buy_count and sell_count >= 2:
                direction = "SELL"
                strength = sell_count
                confluence.append(f"{sell_count} SELL signals")
            else:
                continue

            dept_buy = sum(1 for d in dept_reports if d["verdict"] == "BULLISH")
            dept_sell = sum(1 for d in dept_reports if d["verdict"] == "BEARISH")
            if direction == "BUY" and dept_buy > dept_sell:
                strength += 1
                confluence.append(f"{dept_buy} departments BULLISH")
            elif direction == "SELL" and dept_sell > dept_buy:
                strength += 1
                confluence.append(f"{dept_sell} departments BEARISH")

            if global_report["global_verdict"] == "BULLISH" and direction == "BUY":
                strength += 2
                confluence.append("Global BULLISH")
            elif global_report["global_verdict"] == "BEARISH" and direction == "SELL":
                strength += 2
                confluence.append("Global BEARISH")

            news = news_map.get(pair_name)
            if news:
                if news.get("signal") == direction:
                    strength += 1
                    confluence.append(f"News {news['sentiment_summary']}")
                elif news.get("signal") != "NEUTRAL" and news.get("signal") != direction:
                    strength -= 1
                    confluence.append(f"News CONFLICT ({news['sentiment_summary']})")

            tf = tf_map.get(pair_name)
            if tf:
                if not tf.get("conflict"):
                    if tf.get("htf_signal") == direction:
                        strength += 1
                        confluence.append(f"Multi-TF aligned ({tf['htf_signal']})")
                    elif tf.get("htf_signal") != "NEUTRAL" and tf.get("htf_signal") != direction:
                        strength -= 1
                        confluence.append(f"Multi-TF CONFLICT")

            if strength >= self.min_signal_strength:
                decisions.append({
                    "pair": pair_name,
                    "direction": direction,
                    "strength": strength,
                    "confluence": confluence,
                    "buy_signals": buy_count,
                    "sell_signals": sell_count,
                })

        decisions.sort(key=lambda x: x["strength"], reverse=True)
        return decisions[:self.max_positions]

    def process_decisions(self, decisions: list[dict], prices: list[dict]) -> list[str]:
        events = []
        price_map = {p["name"]: p["price"] for p in prices}

        trade_events = self.update_positions(price_map)
        events.extend(trade_events)

        closed_this_cycle = {e.split()[2] for e in trade_events if e.startswith("SL") or e.startswith("TP") or e.startswith("TRAILING")}

        if not self._check_drawdown():
            events.append("MAX DRAWDOWN REACHED — trading suspended")
            return events

        opened_this_cycle = set()
        for dec in decisions:
            pair = dec["pair"]
            direction = dec["direction"]
            price = price_map.get(pair)
            if price is None:
                continue
            if pair in opened_this_cycle:
                continue
            if any(p.pair == pair for p in self.positions):
                continue
            if pair in closed_this_cycle:
                continue
            if pair in self._cooldowns and datetime.now() < self._cooldowns[pair]:
                continue
            if len(self.positions) >= self.max_positions:
                break

            atr_pips = self._get_atr_pips(pair)
            pip = get_pip_size(pair)
            sl_pips = round(atr_pips * 1.5)
            tp_pips = round(atr_pips * 2.5)
            sl_distance = sl_pips * pip
            tp_distance = tp_pips * pip

            if direction == "BUY":
                sl = price - sl_distance
                tp = price + tp_distance
            else:
                sl = price + sl_distance
                tp = price - tp_distance

            risk_amount = self.balance * self.risk_per_trade
            if sl_distance == 0:
                continue
            size = risk_amount / sl_distance

            pos = Position(
                pair=pair,
                side=direction,
                entry_price=price,
                size=size,
                stop_loss=sl,
                take_profit=tp,
                trailing_stop=sl,
                atr_at_entry=atr_pips,
                signal_strength=dec["strength"],
                confluence=dec["confluence"],
            )
            self.positions.append(pos)
            self._cooldowns[pair] = datetime.now() + timedelta(minutes=30)
            opened_this_cycle.add(pair)
            events.append(
                f"OPEN {direction} {pair} @ {price:.5f} "
                f"| SL={sl:.5f} TP={tp:.5f} "
                f"| Strength={dec['strength']} "
                f"| [{', '.join(dec['confluence'][:3])}]"
            )

        return events

    def update_pnl(self, prices: dict[str, float]):
        for pos in self.positions:
            current = prices.get(pos.pair)
            if current is None:
                continue
            if pos.side == "BUY":
                pos.pnl = (current - pos.entry_price) * pos.size
            else:
                pos.pnl = (pos.entry_price - current) * pos.size

    def update_positions(self, prices: dict[str, float]) -> list[str]:
        events = []
        closed = []
        for pos in self.positions:
            current = prices.get(pos.pair)
            if current is None:
                continue

            if pos.side == "BUY":
                pos.pnl = (current - pos.entry_price) * pos.size
                pnl_pct = (current - pos.entry_price) / pos.entry_price
            else:
                pos.pnl = (pos.entry_price - current) * pos.size
                pnl_pct = (pos.entry_price - current) / pos.entry_price

            if pnl_pct > pos.highest_pnl:
                pos.highest_pnl = pnl_pct

            if pnl_pct >= self.trailing_stop_activation:
                pip = get_pip_size(pos.pair)
                trail_pips = round(pos.atr_at_entry * 1.0)
                trail_dist = trail_pips * pip
                if pos.side == "BUY":
                    new_trail = current - trail_dist
                    if new_trail > pos.trailing_stop:
                        pos.trailing_stop = new_trail
                else:
                    new_trail = current + trail_dist
                    if new_trail < pos.trailing_stop:
                        pos.trailing_stop = new_trail

            exit_reason = None
            if pos.side == "BUY":
                if current <= pos.stop_loss:
                    exit_reason = "SL"
                elif current >= pos.take_profit:
                    exit_reason = "TP"
                elif current <= pos.trailing_stop and pos.highest_pnl >= self.trailing_stop_activation:
                    exit_reason = "TRAILING"
            else:
                if current >= pos.stop_loss:
                    exit_reason = "SL"
                elif current <= pos.take_profit:
                    exit_reason = "TP"
                elif current >= pos.trailing_stop and pos.highest_pnl >= self.trailing_stop_activation:
                    exit_reason = "TRAILING"

            if exit_reason:
                closed.append((pos, current, exit_reason))

        for pos, exit_price, reason in closed:
            self.balance += pos.pnl
            result = "WIN" if pos.pnl > 0 else "LOSS"
            self._cooldowns[pos.pair] = datetime.now() + timedelta(minutes=30)
            self.history.append(TradeHistory(
                pair=pos.pair,
                side=pos.side,
                entry_price=pos.entry_price,
                exit_price=exit_price,
                size=pos.size,
                entry_time=pos.entry_time,
                exit_time=datetime.now().isoformat(),
                pnl=round(pos.pnl, 2),
                result=result,
                signal_strength=pos.signal_strength,
                confluence=pos.confluence,
                exit_reason=reason,
            ))
            self.positions.remove(pos)
            events.append(
                f"{reason} {pos.side} {pos.pair} "
                f"| Entry={pos.entry_price:.5f} Exit={exit_price:.5f} "
                f"| PnL={pos.pnl:+.2f} ({result})"
            )

        if closed:
            self._save_history()

        return events

    def close_position(self, pair: str, current_price: float) -> Position | None:
        for pos in self.positions:
            if pos.pair == pair:
                if pos.side == "BUY":
                    pos.pnl = (current_price - pos.entry_price) * pos.size
                else:
                    pos.pnl = (pos.entry_price - current_price) * pos.size
                self.balance += pos.pnl
                result = "WIN" if pos.pnl > 0 else "LOSS"
                self.history.append(TradeHistory(
                    pair=pos.pair,
                    side=pos.side,
                    entry_price=pos.entry_price,
                    exit_price=current_price,
                    size=pos.size,
                    entry_time=pos.entry_time,
                    exit_time=datetime.now().isoformat(),
                    pnl=round(pos.pnl, 2),
                    result=result,
                    signal_strength=pos.signal_strength,
                    confluence=pos.confluence,
                    exit_reason="MANUAL",
                ))
                self.positions.remove(pos)
                self._save_history()
                return pos
        return None

    def get_stats(self) -> dict:
        total_trades = len(self.history)
        wins = sum(1 for t in self.history if t.result == "WIN")
        losses = total_trades - wins
        total_pnl = sum(t.pnl for t in self.history)
        equity = self.balance + sum(p.pnl for p in self.positions)
        max_pnl = max((t.pnl for t in self.history), default=0)
        max_loss = min((t.pnl for t in self.history), default=0)

        avg_win = 0
        avg_loss = 0
        if wins > 0:
            avg_win = sum(t.pnl for t in self.history if t.result == "WIN") / wins
        if losses > 0:
            avg_loss = sum(t.pnl for t in self.history if t.result == "LOSS") / losses

        profit_factor = abs(sum(t.pnl for t in self.history if t.pnl > 0) / sum(t.pnl for t in self.history if t.pnl < 0)) if sum(t.pnl for t in self.history if t.pnl < 0) != 0 else 0

        drawdown = (self.initial_balance - equity) / self.initial_balance * 100 if equity < self.initial_balance else 0

        return {
            "name": self.name,
            "balance": round(self.balance, 2),
            "equity": round(equity, 2),
            "total_pnl": round(total_pnl, 2),
            "roi": round((equity - self.initial_balance) / self.initial_balance * 100, 2),
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total_trades * 100, 1) if total_trades > 0 else 0,
            "open_positions": len(self.positions),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_pnl": round(max_pnl, 2),
            "max_loss": round(max_loss, 2),
            "drawdown_pct": round(drawdown, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct * 100, 1),
        }
