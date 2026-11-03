"""Suite for skills/pilot-beckie/tools/ap.py.

From the repo root:  python3 -m unittest discover -s tests
"""
import sys
import os
import json
import shutil
import tempfile
import unittest
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta, timezone

HERE = Path(__file__).resolve()
SKILL_DIR = HERE.parents[1] / "skills" / "pilot-beckie"
AP_FILE = SKILL_DIR / "tools" / "ap.py"
STUB_PAGE = ('<!doctype html><title>stub</title><script>/*STATE-BEGIN*/window.STATE=null;/*STATE-END*/'
             '</script><script src="state.js"></script>\n')
GIT_IDENTITY = {"GIT_AUTHOR_NAME": "suite", "GIT_AUTHOR_EMAIL": "suite@example.invalid",
                "GIT_COMMITTER_NAME": "suite", "GIT_COMMITTER_EMAIL": "suite@example.invalid"}


def load_tool():
    loader = importlib.util.spec_from_file_location("ap_under_test", AP_FILE)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


ap = load_tool()

# Garden diary project: three wishes the user stated plus one dropped idea.
WISHES = """# Что просил пользователь

| № | Слова пользователя | Статус | Почему | Где |
|---|---|---|---|---|
| R01 | «записывать каждый полив» | in-spec | бриф, абзац 1 | — |
| R02 | «хранить в sqlite \\| или в csv» | in-spec | | — |
| R03 | «push-уведомления» | dropped | «пока без них» | — |
| R05 | «график по неделям» | in-spec | | — |
"""


def card(tid, name, needs, after, paths, wave, review="нет", model=None):
    """A ticket file in the plan's markdown format."""
    body = [f"# {tid} — {name}", "",
            f"**Волна:** {wave}",
            f"**Требования:** {needs}",
            f"**Зона:** {' · '.join('`' + p + '`' for p in paths)}",
            f"**Зависит от:** {after}",
            f"**Ревью:** {review}"]
    if model:
        body.append(f"**Модель:** {model}")
    return "\n".join(body) + "\n"


STORE = card("01", "Хранилище", "R01, R05", "—", ["app/store/"], 1, "да — схема данных", "opus")
SCREEN = card("02", "Экран поливов", "R01.1, R02, A01", "01", ["app/ui/"], 2)


def sh_git(where, *args):
    out = subprocess.run(["git", *args], cwd=where, env={**os.environ, **GIT_IDENTITY},
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


class Project:
    """A throwaway git repo with .pilot-beckie/ holding a copy of the tool and a stub page."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="apsuite-"))
        sh_git(self.root, "init", "-q")
        sh_git(self.root, "commit", "-q", "--allow-empty", "-m", "empty")
        self.folder = self.root / ".pilot-beckie"
        self.folder.mkdir()
        (self.folder / "dashboard.html").write_text(STUB_PAGE, encoding="utf-8")
        shutil.copyfile(AP_FILE, self.folder / "ap.py")

    def call(self, *argv):
        env = {**os.environ, **GIT_IDENTITY, "PILOT_BECKIE_NO_UPDATE_CHECK": "1"}
        done = subprocess.run([sys.executable, str(self.folder / "ap.py"), *argv, "--no-serve"],
                              cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8")
        return done.returncode, done.stdout + done.stderr

    @property
    def state(self):
        text = (self.folder / "state.js").read_text(encoding="utf-8")
        return json.loads(text.split("=", 1)[1])

    def state_bytes(self):
        return (self.folder / "state.js").read_bytes()

    def run_folder(self):
        return self.folder / self.state["dir"]

    def write(self, rel, text):
        target = self.run_folder() / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def wishes(self):
        return (self.run_folder() / "manifest.md").read_text(encoding="utf-8")

    def wish_row(self, rid):
        return [ln for ln in self.wishes().splitlines() if ln.startswith(f"| {rid} ")][0]

    def ticket(self, tid):
        return {tk["id"]: tk for tk in self.state["tickets"]}[tid]

    def phase(self, sid):
        return {st["id"]: st for st in self.state["stages"]}[sid]

    def requirement(self, rid):
        return {item["id"]: item for item in self.state["reqList"]}[rid]

    def readme(self):
        return (self.folder / "README.md").read_text(encoding="utf-8")


class Run(unittest.TestCase):
    def setUp(self):
        self.p = Project()
        self.addCleanup(shutil.rmtree, self.p.root, ignore_errors=True)

    def go(self, *argv):
        code, out = self.p.call(*argv)
        self.assertEqual(0, code, msg=out)
        return out

    def refused(self, *argv):
        code, out = self.p.call(*argv)
        self.assertNotEqual(0, code, msg=out)
        return out

    def start(self, slug="plant-log"):
        return self.go("init", "--skill-dir", str(SKILL_DIR), "--title", "Дневник", "--slug", slug)

    def with_plan(self):
        self.p.write("manifest.md", WISHES)
        self.p.write("tickets/01-store.md", STORE)
        self.p.write("tickets/02-screen.md", SCREEN)

    # T1
    def test_init_creates_run(self):
        self.start()
        st = self.p.state
        self.assertTrue((self.p.run_folder() / "tickets").is_dir())
        self.assertRegex(st["dir"], r"^\d{4}-\d\d-\d\d-plant-log--wip$")
        self.assertRegex(st["startedAt"], r"T\d\d:\d\d:\d\d[+-]\d\d:\d\d$")
        self.assertEqual(["active", *["pending"] * 7], [x["status"] for x in st["stages"]])
        self.assertIn(".pilot-beckie/serve.*", (self.p.root / ".gitignore").read_text(encoding="utf-8"))
        self.assertIn("в работе", self.p.readme())
        self.assertIn("window.STATE={", (self.p.folder / "dashboard.html").read_text(encoding="utf-8"))

    # T2
    def test_init_refuses_unfinished_run(self):
        self.start()
        self.assertIn("продолжение", self.refused("init", "--slug", "orchard"))

    # T3
    def test_init_after_finish_archives_old_state(self):
        self.start()
        self.go("finish", "--result", "первая версия")
        archived_dir = self.p.state["dir"]
        self.start("next-round")
        self.assertFalse(archived_dir.endswith("--wip"))
        self.assertTrue((self.p.folder / archived_dir / "state.js").is_file())
        self.assertTrue(self.p.state["dir"].endswith("next-round--wip"))

    # T4
    def test_stage_closes_previous(self):
        self.start()
        self.go("stage", "manifest")
        self.assertEqual("done", self.p.phase("preflight")["status"])
        self.assertEqual("active", self.p.phase("manifest")["status"])

    # T5
    def test_later_stage_closes_build(self):
        self.start()
        for sid in ("build", "review"):
            self.go("stage", sid)
        self.assertEqual("done", self.p.phase("build")["status"])

    # T6
    def test_artifact_closes_stage_and_warns(self):
        self.start()
        self.p.write("manifest.md", WISHES)
        out = self.go("stage", "spec")
        self.assertIn("briefing", out)
        self.assertEqual("pending", self.p.phase("briefing")["status"])
        self.assertEqual("done", self.p.phase("manifest")["status"])

    # T7
    def test_skip_requires_note(self):
        self.start()
        self.refused("stage", "briefing", "skip")
        self.go("stage", "briefing", "skip", "--note", "пользователь всё описал сам")
        self.assertEqual("skipped", self.p.phase("briefing")["status"])

    # T8
    def test_republish_keeps_progress_takes_plan(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        self.go("ticket", "01", "start")
        self.go("ticket", "01", "repair", "--note", "нет миграции")
        first_start = self.p.ticket("01")["startedAt"]
        self.p.write("tickets/01-store.md", card("01", "Хранилище и миграции", "R05", "—", ["app/db/"], 1))
        self.go("tickets")
        store = self.p.ticket("01")
        self.assertEqual(["нет миграции"], store["repairFindings"])
        self.assertEqual("repair", store["status"])
        self.assertEqual(1, store["repairs"])
        self.assertEqual(first_start, store["startedAt"])
        self.assertEqual("Хранилище и миграции", store["title"])
        self.assertEqual(["R05"], store["requirements"])
        self.assertEqual(["app/db/"], store["zone"])
        self.assertEqual("нет", store["review"])
        self.assertEqual(["01"], self.p.requirement("R05")["tickets"])
        self.assertEqual(["02"], self.p.requirement("R01")["tickets"])
        self.assertEqual(["A01", "R01", "R02"], self.p.ticket("02")["reqs"])

    # T9
    def test_tickets_publish(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        screen, store = self.p.ticket("02"), self.p.ticket("01")
        self.assertEqual("pending", screen["status"])
        self.assertEqual(["01"], screen["blockedBy"])
        self.assertEqual(["R01.1", "R02", "A01"], screen["requirements"])
        self.assertEqual("да — схема данных", store["review"])
        self.assertEqual(["app/store/"], store["zone"])
        r01 = self.p.wish_row("R01")
        self.assertIn("T01, T02", r01)
        self.assertIn("in-ticket", r01)
        self.assertIn("dropped", self.p.wish_row("R03"))
        self.assertEqual(3, self.p.state["requirements"]["inTicket"])

    # T10
    def test_check_plan_sound(self):
        self.start()
        self.with_plan()
        self.assertIn("G3: трасса сходится", self.go("check-plan"))

    # T11
    def test_check_plan_catches_defects(self):
        self.start()
        self.with_plan()
        self.p.write("tickets/03-calendar.md", card("03", "Календарь", "R02", "02", ["app/ui/calendar/"], 2))
        self.p.write("tickets/07-misc.md", "# 07 — Разное\n\n**Волна:** 1\n**Требования:** —\n**Зависит от:** —\n")
        out = self.go("check-plan")
        expected = ["у таска 07 нет зоны",
                    "таск 07 ни к чему не привязан",
                    "таски 02 и 03 в одной волне пишут в app/ui/calendar/",
                    "таск 03 в волне 2, но его зависимости позволяют не раньше 3"]
        for needle in expected:
            self.assertIn(needle, out)

    # T12
    def test_check_plan_uncovered_requirement(self):
        self.start()
        self.with_plan()
        self.p.write("manifest.md", WISHES + "| G01 | «работает офлайн» | in-spec | | — |\n")
        self.assertIn("требование G01", self.go("check-plan"))

    # T13
    def test_done_closes_rows_when_all_tickets_done(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        self.go("ticket", "01", "start")
        self.go("ticket", "01", "done", "--placeholder", "R05", "--commit", "abcdef01234567", "--tests", "4/0")
        self.assertIn("abcdef0", self.p.wish_row("R05"))  # first 7 chars of the commit
        self.assertIn("placeholder", self.p.wish_row("R05"))
        self.assertIn("in-ticket", self.p.wish_row("R01"))  # 02 is still open
        self.go("ticket", "02", "start")
        self.go("ticket", "02", "done", "--commit", "fedcba98765432", "--tests", "9/1")
        for rid in ("R01", "R02"):
            self.assertIn("| done |", self.p.wish_row(rid))
        st = self.p.state
        self.assertEqual({"passed": 9, "failed": 1}, st["tests"])
        self.assertEqual(1, st["requirements"]["placeholder"])
        self.assertEqual(2, st["requirements"]["done"])

    # T14
    def test_ticket_lifecycle_counters(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        self.go("ticket", "01", "02", "start")
        self.go("ticket", "02", "retry")
        self.go("ticket", "01", "review")
        self.go("ticket", "01", "repair", "--note", "индекс не создан")
        store, screen = self.p.ticket("01"), self.p.ticket("02")
        self.assertEqual(["индекс не создан"], store["repairFindings"])
        self.assertEqual(("repair", 1), (store["status"], store["repairs"]))
        self.assertTrue(screen.get("startedAt"))
        self.assertEqual(1, screen["retries"])
        self.go("ticket", "02", "reset")
        screen = self.p.ticket("02")
        self.assertNotIn("startedAt", screen)
        self.assertEqual("pending", screen["status"])

    # T15
    def test_unknown_ticket_refused(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        self.refused("ticket", "42", "start")

    # T16
    def test_escaped_pipe_survives_rewrite(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        self.assertIn("| R02 | «хранить в sqlite \\| или в csv» | in-ticket |", self.p.wishes())

    # T17
    def test_d_rows_are_constraints(self):
        self.start()
        self.with_plan()
        self.p.write("manifest.md", WISHES + "| D01 | «без облака» | in-spec | | — |\n")
        self.assertNotIn("D01", self.go("check-plan"))
        self.assertEqual(4, self.p.state["requirements"]["total"])

    # T18
    def test_dependencies_normalize(self):
        self.start()
        self.with_plan()
        self.p.write("tickets/05-export.md", card("05", "Экспорт", "R02", "T02, T1", ["app/export/"], 3))
        self.go("tickets")
        self.assertEqual(["02", "01"], self.p.ticket("05")["blockedBy"])

    # T19
    def test_lettered_dependencies(self):
        self.start()
        self.p.write("manifest.md", WISHES)
        self.p.write("tickets/12-base.md", card("12", "Основа", "R01", "—", ["core/"], 1))
        self.p.write("tickets/K12-api.md", card("K12", "API", "R02", "—", ["api/"], 2))
        self.p.write("tickets/K13-cli.md", card("K13", "CLI", "R05", "K12", ["cli/"], 2))
        self.p.write("tickets/K14-docs.md", card("K14", "Доки", "R05", "Z9", ["docs/"], 3))
        out = self.go("check-plan")
        self.assertFalse(self.p.state["gates"]["G3"]["ok"])
        self.assertIn("таск K14 зависит от несуществующего Z9", out)
        self.assertIn("таск K13 в волне 2, но его зависимости позволяют не раньше 3", out)
        self.assertEqual(["K12"], self.p.ticket("K13")["blockedBy"])

    # T20
    def test_empty_tickets_dir_keeps_plan_pending(self):
        self.start()
        self.p.write("manifest.md", WISHES)
        self.go("stage", "build")
        self.assertEqual("pending", self.p.phase("plan")["status"])
        self.p.write("tickets/01-store.md", STORE)
        self.go()
        self.assertEqual("done", self.p.phase("plan")["status"])

    # T21
    def test_add_set_numbers(self):
        self.start()
        self.go("add", "concerns", "сервер медленный")
        for _ in range(2):
            self.go("add", "debt.emptyEnv", "WEATHER_KEY")
        self.go("set", "baseCommit=9f8e7d6", "tier=T1")
        self.go("add", "report", "первое", "второе")
        self.go("coverage", "deferred=2", "found=3", "fixed=1", "--item", "R09 — потом")
        self.go("blind", "matched=5", "checked=6", "--mismatch", "R05 — нет подписи оси")
        st = self.p.state
        self.assertEqual({"checked": 6, "matched": 5, "mismatches": ["R05 — нет подписи оси"]}, st["blind"])
        self.assertEqual({"found": 3, "fixed": 1, "deferred": 2, "items": ["R09 — потом"]}, st["coverage"])
        self.assertEqual(["первое", "второе"], st["report"])
        self.assertEqual("9f8e7d6", st["baseCommit"])
        self.assertEqual("T1", st["tier"])
        self.assertEqual(["WEATHER_KEY"], st["debt"]["emptyEnv"])
        self.assertEqual(["сервер медленный"], st["concerns"])

    # T22
    def test_beats(self):
        self.start()
        fresh = self.p.state
        self.assertEqual([fresh["startedAt"]], fresh["beats"])
        self.go("add", "report", "строка")
        self.go()
        later = self.p.state
        beats = later["beats"]
        self.assertTrue(len(beats) <= 2)
        self.assertEqual(sorted(set(beats)), beats)
        self.assertEqual(later["updatedAt"], beats[-1])

    # T23
    def test_ask_answered(self):
        self.start()
        self.go("stage", "briefing")
        self.go("ask", "briefing", "--note", "уточнить сорта растений")
        waiting = self.p.state["waiting"]
        self.assertEqual("уточнить сорта растений", waiting["note"])
        self.assertEqual("briefing", waiting["kind"])
        self.assertEqual(self.p.state["updatedAt"], waiting["since"])
        self.go("answered")
        st = self.p.state
        self.assertEqual(1, len(st["waits"]))
        self.assertEqual("briefing", st["waits"][0]["kind"])
        self.assertIsNone(st["waiting"])
        self.assertGreaterEqual(ap.ts(st["waits"][0]["to"]), ap.ts(st["waits"][0]["from"]))

    # T24
    def test_moving_on_closes_wait(self):
        self.start()
        self.go("ask", "spec")
        self.go("add", "report", "заметка")
        self.assertEqual("spec", self.p.state["waiting"]["kind"])
        self.go("stage", "plan")
        st = self.p.state
        self.assertEqual(["spec"], [item["kind"] for item in st["waits"]])
        self.assertIsNone(st["waiting"])

    # T25
    def test_ask_unknown_kind(self):
        self.start()
        self.refused("ask", "coffee")

    # T26
    def test_log_records_events_not_syncs(self):
        self.start()
        self.p.write("tickets/01-store.md", STORE)
        self.go("tickets")
        self.go("ticket", "01", "start")
        self.go("ticket", "01", "repair", "--note", "забыт индекс")
        self.go("ticket", "01", "done", "--tests", "12/0")
        self.go("sync")
        events = self.p.state["log"]
        self.assertEqual(["init", "tickets", "ticket", "ticket", "ticket"], [e["k"] for e in events])
        self.assertEqual(["start", "repair", "done"], [e["act"] for e in events[2:]])
        self.assertNotIn("act", events[0])
        self.assertEqual("забыт индекс", events[3]["note"])
        self.assertEqual({"passed": 12, "failed": 0}, events[-1]["tests"])
        self.assertEqual(["01"], events[-1]["ids"])

    # T27
    def test_gates_follow_events(self):
        self.start()
        self.with_plan()
        self.p.write("manifest.md", WISHES.replace("| R05 | «график по неделям» | in-spec |",
                                                   "| R05 | «график по неделям» | open |"))
        self.go("stage", "spec")
        g1 = self.p.state["gates"]["G1"]
        self.assertEqual({"ok": False, "open": 1, "total": 4}, {k: g1[k] for k in ("ok", "open", "total")})
        self.p.write("manifest.md", WISHES)
        self.go("stage", "spec", "done")
        self.go("coverage", "found=1", "fixed=0", "deferred=1")
        self.go("check-plan")
        self.go("blind", "checked=5", "matched=4", "--mismatch", "R01 — дата не та")
        gates = self.p.state["gates"]
        self.assertTrue(gates["G1"]["ok"])
        self.assertTrue(gates["G2"]["ok"])
        self.assertTrue(gates["G3"]["ok"])
        self.assertEqual((False, 4, 5), (gates["G4"]["ok"], gates["G4"]["matched"], gates["G4"]["checked"]))

    # T28
    def test_gate_numbers_required(self):
        self.start()
        self.go("coverage", "found=3", "fixed=1", "deferred=1")
        self.go("blind", "checked=2", "matched=1", "--mismatch", "R02 — пусто")
        snapshot = self.p.state_bytes()
        bad_calls = [
            ["blind", "checked=2", "matched=5"],
            ["coverage", "found=1", "deferred=0"],
            ["blind", "matched=1"],
            ["coverage", "found=1", "fixed=1", "deferred=1", "bogus=2"],
            ["coverage"],
            ["coverage", "deferred=2"],
            ["blind"],
            ["coverage", "found=x", "fixed=0", "deferred=0"],
        ]
        for argv in bad_calls:
            with self.subTest(argv=argv):
                self.assertIn("ошибка", self.refused(*argv))
                self.assertEqual(snapshot, self.p.state_bytes())
        gates = self.p.state["gates"]
        self.assertFalse(gates["G4"]["ok"])
        self.assertFalse(gates["G2"]["ok"])
        self.assertEqual(["R02 — пусто"], self.p.state["blind"]["mismatches"])

    # T29
    def test_help_touches_nothing(self):
        self.assertIn("Учёт прогона Pilot by Beckie", self.go("--help"))
        self.assertFalse((self.p.folder / "state.js").exists())
        self.start()
        self.go("coverage", "found=4", "fixed=1", "deferred=0")
        snapshot = self.p.state_bytes()
        for argv in (["stage", "final", "--help"], ["-h"], ["blind", "-h"], ["help"],
                     ["coverage", "--help"], ["--help"]):
            with self.subTest(argv=argv):
                self.assertIn("ap.py coverage found=", self.go(*argv))
                self.assertEqual(snapshot, self.p.state_bytes())
        self.assertFalse(self.p.state["gates"]["G2"]["ok"])

    # T30
    def test_requirements_carry_user_words(self):
        self.start()
        quote = "| R05 | **(по смыслу)** `«неделя \\| месяц»` |"
        self.p.write("manifest.md", WISHES.replace("| R05 | «график по неделям» |", quote)
                     + "| D01 | «без облака» | in-spec | | — |\n")
        self.go()
        self.assertEqual(["R01", "R02", "R03", "R05"], [item["id"] for item in self.p.state["reqList"]])
        self.assertEqual("(по смыслу) «неделя | месяц»", self.p.requirement("R05")["text"])
        self.assertEqual("«пока без них»", self.p.requirement("R03")["why"])
        self.assertEqual({"id": "R01", "text": "«записывать каждый полив»", "status": "in-spec",
                          "kind": "work", "tickets": []}, self.p.requirement("R01"))

    # T31
    def test_page_gets_kinds(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        self.go("ticket", "02", "repair")
        self.go("ticket", "01", "start")
        st = self.p.state
        self.assertEqual(list(ap.ORDER), [x["id"] for x in st["stages"]])
        self.assertEqual({"01": "now", "02": "fix"}, {tk["id"]: tk["kind"] for tk in st["tickets"]})

    # T32
    def test_status_typo_counts_as_open(self):
        self.start()
        self.p.write("manifest.md", WISHES.replace("| R05 | «график по неделям» | in-spec |",
                                                   "| R05 | «график по неделям» | in_spec |"))
        self.assertIn("! R05: статуса «in_spec» нет", self.go())
        counts = self.p.state["requirements"]
        self.assertEqual(2, counts["work"])
        self.assertEqual(1, counts["open"])
        self.assertEqual("open", self.p.requirement("R05")["kind"])

    # T33
    def test_reopen_drops_coverage(self):
        self.start()
        self.go("coverage", "found=1", "fixed=1", "deferred=0")
        self.go("finish")
        self.go("reopen")
        st = self.p.state
        self.assertNotIn("G2", st["gates"])
        self.assertIsNone(st["coverage"])

    # T34
    def test_every_write_bumps_rev(self):
        self.start()
        before = self.p.state["rev"]
        self.go()
        self.assertEqual(before + 1, self.p.state["rev"])

    # T35
    def test_finish_lands_run(self):
        self.start()
        self.with_plan()
        sh_git(self.p.root, "add", "--", str(self.p.run_folder()))
        sh_git(self.p.root, "commit", "-q", "-m", "plan files")
        self.go("finish", "--result", "Дневник поливов готов")
        st = self.p.state
        self.assertEqual("Дневник поливов готов", st["result"])
        self.assertTrue(st["finishedAt"])
        self.assertNotRegex(st["dir"], r"--wip$")
        self.assertTrue((self.p.folder / st["dir"]).is_dir())
        self.assertEqual(set(), {x["status"] for x in st["stages"]} - {"done", "skipped"})
        self.assertIn("| сдан | Дневник поливов готов |", self.p.readme())
        porcelain = sh_git(self.p.root, "status", "--short").splitlines()
        self.assertTrue([ln for ln in porcelain if ln[:1] == "R"], porcelain)

    # T36
    def test_reopen_puts_wip_back(self):
        self.start()
        self.go("finish")
        self.go("reopen")
        st = self.p.state
        final = self.p.phase("final")
        self.assertEqual("active", self.p.phase("manifest")["status"])
        self.assertEqual("pending", final["status"])
        self.assertNotIn("finishedAt", final)
        self.assertIsNone(st["finishedAt"])
        self.assertRegex(st["dir"], r"--wip$")

    # T37
    def test_commits_checks_history(self):
        self.start()
        self.with_plan()
        self.go("tickets")
        sh_git(self.p.root, "commit", "-q", "--allow-empty", "-m", "store")
        survivor = sh_git(self.p.root, "rev-parse", "HEAD")
        sh_git(self.p.root, "commit", "-q", "--allow-empty", "-m", "screen")
        doomed = sh_git(self.p.root, "rev-parse", "HEAD")
        for tid, sha in (("01", survivor), ("02", doomed)):
            self.go("ticket", tid, "start")
            self.go("ticket", tid, "done", "--commit", sha)
        self.assertIn("коммиты сданных тасков на месте", self.go("commits"))
        sh_git(self.p.root, "reset", "-q", "--hard", survivor)
        events_before = len(self.p.state["log"])
        out = self.go("commits")
        self.assertNotIn("таск 01", out)
        self.assertIn(f"! таск 02: коммита {doomed[:12]} нет в истории", out)
        self.assertEqual(events_before, len(self.p.state["log"]))
        self.assertEqual("done", self.p.ticket("02")["status"])


class Core(unittest.TestCase):
    """In-process calls through the Python API."""

    def setUp(self):
        base = tempfile.mkdtemp(prefix="apcore-")
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        runtime = Path(base, ".pilot-beckie")
        runtime.mkdir()
        ap.set_root(runtime)
        ap.execute(["init", "--slug", "herbarium"])

    # T38
    def test_refusal_is_exception(self):
        before = Path(ap.STATE).read_bytes()
        with self.assertRaises(ap.Stop) as caught:
            ap.execute(["ticket", "77", "start"])
        self.assertEqual(before, Path(ap.STATE).read_bytes())
        self.assertIn("таска 77 нет", str(caught.exception))

    # T39
    def test_execute_returns_state(self):
        state, _notes, cmd, _opt = ap.execute(["stage", "manifest"])
        self.assertGreaterEqual(state["rev"], 2)
        self.assertEqual("stage", cmd)
        self.assertEqual(["done", "active"], [x["status"] for x in state["stages"][:2]])

    # T40
    def test_reconcile_by_artifact(self):
        folder = Path(ap.run_dir(ap.read_state()))
        (folder / "spec.md").write_text("# Спецификация\n", encoding="utf-8")
        state, notes, _, _ = ap.execute(["stage", "build"])
        status = {x["id"]: x["status"] for x in state["stages"]}
        self.assertEqual("active", status["build"])
        self.assertEqual("pending", status["manifest"])
        self.assertEqual("done", status["spec"])
        self.assertEqual("done", status["preflight"])
        self.assertTrue([n for n in notes if n.startswith("! этап manifest пропущен")], notes)
        self.assertEqual([], [n for n in notes if "этап spec" in n])


ZONE = timezone(timedelta(hours=5))
MINUTE = 60000


def stamp(minutes):
    return (datetime(2026, 11, 3, 9, 30, tzinfo=ZONE) + timedelta(minutes=minutes)).isoformat()


def derived(minutes, **fields):
    state = {"startedAt": stamp(minutes[0]), "updatedAt": stamp(minutes[-1]),
             "beats": [stamp(m) for m in minutes], "waits": [], "stages": [], "tickets": []}
    state.update(fields)
    return ap.derive(state)


class Timing(unittest.TestCase):
    # T41
    def test_idle_gap_is_capped(self):
        clock = derived([0, 10, 190])["timing"]
        self.assertEqual(int(ap.ts(stamp(190)) * 1000), clock["lastMs"])
        self.assertEqual(55 * MINUTE, clock["runMs"])  # 10 + capped 45

    # T42
    def test_waits_subtract(self):
        paused = derived([0, 10, 40, 50], waits=[{"kind": "plan", "from": stamp(10), "to": stamp(40)}])
        self.assertEqual(20 * MINUTE, paused["timing"]["runMs"])
        open_wait = derived([0, 10], waiting={"kind": "action", "since": stamp(4), "note": None})
        self.assertIsNone(open_wait["timing"]["eta"])
        self.assertEqual(4 * MINUTE, open_wait["timing"]["runMs"])

    # T43
    def test_eta_follows_chain(self):
        state = derived([0, 5, 10, 15, 20, 25, 30],
                        stages=[{"id": "build", "status": "active", "startedAt": stamp(0)}],
                        tickets=[{"id": "01", "status": "done", "startedAt": stamp(0), "finishedAt": stamp(10)},
                                 {"id": "02", "status": "in-progress", "startedAt": stamp(10)},
                                 {"id": "03", "status": "pending", "blockedBy": ["02"]}])
        clock = state["timing"]
        self.assertEqual(20 * MINUTE, state["tickets"][1]["activeMs"])
        self.assertEqual(10, clock["median"])
        self.assertFalse(clock["lateEta"])
        critical = 11  # 02 has 1 min left (10 − 20, floored at 1) + 03 at the median
        left = critical + max(10, 0.5 * (30 + critical)) + 8
        self.assertEqual([ap.rnd(0.75 * left), ap.rnd(1.4 * left)], clock["eta"])


class Pure(unittest.TestCase):
    # T44
    def test_is_ours(self):
        folder = ap.A
        self.assertTrue(ap.is_ours(f"/opt/py/bin/python3.12 -m http.server 49152 --directory {folder} --bind 127.0.0.1"))
        self.assertFalse(ap.is_ours(f"/opt/py/bin/python3.12 -m http.server 49152 --directory {folder}2"))
        self.assertFalse(ap.is_ours(f"node http-server --directory {folder}"))

    # T45
    def test_version_reads_front_matter_only(self):
        nested = "---\ntitle: demo\nextra:\n    version: '2.0.1'\n---\n# demo\n"
        self.assertEqual((2, 0, 1), ap._version(nested))
        self.assertIsNone(ap._version("---\ntitle: demo\n---\nversion: 4.5.6\n"))

    # T46
    def test_skill_declares_version(self):
        self.assertIsNotNone(ap._version((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
