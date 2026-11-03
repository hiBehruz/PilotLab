#!/usr/bin/env python3
"""Сколько стоил прогон и соблюдались ли правила — разбор логов сессии Claude Code
(контексты, роли, рост контекста).

  measure-run.py <путь проекта> [часть id сессии]
"""
import glob
import json
import os
import re
import sys
from datetime import datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

TESTS_CMD = ("pytest", "npm test", "go test", "cargo test", "unittest")
EDIT_TOOLS = ("Edit", "Write", "NotebookEdit")
# Порядок проверки важен: «повторное ревью» должно сработать раньше, чем «правки» в ремонте.
ROLE_ORDER = ("ревью*", "ремонт", "ревью", "приёмка", "память", "разведка", "исполнитель")
ROLE_WORDS = {
    "ревью*": [r"повторн\S*\s+ревью", "re-review"],
    "ремонт": [r"\bfix", "repair", "доработка", "дозапрос", "правки", "ремонт"],
    "ревью": ["craft", "ремесл", "рецензент", "review", "ревью"],
    "приёмка": [r"\bg2\b", "coverage", "покрыт", "blind", "слеп"],
    "память": [r"agents\.md", r"claude\.md", r"\badr\b", "memory", "памят"],
    "разведка": ["notes", "explor", "развед"],
    "исполнитель": [r"^t?\d{2}\b", "executor", "исполн", "ticket", "таск"],
}
ROLE_RX = {name: re.compile("|".join(words), re.I) for name, words in ROLE_WORDS.items()}
RULE = "-" * 88


def when(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def looks_like_test(target):
    name = os.path.basename(target)
    in_test_dir = any(part in target for part in ("/test/", "/tests/"))
    return in_test_dir or ".test." in name or name.startswith("test_")


def measure(path):
    stamps, calls, tools = [], {}, {}
    tests = {"runs": 0, "test_edits": 0, "code_edits": 0}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            t = when(row.get("timestamp"))
            if t is not None:
                stamps.append(t)
            msg = row.get("message") if isinstance(row.get("message"), dict) else {}
            if (msg.get("role") or row.get("type")) != "assistant":
                continue
            if msg.get("usage"):
                calls[msg.get("id") or id(row)] = msg["usage"]  # у вызова считается последний usage
            for item in msg.get("content") or []:
                if not isinstance(item, dict) or item.get("type") != "tool_use":
                    continue
                name, inp = item.get("name"), item.get("input") or {}
                tools[name] = tools.get(name, 0) + 1
                if name == "Bash" and any(k in str(inp.get("command", "")) for k in TESTS_CMD):
                    tests["runs"] += 1
                elif name in EDIT_TOOLS:
                    target = str(inp.get("file_path") or inp.get("notebook_path") or "")
                    tests["test_edits" if looks_like_test(target) else "code_edits"] += 1
    out = write = read = cold = 0
    sizes = []
    for u in calls.values():
        o, w, r = (u.get(k) or 0 for k in ("output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        out, write, read = out + o, write + w, read + r
        cold += w > 20000
        size = r + w + (u.get("input_tokens") or 0)
        if size > 0:
            sizes.append(size)
    stamps.sort()
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    return {"steps": len(sizes), "avg": sum(sizes) / len(sizes) if sizes else 0, "max": max(sizes, default=0),
            "over": sum(s > 120000 for s in sizes), "out": out, "write": write, "read": read, "cold": cold,
            "norm": 5 * out + 1.25 * write + 0.1 * read,  # относительные единицы, не деньги
            "active": sum(g for g in gaps if g <= 300), "idle": sum(g for g in gaps if g > 300),
            "test_edits": tests["test_edits"], "code_edits": tests["code_edits"], "test_runs": tests["runs"],
            "tools": tools}


def role(label):
    if label == "Оркестратор":
        return "оркестратор"
    for name in ROLE_ORDER:
        if ROLE_RX[name].search(label):
            return name.rstrip("*")
    return "прочее"


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "—"


def short(labels, n=24):
    return ", ".join(l[:n] for l in labels[:4])


def main(argv):
    if not argv:
        sys.exit(__doc__)
    project = os.path.abspath(os.path.expanduser(argv[0]))
    logs = os.path.join(os.path.expanduser("~/.claude/projects"),
                        "".join("-" if c.isascii() and not c.isalnum() else c for c in project))
    if not os.path.isdir(logs):
        sys.exit(f"нет логов: {logs}")
    sessions = sorted(glob.glob(os.path.join(logs, "*.jsonl")))
    if not sessions:
        sys.exit(f"нет сессий в {logs}")

    def subs(path):
        return sorted(glob.glob(os.path.join(path[:-6], "subagents", "*.jsonl")))

    if len(argv) > 1:
        main_log = next((p for p in sessions if argv[1] in os.path.basename(p)), None)
        if not main_log:
            sys.exit("сессия не найдена")
    else:
        main_log = max(sessions, key=lambda p: (len(subs(p)), os.path.getsize(p)))
    sid = os.path.basename(main_log)[:-6]
    if len(sessions) > 1:
        print(f"сессий: {len(sessions)}, беру {sid[:8]} (сабагентов: {len(subs(main_log))}); "
              f"другую — вторым аргументом id сессии")

    contexts = [("Оркестратор", measure(main_log))]
    for p in subs(main_log):
        label = os.path.basename(p)[:-6]
        try:
            with open(p[:-6] + ".meta.json", encoding="utf-8") as f:
                label = json.load(f).get("description") or label
        except (OSError, ValueError, AttributeError):
            pass
        contexts.append((label, measure(p)))
    contexts.sort(key=lambda c: -c[1]["norm"])
    total = sum(m["norm"] for _, m in contexts) or 1

    print(f"\nПрогон: {project} · контекстов: {len(contexts)}\n{RULE}")
    print(f"{'Контекст':37} {'шаги':>6} {'ср.K':>7} {'макс.K':>7} {'>120K':>6} {'норма M':>9} {'доля':>6}")
    print(RULE)
    for label, m in contexts:
        print(f"{label[:37]:37} {m['steps']:>6} {m['avg'] / 1000:>7.0f} {m['max'] / 1000:>7.0f} {m['over']:>6} "
              f"{m['norm'] / 1e6:>9.2f} {pct(m['norm'], total):>6}")
    print(RULE)
    print(f"{'ИТОГО':37} {sum(m['steps'] for _, m in contexts):>6} {'':>7} {'':>7} {'':>6} {total / 1e6:>9.2f}")

    by_role = {}
    for label, m in contexts:
        r = by_role.setdefault(role(label), [0, 0])
        r[0] += 1
        r[1] += m["norm"]
    print("\nПо ролям:")
    for name, (n, norm) in sorted(by_role.items(), key=lambda x: -x[1][1]):
        print(f"  {name:14} контекстов {n:>3} · норма {norm / 1e6:>7.2f} M · {pct(norm, total)}")

    out, write, read = (sum(m[k] for _, m in contexts) for k in ("out", "write", "read"))
    parts = (("чтение кэша", 0.1 * read), ("запись кэша", 1.25 * write), ("генерация", 5 * out))
    print("\nИз чего цена:")
    for name, v in parts:
        share = v / total
        print(f"  {name:12} {share * 100:5.1f}% {'█' * round(share * 46)}")
    if out:
        print(f"  прочитано на токен ответа: {(read + write) / out:.0f}:1")

    print("\nПравила:")
    fat = [l for l, m in contexts if m["avg"] > 180000]
    print(f"  контекстов со средним > 180K: {len(fat)}" + (f" ({short(fat)})" if fat else ""))
    te, ce = (sum(m[k] for _, m in contexts) for k in ("test_edits", "code_edits"))
    print(f"  правок тестов: {te} ({pct(te, te + ce)}), правок кода: {ce} ({pct(ce, te + ce)})")
    print(f"  прогонов тестов: {sum(m['test_runs'] for _, m in contexts)}")
    stale = [l for l, m in contexts if m["read"] > 0 and m["write"] / m["read"] > 0.10]
    print(f"  протухший кэш (запись/чтение > 10%): {len(stale)}" + (f" ({short(stale)})" if stale else ""))

    execs = [(l, m) for l, m in contexts if role(l) == "исполнитель" and m["steps"] > 0]
    if execs:
        small = [l for l, m in execs if m["max"] < 150000]
        big = [l for l, m in execs if m["max"] > 450000]
        print(f"  исполнители недогружены (макс < 150K, кандидаты на слияние): {len(small)}"
              + (f" ({short(small)})" if small else ""))
        print(f"  исполнители перегружены (макс > 450K, стоило дробить): {len(big)}"
              + (f" ({short(big)})" if big else ""))

    act, idle = (sum(m[k] for _, m in contexts) for k in ("active", "idle"))
    if act or idle:
        print(f"\nВремя: активно {act / 60:.0f} мин, простой {idle / 60:.0f} мин, активно {pct(act, act + idle)}")


if __name__ == "__main__":
    main(sys.argv[1:])
