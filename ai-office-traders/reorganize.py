import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))

dirs = ["core", "data", "llm", "it", "utils", "scripts", "logs"]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

moves = {
    "core": ["config.py", "staff.py", "staff_config.json", "analyst_engine.py", "trader.py", "debate.py"],
    "data": ["market_data.py", "m15_data.py", "multi_tf.py", "news.py", "technical_analysis.py", "adaptive_weights.py"],
    "llm": ["llm_client.py"],
    "it": ["it_monitor_IT.py", "it_errors_IT.py", "it_performance_IT.py", "it_review_IT.py", "it_tests_IT.py", "it_notifications_IT.py"],
    "utils": ["notifications.py", "show_staff.py"],
    "scripts": ["run.bat", "install.bat", "web.bat", "test_python.bat"],
    "logs": ["it_log.md", "it_notifications.json", "trade_history.json", "debate_history.json", "debate_memory.json"],
}

for folder, files in moves.items():
    for f in files:
        src = os.path.join(BASE, f)
        dst = os.path.join(BASE, folder, f)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"  {f} -> {folder}/")

for f in ["table.csv", "free_models.txt", "list_models.py", "output.txt"]:
    src = os.path.join(BASE, f)
    if os.path.exists(src):
        os.remove(src)
        print(f"  Удалён: {f}")

print("\nГотово! Структура:")
for d in ["", "core/", "data/", "llm/", "it/", "utils/", "scripts/", "logs/", "templates/", "static/"]:
    path = os.path.join(BASE, d)
    if os.path.exists(path):
        files = os.listdir(path)
        print(f"  {d or '.'}: {len(files)} файлов")
