# State snapshot

Last updated: 2026-07-05

## Repo

- Location: `C:\Users\PC\sysmon-parser`
- Remote: `origin` → https://github.com/baobao26/sysmon-parser (public)
- Branch: `master`, tracking `origin/master`, working tree clean
- Commits:
  - `712cd5c` — Add Sysmon Event ID 1 XML-to-JSON parser (`parser.py`, `CLAUDE.md`, `README.md`, `samples/event1.xml`, `samples/multi_events.xml`, `.gitignore`)
  - `9eac191` — Add HANDOFF.md summarizing project, usage, remaining work, and design decisions

## Files

| File | Purpose |
| --- | --- |
| `parser.py` | The CLI tool itself |
| `CLAUDE.md` | Project spec / guidance for Claude Code |
| `README.md` | CLI usage and filter reference |
| `HANDOFF.md` | What was built, how to use it, what's left, and why key decisions were made |
| `samples/event1.xml` | Single-event fixture (`whoami.exe`) |
| `samples/multi_events.xml` | 3-event process-chain fixture |
| `.gitignore` | Excludes `.claude/settings.local.json` and Python build artifacts |
| `.claude/settings.local.json` | Local tool permission config — gitignored, not pushed |

## Environment (this machine)

- Python 3.12.10 installed via winget at `C:\Users\PC\AppData\Local\Programs\Python\Python312\python.exe` — **not yet on PATH** in this session's shell; call by full path or open a new terminal window to pick up the updated PATH.
- Git 2.55.0.2 installed via winget at `C:\Program Files\Git\cmd\git.exe` — same PATH caveat as Python.
- GitHub CLI 2.96.0 installed via winget at `C:\Program Files\GitHub CLI\gh.exe` — same PATH caveat.
- `gh` is authenticated as GitHub account `baobao26` (token scopes: `gist`, `read:org`, `repo`, `workflow`).
- A new terminal window opened after these installs should have all three on PATH normally (`python`, `git`, `gh` callable by name); this session's shell was started before the installs and doesn't see the update.

## Outstanding

See `HANDOFF.md` → "What's left to do" for functional/scope items (no automated tests, single-event-ID support only, no directory input, no output-to-file flag, minimal error handling on bad paths). Nothing is currently in progress; the repo is in a clean, pushed state.
