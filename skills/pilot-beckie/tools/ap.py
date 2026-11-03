#!/usr/bin/env python3
"""Учёт прогона Pilot by Beckie: state.js, снимок в dashboard.html, локальный сервер.

Живёт в <проект>/.pilot-beckie/ap.py и вызывается оттуда, по одной команде на событие сборки.
Только стандартная библиотека.
"""
import sys
import os
import re
import json
import math
import glob
import time
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from urllib import request as urlreq

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

USAGE = """Учёт прогона Pilot by Beckie — одна команда на одно событие сборки.

Начать:
  ap.py init --slug repair-bot [--title Бот] [--mode semi] [--depth normal] [--force]
        [--skill-dir DIR] [--brief-file F] [--memory-file F] [--memory-owner NAME]
Этапы и план:
  ap.py stage spec [start|done|skip|fail] [--note причина]
  ap.py tickets                       опубликовать tickets/*.md
  ap.py check-plan                    гейт G3: каждое требование ведёт в таск
  ap.py set tier=T2 baseCommit=abc1234
Сборка:
  ap.py ticket 01 02 start            (также review, repair, done, fail, retry, reset)
        [--note …] [--tests 34/0] [--commit SHA] [--placeholder R05]
  ap.py tests 34/0
  ap.py add report|concerns|additions|debt.emptyEnv|debt.placeholders|debt.assumptions ТЕКСТ…
Проверки:
  ap.py coverage found=3 fixed=2 deferred=1 [--item "R07 — отложено"]…
  ap.py blind checked=4 matched=3 [--mismatch "R02 — не видно"]…
Ожидание пользователя:
  ap.py ask briefing|spec|plan|action|stop [--note …]
  ap.py answered
Конец и возврат:
  ap.py finish [--result "что сдано"]
  ap.py reopen
  ap.py commits                       коммиты сданных тасков ещё в истории?
  ap.py                               пересобрать снимок и поднять сервер

Флаги: --no-serve (сервер не трогать), --stop (погасить сервер),
       --check-update (есть ли новая версия), --help."""

BEGIN, END = "/*STATE-BEGIN*/", "/*STATE-END*/"
REPO = "hiBehruz/PilotLab"
REMOTE_SKILL = f"https://raw.githubusercontent.com/{REPO}/main/skills/pilot-beckie/SKILL.md"
STOP_DELAY, BEATS_KEPT, LOG_KEPT, QUOTE_MAX, IDLE_CAP = 12, 2000, 300, 240, 45 * 60
HOST = "127.0.0.1"
WIN = os.name == "nt"

ORDER = ("preflight", "manifest", "briefing", "spec", "plan", "build", "review", "final")
RANK = {sid: n for n, sid in enumerate(ORDER)}
WAITS = ("briefing", "spec", "plan", "action", "stop")
ARTIFACT = {"plan": "tickets/*.md", "spec": "spec.md", "manifest": "manifest.md"}
STAGE_STATUS = {"start": "active", "done": "done", "skip": "skipped", "fail": "failed"}
# действие над таском → новый статус
ACTIONS = {"done": "done", "fail": "failed", "start": "in-progress", "retry": "in-progress",
           "review": "review", "repair": "repair", "reset": "pending"}
# статус таска → вид на странице
KIND = {"pending": "wait", "failed": "bad", "repair": "fix", "review": "rev", "in-progress": "now", "done": "done"}
MOVE_ON = set("finish reopen tickets ticket check-plan stage tests coverage blind".split())
LIST_KEYS = ("concerns", "additions", "report", "debt.placeholders", "debt.assumptions", "debt.emptyEnv")
OPEN_TICKET = ("in-progress", "review", "repair", "pending")


def _camel(status):
    head, *rest = status.split("-")
    return head + "".join(w.title() for w in rest)


# статус требования: вид на странице и флаги.
# L — живое (G3 требует таск), C — закрывается сдачей таска, W — странице нужна причина
_REQ_TABLE = """
C   open         open
LC  in-spec      work
LC  in-ticket    work
-   done         done
LW  placeholder  placeholder
W   deferred     deferred
W   dropped      dropped
"""
REQ = {}
for _row in _REQ_TABLE.split("\n"):
    if _row.strip():
        _flags, _status, _kind = _row.split()
        REQ[_status] = (_camel(_status), _kind, _flags.strip("-"))
COUNTERS = [c for c, _, _ in REQ.values()] + ["work"]


class Stop(Exception):
    """Отказ: команда не выполнена, ничего не записано."""


def set_root(path):
    global A, ROOT, STATE, PAGE, README, PID, LOG, GITIGNORE, _DIR_RE
    A = os.path.abspath(path)
    ROOT = os.path.dirname(A)
    STATE = os.path.join(A, "state.js")
    PAGE = os.path.join(A, "dashboard.html")
    README = os.path.join(A, "README.md")
    PID = os.path.join(A, "serve.pid")
    LOG = os.path.join(A, "serve.log")
    GITIGNORE = os.path.join(ROOT, ".gitignore")
    folder = os.path.normcase(os.path.normpath(A)).replace("\\", "/")
    _DIR_RE = re.compile(r'--directory\s+"?' + re.escape(folder) + r'"?(?:\s|$)')


set_root(os.path.dirname(os.path.abspath(__file__)))
_HTTP_RE = re.compile(r"-m\s+http\.server\b")
REQ_TOKEN = re.compile(r"[a-zA-Z]*[0-9]+[a-z]?(?:\.[0-9]+)?")
DEP_TOKEN = re.compile(r"[a-zA-Z]*[0-9]+[a-z]?")
ROW_ID = re.compile(r"[RGD]\d+[a-z]?")


# ---------- small helpers ----------

def now():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def ts(iso):
    if not isinstance(iso, str) or not iso:
        return None
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(iso).timestamp()
    except ValueError:
        return None


def sopt(opt, key):
    value = opt.get(key)
    return value if isinstance(value, str) and value else None


def slurp(path):
    return Path(path).read_text(encoding="utf-8")


def put_file(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def write_atomic(path, text):
    tmp = path + ".tmp"
    put_file(tmp, text)
    os.replace(tmp, path)


def git(*args):
    try:
        return subprocess.run(["git", *args], timeout=30, capture_output=True).returncode
    except Exception:
        return 1


def run_dir(state):
    folder = state.get("dir") or ""
    return os.path.join(A, folder) if folder else A


def parse_args(argv):
    """Позиционные + {опция: последнее значение}; все повторы — в opt['_multi']."""
    pos, opt, multi = [], {}, {}
    rest = list(argv)
    while rest:
        tok = rest.pop(0)
        if not tok.startswith("--"):
            pos.append(tok)
            continue
        name = tok[2:]
        value = rest.pop(0) if rest and not rest[0].startswith("--") else True
        opt[name] = value
        multi.setdefault(name, []).append(value)
    opt["_multi"] = multi
    return pos, opt


# ---------- state file ----------

def read_state():
    if not os.path.exists(STATE):
        return None
    text = slurp(STATE)
    first_line = text.split("\n", 1)[0]
    offset = text.index("=") + 1 if "=" in first_line else 0
    body = text[offset:].strip().rstrip(";")
    try:
        return json.loads(body)
    except json.JSONDecodeError as err:
        line = err.lineno + text[:text.find(body, offset)].count("\n")  # номер строки в самом файле
        raise Stop(f"state.js не читается: строка {line}: {err.msg} — поправь эту строку или начни заново "
                   f"(ap.py init --force)")


def save(s):
    s["rev"] = 1 + (s.get("rev") or 0)
    write_atomic(STATE, "window.STATE =\n" + json.dumps(s, indent=2, ensure_ascii=False) + "\n")


def beat(s):
    beats = s.get("beats") or []
    stamp = s["updatedAt"]
    if stamp not in beats:
        beats.append(stamp)
    s["beats"] = beats[-BEATS_KEPT:]


def _meaningful(value):
    return value is not None and value != "" and value != []


def log(s, event, /, **extra):
    entry = {"t": s.get("updatedAt"), "k": event, **{name: val for name, val in extra.items() if _meaningful(val)}}
    s["log"] = ((s.get("log") or []) + [entry])[-LOG_KEPT:]


def close_wait(s):
    pending = s.get("waiting")
    if not pending:
        return
    closed = {"kind": pending.get("kind"), "from": pending.get("since"), "to": s["updatedAt"]}
    s["waits"] = (s.get("waits") or []) + [closed]
    s["waiting"] = None
    log(s, "answered", kind=closed["kind"])


def set_gate(s, gate, ok, **numbers):
    numbers = {name: val for name, val in numbers.items() if val is not None}
    gates = s.get("gates") or {}
    gates[gate] = {"ok": ok, "at": s["updatedAt"], **numbers}
    s["gates"] = gates
    log(s, "gate", g=gate, ok=ok, **numbers)


def norm_stages(s):
    known = {}
    for item in s.get("stages") or []:
        if isinstance(item, dict):
            known[item.get("id")] = item
    s["stages"] = [known.get(sid, {"id": sid, "status": "pending"}) for sid in ORDER]


def stage(s, sid):
    return s["stages"][RANK[sid]]


def move_stage(st, act, t, note=None):
    if act == "reset":
        st["status"] = "pending"
        for key in ("startedAt", "finishedAt", "note"):
            st.pop(key, None)
        return
    st["status"] = STAGE_STATUS[act]
    st["startedAt"] = st.get("startedAt") or t
    if act != "start":
        st["finishedAt"] = t
    else:
        st.pop("finishedAt", None)
    if isinstance(note, str) and note:
        st["note"] = note


# ---------- manifest ----------

def cells(line):
    return re.split(r"(?<!\\)\|", line.strip().strip("|"))


def clean_id(cell):
    return cell.strip().strip("`*")


def plain(cell):
    out = cell.replace("\\|", "|")
    out = re.sub(r"[*`]", "", out).strip()
    if len(out) > QUOTE_MAX:
        out = out[:QUOTE_MAX - 1].rstrip() + "…"
    return out


def manifest_path(s):
    return os.path.join(run_dir(s), "manifest.md")


def manifest_rows(s):
    """Строки-требования манифеста или None, если файла нет."""
    try:
        text = slurp(manifest_path(s))
    except OSError:
        return None
    found = []
    for raw in text.splitlines():
        parts = cells(raw)
        if len(parts) < 3 or not ROW_ID.fullmatch(clean_id(parts[0])):
            continue
        words = parts[2].strip().strip("`*").split()
        status = words[0].strip("`*").lower() if words else ""
        found.append({"id": clean_id(parts[0]), "text": plain(parts[1]), "status": status or "open",
                      "why": plain(parts[3]) if len(parts) > 3 else ""})
    return found


def merge_where(cur, where):
    if cur in ("", "—", "-"):
        return where
    if where in cur:
        return cur
    return f"{cur} → {where}"


def update_manifest(s, changes):
    """changes: {id: (status, where)} → список изменённых id."""
    path = manifest_path(s)
    try:
        lines = slurp(path).split("\n")
    except OSError:
        return []
    touched = []
    for n, original in enumerate(lines):
        if original.lstrip()[:1] != "|":
            continue
        parts = cells(original)
        rid = clean_id(parts[0])
        if rid not in changes or len(parts) < 3:
            continue
        status, where = changes[rid]
        parts[2] = f" {status} "
        if where and len(parts) >= 5:
            parts[4] = f" {merge_where(parts[4].strip(), where)} "
        rebuilt = "|" + "|".join(parts) + "|"
        if rebuilt != original:
            lines[n] = rebuilt
            touched.append(rid)
    if touched:
        write_atomic(path, "\n".join(lines))
    return touched


def req(status):
    return REQ.get(status) or REQ["open"]


def recount(s):
    rows = manifest_rows(s)
    if rows is None:
        return []
    statuses = ", ".join(REQ)
    warnings = []
    for row in rows:
        if row["status"] not in REQ:
            warnings.append(f"! {row['id']}: статуса «{row['status']}» нет ({statuses}) — "
                            f"считаю открытым, поправь в manifest.md")
    counts = {name: 0 for name in COUNTERS}
    req_list = []
    for row in rows:
        if row["id"].startswith("D"):  # D — ограничения, не требования
            continue
        counter, kind, flags = req(row["status"])
        counts[counter] += 1
        if kind == "work":
            counts["work"] += 1
        item = {key: row[key] for key in ("id", "text", "status")}
        item["kind"] = kind
        if "W" in flags and row["why"] not in ("", "—", "-"):
            item["why"] = row["why"]
        req_list.append(item)
    s["requirements"] = {"total": len(req_list), **counts}
    s["reqList"] = req_list
    return warnings


# ---------- tickets ----------

def reqs_of(tk):
    return sorted({entry.split(".")[0] for entry in tk.get("requirements") or []})


def ticket_title(lines):
    heading = next((ln for ln in lines if ln.startswith("# ")), None)
    if heading is None:
        return ""
    m = re.match(r"#\s*\w+\s*[—–-]\s*(.*)", heading)
    if not m:
        return heading
    return m.group(1).strip() or heading[2:].strip()


def ticket_fields(lines):
    fields = {}
    for ln in lines:
        m = re.match(r"\*\*([^*]+?)\s*:?\s*\*\*\s*:?\s*(.*)$", ln)
        if m:
            fields[m.group(1).strip().lower()] = m.group(2).strip()
    return fields


def parse_ticket(path):
    name = os.path.basename(path)
    lines = [ln.strip() for ln in slurp(path).splitlines()]
    fields = ticket_fields(lines)

    def pick(ru, en):  # русское поле главнее, даже пустое
        return fields[ru] if ru in fields else fields.get(en)

    lead = re.match(r"(\w+?)[-_.]", name)
    wave_digits = re.search(r"\d+", pick("волна", "wave") or "")
    return {"id": lead.group(1) if lead else name[:2],
            "title": ticket_title(lines),
            "requirements": REQ_TOKEN.findall(pick("требования", "requirements") or ""),
            "blockedBy": DEP_TOKEN.findall(pick("зависит от", "blocked by") or ""),
            "wave": None if wave_digits is None else int(wave_digits.group()),
            "zone": re.findall(r"`([^`]*)`", pick("зона", "zone") or ""),
            "review": pick("ревью", "review") or None,
            "model": pick("модель", "model") or None}


def norm_dep(ref, known):
    if ref in known:
        return ref
    m = re.fullmatch(r"[Tt]?(\d+)", ref)
    return ref if m is None else f"{int(m.group(1)):02d}"


def publish(s):
    files = sorted(glob.glob(os.path.join(run_dir(s), "tickets", "*.md")))
    if not files:
        return f"нет файлов в {s.get('dir')}/tickets/"
    previous = {}
    for tk in s.get("tickets") or []:
        previous[tk.get("id")] = tk
    published = []
    for path in files:
        fresh = parse_ticket(path)
        merged = dict(previous.get(fresh["id"], {}))  # прогресс из прошлой публикации,
        merged.update(fresh)                            # план — из файла
        for key, default in (("status", "pending"), ("retries", 0), ("repairs", 0)):
            if merged.get(key) is None:
                merged[key] = default
        published.append(merged)
    known = {tk["id"] for tk in published}
    for tk in published:
        tk["blockedBy"] = [norm_dep(ref, known) for ref in tk["blockedBy"]]
    s["tickets"] = published

    status_of = {row["id"]: row["status"] for row in manifest_rows(s) or []}
    holders = {}
    for tk in published:
        for rid in reqs_of(tk):
            holders.setdefault(rid, []).append(f"T{tk['id']}")
    changes = {}
    for rid, names in holders.items():
        if status_of.get(rid) == "in-spec":
            changes[rid] = ("in-ticket", ", ".join(names))
    moved = update_manifest(s, changes)
    note = f"тасков опубликовано: {len(published)}"
    return note + f" · в манифесте in-ticket: {len(moved)}" if moved else note


def zones_clash(za, zb):
    a, b = za.rstrip("/") + "/", zb.rstrip("/") + "/"
    return a.startswith(b) or b.startswith(a)


def plan_problems(rows, tickets):
    known = {tk["id"] for tk in tickets}
    in_manifest = {row["id"] for row in rows}
    covered = set()
    for tk in tickets:
        covered.update(reqs_of(tk))
    problems = []
    for row in rows:
        live = "L" in req(row["status"])[2]
        if live and not row["id"].startswith("D") and row["id"] not in covered:
            problems.append(f"требование {row['id']} ({row['status']}) не попало ни в один таск")
    for tk in tickets:
        tid = tk["id"]
        if not tk.get("requirements"):
            problems.append(f"таск {tid} ни к чему не привязан — эту работу никто не просил")
        for rid in reqs_of(tk):
            if rid[:1] in "RGD" and rid not in in_manifest:
                problems.append(f"таск {tid} ссылается на {rid}, которого нет в манифесте")
        if not tk.get("zone"):
            problems.append(f"у таска {tid} нет зоны")
        if tk.get("wave") is None:
            problems.append(f"у таска {tid} нет волны")
        for ref in tk.get("blockedBy") or []:
            if ref not in known:
                problems.append(f"таск {tid} зависит от несуществующего {ref}")
    wave_of = {tk["id"]: tk.get("wave") for tk in tickets}
    for tk in tickets:
        earliest = 1 + max((wave_of.get(ref) or 0 for ref in tk.get("blockedBy") or []), default=0)
        wave = tk.get("wave")
        if wave is not None and wave < earliest:
            problems.append(f"таск {tk['id']} в волне {wave}, но его зависимости позволяют не раньше {earliest}")
    for i, first in enumerate(tickets):
        for second in tickets[i + 1:]:
            if first.get("wave") is None or first.get("wave") != second.get("wave"):
                continue
            for za in first.get("zone") or []:
                for zb in second.get("zone") or []:
                    if zones_clash(za, zb):
                        wider = za if len(za) >= len(zb) else zb
                        problems.append(f"таски {first['id']} и {second['id']} в одной волне пишут в {wider}")
    return problems


# ---------- README registry, .gitignore, renames ----------

README_HEAD = """# .pilot-beckie — как читать эту папку

- `dashboard.html` открывается сам и обновляется, пока идёт сборка; `index.html` — тот же файл.
- `<дата>-<проект>/` — одна сборка; `--wip` в имени значит «ещё в работе». Внутри: бриф с датой, `manifest.md`, `spec.md`, `tickets/`.
- `PROGRESS.md` — что осталось после последней сборки. Чтобы продолжить, скажи «продолжи Pilot by Beckie».
"""
RUNS_HEAD = "## Прогоны\n\n| Начат | Папка | Статус | Итог |\n|---|---|---|---|\n"


def readme_row(s, status, result=None):
    try:
        text = slurp(README)
    except OSError:
        text = README_HEAD + "\n" + RUNS_HEAD
    if text.find("## Прогоны") < 0:
        text = "\n\n".join([text.rstrip("\n"), RUNS_HEAD])
    folder = s.get("dir") or ""
    base = folder[:-len("--wip")] if folder.endswith("--wip") else folder
    marks = (f"`{base}`", f"`{base}--wip`")
    row = f"| {folder[:10]} | `{folder}` | {status} | {result or '—'} |"
    lines = text.splitlines()
    last = None
    for n, ln in enumerate(lines):
        if ln.startswith("|") and any(mark in ln for mark in marks):
            last = n
    if last is None:
        lines.append(row)
    else:
        lines[last] = row
    put_file(README, "\n".join(lines) + "\n")


def ensure_gitignore():
    try:
        text = slurp(GITIGNORE)
    except OSError:
        text = ""
    if any(ln.startswith(".pilot-beckie/serve.*") for ln in text.splitlines()):
        return
    sep = "\n" if text and not text.endswith("\n") else ""
    with open(GITIGNORE, "a", encoding="utf-8", newline="\n") as f:
        f.write(sep + ".pilot-beckie/serve.*\n")


def rename(src, dst):
    """git mv, чтобы git видел переименование; без git — обычный rename."""
    if git("-C", A, "mv", src, dst) != 0:
        try:
            Path(A, src).rename(Path(A, dst))
        except OSError:
            return False
    return True


# ---------- commands ----------

def fresh_state(opt, slug, t):
    s = {"version": 2, "slug": slug, "dir": f"{t[:10]}-{slug}--wip", "title": sopt(opt, "title") or slug}
    s["mode"] = sopt(opt, "mode") or "semi"
    s["depth"] = sopt(opt, "depth") or "normal"
    s["tier"] = None
    s["briefFile"] = sopt(opt, "brief-file")
    s["memoryFile"] = sopt(opt, "memory-file") or "AGENTS.md"
    s["memoryOwner"] = sopt(opt, "memory-owner") or "pilot-beckie"
    s["skillDir"] = sopt(opt, "skill-dir")
    s["baseCommit"] = None
    s.update(startedAt=t, updatedAt=t, finishedAt=None)
    s["stages"] = [{"id": sid, "status": "pending"} for sid in ORDER]
    s["stages"][0].update(status="active", startedAt=t)
    s["requirements"] = {name: 0 for name in ("total", "done", "inTicket", "inSpec", "placeholder",
                                              "deferred", "dropped")}
    s["tickets"], s["tests"] = [], None
    s["debt"] = {key: [] for key in ("placeholders", "assumptions", "emptyEnv")}
    s["additions"], s["concerns"] = [], []
    s["coverage"] = s["blind"] = None
    s["beats"], s["rev"] = [t], 0
    s["waiting"], s["waits"] = None, []
    s["log"], s["reqList"], s["gates"] = [], [], {}
    s["result"], s["timing"] = None, {}
    return s


def cmd_init(opt, notes):
    slug = sopt(opt, "slug")
    if not slug:
        raise Stop("нужен --slug: ap.py init --slug repair-bot")
    old = read_state()
    if old is not None:
        if not opt.get("force") and not old.get("finishedAt"):
            raise Stop(f"в {old.get('dir')} идёт прогон — это продолжение, а не новый запуск "
                       f"(новый поверх — ap.py init --force)")
        old_dir = old.get("dir")
        if old_dir and Path(A, old_dir).is_dir():
            archived = f"{old_dir}/state.js"
            if git("-C", A, "mv", "-f", "state.js", archived) != 0:
                Path(STATE).replace(Path(A, archived))
            notes.append(f"прошлый прогон в архиве: {archived}")
    s = fresh_state(opt, slug, now())
    log(s, "init")
    Path(run_dir(s), "tickets").mkdir(parents=True, exist_ok=True)
    save(s)
    ensure_gitignore()
    readme_row(s, "в работе")
    notes.append(f"папка прогона: .pilot-beckie/{s['dir']}")
    return s


def gate_g1(s):
    rows = [row for row in manifest_rows(s) or [] if not row["id"].startswith("D")]
    if rows:
        still_open = len([row for row in rows if req(row["status"])[1] == "open"])
        set_gate(s, "G1", still_open == 0, open=still_open, total=len(rows))


def cmd_stage(s, args, opt, notes):
    if not args:
        raise Stop("ap.py stage <этап> [start|done|skip|fail] [--note …]")
    sid = args[0]
    act = args[1] if len(args) > 1 else "start"
    if sid not in RANK:
        raise Stop(f"этапа {sid} нет: {', '.join(ORDER)}")
    if act not in STAGE_STATUS:
        raise Stop(f"действие {act} не знаю: start, done, skip, fail")
    note = opt.get("note")
    needs_reason = act in ("skip", "fail")
    if needs_reason and not note:
        raise Stop(f"stage {sid} {act} требует причину: --note …")
    move_stage(stage(s, sid), act, s["updatedAt"], note)
    if sid == "spec" and act in ("start", "done"):
        gate_g1(s)
    log(s, "stage", id=sid, act=act, note=note if needs_reason and isinstance(note, str) else None)


def cmd_tickets(s, args, opt, notes):
    notes.append(publish(s))
    log(s, "tickets", n=len(s.get("tickets") or []))


def cmd_check_plan(s, args, opt, notes):
    rows = manifest_rows(s) or []  # статусы до публикации
    publish(s)
    problems = plan_problems(rows, s.get("tickets") or [])
    if problems:
        notes.extend("! " + text for text in problems)
    else:
        notes.append("G3: трасса сходится")
    set_gate(s, "G3", len(problems) == 0, problems=len(problems))


def parse_tests(value):
    m = re.fullmatch(r"\s*(\d+)\s*(?:/\s*(\d+))?\s*", value) if isinstance(value, str) else None
    if m is None:
        raise Stop(f"тесты пишутся как ПРОШЛО/УПАЛО, например 34/0 (а не «{value}»)")
    passed, failed = int(m.group(1)), int(m.group(2) or 0)
    return {"passed": passed, "failed": failed}


def close_reqs(s, tk, opt):
    rows = {row["id"]: row for row in manifest_rows(s) or []}
    as_placeholder = set(ROW_ID.findall(sopt(opt, "placeholder") or ""))
    commit = opt.get("commit")
    where = commit[:7] if isinstance(commit, str) else ""
    changes = {}
    for rid in reqs_of(tk):
        row = rows.get(rid)
        if row is None or "C" not in req(row["status"])[2]:
            continue
        unfinished = [other for other in s.get("tickets") or []
                      if rid in reqs_of(other) and other is not tk and other.get("status") != "done"]
        if unfinished:
            continue
        new_status = "done"
        if rid in as_placeholder:
            new_status = "placeholder"
        changes[rid] = (new_status, where)
    if changes:
        update_manifest(s, changes)


def apply_ticket_action(s, tk, act, t, note, opt):
    tk["status"] = ACTIONS[act]
    if act in ("start", "retry", "done", "fail"):
        tk["startedAt"] = tk.get("startedAt") or t
    if act == "start":
        tk.pop("finishedAt", None)
    elif act == "retry":
        tk["retries"] = (tk.get("retries") or 0) + 1
    elif act == "repair":
        tk["repairs"] = (tk.get("repairs") or 0) + 1
        if note:
            tk.setdefault("repairFindings", []).append(note)
    elif act == "reset":
        for key in ("startedAt", "finishedAt"):
            tk.pop(key, None)
    elif act in ("done", "fail"):
        tk["finishedAt"] = t
        if note and act == "fail":
            tk.setdefault("concerns", []).append(note)
    if act == "done":
        close_reqs(s, tk, opt)


def cmd_ticket(s, args, opt, notes):
    chosen = [a for a in args if a in ACTIONS]
    ids = [a for a in args if a not in ACTIONS]
    if len(chosen) != 1 or not ids:
        raise Stop(f"ap.py ticket <id…> <{'|'.join(ACTIONS)}>")
    act = chosen[0]
    note = sopt(opt, "note")
    tests = parse_tests(opt["tests"]) if opt.get("tests") else None
    commit = opt.get("commit")
    by_id = {tk.get("id"): tk for tk in s.get("tickets") or []}
    for tid in ids:
        if tid not in by_id:
            raise Stop(f"таска {tid} нет — сначала опубликуй план: ap.py tickets")
        tk = by_id[tid]
        apply_ticket_action(s, tk, act, s["updatedAt"], note, opt)
        if tests:
            tk["tests"] = dict(tests)
            s["tests"] = dict(tests)
        if isinstance(commit, str):
            tk["commit"] = commit[:12]
    log(s, "ticket", ids=ids, act=act, tests=tests, note=note if act in ("repair", "fail") else None)


def cmd_set(s, args, opt, notes):
    pairs = []
    for arg in args:
        key, eq, value = arg.partition("=")
        if not (eq and key) or key in ("stages", "tickets", "requirements"):
            raise Stop(f"set ждёт ключ=значение (кроме stages, tickets, requirements), а не «{arg}»")
        pairs.append((key, None if value in ("", "null") else value))
    s.update(pairs)
    if any(arg.startswith("tier=") for arg in args):
        log(s, "tier", v=s.get("tier"))


def cmd_add(s, args, opt, notes):
    if len(args) < 2 or args[0] not in LIST_KEYS:
        raise Stop(f"ap.py add <{'|'.join(LIST_KEYS)}> ТЕКСТ…")
    key, values = args[0], args[1:]
    if key.startswith("debt."):
        if not isinstance(s.get("debt"), dict):
            s["debt"] = {}
        container, field = s["debt"], key.split(".", 1)[1]
    else:
        container, field = s, key
    target = container.get(field) or []
    container[field] = target
    fresh = [v for v in values if v not in target]  # повторы внутри вызова тоже считаются
    for v in fresh:
        if v not in target:
            target.append(v)
    if fresh:
        log(s, "add", key=key, n=len(fresh))


def cmd_tests(s, args, opt, notes):
    if not args:
        raise Stop("ap.py tests ПРОШЛО/УПАЛО, например 34/0")
    s["tests"] = parse_tests(args[0])
    log(s, "tests", passed=s["tests"]["passed"], failed=s["tests"]["failed"])


def numbers(args, keys, usage):
    got = {}
    for arg in args:
        m = re.fullmatch(r"(\w+)=(\d+)", arg)
        if m is None or m.group(1) not in keys:
            raise Stop(f"не понимаю «{arg}» — {usage}")
        got[m.group(1)] = int(m.group(2))
    absent = [name for name in keys if name not in got]
    if absent:  # пропущенный счётчик — не ноль
        raise Stop(f"не хватает {', '.join(absent)} — {usage}")
    return got


def strings(opt, key):
    return [v for v in opt["_multi"].get(key, []) if isinstance(v, str)]


def cmd_coverage(s, args, opt, notes):
    got = numbers(args, ("found", "fixed", "deferred"), "ap.py coverage found=N fixed=N deferred=N [--item …]")
    s["coverage"] = dict(got, items=strings(opt, "item"))
    set_gate(s, "G2", got["found"] <= got["fixed"] + got["deferred"], **got)


def cmd_blind(s, args, opt, notes):
    got = numbers(args, ("checked", "matched"), "ap.py blind checked=N matched=N [--mismatch …]")
    if got["matched"] > got["checked"]:
        raise Stop("совпавших больше, чем проверенных")
    mismatches = strings(opt, "mismatch")
    s["blind"] = dict(got, mismatches=mismatches)
    set_gate(s, "G4", not mismatches, **got)


def cmd_ask(s, args, opt, notes):
    kind = args[0] if args else None
    if kind not in WAITS:
        raise Stop(f"ap.py ask {'|'.join(WAITS)} [--note …]")
    pending = s.get("waiting") or None
    same_kind = bool(pending) and pending.get("kind") == kind
    if pending and not same_kind:
        close_wait(s)
    since = pending.get("since") if same_kind else s["updatedAt"]
    note = sopt(opt, "note")
    s["waiting"] = {"kind": kind, "since": since, "note": note}
    log(s, "ask", kind=kind, note=note)


def cmd_answered(s, args, opt, notes):
    close_wait(s)


def cmd_finish(s, args, opt, notes):
    t = s["updatedAt"]
    for st in s["stages"]:
        if st["status"] == "active" or (st["id"] == "final" and st["status"] == "pending"):
            move_stage(st, "done", t)
        elif st["status"] == "pending":
            move_stage(st, "skip", t, st.get("note") or "не понадобился")
    leftovers = [tk for tk in s.get("tickets") or [] if tk.get("status") in OPEN_TICKET]
    notes.extend(f"! таск {tk['id']} закрыт незавершённым ({tk['status']})" for tk in leftovers)
    folder = s.get("dir") or ""
    if folder.endswith("--wip"):
        target = folder[:-len("--wip")]
        if Path(A, target).exists():
            notes.append(f"! папка {target} уже есть — оставляю {folder}")
        elif not rename(folder, target):
            notes.append(f"! не смог переименовать {folder}")
        else:
            s["dir"] = target
            notes.append(f"папка прогона: .pilot-beckie/{target}")
    s["result"] = sopt(opt, "result")
    s["finishedAt"] = t
    readme_row(s, "сдан", s["result"])
    log(s, "finish", result=s["result"])


def cmd_reopen(s, args, opt, notes):
    folder = s.get("dir") or ""
    if folder and not folder.endswith("--wip") and rename(folder, folder + "--wip"):
        s["dir"] = folder + "--wip"
    s.update(finishedAt=None, blind=None, coverage=None, result=None)
    for st in s["stages"]:
        if st["id"] != "preflight":
            move_stage(st, "reset", None)
    move_stage(stage(s, "manifest"), "start", s["updatedAt"])
    s["gates"] = {}
    readme_row(s, "в работе")
    log(s, "reopen")


def commit_in_history(sha):
    return git("-C", ROOT, "merge-base", "--is-ancestor", sha, "HEAD") == 0


def cmd_commits(s, args, opt, notes):
    lost = [tk for tk in s.get("tickets") or []
            if tk.get("status") == "done" and tk.get("commit") and not commit_in_history(tk["commit"])]
    for tk in lost:
        notes.append(f"! таск {tk['id']}: коммита {tk['commit']} нет в истории — `ap.py ticket {tk['id']} reset`")
    if not lost:
        notes.append("коммиты сданных тасков на месте")


def cmd_sync(s, args, opt, notes):
    pass


COMMANDS = {"": cmd_sync, "sync": cmd_sync, "stage": cmd_stage, "tickets": cmd_tickets,
            "check-plan": cmd_check_plan, "ticket": cmd_ticket, "set": cmd_set, "add": cmd_add,
            "tests": cmd_tests, "coverage": cmd_coverage, "blind": cmd_blind, "ask": cmd_ask,
            "answered": cmd_answered, "finish": cmd_finish, "reopen": cmd_reopen, "commits": cmd_commits}


# ---------- reconcile, derive, timing ----------

def reconcile(s):
    norm_stages(s)
    stages, notes = s["stages"], []
    # 1. активный этап закрывается, когда стартовал более поздний
    active_now = [st for st in stages if st["status"] == "active"]
    for st in active_now:
        later = sorted(o["startedAt"] for o in active_now if RANK[o["id"]] > RANK[st["id"]] and o.get("startedAt"))
        if later:
            st["status"], st["finishedAt"] = "done", later[0]
            notes.append(f"{st['id']} закрыт ({later[0][11:19]})")
    # 2. пропущенный этап с готовым артефактом считается пройденным
    reached = [RANK[st["id"]] for st in stages if st["status"] in ("active", "done")]
    if reached and s.get("dir"):
        edge = max(reached)
        for st in stages:
            rank, art = RANK[st["id"]], ARTIFACT.get(st["id"])
            if not art or rank >= edge or st["status"] != "pending":
                continue
            if not glob.glob(os.path.join(run_dir(s), art)):
                continue
            later = sorted(o["startedAt"] for o in stages if RANK[o["id"]] > rank and o.get("startedAt"))
            when = later[0] if later else s.get("updatedAt")
            st.update(status="done", finishedAt=when, startedAt=st.get("startedAt") or when)
            notes.append(f"{st['id']} отмечен пройденным по файлу {art}")
    # 3. остальные пропуски — предупреждение
    running = [RANK[st["id"]] for st in stages if st["status"] == "active"]
    if running:
        top = max(running)
        gaps = [st["id"] for st in stages if st["status"] == "pending" and RANK[st["id"]] < top]
        for sid in gaps[:5]:
            notes.append(f"! этап {sid} пропущен в учёте: был — `stage {sid} done`, не было — "
                         f"`stage {sid} skip --note причина`. Это бухгалтерия, не расследуй")
    return notes


def ms(sec):
    if sec is None:
        return None
    return int(sec * 1000)


def rnd(x):
    return math.floor(x + 0.5)


def overlap(lo, hi, span):
    start, end = span
    return max(0, min(hi, end) - max(lo, start))


def timing(s):
    stages = s["stages"]
    tickets = s.get("tickets") or []
    waits = s.get("waits") or []
    stamps = [s.get("startedAt"), s.get("updatedAt"), s.get("finishedAt")] + list(s.get("beats") or [])
    for item in stages + tickets:
        stamps.extend((item.get("startedAt"), item.get("finishedAt")))
    for w in waits:
        stamps.extend((w.get("from"), w.get("to")))
    points = sorted({sec for sec in map(ts, stamps) if sec is not None})
    last = points[-1] if points else None
    finished = bool(s.get("finishedAt"))

    pauses = []
    for w in waits:
        pauses.append((ts(w.get("from")), ts(w.get("to"))))
    if s.get("waiting") and not finished:
        pauses.append((ts(s["waiting"].get("since")), last))
    pauses = [(lo, hi) for lo, hi in pauses if None not in (lo, hi) and hi > lo]

    def worked(start, end=None):
        lo = ts(start)
        if lo is None:
            return None
        hi = ts(end) if end else last
        if hi is None or hi <= lo:
            return 0
        edges = [lo] + [p for p in points if lo < p < hi] + [hi]
        total = 0
        for x, y in zip(edges, edges[1:]):
            net = (y - x) - sum(overlap(x, y, span) for span in pauses)
            total += min(IDLE_CAP, max(0, net))  # дольше IDLE_CAP без событий — простой
        return total

    for item in stages + tickets:
        item.pop("activeMs", None)
        if item.get("startedAt"):
            item["activeMs"] = ms(worked(item["startedAt"], item.get("finishedAt")))

    durations = []
    for tk in tickets:
        if tk.get("kind") == "done" and tk.get("finishedAt") and tk.get("activeMs") is not None:
            durations.append(max(1, rnd(tk["activeMs"] / 60000)))
    durations.sort()
    median = durations[len(durations) // 2] if durations else None
    per_ticket = median or 10

    def remaining(tk):
        kind = tk.get("kind")
        if kind == "now" and tk.get("activeMs") is not None:
            return max(1, per_ticket - tk["activeMs"] / 60000)
        return {"done": 0, "rev": 0.2 * per_ticket, "fix": 0.5 * per_ticket}.get(kind, per_ticket)

    index, memo = {tk.get("id"): tk for tk in tickets}, {}

    def chain(tid, path):
        tk = index.get(tid)
        if tk is None or tk.get("kind") == "done":
            return 0
        if tid in path:  # цикл: только своё время
            return remaining(tk)
        if tid not in memo:
            deps = [chain(ref, path | {tid}) for ref in tk.get("blockedBy") or []]
            memo[tid] = remaining(tk) + max([0, *deps])
        return memo[tid]

    critical = max([0] + [chain(tk.get("id"), frozenset()) for tk in tickets])
    minutes = {st["id"]: (st.get("activeMs") or 0) / 60000 for st in stages}
    current = next((st["id"] for st in stages if st["status"] == "active"), None)
    left, late = None, False
    calm = not finished and not s.get("waiting") and all(st["status"] != "failed" for st in stages)
    if calm and current == "build" and median is not None:
        left = critical + max(10, 0.5 * (minutes["build"] + critical)) + 8
    elif calm and current == "review":
        left, late = 8 + max(5, 0.6 * minutes["build"] - minutes["review"]), True
    elif calm and current == "final":
        left, late = max(3, 10 - minutes["final"]), True
    eta = [max(1, rnd(0.75 * left)), max(2, rnd(1.4 * left))] if left else None
    s["timing"] = {"runMs": ms(worked(s.get("startedAt"), s.get("finishedAt"))), "lastMs": ms(last),
                   "capMs": IDLE_CAP * 1000, "median": median, "eta": eta, "lateEta": late}


def derive(s):
    tickets = s.get("tickets") or []
    for tk in tickets:
        tk["reqs"] = reqs_of(tk)
        tk["kind"] = KIND.get(tk.get("status"), "wait")
    for item in s.get("reqList") or []:
        item["tickets"] = [tk.get("id") for tk in tickets if item.get("id") in tk["reqs"]]
    norm_stages(s)
    gates = s.get("gates") or {}
    s["gates"] = gates
    cov = s.get("coverage")
    if cov and "G2" not in gates:  # старые состояния без записанного гейта
        gates["G2"] = {"ok": cov["found"] <= cov["fixed"] + cov["deferred"],
                       **{key: cov[key] for key in ("found", "fixed", "deferred")}}
    blind = s.get("blind")
    if blind and "G4" not in gates:
        gates["G4"] = {"ok": not blind.get("mismatches"), "checked": blind["checked"], "matched": blind["matched"]}
    timing(s)
    return s


def execute(argv):
    pos, opt = parse_args(argv)
    cmd = pos[0] if pos else ""
    args, notes = pos[1:], []
    if cmd == "init":
        s = cmd_init(opt, notes)
    else:
        s = read_state()
        if s is None:
            raise Stop("state.js ещё нет — начни с ap.py init --slug …")
        norm_stages(s)
        if cmd not in ("", "sync", "commits"):
            s["updatedAt"] = now()
            beat(s)
        if cmd in MOVE_ON:
            close_wait(s)
        handler = COMMANDS.get(cmd)
        if handler is None:
            raise Stop(f"команды «{cmd}» нет — список в начале ap.py")
        handler(s, args, opt, notes)
    notes = reconcile(s) + notes + recount(s)
    derive(s)
    save(s)
    return s, notes, cmd, opt


# ---------- page snapshot ----------

def snapshot(s):
    try:
        page = slurp(PAGE)
    except OSError:
        return "страницы нет — скопируй dashboard.html из скилла заново"
    head = page.find(BEGIN)
    tail = page.find(END, head + len(BEGIN)) if head >= 0 else -1
    if tail < 0:
        return "на странице нет меток снимка — скопируй dashboard.html заново"
    payload = json.dumps(s, ensure_ascii=False).replace("</", "<\\/")
    updated = f"{page[:head + len(BEGIN)]}window.STATE={payload};{page[tail:]}"
    if updated != page:
        write_atomic(PAGE, updated)
    return "дашборд обновлён"


# ---------- server ----------

SPAWN_FLAGS = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
               if WIN else {"start_new_session": True})


def spawn(argv, **streams):
    """Отцепленный процесс: переживает выход ap.py."""
    return subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, **streams, **SPAWN_FLAGS)


def read_pid():
    try:
        fields = slurp(PID).split()
        return int(fields[0]), int(fields[1])
    except (OSError, ValueError, IndexError):
        return None, None


def page_url(port):
    return f"http://localhost:{port}/dashboard.html"


def http_ok(port):
    direct = urlreq.build_opener(urlreq.ProxyHandler({}))
    try:
        with direct.open(f"http://{HOST}:{port}/dashboard.html", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def free_port(prefer):
    candidates = [prefer, 0] if prefer else [0]
    for port in candidates:
        with socket.socket() as sock:
            if not WIN:  # на Windows SO_REUSEADDR позволяет угнать чужой порт
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((HOST, port))
            except OSError:
                continue
            return sock.getsockname()[1]
    return None


def capture(argv):
    try:
        done = subprocess.run(argv, timeout=10, text=True, capture_output=True)
    except Exception:
        return ""
    return done.stdout or ""


def powershell(script):
    return capture(["powershell", "-NoProfile", "-Command", script])


def procs():
    if WIN:
        listing = powershell("Get-CimInstance -ClassName Win32_Process -Filter \"Name LIKE 'python%'\" | "
                             "% { \"{0}`t{1}\" -f $_.ProcessId, $_.CommandLine }")
        sep = "\t"
    else:
        listing, sep = capture(["ps", "-Ao", "pid=,command="]), " "
    for raw in listing.splitlines():
        head, _, command = raw.strip().partition(sep)
        if head.isdigit():
            yield int(head), command.strip()


def cmdline(pid):
    if WIN:
        return powershell(f"(Get-CimInstance -ClassName Win32_Process -Filter \"ProcessId={pid}\").CommandLine").strip()
    return capture(["ps", "-p", str(pid), "-o", "command="]).strip()


def kill(pid):
    try:
        os.kill(pid, 15)
    except Exception:
        pass


def is_ours(cmd):
    """Узко: только наш http.server с --directory ровно этой папки — чужие серверы не трогаем."""
    line = cmd.replace("\\", "/")
    if WIN:
        line = line.lower()
    return _HTTP_RE.search(line) is not None and _DIR_RE.search(line) is not None


def kill_orphans(keep=None):
    me = os.getpid()
    victims = [pid for pid, line in procs() if pid != me and pid != keep and is_ours(line)]
    for victim in victims:
        kill(victim)
    return len(victims)


def start_server(port):
    port_arg = str(port)
    argv = [sys.executable, "-m", "http.server", port_arg, "--bind", HOST, "--directory", A]
    with open(LOG, "a") as errlog:
        return spawn(argv, stderr=errlog)


def serve(s):
    port, pid = read_pid()
    if s.get("finishedAt"):
        kill_orphans(keep=pid)
        return "прогон закрыт"
    if any(os.environ.get(var) for var in ("SSH_CONNECTION", "CI")):
        return f"удалённая сессия — без сервера, дашборд: {PAGE}"
    if pid and port and is_ours(cmdline(pid)) and http_ok(port):
        return page_url(port)
    kill_orphans()
    port = free_port(port)  # прежний порт — открытая вкладка оживёт сама
    if port is None:
        return f"нет порта — открой дашборд файлом: {PAGE}"
    try:
        child = start_server(port)
    except OSError as err:
        return f"сервер не поднялся ({err}) — открой дашборд файлом: {PAGE}"
    for _attempt in range(10):
        if http_ok(port):
            put_file(PID, f"{port} {child.pid}\n")
            return f"сервер поднят: {page_url(port)}"
        try:
            child.wait(0.5)
        except subprocess.TimeoutExpired:
            continue
        break  # процесс умер — ждать нечего
    child.terminate()
    return f"сервер не ответил — открой дашборд файлом: {PAGE}"


def stop_later():
    try:
        spawn([sys.executable, os.path.abspath(__file__), "--stop-now"], stderr=subprocess.DEVNULL)
    except OSError:
        pass
    return f"сервер погаснет через {STOP_DELAY} с"


def stop_now():
    time.sleep(STOP_DELAY)  # странице хватит времени забрать финальное состояние
    pid = read_pid()[1]
    if pid is not None and is_ours(cmdline(pid)):
        kill(pid)
    kill_orphans()
    for leftover in (PID, LOG):
        try:
            os.remove(leftover)
        except OSError:
            pass


# ---------- update check ----------

def _version(text):
    if not text.startswith("---"):
        return None
    front = text.split("\n---", 1)[0]
    m = re.search(r"^\s*version:\s*[\"']?(\d+(?:\.\d+)*)", front, re.M)
    if m is None:
        return None
    return tuple(map(int, m.group(1).split(".")))


def remote_version():
    try:
        with urlreq.urlopen(REMOTE_SKILL, timeout=3) as resp:
            chunk = resp.read(64 * 1024)
    except Exception:
        return None
    return _version(chunk.decode("utf-8", "replace"))


def dotted(version):
    return ".".join(str(n) for n in version)


def check_update(s):
    if os.environ.get("PILOT_BECKIE_NO_UPDATE_CHECK"):
        return None
    skill_dir = s.get("skillDir")
    if not skill_dir:
        return None
    try:
        local = _version(slurp(os.path.join(skill_dir, "SKILL.md")))
    except OSError:
        return None
    remote = remote_version()
    if remote is None or (local is not None and remote <= local):
        return None
    home = os.path.normcase(os.path.expanduser("~"))
    installed_globally = os.path.normcase(os.path.normpath(os.path.abspath(skill_dir))).startswith(
        os.path.join(home, "."))
    command = "npx skills update pilot-beckie" + (" -g" if installed_globally else "")
    have = dotted(local) if local else "без номера"
    return (f"вышел Pilot Lab {dotted(remote)} (у тебя {have}): `{command}` · "
            f"что нового — github.com/{REPO}/blob/main/CHANGELOG.md")


# ---------- CLI ----------

def server_phrase(s, cmd, opt):
    if opt.get("stop") or cmd == "finish":
        return stop_later()
    if opt.get("no-serve"):
        return "сервер не проверял"
    return serve(s)


def main(argv):
    wants_help = argv[:1] == ["help"] or any(tok in ("--help", "-h") for tok in argv)
    if wants_help:
        print(USAGE)
        return 0
    if "--stop-now" in argv:
        stop_now()
        return 0
    try:
        s, notes, cmd, opt = execute(argv)
    except Stop as refusal:
        print(f"ошибка: {refusal}")
        return 1
    snap = snapshot(s)
    srv = server_phrase(s, cmd, opt)
    counts = s.get("requirements") or {}
    print(f"{snap} · {srv} · требований {counts.get('total') or 0}, готово {counts.get('done') or 0}")
    for note in notes:
        print("  " + (note if note.startswith("!") else "· " + note))
    notice = check_update(s) if opt.get("check-update") else None
    if notice:
        print("  ↑ " + notice)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
