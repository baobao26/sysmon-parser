#!/usr/bin/env python3
"""Extract Process Creation (Event ID 1) fields from an exported Sysmon XML event."""

import argparse
import json
import xml.etree.ElementTree as ET

NS = {"ns": "http://schemas.microsoft.com/win/2004/08/events/event"}

INTEGRITY_LEVELS = ["High", "Medium", "Low", "System"]

FIELDS = [
    "EventID",
    "UtcTime",
    "Image",
    "CommandLine",
    "User",
    "IntegrityLevel",
    "ParentImage",
    "ParentCommandLine",
    "Computer",
    "Hashes",
]


def iter_event_elements(root: ET.Element):
    """Yield <Event> elements from a root that is either a single <Event>
    or an <Events> wrapper containing multiple <Event> children."""
    root_tag = root.tag.rsplit("}", 1)[-1]
    if root_tag == "Events":
        yield from root.findall("ns:Event", NS)
    else:
        yield root


def parse_event(event: ET.Element) -> dict | None:
    system = event.find("ns:System", NS)
    event_data = event.find("ns:EventData", NS)
    if system is None or event_data is None:
        return None

    event_id = system.findtext("ns:EventID", namespaces=NS)
    if event_id != "1":
        return None

    data = {d.get("Name"): d.text for d in event_data.findall("ns:Data", NS)}

    return {
        "EventID": event_id,
        "UtcTime": data.get("UtcTime"),
        "Image": data.get("Image"),
        "CommandLine": data.get("CommandLine"),
        "User": data.get("User"),
        "IntegrityLevel": data.get("IntegrityLevel"),
        "ParentImage": data.get("ParentImage"),
        "ParentCommandLine": data.get("ParentCommandLine"),
        "Computer": system.findtext("ns:Computer", namespaces=NS),
        "Hashes": data.get("Hashes"),
    }


def integrity_level_type(value: str) -> str:
    normalized = value.strip().casefold()
    for level in INTEGRITY_LEVELS:
        if level.casefold() == normalized:
            return level
    raise argparse.ArgumentTypeError(
        f"invalid choice: {value!r} (choose from {', '.join(INTEGRITY_LEVELS)})"
    )


def matches_filters(event: dict, args: argparse.Namespace) -> bool:
    if args.image and args.image.casefold() not in (event.get("Image") or "").casefold():
        return False
    if args.user and args.user.casefold() != (event.get("User") or "").casefold():
        return False
    if args.integrity_level and args.integrity_level != (event.get("IntegrityLevel") or ""):
        return False
    if args.command_line:
        command_line = (event.get("CommandLine") or "").casefold()
        if not any(substr.casefold() in command_line for substr in args.command_line):
            return False
    return True


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Extract Sysmon Event ID 1 fields as JSON.")
    arg_parser.add_argument("xml_path", help="Path to an exported Sysmon XML event file")
    arg_parser.add_argument("--image", help="Filter to events whose Image contains this substring (case-insensitive)")
    arg_parser.add_argument("--user", help="Filter to events with this User (case-insensitive exact match)")
    arg_parser.add_argument(
        "--integrity-level",
        type=integrity_level_type,
        help="Filter to events with this IntegrityLevel (High, Medium, Low, System; case-insensitive)",
    )
    arg_parser.add_argument(
        "--command-line",
        action="append",
        help="Filter to events whose CommandLine contains this substring (case-insensitive). "
        "Repeatable; matches if ANY given substring is found (OR).",
    )
    args = arg_parser.parse_args()

    root = ET.parse(args.xml_path).getroot()
    results = [parsed for event in iter_event_elements(root) if (parsed := parse_event(event)) is not None]
    results = [r for r in results if matches_filters(r, args)]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
