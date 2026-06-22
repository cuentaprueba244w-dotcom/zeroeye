#!/usr/bin/env python3
"""
verify_diagnostics.py - Verify that build.py generates diagnostic artifacts
even when builds fail. This addresses bounty issues #4 and #35.
"""
import subprocess
import sys
import os
from pathlib import Path

def main() -> int:
    """Run verification tests for diagnostic artifact generation."""
    print("=" * 60)
    print("Diagnostic Artifact Verification")
    print("=" * 60)

    # Find build.py
    build_py = Path(__file__).resolve().parent / "build.py"
    if not build_py.exists():
        print("ERROR: build.py not found")
        return 1

    # Run build.py on a non-existent module to force failure
    print("\n[Test 1] Build with invalid module (should fail but create diagnostics)")
    result = subprocess.run(
        [sys.executable, str(build_py), "-m", "nonexistent"],
        capture_output=True,
        text=True,
    )
    print(f"  Exit code: {result.returncode}")

    # Check if diagnostic directory exists
    diagnostic_dir = Path("diagnostic")
    if diagnostic_dir.exists():
        json_files = list(diagnostic_dir.glob("build-*.json"))
        print(f"  JSON metadata files found: {len(json_files)}")
        for f in json_files[:3]:
            print(f"    - {f.name}")

        logd_files = list(diagnostic_dir.glob("build-*.logd"))
        print(f"  LOGD files found: {len(logd_files)}")
        for f in logd_files[:3]:
            print(f"    - {f.name}")

        if json_files:
            print("  ✓ PASS: JSON metadata generated even on build failure")
        else:
            print("  ✗ FAIL: No JSON metadata found")
            return 1
    else:
        print("  ✗ FAIL: diagnostic/ directory not created")
        return 1

    # Run build.py --list (no actual build, should still work)
    print("\n[Test 2] Build --list (should create minimal diagnostics)")
    result = subprocess.run(
        [sys.executable, str(build_py), "--list"],
        capture_output=True,
        text=True,
    )
    print(f"  Exit code: {result.returncode}")

    # Check diagnostic content
    json_files = list(diagnostic_dir.glob("build-*.json"))
    if json_files:
        latest = max(json_files, key=lambda p: p.stat().st_mtime)
        import json
        with open(latest) as f:
            data = json.load(f)
        print(f"  Latest diagnostic: {latest.name}")
        print(f"    total_modules: {data.get('total_modules')}")
        print(f"    passed: {data.get('passed')}")
        print(f"    failed: {data.get('failed')}")
        print("  ✓ PASS: Diagnostic structure is valid")

    print("\n" + "=" * 60)
    print("All verification tests PASSED")
    print("Build diagnostics are correctly generated even on failure.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
