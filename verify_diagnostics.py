#!/usr/bin/env python3
"""Verify that build.py generates complete diagnostic artifacts.

Checks that .logd and .json files are present and that the JSON metadata
contains all required fields — module status, elapsed times, and pass/fail
counts — even when builds fail.

Usage:
    python3 verify_diagnostics.py                    # check latest diagnostics
    python3 verify_diagnostics.py --run-build        # run build.py first, then verify
    python3 verify_diagnostics.py --json <path>      # verify a specific .json file
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAGNOSTIC_DIR = ROOT / "diagnostic"

REQUIRED_TOP_KEYS = frozenset({
    "generated_at",
    "commit",
    "diagnostic_logd",
    "total_modules",
    "passed",
    "failed",
    "modules",
})

REQUIRED_MODULE_KEYS = frozenset({
    "name",
    "status",
    "elapsed_seconds",
    "artifact",
    "output",
})

VALID_STATUSES = frozenset({"PASS", "FAIL"})


def find_latest_json() -> Path | None:
    """Return the most recent build-*.json (by mtime), or None."""
    if not DIAGNOSTIC_DIR.exists():
        return None
    candidates = sorted(
        DIAGNOSTIC_DIR.glob("build-????????.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Exclude part files and 00000000 fallback when better options exist
    real = [c for c in candidates if "-part" not in c.name]
    return real[0] if real else (candidates[0] if candidates else None)


def find_matching_logd(json_path: Path) -> Path | None:
    """Find the .logd (or first .logd chunk) matching a .json path."""
    stem = json_path.stem  # e.g. build-db991709
    # Single .logd file
    logd = json_path.with_suffix(".logd")
    if logd.exists():
        return logd
    # Chunked: build-db991709-part001.logd
    chunks = sorted(DIAGNOSTIC_DIR.glob(f"{stem}-part*.logd"))
    return chunks[0] if chunks else None


def validate_json(json_path: Path) -> tuple[bool, list[str]]:
    """Validate diagnostic JSON structure. Returns (passed, errors)."""
    errors: list[str] = []

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, [f"Cannot parse {json_path.name}: {e}"]

    if not isinstance(data, dict):
        return False, [f"{json_path.name} is not a JSON object"]

    # Top-level required keys
    missing_top = REQUIRED_TOP_KEYS - set(data.keys())
    if missing_top:
        errors.append(f"Missing top-level keys: {', '.join(sorted(missing_top))}")

    # Module count consistency
    total = data.get("total_modules")
    modules = data.get("modules")
    passed = data.get("passed")
    failed = data.get("failed")

    if isinstance(modules, list) and isinstance(total, int):
        if len(modules) != total:
            errors.append(
                f"modules array length ({len(modules)}) != total_modules ({total})"
            )
    else:
        errors.append("modules is not a list or total_modules is not an int")

    if isinstance(passed, int) and isinstance(failed, int) and isinstance(total, int):
        if passed + failed != total:
            errors.append(
                f"passed ({passed}) + failed ({failed}) != total_modules ({total})"
            )
    else:
        errors.append("passed/failed/total_modules have wrong types")

    # Per-module validation
    if isinstance(modules, list):
        for i, mod in enumerate(modules):
            if not isinstance(mod, dict):
                errors.append(f"module[{i}] is not an object")
                continue
            missing_mod = REQUIRED_MODULE_KEYS - set(mod.keys())
            if missing_mod:
                errors.append(
                    f"module[{i}] ({mod.get('name', '?')}): "
                    f"missing keys: {', '.join(sorted(missing_mod))}"
                )
            status = mod.get("status")
            if status not in VALID_STATUSES:
                errors.append(
                    f"module[{i}] ({mod.get('name', '?')}): "
                    f"invalid status '{status}' (expected PASS or FAIL)"
                )
            elapsed = mod.get("elapsed_seconds")
            if not isinstance(elapsed, (int, float)) or elapsed < 0:
                errors.append(
                    f"module[{i}] ({mod.get('name', '?')}): "
                    f"invalid elapsed_seconds: {elapsed}"
                )

    return len(errors) == 0, errors


def check_logd(json_path: Path) -> tuple[bool, str]:
    """Verify the matching .logd exists and is non-empty."""
    logd = find_matching_logd(json_path)
    if logd is None:
        return False, f"No .logd found matching {json_path.name}"
    if not logd.exists():
        return False, f"{logd.name} does not exist"
    size = logd.stat().st_size
    if size == 0:
        return False, f"{logd.name} is empty"
    return True, f"{logd.name} ({size:,} bytes)"


def run_build() -> bool:
    """Run build.py in the repo root. Returns True if exit code is 0."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "build.py")],
        cwd=str(ROOT),
        capture_output=False,
        timeout=600,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify build diagnostic artifacts from build.py"
    )
    parser.add_argument(
        "--run-build",
        action="store_true",
        help="Run build.py before verifying diagnostics",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Verify a specific diagnostic .json file",
    )
    args = parser.parse_args()

    if args.run_build:
        print("Running build.py ...")
        build_ok = run_build()
        print(f"build.py exited with {'success' if build_ok else 'failure'}\n")

    json_path = args.json if args.json else find_latest_json()
    if json_path is None:
        print("FAIL: No diagnostic .json found in diagnostic/")
        print("Run 'python3 build.py' first, or use --run-build")
        return 1

    print(f"Verifying: {json_path.name}")

    # Validate JSON
    json_ok, json_errors = validate_json(json_path)
    if json_ok:
        print("  JSON structure: PASS")
        # Show summary
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            print(
                f"    modules={data['total_modules']}, "
                f"passed={data['passed']}, "
                f"failed={data['failed']}"
            )
        except Exception:
            pass
    else:
        print("  JSON structure: FAIL")
        for err in json_errors:
            print(f"    - {err}")

    # Check .logd
    logd_ok, logd_msg = check_logd(json_path)
    status = "PASS" if logd_ok else "FAIL"
    print(f"  .logd artifact: {status}  ({logd_msg})")

    all_ok = json_ok and logd_ok
    print(f"\nOverall: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
