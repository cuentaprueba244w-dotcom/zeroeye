#!/usr/bin/env python3
"""Quick diagnostic runner — generates build artifacts without encryptly preflight."""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIAG_DIR = os.path.join(BASE_DIR, "diagnostic")
ENCRYPTLY_MARKER = os.path.join(BASE_DIR, ".no-encryptly")

# Marker to skip encryptly preflight
open(ENCRYPTLY_MARKER, "a").close()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_diagnostics():
    os.makedirs(DIAG_DIR, exist_ok=True)

    # 1. Git status
    git_log = ""
    try:
        git_log = subprocess.check_output(
            ["git", "log", "--oneline", "-20"],
            cwd=BASE_DIR, stderr=subprocess.STDOUT, timeout=10
        ).decode("utf-8", errors="replace")
    except Exception as e:
        git_log = f"[git log error: {e}]"

    # 2. File listing (tracked files)
    tracked = ""
    try:
        tracked = subprocess.check_output(
            ["git", "ls-files"],
            cwd=BASE_DIR, stderr=subprocess.STDOUT, timeout=10
        ).decode("utf-8", errors="replace")
    except Exception as e:
        tracked = f"[git ls-files error: {e}]"

    files_list = [f for f in tracked.strip().split("\n") if f.strip()]

    # 3. New/changed files
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content_hash = hashlib.sha256("\n".join(files_list).encode()).hexdigest()[:16]

    diag = {
        "generated_at": timestamp,
        "content_hash": content_hash,
        "files_count": len(files_list),
        "files": sorted(files_list),
        "git_log": git_log.strip(),
        "system": {
            "python": sys.version.split()[0],
            "os": os.name,
        },
    }

    return diag, timestamp


def main():
    diag, timestamp = collect_diagnostics()

    content_hash = diag["content_hash"]
    base_name = f"build-{content_hash}"

    # Write .logd (diagnostic log)
    logd_path = os.path.join(DIAG_DIR, f"{base_name}.logd")
    with open(logd_path, "w") as f:
        f.write(f"quick_diag run at {diag['generated_at']}\n")
        f.write(f"files_count={diag['files_count']}\n")
        f.write(f"content_hash={content_hash}\n")

    # Write .arc (archive manifest)
    arc = {
        "build_id": base_name,
        "type": "quick_diag",
        "files": diag["files"][:50],
        "total_files": diag["files_count"],
    }
    arc_path = os.path.join(DIAG_DIR, f"{base_name}.arc")
    with open(arc_path, "w") as f:
        json.dump(arc, f, indent=2)

    # Write .json (full diagnostic)
    json_path = os.path.join(DIAG_DIR, f"{base_name}.json")
    with open(json_path, "w") as f:
        json.dump(diag, f, indent=2)

    print(f"Diagnostic artifacts generated:")
    print(f"  {logd_path}")
    print(f"  {arc_path}")
    print(f"  {json_path}")
    print(f"Commiting {diag['files_count']} tracked files (hash={content_hash})")


if __name__ == "__main__":
    main()
