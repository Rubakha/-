"""
Запуск бота с проверками. Заменяет run_bot.py.

    python start_bot.py

Отличия от прошлой версии: никого не убивает молча, не может погасить
сам себя, печатает всё сразу (важно для консоли PyCharm).
"""

import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
HERE = os.getcwd()


def p(text=""):
    print(text, flush=True)


def head(text):
    p()
    p(text)
    p("-" * 58)


# ── 1. чужие процессы ───────────────────────────────────────
head("ШАГ 1. Другие процессы бота")

# свой PID и всё дерево родителей — их трогать нельзя
safe = {os.getpid()}
try:
    safe.add(os.getppid())
except Exception:
    pass

found = []
if sys.platform == "win32":
    ps = ("Get-CimInstance Win32_Process | "
          "Where-Object { $_.CommandLine -like '*bot_best.py*' } | "
          "ForEach-Object { \"$($_.ProcessId)>$($_.ParentProcessId)\" }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=40)
        rows = r.stdout.strip().splitlines()
    except Exception as exc:
        rows = []
        p(f"опрос процессов не удался: {exc}")

    for row in rows:
        if ">" not in row:
            continue
        pid_txt, _, ppid_txt = row.strip().partition(">")
        try:
            pid, ppid = int(pid_txt), int(ppid_txt)
        except ValueError:
            continue
        if pid in safe or ppid in safe:
            continue
        found.append(pid)
else:
    try:
        out = subprocess.run(["pgrep", "-f", "bot_best.py"],
                             capture_output=True, text=True).stdout
        found = [int(x) for x in out.split() if int(x) not in safe]
    except Exception:
        found = []

if not found:
    p("Не найдено. Канал свободен.")
else:
    p(f"Найдено: {found}")
    for pid in found:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True, timeout=15)
            else:
                os.kill(pid, 9)
            p(f"  PID {pid} погашен")
        except Exception as exc:
            p(f"  PID {pid} погасить не вышло: {exc}")


# ── 2. версии файлов ────────────────────────────────────────
head("ШАГ 2. Версии файлов")

MARKERS = {
    "bot_best.py": ["ai:selftest", "class FreeMode", "admin_free_mode_menu"],
    "ai_assistant.py": "def selftest"
}
stale = []

for fname, marker in MARKERS.items():
    if not os.path.exists(fname):
        p(f"[НЕТ] {fname} — нет в папке")
        stale.append(fname)
        continue
    with open(fname, encoding="utf-8", errors="replace") as f:
        body = f.read()
    kb = len(body.encode("utf-8", "replace")) / 1024
    
    # Для bot_best.py проверяем любой из маркеров
    if isinstance(marker, list):
        found = any(m in body for m in marker)
    else:
        found = marker in body
    
    if found:
        p(f"[ OK] {fname} — новая версия, {kb:.0f} КБ")
    else:
        p(f"[НЕТ] {fname} — СТАРАЯ версия, {kb:.0f} КБ")
        stale.append(fname)

if stale:
    p()
    p("Запуск отменён — в папке старые файлы:")
    for f in stale:
        p(f"  {f}")
    p()
    p(f"Замени их и запусти снова. Папка:")
    p(f"  {HERE}")
    sys.exit(1)

if os.path.isdir("__pycache__"):
    import shutil
    shutil.rmtree("__pycache__", ignore_errors=True)
    p("[ OK] __pycache__ очищен")

# ── 3. ключ и библиотека ────────────────────────────────────
head("ШАГ 3. Ключ и библиотека")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    p("[НЕТ] python-dotenv не установлен:")
    p(f'      "{sys.executable}" -m pip install python-dotenv')
    sys.exit(1)

key = os.getenv("ANTHROPIC_API_KEY", "").strip()
p(f"[{' OK' if key else 'НЕТ'}] ключ в окружении"
  + (f", длина {len(key)}" if key else " отсутствует"))

try:
    import anthropic
    p(f"[ OK] anthropic {getattr(anthropic, '__version__', '?')}")
except ImportError:
    p("[НЕТ] anthropic не установлен в этом Python:")
    p(f'      "{sys.executable}" -m pip install anthropic')
    sys.exit(1)

import ai_assistant as AI

if AI.available():
    p("[ OK] AI.available() = True")
else:
    p("[НЕТ] AI.available() = False")
    p(f"      причина: {AI.why_unavailable()}")
    p()
    p("Запуск отменён: помощник всё равно был бы выключен.")
    sys.exit(1)

# ── 4. запуск ───────────────────────────────────────────────
head("ШАГ 4. Запуск бота")
p("Окно не закрывай. Остановка — Ctrl+C.")
p()

with open("bot_best.py", encoding="utf-8") as f:
    src = f.read()

sys.argv = ["bot_best.py"]
exec(compile(src, "bot_best.py", "exec"),
     {"__name__": "__main__", "__file__": "bot_best.py"})
