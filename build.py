#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Any

ROOT: Path = Path(__file__).resolve().parent
DIAGNOSTIC_DIR: Path = ROOT / "diagnostic"


def current_commit_id() -> str:
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=5,
        )
        commit: str = result.stdout.strip()
        if result.returncode == 0 and len(commit) >= 8:
            return commit[:8]
    except Exception:
        pass
    return "00000000"


def diagnostic_paths_for_commit() -> tuple:
    DIAGNOSTIC_DIR.mkdir(parents=True, exist_ok=True)
    commit_id: str = current_commit_id()
    return (DIAGNOSTIC_DIR / f"build-{commit_id}.logd",
            DIAGNOSTIC_DIR / f"build-{commit_id}.json",
            commit_id)


def build() -> dict[str, Any]:
    logd_path, metadata_path, commit_id = diagnostic_paths_for_commit()
    
    # Collect diagnostic data
    log_lines: list[str] = [
        f"Build time: {datetime.datetime.now().isoformat()}",
        f"Python: {sys.version}",
        f"Commit: {commit_id}",
        "",
    ]
    
    # Simulate build steps
    steps: list[str] = ["backend", "frontend", "worker", "docs"]
    modules_built: list[str] = []
    
    for step in steps:
        step_dir = ROOT / step
        if step_dir.exists():
            result = subprocess.run(
                ["cargo", "build"] if step in ("backend", "worker") else ["npm", "run", "build"],
                cwd=str(step_dir), capture_output=True, text=True, timeout=300,
            )
            log_lines.append(f"=== {step} ===")
            log_lines.append(f"exit_code: {result.returncode}")
            log_lines.append(f"stdout: {result.stdout[-1000:]}")
            log_lines.append(f"stderr: {result.stderr[-1000:]}")
            log_lines.append("")
            modules_built.append(step)
    
    # Write .logd file
    logd_content: str = "\n".join(log_lines)
    logd_path.write_text(logd_content)
    
    # Write .json metadata
    metadata: dict[str, Any] = {
        "commit_id": commit_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "modules_built": modules_built,
        "logd_size": logd_path.stat().st_size,
        "diagnostic_exists": True,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))
    
    return metadata


def verify() -> dict[str, Any]:
    commit_id: str = current_commit_id()
    logd_path: Path = DIAGNOSTIC_DIR / f"build-{commit_id}.logd"
    metadata_path: Path = DIAGNOSTIC_DIR / f"build-{commit_id}.json"
    
    result: dict[str, Any] = {
        "diagnostics_exist": False,
        "logd_exists": logd_path.exists(),
        "metadata_exists": metadata_path.exists(),
        "logd_size": logd_path.stat().st_size if logd_path.exists() else 0,
        "metadata_valid": False,
        "build_completed": False,
    }
    
    if metadata_path.exists():
        try:
            data: dict[str, Any] = json.loads(metadata_path.read_text())
            result["metadata_valid"] = True
            if data.get("modules_built"):
                result["build_completed"] = True
            result["metadata"] = data
        except (json.JSONDecodeError, Exception):
            pass
    
    if logd_path.exists() and result.get("build_completed"):
        result["diagnostics_exist"] = True
    
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="ZeroEye build with diagnostics")
    parser.add_argument("--verify", action="store_true", help="Verify diagnostics")
    args = parser.parse_args()
    
    if args.verify:
        result: dict[str, Any] = verify()
        print(json.dumps(result, indent=2))
        if not result["diagnostics_exist"]:
            print("Diagnostics verification: FAILED")
            sys.exit(1)
        print("Diagnostics verification: PASSED")
        sys.exit(0)
    
    metadata: dict[str, Any] = build()
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
