#!/usr/bin/env python3
"""Validate build diagnostic metadata and encrypted log artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "commit",
    "diagnostic_logd",
    "total_modules",
    "passed",
    "failed",
    "modules",
}
REQUIRED_MODULE_FIELDS = {"name", "status", "elapsed_seconds", "output"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate_report(metadata_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    report = load_json(metadata_path)

    missing = REQUIRED_TOP_LEVEL - report.keys()
    if missing:
        errors.append(f"{metadata_path}: missing required fields: {', '.join(sorted(missing))}")

    modules = report.get("modules")
    if not isinstance(modules, list):
        errors.append(f"{metadata_path}: modules must be a list")
        modules = []

    total_modules = report.get("total_modules")
    passed = report.get("passed")
    failed = report.get("failed")
    if total_modules != len(modules):
        errors.append(f"{metadata_path}: total_modules does not match modules length")

    observed_passed = sum(1 for module in modules if module.get("status") == "PASS")
    observed_failed = sum(1 for module in modules if module.get("status") == "FAIL")
    if passed != observed_passed:
        errors.append(f"{metadata_path}: passed count does not match module statuses")
    if failed != observed_failed:
        errors.append(f"{metadata_path}: failed count does not match module statuses")

    for index, module in enumerate(modules):
        if not isinstance(module, dict):
            errors.append(f"{metadata_path}: module {index} must be an object")
            continue
        missing_module_fields = REQUIRED_MODULE_FIELDS - module.keys()
        if missing_module_fields:
            errors.append(
                f"{metadata_path}: module {index} missing fields: "
                f"{', '.join(sorted(missing_module_fields))}"
            )
        if module.get("status") not in {"PASS", "FAIL"}:
            errors.append(f"{metadata_path}: module {index} has invalid status")
        if not isinstance(module.get("elapsed_seconds"), (int, float)):
            errors.append(f"{metadata_path}: module {index} elapsed_seconds must be numeric")

    logd_value = report.get("diagnostic_logd")
    logd_paths = logd_value if isinstance(logd_value, list) else [logd_value]
    for logd in logd_paths:
        if not isinstance(logd, str) or not logd:
            errors.append(f"{metadata_path}: diagnostic_logd must reference a .logd artifact")
            continue
        if Path(logd).is_absolute():
            errors.append(f"{metadata_path}: diagnostic_logd must be repository-relative")
            continue
        logd_path = repo_root / logd
        if logd_path.suffix != ".logd":
            errors.append(f"{metadata_path}: diagnostic_logd must end with .logd")
        if not logd_path.exists():
            errors.append(f"{metadata_path}: missing diagnostic artifact {logd}")
        elif logd_path.stat().st_size == 0:
            errors.append(f"{metadata_path}: diagnostic artifact {logd} is empty")

    return errors


def metadata_for_commit(repo_root: Path, commit: str) -> Path:
    return repo_root / "diagnostic" / f"build-{commit}.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate build diagnostic artifacts")
    parser.add_argument("--commit", help="Commit prefix used in diagnostic/build-<commit>.json")
    parser.add_argument("--metadata", type=Path, help="Explicit diagnostic metadata JSON path")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    metadata_path = args.metadata or metadata_for_commit(repo_root, args.commit or "")
    if not args.metadata and not args.commit:
        parser.error("either --commit or --metadata is required")

    errors = validate_report(metadata_path.resolve(), repo_root)
    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"Diagnostic metadata valid: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
