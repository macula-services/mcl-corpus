#!/usr/bin/env python3
"""The wall-to-tree rule as a function.

Given one Division's wall file (its meaning, names only), return the folders
its three applications must have, keyed "cmd", "prj" and "qry", by the table in
philosophy/EVENT_STORMING.md ("What each note becomes").

The function is not a restated list. It derives each folder name from the
naming rules in skills/NAMING_CONVENTIONS.md and skills/INTEGRATION_ACTORS.md.
test_folders_from_wall.py holds it to the page by reading the book club's
worked example out of philosophy/EVENT_STORMING.md and comparing exactly, so
the page and the function cannot drift apart.

Run with python3, no dependencies.
"""
from __future__ import annotations

import re

_VERSION = re.compile(r"_v\d+$")


def _without_version(name: str) -> str:
    return _VERSION.sub("", name)


def folders_from_wall(wall: dict) -> dict[str, list[str]]:
    """Map a wall file to the folders its CMD, PRJ and QRY apps must hold.

    Raises ValueError, naming the note, where the wall cannot be read to a
    folder set: a policy with more than one input event, a leaving fact that
    is no desk's event, or two notes asking for one CMD or QRY folder. Each is
    refused, never guessed.
    """
    cmd: list[str] = []
    prj: list[str] = []
    qry: list[str] = []

    events_of_desks: dict[str, str] = {}
    for desk in wall["desks"]:
        name = desk["name"]
        cmd.append(name)
        events_of_desks[desk["event"]] = name
        if desk.get("feeds"):
            prj.append(_without_version(desk["event"]))

    for policy in wall.get("policies", []):
        on = policy["on"]
        if len(on) != 1:
            raise ValueError(
                f"a policy with {len(on)} inputs ({', '.join(on)}) has no decided folder name"
            )
        cmd.append(f"on_{on[0]}_maybe_{policy['maybe']}")

    for event in wall.get("facts_that_leave", []):
        if event not in events_of_desks:
            raise ValueError(f"a fact that leaves is no desk's event: {event}")
        cmd.append(f"emit_{event}_to_mesh")

    for arriving in wall.get("facts_that_arrive", []):
        cmd.append(f"on_{arriving['fact']}_from_mesh_{arriving['maybe']}")

    for read_model in wall.get("read_models", []):
        for question in read_model["questions"]:
            qry.append(question)

    # Two notes that ask for one CMD or QRY folder would collapse into it unseen
    # (two desks of one name, a policy written twice). PRJ is left out: two
    # versions of one event share their projection folder by the table's rule.
    for app, folders in (("cmd", cmd), ("qry", qry)):
        twice = sorted({folder for folder in folders if folders.count(folder) > 1})
        if twice:
            raise ValueError(f"the wall asks for {', '.join(twice)} more than once in {app}")

    return {"cmd": cmd, "prj": prj, "qry": qry}


if __name__ == "__main__":
    import json
    import sys

    with open(sys.argv[1], encoding="utf-8") as handle:
        wall = json.load(handle)
    for app, folders in folders_from_wall(wall).items():
        for folder in folders:
            print(f"{app}\t{folder}")
