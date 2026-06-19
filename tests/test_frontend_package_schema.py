import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "frontend-package.schema.json"
VALID_EXAMPLE = ROOT / "schemas" / "examples" / "frontend-package.valid.json"
INVALID_EXAMPLE = ROOT / "schemas" / "examples" / "frontend-package.invalid.json"
FRONTEND_PACKAGE = ROOT / "frontend" / "package.json"


class SchemaValidationError(AssertionError):
    pass


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_ref(schema, ref):
    if not ref.startswith("#/"):
        raise SchemaValidationError(f"unsupported ref: {ref}")
    value = schema
    for part in ref[2:].split("/"):
        value = value[part]
    return value


def validate(instance, schema_fragment, root_schema, path="$"):
    if "$ref" in schema_fragment:
        schema_fragment = resolve_ref(root_schema, schema_fragment["$ref"])

    expected_type = schema_fragment.get("type")
    if expected_type:
        type_checks = {
            "object": lambda value: isinstance(value, dict),
            "string": lambda value: isinstance(value, str),
            "boolean": lambda value: isinstance(value, bool),
        }
        if expected_type not in type_checks:
            raise SchemaValidationError(f"{path}: unsupported schema type {expected_type}")
        if not type_checks[expected_type](instance):
            raise SchemaValidationError(f"{path}: expected {expected_type}")

    if "enum" in schema_fragment and instance not in schema_fragment["enum"]:
        raise SchemaValidationError(f"{path}: value {instance!r} is not allowed")

    if isinstance(instance, str):
        min_length = schema_fragment.get("minLength")
        if min_length is not None and len(instance) < min_length:
            raise SchemaValidationError(f"{path}: string is too short")
        pattern = schema_fragment.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            raise SchemaValidationError(f"{path}: does not match pattern {pattern}")

    if isinstance(instance, dict):
        for required in schema_fragment.get("required", []):
            if required not in instance:
                raise SchemaValidationError(f"{path}: missing required key {required}")

        properties = schema_fragment.get("properties", {})
        for key, subschema in properties.items():
            if key in instance:
                validate(instance[key], subschema, root_schema, f"{path}.{key}")

        pattern_properties = schema_fragment.get("patternProperties", {})
        additional_properties = schema_fragment.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                continue
            matched = False
            for pattern, subschema in pattern_properties.items():
                if re.search(pattern, key):
                    validate(value, subschema, root_schema, f"{path}.{key}")
                    matched = True
                    break
            if matched:
                continue
            if isinstance(additional_properties, dict):
                validate(value, additional_properties, root_schema, f"{path}.{key}")
            elif additional_properties is False:
                raise SchemaValidationError(f"{path}: unexpected key {key}")


class FrontendPackageSchemaTests(unittest.TestCase):
    def test_schema_has_required_draft_07_metadata(self):
        schema = load_json(SCHEMA_PATH)

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft-07/schema#")
        for key in ("$id", "title", "description", "type", "properties"):
            self.assertIn(key, schema)
        self.assertEqual(schema["type"], "object")

    def test_schema_validates_examples_and_current_frontend_package(self):
        schema = load_json(SCHEMA_PATH)

        for path in (VALID_EXAMPLE, FRONTEND_PACKAGE):
            with self.subTest(path=path):
                validate(load_json(path), schema, schema)

    def test_schema_rejects_invalid_example(self):
        schema = load_json(SCHEMA_PATH)

        with self.assertRaises(SchemaValidationError):
            validate(load_json(INVALID_EXAMPLE), schema, schema)


if __name__ == "__main__":
    unittest.main()
