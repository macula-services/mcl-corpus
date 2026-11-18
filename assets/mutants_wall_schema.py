#!/usr/bin/env python3
"""Mutation test for check_wall_schema: each rule is a mutant, and a mutant
that survives (the pinning test still passes) shows the test is not aimed at it.

The test runs with -B, so no bytecode of a mutant is cached: a mutant of the
same length restored within the same second would otherwise leave its .pyc
valid, and every later import would run the mutant.

For each rule it holds the file's bytes, writes the mutated form, runs
test_wall_schema.py, and restores the bytes in a finally. A mutant is killed
when the test fails under it.

Run with python3, no dependencies: python3 assets/mutants_wall_schema.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE / "check_wall_schema.py"
TEST = HERE / "test_wall_schema.py"

# (label, the bytes to find, the bytes to put in their place). Each search
# string names one rule and appears exactly once in the source.
MUTANTS: list[tuple[str, str, str]] = [
    ("the schema is applied", 'return _check(wall, SCHEMA, "")', "return []"),
    ("an extra key is refused", "if key not in props:", "if False:"),
    ("a wrong type is refused", 'if schema.get("type") is not None and not _matches(value, schema["type"]):', "if False:"),
    ("a required key is refused", "if key not in value:", "if False:"),
    ("a repeated item is refused", "if item in seen[:i]:", "if False:"),
    ("a short list is refused", 'if len(value) < schema.get("minItems", 0):', "if False:"),
    ("an unknown schema keyword is named", "if key not in APPLIED | DESCRIBING]", "if False]"),
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
            run = subprocess.run([sys.executable, "-B", str(TEST)], capture_output=True, text=True)
        finally:
            SOURCE.write_bytes(original)
        if run.returncode == 0:
            print(f"SURVIVOR {label}: the test passes under the mutant")
            survivors.append(label)
        else:
            print(f"killed {label}")
    if survivors:
        print(f"mutants_wall_schema: {len(survivors)} survivor(s): {', '.join(survivors)}")
        return 1
    print("mutants_wall_schema: every rule is killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
