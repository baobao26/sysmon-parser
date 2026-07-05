# Handoff: sysmon-parser

## What we built

A single-file Python CLI (`parser.py`) that extracts Process Creation (Sysmon Event ID 1) fields from exported Sysmon XML logs and prints them as JSON.

- **Input**: a Sysmon event log already exported to XML (e.g. via `wevtutil` or `Get-WinEvent`) — not a raw `.evtx` file. Two export shapes are handled transparently:
  - a single `<Event>` document as the XML root
  - an `<Events>` wrapper containing multiple `<Event>` children
- **Output**: one entry per matching event, in one of three formats selected by `--format` (default `json`): a JSON array, `jsonl` (one JSON object per line), or `csv` (with a header row). Fields: `EventID`, `UtcTime`, `Image`, `CommandLine`, `User`, `IntegrityLevel`, `ParentImage`, `ParentCommandLine`, `Computer`, `Hashes`.
- Only events with `EventID == 1` are extracted; other event types (or malformed events missing `System`/`EventData`) are silently skipped.
- Optional CLI filters narrow the output: `--image` (substring), `--user` (exact), `--integrity-level` (restricted to `High`/`Medium`/`Low`/`System`), `--command-line` (substring, repeatable/OR'd). All text matching is case-insensitive. Different filters combine with AND.
- `--stats` switches to triage mode: instead of individual events, it prints one JSON object with `TotalEvents`, `UniqueProcesses`, `UniqueUsers`, and `EventsByIntegrityLevel`, computed over the already-filtered result set. It ignores `--format`.

Supporting files:
- `samples/event1.xml` — a single `whoami.exe` Process Creation event.
- `samples/multi_events.xml` — a 3-event process chain (`explorer.exe → cmd.exe → powershell.exe -nop -w hidden -ep bypass → certutil.exe -urlcache ...`) wrapped in `<Events>`, used to exercise multi-event parsing and filtering.
- `samples/large_export.xml` — a generated 85-event fixture (80 Event ID 1 events spread across 15 process images and 3 users, evenly split across all 4 integrity levels, plus 5 Event ID 3 network events interleaved to exercise the non-Event-ID-1 skip path) — used to validate `--stats` and `--format` at a larger scale than the hand-written fixtures.
- `README.md` — full CLI usage, format, and filter reference with worked examples.
- `.gitignore` — excludes `.claude/settings.local.json` (machine-local permission config) and Python build artifacts.

No external dependencies — standard library only (`argparse`, `csv`, `json`, `xml.etree.ElementTree`).

## How to use it

```
python parser.py <xml_path> [filters]
```

Examples:

```
python parser.py samples/event1.xml
python parser.py samples/multi_events.xml
python parser.py samples/multi_events.xml --image powershell
python parser.py samples/multi_events.xml --user "CONDEF\Administrator"
python parser.py samples/multi_events.xml --integrity-level high --command-line urlcache --command-line="-nop"
python parser.py samples/multi_events.xml --format jsonl
python parser.py samples/multi_events.xml --format csv
python parser.py samples/large_export.xml --stats
```

Note: a filter value starting with `-` (e.g. `-enc`) must be passed as `--command-line="-enc"`, not as a separate argument, or argparse will misread it as a new flag. Full details are in `README.md`.

Requires Python 3.10+ (uses the `X | None` type-hint syntax).

## What's left to do

Nothing was requested beyond the current scope, but if this project continues, the natural next steps are:

- **No automated tests.** All verification so far has been manual, ad hoc CLI runs against the two sample files. There's no `pytest`/`unittest` suite, so regressions in `parse_event`, `iter_event_elements`, or the filter logic wouldn't be caught automatically.
- **No handling for other Sysmon event types.** Only Event ID 1 is supported; extending to other Sysmon event IDs (e.g. Event ID 3 network connections, Event ID 11 file creation) would need new field mappings and likely a `--event-id` selector.
- **No directory/glob input support.** The tool takes exactly one file path; batch-processing a directory of exported XML files would need to be added explicitly if that becomes a use case.
- **No output-to-file option.** Output always goes to stdout; a `-o`/`--output` flag might be worth adding if this gets wired into a larger pipeline.
- **Minimal error handling.** A missing/invalid file path currently surfaces as a raw Python traceback (from `ET.parse`) rather than a clean CLI error message.
- **Git identity used for commits is a placeholder.** The initial commit was made with `user.name`/`user.email` set locally to the email on file (`ung.katrina@gmail.com`) since no git identity existed in this environment — confirm this is the desired identity before pushing anywhere.

## Decisions made and why

- **Flat `parser.py` script, not a packaged project.** Early on, an attempt to scaffold a full package (`pyproject.toml`, `src/` layout, console-script entry point) was explicitly rejected in favor of a single script — this is a small, self-contained tool, not a distributable library.
- **Namespace-aware XML parsing.** Sysmon's exported XML declares the default namespace `http://schemas.microsoft.com/win/2004/08/events/event`; every `.find()`/`.findall()` call goes through an `NS` dict rather than assuming unqualified tag names, since unqualified lookups silently return nothing under a default namespace.
- **Two supported root shapes.** `wevtutil` and `Get-WinEvent` don't necessarily produce the same wrapper structure — some exports are a single `<Event>`, others wrap multiple in `<Events>`. `iter_event_elements()` normalizes over both so the rest of the code doesn't care which shape it got. This was added after `samples/multi_events.xml` exposed a crash in the original single-event-only implementation.
- **Silent skipping over raising, for non-Event-ID-1 or malformed events.** A mixed-content export (multiple event types, or occasional malformed entries) shouldn't abort the whole run — `parse_event` returns `None` for anything that isn't a well-formed Event ID 1, and the caller filters those out.
- **Case-insensitive filters, via `.casefold()`.** Confirmed with the user: `Image`, `User`, `IntegrityLevel`, and `CommandLine` filters should all be case-insensitive, matching how Windows itself treats paths and usernames. `.casefold()` was chosen over `.lower()` deliberately for more robust case folding.
- **`--integrity-level` restricted to 4 known values via a custom `type=` function, not `choices=`.** `argparse`'s built-in `choices=` does exact, case-sensitive matching, which would reject `high`/`HIGH`. A custom `integrity_level_type()` normalizes the input's case first, then validates against the canonical list, giving a clear error message listing valid options.
- **`--command-line` is repeatable and OR's substrings (`action="append"`), while other filters are single-value and AND together.** This mirrors a natural use case — "match if the command line contains any of these known-suspicious substrings" — without conflating it with the AND-combination semantics across different filter *fields*.
- **Output is always a JSON array (in `json` mode), even for one match or zero matches.** Keeps the output shape consistent regardless of input shape (single `<Event>` vs `<Events>` wrapper) or how many filters narrowed the result, so downstream tooling never needs to special-case "one result" vs "many."
- **`--format` adds `jsonl` and `csv` alongside the default `json`, dispatched through a `WRITERS` dict rather than an if/elif chain.** `jsonl` exists for streaming/piping into line-oriented tools (e.g. `grep`, `jq -c` per line) without loading a whole array; `csv` uses `csv.DictWriter` (not manual string joining) so fields containing commas or quotes — notably `Hashes` and quoted `CommandLine` values — are escaped correctly per the CSV spec instead of corrupting the output.
- **`--stats` is a separate mode, not a `--format` choice.** It answers a different question ("what's in this file") rather than "how do I encode the matched events," and it composes with existing filters (stats over a filtered subset) rather than requiring its own filter logic. Deliberately ignores `--format` since its output is always one JSON object regardless.
- **`.claude/settings.local.json` is gitignored, not committed.** It's machine-local tool permission config, not project source, so it was excluded from the initial commit via `.gitignore` rather than tracked.
