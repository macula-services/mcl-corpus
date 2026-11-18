#!/usr/bin/env python3
"""A dependency-free reader of wall_schema.json's own subset.

Validates one Division's wall file against assets/wall_schema.json — the
"names only" shape — and returns a list of refusals, one per key or value the
schema does not allow, each naming its JSON path. It reads the schema itself,
so the shape and this reader cannot drift apart.

The subset is the parts of JSON Schema the wall file uses: type (a string or a
list of strings), required, properties, additionalProperties: false, items,
minItems and uniqueItems. Loading refuses a schema that uses any other keyword
than those and the describing ones, so a promise the schema makes is never one
this reader skips. No JSON Schema library is needed.

Run with python3, no dependencies.
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / "wall_schema.json").read_text(encoding="utf-8"))

# The keywords this reader applies, and those that only describe. A keyword the
# schema uses outside this set would be a promise the reader silently does not
# keep, so loading refuses it by name instead.
APPLIED = {"type", "required", "properties", "additionalProperties", "items", "minItems", "uniqueItems"}
DESCRIBING = {"$schema", "title", "description"}


def _unknown_keywords(schema: dict, path: str = "") -> list[str]:
    found = [f"{path or '/'}: {key}" for key in schema if key not in APPLIED | DESCRIBING]
    for key, sub in (schema.get("properties") or {}).items():
        found += _unknown_keywords(sub, f"{path}/properties/{key}")
    if isinstance(schema.get("items"), dict):
        found += _unknown_keywords(schema["items"], f"{path}/items")
    return found


if _unknown_keywords(SCHEMA):
    raise ValueError(f"wall_schema.json uses keywords this reader does not apply: {', '.join(_unknown_keywords(SCHEMA))}")


def check_wall_schema(wall: dict) -> list[str]:
    """Return every refusal as a JSON path and a reason; empty when the wall fits."""
    return _check(wall, SCHEMA, "")


def _matches(value, types) -> bool:
    for t in types if isinstance(types, list) else [types]:
        if t == "string" and isinstance(value, str):
            return True
        if t == "object" and isinstance(value, dict):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "null" and value is None:
            return True
        if t == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
    return False


def _expected(types) -> str:
    names = types if isinstance(types, list) else [types]
    return " or ".join(names)


def _actual(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _check(value, schema: dict, path: str) -> list[str]:
    failures: list[str] = []
    if schema.get("type") is not None and not _matches(value, schema["type"]):
        failures.append(f"{path or '/'}: expected {_expected(schema['type'])}, got {_actual(value)}")
        return failures
    if isinstance(value, dict):
        props = schema.get("properties") or {}
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    failures.append(f"{path}/{key}: not a name the schema allows")
        for key in schema.get("required") or []:
            if key not in value:
                failures.append(f"{path}/{key}: required by the schema")
        for key, sub in props.items():
            if key in value:
                failures += _check(value[key], sub, f"{path}/{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            failures.append(f"{path}: needs at least {schema['minItems']} item(s), has {len(value)}")
        if schema.get("uniqueItems"):
            seen = [json.dumps(item, sort_keys=True) for item in value]
            for i, item in enumerate(seen):
                if item in seen[:i]:
                    failures.append(f"{path}/{i}: repeats {path}/{seen.index(item)}")
        if schema.get("items") is not None:
            for i, item in enumerate(value):
                failures += _check(item, schema["items"], f"{path}/{i}")
    return failures


if __name__ == "__main__":
    import sys

    wall = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    for refusal in check_wall_schema(wall):
        print(refusal)
