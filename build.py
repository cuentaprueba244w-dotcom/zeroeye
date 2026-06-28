#!/usr/bin/env python3

"""
Build script for Tent of Trials.
Generates diagnostic artifacts (.logd and .json) even on build failure.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

DIAG_DIR = "diagnostic"
BUILD_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_diag_dir() -> None:
    os.makedirs(DIAG_DIR, exist_ok=True)


def generate_diagnostics(modules: List[Dict]) -> None:
    """Generate .logd (plain text) and .json diagnostic artifacts."""
    base_name = f"build-{BUILD_TIMESTAMP}"
    logd_path = os.path.join(DIAG_DIR, f"{base_name}.logd")
    json_path = os.path.join(DIAG_DIR, f"{base_name}.json")

    # Build diagnostic summary
    total_passed = sum(1 for m in modules if m["status"] == "pass")
    total_failed = sum(1 for m in modules if m["status"] == "fail")
    total_modules = len(modules)

    diagnostic = {
        "build_timestamp": BUILD_TIMESTAMP,
        "total_modules": total_modules,
        "passed": total_passed,
        "failed": total_failed,
        "modules": modules,
    }

    # Write .logd (human readable)
    with open(logd_path, "w") as f:
        f.write(f"Tent of Trials Build Diagnostics\n")
        f.write(f"Build Timestamp: {BUILD_TIMESTAMP}\n")
        f.write(f"Total Modules: {total_modules}\n")
        f.write(f"Passed: {total_passed}\n")
        f.write(f"Failed: {total_failed}\n")
        f.write(f"\n--- Module Details ---\n")
        for m in modules:
            f.write(f"\nModule: {m['name']}\n")
            f.write(f"  Status: {m['status']}\n")
            f.write(f"  Elapsed: {m['elapsed_seconds']:.3f}s\n")
            if m.get("error"):
                f.write(f"  Error: {m['error']}\n")

    print(f"[diagnostic] Wrote {logd_path}")

    # Write .json
    with open(json_path, "w") as f:
        json.dump(diagnostic, f, indent=2)
    print(f"[diagnostic] Wrote {json_path}")


def run_module_build(name: str, command: List[str], cwd: Optional[str] = None) -> Dict:
    """Run a single module build and return diagnostic info."""
    start_time = time.time()
    result = {
        "name": name,
        "status": "pass",
        "elapsed_seconds": 0.0,
        "error": None,
    }
    try:
        print(f"[build] Building module: {name}")
        proc = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        elapsed = time.time() - start_time
        result["elapsed_seconds"] = round(elapsed, 3)

        if proc.returncode != 0:
            result["status"] = "fail"
            result["error"] = proc.stderr[:2000] if proc.stderr else "Exit code {}".format(proc.returncode)
            print(f"[build] Module {name} FAILED (elapsed {elapsed:.2f}s)")
        else:
            print(f"[build] Module {name} PASSED (elapsed {elapsed:.2f}s)")
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        result["status"] = "fail"
        result["error"] = "Build timed out after 600s"
        result["elapsed_seconds"] = round(elapsed, 3)
        print(f"[build] Module {name} TIMEOUT (elapsed {elapsed:.2f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        result["status"] = "fail"
        result["error"] = str(e)[:2000]
        result["elapsed_seconds"] = round(elapsed, 3)
        print(f"[build] Module {name} EXCEPTION: {e}")
    return result


def main() -> None:
    ensure_diag_dir()

    # Define modules to build. Each entry: name, command list, optional cwd.
    modules_to_build = [
        {
            "name": "backend",
            "command": ["cargo", "build", "--release"],
            "cwd": os.path.join(os.path.dirname(__file__), "backend"),
        },
        {
            "name": "frailbox",
            "command": ["make", "-j$(nproc)"],
            "cwd": os.path.join(os.path.dirname(__file__), "frailbox"),
        },
        # Add additional modules as needed
    ]

    module_results = []
    overall_success = True

    # Build each module sequentially (or could parallelize)
    for mod in modules_to_build:
        result = run_module_build(mod["name"], mod["command"], cwd=mod.get("cwd"))
        module_results.append(result)
        if result["status"] != "pass":
            overall_success = False

    # Always generate diagnostics, even if some modules failed
    generate_diagnostics(module_results)

    if not overall_success:
        print("[build] Some modules failed. See diagnostic files for details.")
        sys.exit(1)
    else:
        print("[build] All modules built successfully.")


if __name__ == "__main__":
    main()
