#!/usr/bin/env python3

"""Build script to validate JSON Schema and generate diagnostic artifacts."""

import json
import os
import sys
import uuid
from datetime import datetime

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema package is required. Install with: pip install jsonschema")
    sys.exit(1)

SCHEMA_PATH = "schemas/package.schema.json"
DIAGNOSTIC_DIR = "diagnostic"
BUILD_ID = uuid.uuid4().hex[:8]

def main():
    # Load schema
    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)
    
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    
    # Load built-in examples
    examples = [
        {
            "name": "my-project",
            "version": "1.0.0",
            "description": "A sample project",
            "main": "index.js",
            "scripts": {
                "start": "node index.js"
            },
            "dependencies": {
                "lodash": "^4.17.21"
            }
        },
        {
            "name": "another-project",
            "version": "0.0.1",
            "private": True
        }
    ]
    
    # Validate each example
    errors = []
    for i, example in enumerate(examples):
        try:
            jsonschema.validate(instance=example, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            errors.append(f"Example {i} failed: {e.message}")
    
    # Create diagnostic directory
    os.makedirs(DIAGNOSTIC_DIR, exist_ok=True)
    
    # Build logd content
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    log_lines = [
        f"Build ID: {BUILD_ID}",
        f"Timestamp: {timestamp}",
        f"Schema: {SCHEMA_PATH}",
        f"Examples validated: {len(examples)}",
        f"Errors: {len(errors)}",
        ""
    ]
    if errors:
        log_lines.extend(errors)
    else:
        log_lines.append("All examples passed validation.")
    
    logd_content = "\n".join(log_lines)
    logd_filename = f"build-{BUILD_ID}.logd"
    logd_path = os.path.join(DIAGNOSTIC_DIR, logd_filename)
    with open(logd_path, "w") as f:
        f.write(logd_content)
    
    # Build JSON diagnostic (optional)
    json_diagnostic = {
        "buildId": BUILD_ID,
        "timestamp": timestamp,
        "schema": SCHEMA_PATH,
        "examplesValidated": len(examples),
        "errorCount": len(errors),
        "errors": errors if errors else []
    }
    json_filename = f"build-{BUILD_ID}.json"
    json_path = os.path.join(DIAGNOSTIC_DIR, json_filename)
    with open(json_path, "w") as f:
        json.dump(json_diagnostic, f, indent=2)
    
    print(f"Build {BUILD_ID} completed.")
    print(f"Log: {logd_path}")
    print(f"JSON: {json_path}")
    
    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
