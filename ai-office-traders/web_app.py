from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime

from config import FOREX_PAIRS, TIMEFRAME, ANALYSIS_INTERVAL_MINUTES
from market_data import get_all_prices
from staff import ANALYSTS, DEPARTMENTS_STRUCTURE, get_all_departments
from analyst_engine import analyst_work, department_head_report, global_meeting
from debate import run_debate, format_debate
from multi_tf import run_multi_tf_analysis, format_multi_tf
from adaptive_weights import get_weighted_verdict, get_all_weights, record_signal
from news import analyze_news_for_all_pairs, format_news
from notifications import NotificationManager
from trader import Trader

app = Flask(__name__)
CORS(app)

last_results = {}
notify_mgr = NotificationManager()
trader = Trader("AI Office Trader")


@app.route("/")
def index():
    depts = get_all_departments()
    return render_template("index.html",
                           pairs=FOREX_PAIRS,
                           timeframe=TIMEFRAME,
                           staff_count=len(ANALYSTS),
                           dept_count=len(depts),
                           depts=depts)


@app.route("/api/cycle")
def api_cycle():
    try:
        return _run_cycle()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _run_cycle():
    global last_results
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prices = get_all_prices()
    if not prices:
        return jsonify({"error": "Не удалось получить цены"}), 500

    all_reports = []
    for analyst in ANALYSTS:
        report = analyst_work(analyst, prices)
        all_reports.append(report)

    dept_reports = []
    for dept_name, cfg in DEPARTMENTS_STRUCTURE.items():
        head_id = cfg["head_id"]
        head = next((a for a in ANALYSTS if a.id == head_id and a.department == dept_name), None)
        if not head:
            continue
        member_ids = [a.id for a in ANALYSTS if a.department == dept_name]
        member_reports = [r for r in all_reports if r["analyst_id"] in member_ids]
        head_report = department_head_report(head, member_reports)
        dept_reports.append(head_report)

    debate_messages = run_debate(all_reports)
    global_report = global_meeting(dept_reports)
    weighted = get_weighted_verdict(dept_reports)
    news_results = analyze_news_for_all_pairs(prices)

    try:
        multi_tf_results = run_multi_tf_analysis(prices)
    except Exception:
        multi_tf_results = []

    for r in all_reports:
        for sig in r.get("signals", []):
            pair = sig.get("pair", "")
            analysis_data = {}
            for f in r.get("findings", []):
                if f.get("pair") == pair:
                    analysis_data = f
                    break
            notify_mgr.check_signal_alerts(pair, analysis_data)

    try:
        decisions = trader.evaluate_signals(all_reports, global_report, dept_reports, news_results, multi_tf_results)
        trade_events = trader.process_decisions(decisions, prices)
    except Exception as e:
        trade_events = [f"Trader error: {e}"]
        decisions = []

    last_results = {
        "timestamp": ts,
        "prices": prices,
        "analyst_reports": [_report_summary(r) for r in all_reports],
        "dept_reports": dept_reports,
        "debate": [_debate_msg(m) for m in debate_messages],
        "global_report": global_report,
        "weighted": weighted,
        "news": news_results,
        "multi_tf": multi_tf_results,
        "notifications": notify_mgr.get_recent(20),
        "trader_stats": trader.get_stats(),
        "open_positions": [{
            "pair": pos.pair, "side": pos.side, "entry": pos.entry_price,
            "sl": pos.stop_loss, "tp": pos.take_profit,
            "trailing": pos.trailing_stop,
            "pnl": round(pos.pnl, 2),
            "strength": pos.signal_strength,
            "confluence": pos.confluence,
        } for pos in trader.positions],
        "trade_history": [{
            "pair": t.pair, "side": t.side, "entry": t.entry_price,
            "exit": t.exit_price, "pnl": t.pnl, "result": t.result,
            "exit_reason": t.exit_reason, "strength": t.signal_strength,
        } for t in trader.history[-30:]],
        "trade_events": trade_events,
    }

    return jsonify(last_results)


@app.route("/api/staff")
def api_staff():
    depts = get_all_departments()
    return jsonify({"staff": depts, "total": len(ANALYSTS)})


@app.route("/api/debate")
def api_debate():
    if not last_results:
        return jsonify({"debate": []})
    return jsonify({"debate": last_results.get("debate", [])})


@app.route("/api/weights")
def api_weights():
    return jsonify(get_all_weights())


@app.route("/api/news")
def api_news():
    prices = get_all_prices()
    if not prices:
        return jsonify({"error": "No prices"}), 500
    return jsonify(analyze_news_for_all_pairs(prices))


@app.route("/api/prices")
def api_prices():
    prices = get_all_prices()
    if not prices:
        return jsonify({"prices": []})
    price_dict = {p["name"]: p["price"] for p in prices}
    trader.update_pnl(price_dict)
    return jsonify({
        "prices": prices,
        "trader_stats": trader.get_stats(),
        "open_positions": [{
            "pair": pos.pair, "side": pos.side, "entry": pos.entry_price,
            "sl": pos.stop_loss, "tp": pos.take_profit,
            "trailing": pos.trailing_stop,
            "pnl": round(pos.pnl, 2),
            "strength": pos.signal_strength,
            "confluence": pos.confluence,
        } for pos in trader.positions],
    })


@app.route("/api/notifications")
def api_notifications():
    return jsonify({"notifications": notify_mgr.get_recent(50)})


@app.route("/api/positions")
def api_positions():
    return jsonify({
        "stats": trader.get_stats(),
        "open_positions": [{
            "pair": pos.pair, "side": pos.side, "entry": pos.entry_price,
            "sl": pos.stop_loss, "tp": pos.take_profit,
            "trailing": pos.trailing_stop,
            "pnl": round(pos.pnl, 2),
            "strength": pos.signal_strength,
            "confluence": pos.confluence,
            "entry_time": pos.entry_time,
        } for pos in trader.positions],
        "history": [{
            "pair": t.pair, "side": t.side, "entry": t.entry_price,
            "exit": t.exit_price, "pnl": t.pnl, "result": t.result,
            "exit_reason": t.exit_reason, "strength": t.signal_strength,
            "confluence": t.confluence,
            "entry_time": t.entry_time, "exit_time": t.exit_time,
        } for t in trader.history[-30:]],
    })


@app.route("/api/close_position", methods=["POST"])
def api_close_position():
    data = request.get_json() or {}
    pair = data.get("pair")
    if not pair:
        return jsonify({"error": "pair required"}), 400
    prices = get_all_prices()
    price_map = {p["name"]: p["price"] for p in prices}
    current = price_map.get(pair)
    if current is None:
        return jsonify({"error": f"No price for {pair}"}), 400
    pos = trader.close_position(pair, current)
    if pos:
        return jsonify({"closed": pos.pair, "pnl": round(pos.pnl, 2)})
    return jsonify({"error": "Position not found"}), 404


@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "ok",
        "staff": len(ANALYSTS),
        "departments": len(DEPARTMENTS_STRUCTURE),
        "pairs": len(FOREX_PAIRS),
        "timeframe": TIMEFRAME,
    })


def _report_summary(r):
    return {
        "id": r["analyst_id"],
        "name": r["analyst_name"],
        "department": r["department"],
        "is_head": r.get("is_head", False),
        "summary": r.get("summary", ""),
        "signal_count": len(r.get("signals", [])),
    }


def _debate_msg(m):
    return {
        "speaker": m.get("speaker", ""),
        "department": m.get("department", ""),
        "text": m.get("text", ""),
        "type": m.get("type", ""),
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
