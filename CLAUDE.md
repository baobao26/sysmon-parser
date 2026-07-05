# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Implemented. The tool is a single flat script, `parser.py` — no package structure, no `pyproject.toml`, no external dependencies (standard library only).

## Commands

- **Run**: `python parser.py <xml_path> [filters] [--format json|jsonl|csv] [--stats]` (e.g. `python parser.py samples/event1.xml`, `python parser.py samples/multi_events.xml --image powershell`, `python parser.py samples/large_export.xml --stats`). See `README.md` for the full filter/format reference.
- **Install dependencies**: none — standard library only (`argparse`, `csv`, `json`, `xml.etree.ElementTree`).
- **Lint**: no linter is configured in this repo.
- **Tests**: none exist yet. There is no test suite or test runner configured — verification so far has been manual, ad hoc CLI runs against the fixtures in `samples/`.

## Project goal

A Python tool that parses Sysmon event logs that have been exported to XML (e.g. via `wevtutil` or `Get-WinEvent`), and extracts key fields from **Event ID 1 (Process Creation)** events.

- **Input**: exported Sysmon-to-XML files (not raw `.evtx`).
- **Output**: JSON.

## Fields to extract (per Process Creation event)

- `EventID`
- `UtcTime`
- `Image` (process path)
- `CommandLine`
- `User`
- `IntegrityLevel`
- `ParentImage`
- `ParentCommandLine`
- `Computer`
- `Hashes`

## Architecture

- **Single entry point**: `parser.py`, run directly with `python parser.py <xml_path>`. All logic lives in this one file — `iter_event_elements`, `parse_event`, `matches_filters`, `compute_stats`, `main`.
- **XML namespace handling**: Sysmon's exported XML declares the default namespace `http://schemas.microsoft.com/win/2004/08/events/event`. Every `.find()`/`.findall()` call goes through the module-level `NS` dict rather than assuming unqualified tag names, since unqualified lookups silently return nothing under a default namespace.
- **Two supported input shapes**: `wevtutil` and `Get-WinEvent` exports don't share one wrapper structure — some are a single `<Event>` root, others wrap multiple events in an `<Events>` root. `iter_event_elements(root)` normalizes over both by checking the root's local tag name, so the rest of the code only ever deals with individual `<Event>` elements.
- **Per-event parsing**: `parse_event(event)` extracts `System` and `EventData` from one `<Event>`, returns `None` for anything that isn't a well-formed `EventID == 1` event (missing sections, wrong event type). The caller filters out `None`s, so mixed-content exports or malformed entries don't abort the run.
- **Filtering**: applied after extraction, on the already-built result dicts (not on raw XML elements) via `matches_filters(event, args)`. `--image`/`--user`/`--integrity-level` are single-value and AND together; `--command-line` uses `action="append"` and OR's its substrings. All text matching is case-insensitive via `.casefold()`. `--integrity-level` uses a custom `argparse` `type=` function (`integrity_level_type`) rather than `choices=`, since `choices=` alone is case-sensitive.
- **Output formatting**: `--format` selects one of `write_json`/`write_jsonl`/`write_csv` (looked up from the `WRITERS` dict) — `json` (default) is a single indented array, `jsonl` is one compact JSON object per line, `csv` uses `csv.DictWriter` with `FIELDS` as the header row.
- **Stats mode**: `--stats` bypasses `WRITERS` entirely and prints a single JSON object from `compute_stats(results)` (total events, unique `Image`s, unique `User`s, counts by `IntegrityLevel`) — computed over the already-filtered result set, and it ignores `--format`.
- Sample fixtures for manual testing live in `samples/`: `event1.xml` (single event), `multi_events.xml` (3-event process chain), `large_export.xml` (85 events — 80 Event ID 1 across 15 images/3 users/4 integrity levels, plus 5 Event ID 3 network events mixed in to exercise the non-Event-ID-1 skip path). See `README.md` for usage details and `HANDOFF.md` for design-decision rationale and open items.
