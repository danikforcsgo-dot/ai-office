from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from staff import ANALYSTS, DEPARTMENTS_STRUCTURE, get_all_departments


console = Console()


def show_all():
    depts = get_all_departments()
    console.print(Panel.fit(
        "[bold green]AI Office — Штат аналитиков[/bold green]\n"
        f"Всего сотрудников: {len(ANALYSTS)} | Отделов: {len(depts)}",
        border_style="green"
    ))

    table = Table(title="Штатное расписание", box=box.ROUNDED, show_lines=True)
    table.add_column("#", width=3, justify="center")
    table.add_column("Имя", width=20, style="cyan")
    table.add_column("Должность", width=32)
    table.add_column("Отдел", width=22, style="yellow")
    table.add_column("Обязанности", width=55)
    table.add_column("Инструменты", width=30, style="dim")

    for a in ANALYSTS:
        resp = "\n".join(f"• {r}" for r in a.responsibilities)
        tools = ", ".join(a.tools)
        table.add_row(str(a.id), a.name, a.role, a.department, resp, tools)

    console.print(table)


def show_departments():
    depts = get_all_departments()
    console.print(Panel.fit("[bold]Отделы AI Office[/bold]", border_style="blue"))
    for dept, info in depts.items():
        console.print(f"\n[bold yellow]{dept}[/bold yellow] ({info['count']} чел.):")
        console.print(f"  [cyan]Начальник: {info['head']}[/cyan]")
        for m in info["members"]:
            console.print(f"  {m}")


if __name__ == "__main__":
    import sys
    if "--dept" in sys.argv:
        show_departments()
    else:
        show_all()
