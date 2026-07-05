# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

No source code exists yet. This section describes the intended project so implementation can start from a clear spec.

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

When code is added to this repository, update this file with:
- The commands to install dependencies, run the tool, lint, and run tests (including running a single test)
- The high-level architecture (e.g., how XML is parsed/namespaced, how files/directories are discovered, CLI entry point layout)
