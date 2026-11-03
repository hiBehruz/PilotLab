# Phase 0 — Memory file choice

Read in Phase 0, from `phases/0-preflight.md`. Here you choose the project memory file and who owns it; then you either write the skeleton or keep your hands off the user's file. Later additions during the build, the full description and the ADRs are covered by `phases/9-memory.md`, which you open in Phase 5 and Phase 8, **not now**.

## Why AGENTS.md plus CLAUDE.md

The file this skill creates is `AGENTS.md`, which Claude Code, Codex, Cursor and most agents read natively. The exception is Claude Code: if a `CLAUDE.md` sits in the working directory or in any directory above it, `AGENTS.md` is skipped, and certain sessions never see `AGENTS.md` at all. That is why you add a `CLAUDE.md` holding the single line `@AGENTS.md`. The import does not load the file twice.

## Selection (first match wins)

| # | Found | `memoryFile` | `memoryOwner` | Do |
|---|---|---|---|---|
| 1 | A memory file with `<!-- pilot-beckie:start -->` in it (left by a previous run) | that file | `pilot-beckie` | Update only between the markers. |
| 2 | `CLAUDE.md` or `AGENTS.md` with no markers (it belongs to the user) | that file; with both present, `CLAUDE.md` | `user` | Leave it unwritten for the whole run. Phase 8 proposes additions via `memory-proposal.md` (`phases/9-memory.md`). |
| 3 | Neither | `AGENTS.md` | `pilot-beckie` | Put the skeleton in `AGENTS.md`, and add a `CLAUDE.md` with `@AGENTS.md` as its sole content. |

- If `CLAUDE.md` consists of nothing but `@AGENTS.md`, it is only a pointer; evaluate `AGENTS.md` in its place.
- **If the user already has a `CLAUDE.md`, no `AGENTS.md` is added next to it**: Claude Code would ignore the new file, and two parallel descriptions of the same project diverge over time.
- Record both fields through `init --memory-file <file> --memory-owner <pilot-beckie|user>` (`phases/0-instruments.md`).
- The choice is never a question, in any mode. It is one line in the opening block, no wait:
  - Pilot-owned: «Память проекта — `AGENTS.md` (и `CLAUDE.md` со ссылкой на него).»
  - User-owned: «Память проекта — твой `CLAUDE.md`; я его не трогаю, а в конце предложу, что дописать.»

## Skeleton (Pilot-owned file only)

Do this **ahead of any building**, so that even a run cut short leaves an accurate file. All Pilot content lives between the two exact markers; the text below is the shape, fill the angle brackets.

````markdown
<!-- pilot-beckie:start -->
# <Название проекта>

<Что это и для кого — одна строка.>

## Команды

| Команда | Зачем |
|---|---|
| `<команда>` | поставить зависимости |
| `<команда>` | запустить локально |
| `<команда>` | полная проверка: тесты + типы + линтер |

## Как ведётся работа

Сборки ведёт скилл `/pilot-beckie`; прерванную сборку возобновляет просьба «продолжи Pilot by Beckie». В `.pilot-beckie/` лежат требования, спецификация и таски, а за ходом работы следят по `.pilot-beckie/dashboard.html`. Убрать требование из `manifest.md` может только пользователь.

### Правка без Pilot by Beckie

Мелкие баги и доводка после сборки делаются в обычной сессии, без нового прогона.

Перед правкой нужно прочесть:
1. `.pilot-beckie/PROGRESS.md`: незаконченное, известные баги, договорённости с пользователем.
2. Изменения с момента последней сборки — их показывает команда из первой строки таблицы раздела «История git».
3. По необходимости: `docs/adr/` — почему так; `CONTEXT.md` — словарь; `manifest.md` из папки прогона (она названа в начале `PROGRESS.md`) — что просили.

После правки:
- закоммить по правилам из «История git»;
- допиши строку «дата — что — зачем» в раздел «Правки без Pilot by Beckie» файла `PROGRESS.md`;
- убери исправленный пункт из «Не доделано» или «Известные баги»;
- договорённость пользователя, которую следующей сборке нельзя пересматривать, запиши его словами отдельной строкой в «Договорились — не пересматривать».

### История git

Историю целиком не читай: под каждый вопрос нужен свой срез.

| Что нужно узнать | Команда |
|---|---|
| Изменения, сделанные после последней сдачи | `git log --oneline "$(git log -1 --format=%h --grep='^Pilot by Beckie: сборка сдана')"..HEAD -- . ':(exclude).pilot-beckie'` |
| Работа по одному требованию | `git log --oneline --grep="R02"` |
| Последние изменения файла | `git log --oneline -10 -- <file>` |
| Когда код появился или исчез | `git log --oneline -S "<fragment>"` |
| Почему строка такая | `git blame -L <from>,<to> <file>`, затем `git show <sha>` |
| Состав коммита | `git show --stat <sha>` |

Если в срезе больше ~30 коммитов, поручи его субагенту с просьбой сжать до десяти строк.

Коммит: в заголовке — что сделано (как `fix: …`), в теле — зачем; при правке требования из манифеста добавь `--trailer "Requirements: R02"`. Заголовок `Pilot by Beckie: сборка сдана` использует только сам Pilot: именно по нему ищут последнюю сборку.
<!-- pilot-beckie:end -->
````

- **Skip any command you cannot confirm yet.** A made-up command does more harm than an absent one.
- Content outside the markers belongs to the user: never edit, move or remove it.
- New feature in an already configured repo: the file exists — top it up, never rewrite it. When a Pilot block written by an earlier version has no «История git» or «Правка без Pilot by Beckie» subsection, add the missing ones now, because they are how sessions without this skill find `PROGRESS.md` and leave traceable commits.
