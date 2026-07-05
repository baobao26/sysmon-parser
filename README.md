# sysmon-parser

Extracts key fields from Sysmon Event ID 1 (Process Creation) events and outputs them as JSON.

## Requirements

- Python 3.10+
- No external dependencies (standard library only)

## Input

`parser.py` takes the path to a Sysmon event log that has been exported to XML (e.g. via `wevtutil` or `Get-WinEvent`). Two shapes are supported:

- A single `<Event>` document (see `samples/event1.xml`)
- An `<Events>` wrapper containing multiple `<Event>` children (see `samples/multi_events.xml`)

Only events with `EventID == 1` are extracted; other event types in the file are silently skipped.

## Output

Output goes to stdout, one entry per matching event, with these fields:

`EventID`, `UtcTime`, `Image`, `CommandLine`, `User`, `IntegrityLevel`, `ParentImage`, `ParentCommandLine`, `Computer`, `Hashes`

The output format is controlled by `--format` (default `json`):

| Format | Description |
| --- | --- |
| `json` | A single JSON array containing all matching events (default) |
| `jsonl` | One JSON object per line, newline-delimited — convenient for streaming/piping into other line-oriented tools |
| `csv` | CSV with a header row; fields containing commas or quotes (e.g. `Hashes`, quoted `CommandLine`) are quoted per standard CSV escaping |

```
python parser.py samples/multi_events.xml --format jsonl
python parser.py samples/multi_events.xml --format csv
```

## Usage

```
python parser.py <xml_path> [filters]
```

Examples:

```
python parser.py samples/event1.xml
python parser.py samples/multi_events.xml
```

## Filters

All filters are optional. When multiple different filters are given, they combine with AND (an event must satisfy all of them). Text matching is case-insensitive.

| Filter | Match type | Example |
| --- | --- | --- |
| `--image` | substring | `--image powershell` |
| `--user` | exact | `--user "CONDEF\Administrator"` |
| `--integrity-level` | exact, restricted to `High`/`Medium`/`Low`/`System` | `--integrity-level high` |
| `--command-line` | substring, repeatable (OR) | `--command-line encoded --command-line -enc` |

`--command-line` is the one filter that can be repeated; an event matches if **any** of the given substrings appear in its `CommandLine`.

`--integrity-level` rejects any value outside the four known levels with a usage error, e.g.:

```
parser.py: error: argument --integrity-level: invalid choice: 'Bogus' (choose from High, Medium, Low, System)
```

### Note: filter values starting with `-`

Because these are standard argparse options, a filter value that starts with `-` (like `-enc`) will be misread as a new flag if passed as a separate argument:

```
--command-line -enc      # fails: "expected one argument"
--command-line="-enc"    # works
```

Use the `--flag=value` form for any substring that starts with a dash.

## Examples

```
# All process creation events from an export
python parser.py samples/multi_events.xml

# Only powershell.exe launches
python parser.py samples/multi_events.xml --image powershell

# Everything run by a specific user
python parser.py samples/multi_events.xml --user "CONDEF\Administrator"

# High-integrity events with a suspicious command line
python parser.py samples/multi_events.xml --integrity-level high --command-line urlcache --command-line="-nop"
```
