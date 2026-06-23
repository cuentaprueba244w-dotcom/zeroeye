#!/usr/bin/env python3
"""Verify build.py generates diagnostic artifacts."""
import json, sys, os
from pathlib import Path

DIAGNOSTIC_DIR = Path(__file__).resolve().parent / "diagnostic"

def main():
    """Check that diagnostic .json and .logd files exist."""
    if not DIAGNOSTIC_DIR.is_dir():
        print("FAIL: diagnostic/ directory not found")
        return 1
    json_files = list(DIAGNOSTIC_DIR.glob("*.json"))
    logd_files = list(DIAGNOSTIC_DIR.glob("*.logd"))
    if not json_files:
        print("FAIL: no JSON diagnostic files found")
        return 1
    if not logd_files:
        print("FAIL: no .logd diagnostic files found")
        return 1
    # Validate JSON structure
    with open(json_files[0]) as f:
        report = json.load(f)
    required = ["commit","modules","passed","failed","total_modules"]
    for key in required:
        if key not in report:
            print(f"FAIL: missing {key} in diagnostic report")
            return 1
    print(f"OK: {len(json_files)} JSON, {len(logd_files)} .logd files")
    print(f"     Modules: {report["total_modules"]}, Passed: {report["passed"]}, Failed: {report["failed"]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
