#!/usr/bin/env python3
"""The pin: hold check_wall_schema to the "names only" shape.

A wall in the schema's shape passes, and each way of leaving the shape — an
extra key, a value that is not a name, a missing required key — is refused
naming its JSON path. The cases are built from a minimal wall, not copied from
the schema, so the reader and the schema cannot drift apart while this stays
green.

Run with python3, no dependencies: python3 assets/test_wall_schema.py
"""
from __future__ import annotations

from check_wall_schema import check_wall_schema


def _wall() -> dict:
    return {
        "division": "demo",
        "lanes": ["Staff"],
        "clock": None,
        "desks": [
            {"name": "open_account", "lane": "Staff", "event": "account_opened_v1", "feeds": ["accounts"]}
        ],
        "policies": [],
        "read_models": [],
        "facts_that_leave": [],
        "facts_that_arrive": [],
        "hot_spots": [],
        "clock_notes": [],
        "dossiers": [],
    }


CASES = [
    ("a wall in the schema's shape passes", _wall(), []),
    (
        "an extra key is refused, naming its path",
        {**_wall(), "pipeline": ["validate", "persist"]},
        ["/pipeline: not a name the schema allows"],
    ),
    (
        "a field-typed event is refused, naming its path",
        {
            **_wall(),
            "desks": [
                {"name": "open_account", "lane": "Staff", "event": {"type": "event"}, "feeds": []}
            ],
        },
        ["/desks/0/event: expected string, got object"],
    ),
    (
        "a missing required key is refused, naming its path",
        {k: v for k, v in _wall().items() if k != "division"},
        ["/division: required by the schema"],
    ),
    (
        "a repeated item in a unique list is refused, naming both places",
        {**_wall(), "lanes": ["Staff", "Staff"]},
        ["/lanes/1: repeats /lanes/0"],
    ),
    (
        "a list shorter than its minimum is refused, naming its path",
        {**_wall(), "policies": [{"on": [], "maybe": "greet_member"}]},
        ["/policies/0/on: needs at least 1 item(s), has 0"],
    ),
]


def main() -> int:
    from check_wall_schema import _unknown_keywords

    failures: list[str] = []
    if _unknown_keywords({"type": "object", "pattern": "x"}) != ["/: pattern"]:
        failures.append("a schema keyword the reader does not apply is not named at load")
    for label, wall, want in CASES:
        got = check_wall_schema(wall)
        if got != want:
            failures.append(f"{label}: expected {want}, got {got}")
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("check_wall_schema refuses each way of leaving the shape, by JSON path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
