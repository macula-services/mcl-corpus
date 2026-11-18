#!/usr/bin/env python3
"""The pin: hold folders_from_wall to the page.

Reads philosophy/EVENT_STORMING.md at test time and compares exactly. The
book club's worked example supplies both sides: the desk table becomes the
wall file, and the tree block becomes the expected folders. No copy of the
example lives here, so if the page and the function drift apart, this fails.

Run with python3, no dependencies: python3 assets/test_folders_from_wall.py
"""
from __future__ import annotations

import pathlib
import re

from folders_from_wall import folders_from_wall

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE.parent / "philosophy" / "EVENT_STORMING.md"


def _section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    stop = text.index(end, begin)
    return text[begin:stop]


def _desk_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if line.startswith("|") and "Desk (blue)" not in line and not re.match(r"^\|[-\s|]+\|$", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 6:
                rows.append(cells)
    return rows


def _read_models(text: str) -> list[dict]:
    match = re.search(r"Read models and their questions:\s*(.+)", text)
    sentence = match.group(1) if match else ""
    models: list[dict] = []
    for segment in sentence.split(";"):
        segment = segment.strip()
        if not segment:
            continue
        table = segment.split(" answers")[0].strip()
        questions = re.findall(r"`([^`]+)`", segment)
        models.append({"table": table, "questions": questions})
    return models


def _tree_folders(text: str) -> dict[str, list[str]]:
    fence = text.index("The tree it produces:")
    lines = text[fence:].splitlines()
    # Skip past the opening ``` fence.
    i = lines.index("```") + 1
    folders: dict[str, list[str]] = {"cmd": [], "prj": [], "qry": []}
    current: str | None = None
    while i < len(lines) and lines[i].strip() != "```":
        line = lines[i]
        header = re.match(r"apps/(host|project|query)_\w+/src/", line)
        if header:
            current = {"host": "cmd", "project": "prj", "query": "qry"}[header.group(1)]
        elif current is not None:
            folders[current].extend(re.findall(r"\b([a-z][a-z0-9_]*)/", line))
        i += 1
    return folders


def _wall(rows: list[list[str]], models: list[dict], expected: dict[str, list[str]]) -> dict:
    desks: list[dict] = []
    leaves: list[str] = []
    hot_spots: list[str] = []
    lanes: list[str] = []
    for desk, lane, event, _policy, feeds, leaves_col in rows:
        desk_name = desk.strip("`")
        desks.append(
            {"name": desk_name, "lane": lane, "event": event.strip("`"), "feeds": [feeds] if feeds else []}
        )
        if lane not in lanes:
            lanes.append(lane)
        if leaves_col == "yes":
            leaves.append(event.strip("`"))
        elif leaves_col.startswith("hot spot"):
            hot_spots.append(event.strip("`"))

    # The one policy, taken from the tree block's own folder name, so the
    # function's `on_{event}_maybe_{command}` template is held to the page.
    policy_folders = [f for f in expected["cmd"] if "_maybe_" in f and f.startswith("on_")]
    policies: list[dict] = []
    for folder in policy_folders:
        rest = folder[len("on_"):]
        on, maybe = rest.split("_maybe_", 1)
        policies.append({"on": [on], "maybe": maybe})

    return {
        "division": "bookclub",
        "lanes": lanes,
        "clock": None,
        "desks": desks,
        "policies": policies,
        "read_models": models,
        "facts_that_leave": leaves,
        "facts_that_arrive": [],
        "hot_spots": hot_spots,
        "clock_notes": [],
        "dossiers": [],
    }


def _empty_wall() -> dict:
    return {
        "division": "bookclub",
        "lanes": [],
        "clock": None,
        "desks": [],
        "policies": [],
        "read_models": [],
        "facts_that_leave": [],
        "facts_that_arrive": [],
        "hot_spots": [],
        "clock_notes": [],
        "dossiers": [],
    }


PLANTED = [
    (
        "a fact that arrives becomes its listener folder",
        {**_empty_wall(),
         "facts_that_arrive": [{"fact": "app_available_v1", "maybe": "install_plugin"}]},
        {"cmd": ["on_app_available_v1_from_mesh_install_plugin"], "prj": [], "qry": []},
    ),
    (
        "a policy with two inputs is refused by name",
        {**_empty_wall(), "policies": [{"on": ["a_v1", "b_v1"], "maybe": "c"}]},
        ValueError,
    ),
    (
        "a leaving fact that is no desk's event is refused by name",
        {**_empty_wall(),
         "desks": [{"name": "register_member", "lane": "Member", "event": "member_registered_v1", "feeds": []}],
         "facts_that_leave": ["no_such_event_v1"]},
        ValueError,
    ),
]


def _check_planted() -> list[str]:
    failures: list[str] = []
    for label, wall, want in PLANTED:
        try:
            got = folders_from_wall(wall)
        except ValueError as exc:
            if want is ValueError:
                continue
            failures.append(f"{label}: unexpectedly refused: {exc}")
            continue
        if want is ValueError:
            failures.append(f"{label}: expected refusal, got {got}")
            continue
        if got != want:
            failures.append(f"{label}: expected {want}, got {got}")
    return failures


def main() -> int:
    text = PAGE.read_text(encoding="utf-8")
    worked = _section(text, "## The worked example: the book club", "## What this page is not")
    rows = _desk_rows(worked)
    models = _read_models(worked)
    expected = _tree_folders(worked)

    got = folders_from_wall(_wall(rows, models, expected))
    failures: list[str] = []
    for app in ("cmd", "prj", "qry"):
        want = sorted(expected[app])
        have = sorted(got[app])
        if want != have:
            failures.append(
                f"{app}: expected {want}, got {have} "
                f"(missing {sorted(set(want) - set(have))}, extra {sorted(set(have) - set(want))})"
            )
    failures += _check_planted()
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("folders_from_wall matches philosophy/EVENT_STORMING.md exactly, and the planted cases hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
