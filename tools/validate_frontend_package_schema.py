#!/usr/bin/env python3
"""Validate the frontend package schema against real and example payloads."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "frontend-package.schema.json"
PACKAGE_PATH = ROOT / "frontend" / "package.json"
VALID_EXAMPLE_PATH = ROOT / "schemas" / "examples" / "frontend-package.valid.json"
INVALID_EXAMPLE_PATH = ROOT / "schemas" / "examples" / "frontend-package.invalid.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local JSON pointer refs are supported: {ref}")

    current: Any = root
    for part in ref[2:].split("/"):
        current = current[part]
    if not isinstance(current, dict):
        raise TypeError(f"Reference {ref} did not resolve to an object schema")
    return current


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def validate(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> list[str]:
    if "$ref" in schema:
        return validate(value, resolve_ref(schema["$ref"], root), root, path)

    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type and not type_matches(value, expected_type):
        return [f"{path}: expected {expected_type}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}, got {value!r}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: expected at least {schema['minLength']} characters")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: did not match pattern {schema['pattern']}")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: missing required property")

        property_name_schema = schema.get("propertyNames")
        if property_name_schema:
            for key in value:
                errors.extend(validate(key, property_name_schema, root, f"{path}.{key}<name>"))

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in properties:
                errors.extend(validate(child, properties[key], root, child_path))
            elif additional is False:
                errors.append(f"{child_path}: additional property is not allowed")
            elif isinstance(additional, dict):
                errors.extend(validate(child, additional, root, child_path))

    return errors


def assert_schema_contract(schema: dict[str, Any]) -> None:
    required_top_level = {"$schema", "$id", "title", "description", "type", "properties"}
    missing = sorted(required_top_level - schema.keys())
    if missing:
        raise AssertionError(f"schema is missing required top-level keys: {missing}")
    if schema["type"] != "object":
        raise AssertionError("frontend package schema must describe an object")


def assert_valid(name: str, payload: Any, schema: dict[str, Any]) -> None:
    errors = validate(payload, schema, schema, name)
    if errors:
        raise AssertionError(f"{name} should validate:\n" + "\n".join(errors))


def assert_invalid(name: str, payload: Any, schema: dict[str, Any]) -> None:
    errors = validate(payload, schema, schema, name)
    if not errors:
        raise AssertionError(f"{name} should fail validation")
    print(f"{name}: expected validation failure count={len(errors)}")


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    assert_schema_contract(schema)
    assert_valid("frontend/package.json", load_json(PACKAGE_PATH), schema)
    assert_valid("schemas/examples/frontend-package.valid.json", load_json(VALID_EXAMPLE_PATH), schema)
    assert_invalid(
        "schemas/examples/frontend-package.invalid.json",
        load_json(INVALID_EXAMPLE_PATH),
        schema,
    )
    print("frontend package schema validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
