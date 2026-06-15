import time
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from config import FOREX_PAIRS, TIMEFRAME, ANALYSIS_INTERVAL_MINUTES
from market_data import get_all_prices
from staff import ANALYSTS, DEPARTMENTS_STRUCTURE, get_department_members, get_all_departments
from analyst_engine import analyst_work, department_head_report, global_meeting
from debate import run_debate, format_debate
from multi_tf import run_multi_tf_analysis, format_multi_tf
from news import analyze_news_for_all_pairs, format_news
from notifications import NotificationManager
from trader import Trader

console = Console()
notify_mgr = NotificationManager()
trader = Trader("AI Office Trader")


def display_prices(prices):
    table = Table(title=f"Forex Live [{TIMEFRAME}]", box=box.ROUNDED)
    table.add_column("Pair", style="cyan", width=10)
    table.add_column("Price", justify="right", width=10)
    table.add_column("Open", justify="right", width=10)
    table.add_column("High", justify="right", width=10)
    table.add_column("Low", justify="right", width=10)
    for p in prices:
        table.add_row(p["name"], f"{p['price']:.5f}", f"{p['open']:.5f}", f"{p['high']:.5f}", f"{p['low']:.5f}")
    console.print(table)


def display_analyst_reports(reports):
    table = Table(title="Отчёты аналитиков", box=box.ROUNDED, show_lines=True)
    table.add_column("#", width=3, justify="center")
    table.add_column("Имя", width=18, style="cyan")
    table.add_column("Отдел", width=18, style="yellow")
    table.add_column("Находки", width=60)

    for r in reports:
        findings = []
        for f in r["findings"]:
            parts = []
            for k, v in f.items():
                if k == "signal":
                    continue
                val = ", ".join(v) if isinstance(v, list) else str(v)
                parts.append(f"{k}: {val}")
            findings.append(" | ".join(parts))
        text = "\n".join(findings) if findings else "—"
        head_mark = " ★" if r.get("is_head") else ""
        table.add_row(str(r["analyst_id"]), r["analyst_name"] + head_mark, r["department"], text)

    console.print(table)


def display_dept_reports(dept_reports):
    table = Table(title="Отчёты начальников отделов (совещание)", box=box.HEAVY_EDGE, show_lines=True)
    table.add_column("Отдел", width=20, style="yellow")
    table.add_column("Начальник", width=18, style="cyan")
    table.add_column("Вердикт", width=12)
    table.add_column("BUY/SELL/NEUT", width=15, justify="center")
    table.add_column("Рекомендация", width=45)

    for r in dept_reports:
        color = "green" if r["verdict"] == "BULLISH" else "red" if r["verdict"] == "BEARISH" else "yellow"
        table.add_row(
            r["department"],
            r["head_name"],
            f"[{color}]{r['verdict']}[/]",
            f"{r['buy_signals']}/{r['sell_signals']}/{r['neutral_signals']}",
            r["recommendation"],
        )
    console.print(table)


def display_global_report(report):
    color = "green" if report["global_verdict"] == "BULLISH" else \
            "red" if report["global_verdict"] == "BEARISH" else "yellow"

    lines = [
        f"[bold {color}]ГЛОБАЛЬНЫЙ ВЕРДИКТ: {report['global_verdict']}[/]",
        f"",
        f"[bold]Сигналы:[/] BUY={report['total_buy_signals']} | SELL={report['total_sell_signals']} | NEUTRAL={report['total_neutral_signals']}",
        f"",
        f"[bold green]BULLISH отделы:[/] {', '.join(report['bullish_departments']) or '—'}",
        f"[bold red]BEARISH отделы:[/] {', '.join(report['bearish_departments']) or '—'}",
        f"[yellow]NEUTRAL отделы:[/] {', '.join(report['neutral_departments']) or '—'}",
        f"",
        f"[bold {color}]{report['action_recommendation']}[/]",
    ]

    console.print(Panel("\n".join(lines), title=f"СОВЕЩАНИЕ ОТДЕЛОВ @ {report['timestamp']}", border_style=color, width=90))


def run_cycle():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"\n[bold]{'='*60}[/bold]")
    console.print(f"[bold]  AI OFFICE — ЦИКЛ АНАЛИЗА @ {ts} | TF: {TIMEFRAME}[/bold]")
    console.print(f"[bold]{'='*60}[/bold]\n")

    console.print("[bold cyan]1. Получение цен...[/bold cyan]")
    prices = get_all_prices()
    if not prices:
        console.print("[red]Не удалось получить цены[/red]")
        return
    display_prices(prices)

    console.print("\n[bold cyan]2. Работа аналитиков (33 сотрудника)...[/bold cyan]")
    all_reports = []
    for analyst in ANALYSTS:
        report = analyst_work(analyst, prices)
        all_reports.append(report)
    display_analyst_reports(all_reports)

    console.print("\n[bold cyan]3. Сбор отчётов начальниками отделов...[/bold cyan]")
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

    display_dept_reports(dept_reports)

    console.print("\n[bold cyan]4. Дебаты между аналитиками...[/bold cyan]")
    debate_messages = run_debate(all_reports)
    console.print(Panel(format_debate(debate_messages), title="ДИСКУССИЯ АНАЛИТИКОВ", border_style="magenta", width=100))

    console.print("\n[bold cyan]5. Multi-Timeframe анализ (D1/H4/M15)...[/bold cyan]")
    multi_tf_results = []
    try:
        multi_tf_results = run_multi_tf_analysis(prices)
        console.print(Panel(format_multi_tf(multi_tf_results), title="MULTI-TF ANALYSIS", border_style="cyan", width=100))
    except Exception as e:
        console.print(f"[yellow]Multi-TF: {e}[/yellow]")

    console.print("\n[bold cyan]6. Новостной анализ...[/bold cyan]")
    news_results = []
    try:
        news_results = analyze_news_for_all_pairs(prices)
        console.print(Panel(format_news(news_results), title="NEWS ANALYSIS", border_style="yellow", width=100))
    except Exception as e:
        console.print(f"[yellow]News: {e}[/yellow]")

    console.print("\n[bold cyan]7. Глобальное совещание руководителей...[/bold cyan]")
    global_report = global_meeting(dept_reports)
    display_global_report(global_report)

    console.print("\n[bold cyan]8. Папер-трейдинг...[/bold cyan]")
    try:
        decisions = trader.evaluate_signals(all_reports, global_report, dept_reports, news_results, multi_tf_results)
        if decisions:
            for d in decisions:
                console.print(f"  [bold]Сигнал: {d['direction']} {d['pair']} (strength={d['strength']}) — {', '.join(d['confluence'][:3])}[/bold]")
        else:
            console.print("  [dim]Нет сигналов достаточной силы для входа[/dim]")

        trade_events = trader.process_decisions(decisions, prices)
        for event in trade_events:
            if "OPEN" in event:
                console.print(f"  [green]{event}[/green]")
            elif "SL" in event or "TRAILING" in event:
                console.print(f"  [red]{event}[/red]")
            elif "TP" in event:
                console.print(f"  [bold green]{event}[/bold green]")
            else:
                console.print(f"  [yellow]{event}[/yellow]")
    except Exception as e:
        console.print(f"  [red]Trader error: {e}[/red]")

    stats = trader.get_stats()
    pnl_color = "green" if stats["total_pnl"] >= 0 else "red"
    console.print(f"  Баланс: ${stats['balance']:.2f} | Equity: ${stats['equity']:.2f} | "
                  f"[{pnl_color}]PnL: ${stats['total_pnl']:+.2f}[/] | "
                  f"Win Rate: {stats['win_rate']}% | PF: {stats['profit_factor']} | "
                  f"Max DD: {stats['drawdown_pct']}% | "
                  f"Открытых: {stats['open_positions']}/{trader.max_positions}")

    if trader.positions:
        pos_table = Table(title="Открытые позиции", box=box.ROUNDED)
        pos_table.add_column("Pair", width=10, style="cyan")
        pos_table.add_column("Side", width=5)
        pos_table.add_column("Entry", width=10)
        pos_table.add_column("SL", width=10, style="red")
        pos_table.add_column("TP", width=10, style="green")
        pos_table.add_column("Trail", width=10, style="yellow")
        pos_table.add_column("Str", width=4, justify="center")
        pos_table.add_column("PnL", width=8)
        for pos in trader.positions:
            side_color = "green" if pos.side == "BUY" else "red"
            pnl_c = "green" if pos.pnl >= 0 else "red"
            pos_table.add_row(
                pos.pair, f"[{side_color}]{pos.side}[/]",
                f"{pos.entry_price:.5f}", f"{pos.stop_loss:.5f}",
                f"{pos.take_profit:.5f}", f"{pos.trailing_stop:.5f}",
                str(pos.signal_strength), f"[{pnl_c}]{pos.pnl:+.2f}[/]"
            )
        console.print(pos_table)

    console.print("\n[bold cyan]9. Уведомления...[/bold cyan]")
    for r in all_reports:
        for sig in r.get("signals", []):
            pair = sig.get("pair", "")
            for f in r.get("findings", []):
                if f.get("pair") == pair:
                    notify_mgr.check_signal_alerts(pair, f)

    recent = notify_mgr.get_recent(5)
    if recent:
        for n in recent:
            icon = {"info": "[i]", "warning": "[!]", "critical": "[!!]"}.get(n["severity"], "[*]")
            console.print(f"  {icon} {n['pair']}: {n['message']}")
    else:
        console.print("  [dim]Нет новых уведомлений[/dim]")

    if trader.history:
        console.print("\n[bold cyan]10. Последние сделки...[/bold cyan]")
        hist_table = Table(title="История", box=box.SIMPLE, show_lines=False)
        hist_table.add_column("Pair", width=10, style="cyan")
        hist_table.add_column("Side", width=5)
        hist_table.add_column("Entry", width=10)
        hist_table.add_column("Exit", width=10)
        hist_table.add_column("Reason", width=8)
        hist_table.add_column("PnL", width=8)
        hist_table.add_column("Result", width=6)
        for t in trader.history[-5:]:
            side_color = "green" if t.side == "BUY" else "red"
            pnl_c = "green" if t.result == "WIN" else "red"
            hist_table.add_row(
                t.pair, f"[{side_color}]{t.side}[/]",
                f"{t.entry_price:.5f}", f"{t.exit_price:.5f}",
                t.exit_reason, f"[{pnl_c}]{t.pnl:+.2f}[/]",
                f"[{pnl_c}]{t.result}[/]"
            )
        console.print(hist_table)

    console.print(f"\n[dim]Следующий цикл через {ANALYSIS_INTERVAL_MINUTES} мин...[/dim]")


def show_staff():
    depts = get_all_departments()
    console.print(Panel.fit(
        f"[bold green]AI Office — Штат[/bold green]\n"
        f"Сотрудников: {len(ANALYSTS)} | Отделов: {len(depts)}",
        border_style="green"
    ))

    table = Table(title="Штатное расписание", box=box.ROUNDED, show_lines=True)
    table.add_column("Отдел", width=22, style="yellow")
    table.add_column("Начальник", width=18, style="cyan")
    table.add_column("Сотрудники", width=45)
    table.add_column("Кол-во", width=5, justify="center")

    for dept, info in depts.items():
        members = ", ".join(info["members"])
        table.add_row(dept, info["head"], members, str(info["count"]))

    console.print(table)


def show_help():
    console.print(Panel.fit(
        "[bold]AI Office — Команды:[/]\n\n"
        "  python main.py          — Запуск цикла (непрерывно)\n"
        "  python main.py --once   — Один цикл\n"
        "  python main.py --staff  — Список сотрудников\n"
        "  python main.py --web    — Запуск веб-интерфейса (port 5000)\n"
        "  python main.py --stats  — Статистика трейдера\n"
        "  python main.py --history — История сделок\n"
        "  python main.py --reset  — Сброс баланса и истории\n"
        "  python main.py --help   — Справка",
        title="Помощь", border_style="blue"
    ))


def show_trader_stats():
    stats = trader.get_stats()
    color = "green" if stats["total_pnl"] >= 0 else "red"
    lines = [
        f"[bold {color}]Баланс: ${stats['balance']:.2f}[/]",
        f"Equity: ${stats['equity']:.2f}",
        f"[bold {color}]PnL: ${stats['total_pnl']:+.2f} ({stats['roi']:+.2f}%)[/]",
        f"",
        f"Всего сделок: {stats['total_trades']}",
        f"WIN: {stats['wins']} | LOSS: {stats['losses']}",
        f"Win Rate: {stats['win_rate']}%",
        f"Profit Factor: {stats['profit_factor']}",
        f"Средний WIN: ${stats['avg_win']:.2f} | Средний LOSS: ${stats['avg_loss']:.2f}",
        f"Макс. PnL: ${stats['max_pnl']:.2f} | Макс. Loss: ${stats['max_loss']:.2f}",
        f"Drawdown: {stats['drawdown_pct']:.2f}% (max: {stats['max_drawdown_pct']}%)",
        f"Открытых позиций: {stats['open_positions']}/{trader.max_positions}",
    ]
    console.print(Panel("\n".join(lines), title=f"TRADER: {stats['name']}", border_style=color, width=70))

    if trader.positions:
        pos_table = Table(title="Открытые позиции", box=box.ROUNDED)
        pos_table.add_column("Pair", width=10, style="cyan")
        pos_table.add_column("Side", width=5)
        pos_table.add_column("Entry", width=10)
        pos_table.add_column("SL", width=10, style="red")
        pos_table.add_column("TP", width=10, style="green")
        pos_table.add_column("Trail", width=10, style="yellow")
        pos_table.add_column("Str", width=4, justify="center")
        pos_table.add_column("PnL", width=8)
        for pos in trader.positions:
            side_color = "green" if pos.side == "BUY" else "red"
            pnl_c = "green" if pos.pnl >= 0 else "red"
            pos_table.add_row(
                pos.pair, f"[{side_color}]{pos.side}[/]",
                f"{pos.entry_price:.5f}", f"{pos.stop_loss:.5f}",
                f"{pos.take_profit:.5f}", f"{pos.trailing_stop:.5f}",
                str(pos.signal_strength), f"[{pnl_c}]{pos.pnl:+.2f}[/]"
            )
        console.print(pos_table)


def show_trade_history():
    if not trader.history:
        console.print("[yellow]Нет сделок в истории[/yellow]")
        return
    table = Table(title="История сделок", box=box.ROUNDED, show_lines=True)
    table.add_column("Pair", width=10, style="cyan")
    table.add_column("Side", width=5)
    table.add_column("Entry", width=10)
    table.add_column("Exit", width=10)
    table.add_column("Reason", width=8)
    table.add_column("Str", width=4, justify="center")
    table.add_column("PnL", width=8)
    table.add_column("Result", width=6)
    table.add_column("Confluence", width=30)
    for t in trader.history[-20:]:
        side_color = "green" if t.side == "BUY" else "red"
        pnl_c = "green" if t.result == "WIN" else "red"
        conf = ", ".join(t.confluence[:3]) if t.confluence else "—"
        table.add_row(
            t.pair, f"[{side_color}]{t.side}[/]",
            f"{t.entry_price:.5f}", f"{t.exit_price:.5f}",
            t.exit_reason, str(t.signal_strength),
            f"[{pnl_c}]{t.pnl:+.2f}[/]", f"[{pnl_c}]{t.result}[/]",
            conf
        )
    console.print(table)


def run_forever():
    console.print(Panel.fit(
        f"[bold green]AI OFFICE — Forex Analytics[/bold green]\n"
        f"Pairs: {len(FOREX_PAIRS)} | Staff: {len(ANALYSTS)} | TF: {TIMEFRAME} | Interval: {ANALYSIS_INTERVAL_MINUTES}m",
        border_style="green"
    ))

    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            console.print("\n[yellow]Завершение...[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Ошибка: {e}[/red]")

        try:
            time.sleep(ANALYSIS_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            console.print("\n[yellow]Завершение...[/yellow]")
            break


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        show_help()
    elif "--staff" in args:
        show_staff()
    elif "--stats" in args:
        show_trader_stats()
    elif "--history" in args:
        show_trade_history()
    elif "--reset" in args:
        from trader import TRADES_FILE
        if os.path.exists(TRADES_FILE):
            os.remove(TRADES_FILE)
        console.print("[green]Баланс и история сброшены[/green]")
    elif "--once" in args:
        run_cycle()
    elif "--web" in args:
        from web_app import app
        print("[bold green]Запуск веб-сервера на http://localhost:5000[/]")
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        run_forever()
