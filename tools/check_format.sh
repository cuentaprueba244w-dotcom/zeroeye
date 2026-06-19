#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

python3 - <<'PY'
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".c", ".cpp", ".css", ".go", ".h", ".hpp", ".hs", ".html", ".java",
    ".js", ".json", ".jsx", ".lua", ".md", ".py", ".rb", ".rs", ".sh",
    ".sql", ".tf", ".toml", ".ts", ".tsx", ".yaml", ".yml",
}
TEXT_NAMES = {
    ".editorconfig",
    ".gitignore",
    "Cargo.toml",
    "Makefile",
}
SKIP_PREFIXES = (
    ".git/",
    "backend/target/",
    "compliance/build/",
    "diagnostic/",
    "frailbox/build/",
    "frailbox/engine/build/",
    "frontend/dist/",
    "frontend/node_modules/",
)


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], text=True)
    return [Path(line) for line in output.splitlines() if line]


def is_text_target(path: Path) -> bool:
    as_posix = path.as_posix()
    if any(as_posix.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    return path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES


def inspect(path: Path) -> list[str]:
    data = path.read_bytes()
    errors: list[str] = []
    if b"\r\n" in data or b"\r" in data:
        errors.append("uses CRLF/CR line endings")
    if data and not data.endswith(b"\n"):
        errors.append("is missing a final newline")

    if path.suffix != ".md":
        for lineno, line in enumerate(data.splitlines(), start=1):
            if line.rstrip(b" \t") != line:
                errors.append(f"line {lineno} has trailing whitespace")
                break
    return errors


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        if not is_text_target(path):
            continue
        for error in inspect(path):
            failures.append(f"{path}: {error}")

    if failures:
        print("Format check failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print("Format check passed")
    return 0


raise SystemExit(main())
PY
