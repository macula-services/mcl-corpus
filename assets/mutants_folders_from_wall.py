#!/usr/bin/env python3
"""Mutation test for folders_from_wall: each rule is a mutant, and a mutant that
survives (the pinning test still passes) shows the test is not aimed at it.

For each rule it holds the file's bytes, writes the mutated form, runs
test_folders_from_wall.py, and restores the bytes in a finally. A mutant is
killed when the test fails under it; a survivor means the test must be re-aimed
at that rule.

Run with python3, no dependencies: python3 assets/mutants_folders_from_wall.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE / "folders_from_wall.py"
TEST = HERE / "test_folders_from_wall.py"

# (label, the bytes to find, the bytes to put in their place). Each search
# string names one rule and appears exactly once in the source.
MUTANTS: list[tuple[str, str, str]] = [
    ("a desk is one folder", "cmd.append(name)", "cmd.append(\"bogus_\" + name)"),
    ("a PRJ folder drops the version", "prj.append(_without_version(desk[\"event\"]))", "prj.append(desk[\"event\"])"),
    ("a policy folder names the command", "cmd.append(f\"on_{on[0]}_maybe_{policy['maybe']}\")", "cmd.append(f\"on_{on[0]}_maybe_bogus\")"),
    ("an emitter folder says to_mesh", "cmd.append(f\"emit_{event}_to_mesh\")", "cmd.append(f\"emit_{event}_from_mesh\")"),
    ("a listener folder says from_mesh", "cmd.append(f\"on_{arriving['fact']}_from_mesh_{arriving['maybe']}\")", "cmd.append(f\"on_{arriving['fact']}_from_pg_{arriving['maybe']}\")"),
    ("a question is one folder", "qry.append(question)", "qry.append(question + \"_bogus\")"),
    ("a multi-input policy is refused", "if len(on) != 1:", "if False:"),
    ("a folder asked for twice is refused", "if twice:", "if False:"),
]


def main() -> int:
    original = SOURCE.read_bytes()
    survivors: list[str] = []
    for label, find, replace in MUTANTS:
        mutated = original.replace(find.encode(), replace.encode())
        if mutated == original:
            print(f"UNREACHED {label}: the mutation did not change the source")
            survivors.append(label)
            continue
        SOURCE.write_bytes(mutated)
        try:
            run = subprocess.run([sys.executable, str(TEST)], capture_output=True, text=True)
        finally:
            SOURCE.write_bytes(original)
        if run.returncode == 0:
            print(f"SURVIVOR {label}: the test passes under the mutant")
            survivors.append(label)
        else:
            print(f"killed {label}")
    if survivors:
        print(f"mutants_folders_from_wall: {len(survivors)} survivor(s): {', '.join(survivors)}")
        return 1
    print("mutants_folders_from_wall: every rule is killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
