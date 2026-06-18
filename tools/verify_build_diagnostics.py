#!/usr/bin/env python3
"""Verify build.py diagnostic metadata and artifact references."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC_DIR = ROOT / "diagnostic"


def load_build_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("zeroeye_build", ROOT / "build.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def as_logd_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise AssertionError(f"diagnostic_logd must be a string, list of strings, or null: {value!r}")


def validate_report_shape(report: dict[str, Any], label: str) -> None:
    required = {
        "commit",
        "diagnostic_logd",
        "diagnostic_logd_error",
        "total_modules",
        "passed",
        "failed",
        "modules",
        "pr_note",
    }
    missing = sorted(required - report.keys())
    assert_true(not missing, f"{label}: missing required keys {missing}")
    assert_true(
        report["passed"] + report["failed"] == report["total_modules"],
        f"{label}: passed + failed must equal total_modules",
    )
    assert_true(
        len(report["modules"]) == report["total_modules"],
        f"{label}: modules length must equal total_modules",
    )

    for index, module in enumerate(report["modules"]):
        prefix = f"{label}: modules[{index}]"
        for key in ("name", "status", "elapsed_seconds", "artifact", "output"):
            assert_true(key in module, f"{prefix}: missing {key}")
        assert_true(module["status"] in {"PASS", "FAIL"}, f"{prefix}: invalid status")
        assert_true(
            isinstance(module["elapsed_seconds"], (int, float))
            and not isinstance(module["elapsed_seconds"], bool),
            f"{prefix}: elapsed_seconds must be numeric",
        )

    logd_refs = as_logd_list(report["diagnostic_logd"])
    if logd_refs:
        for relpath in logd_refs:
            path = Path(relpath)
            assert_true(not path.is_absolute(), f"{label}: logd path must be repository-relative")
            assert_true(path.suffix == ".logd", f"{label}: logd path must end in .logd")
            assert_true("\\" not in relpath, f"{label}: logd path must use forward slashes")
    else:
        assert_true(
            bool(report.get("diagnostic_logd_error") or report.get("message_blocker")),
            f"{label}: missing logd must include diagnostic_logd_error or message_blocker",
        )


def validate_builder_contract() -> None:
    build = load_build_module()
    results = [
        ("backend", True, 1.2345, "backend ok", "backend/target"),
        ("frailbox", False, 0.25, "compile failed", None),
    ]
    report = build.build_diagnostic_report(
        results,
        "deadbeef",
        logd_relpaths=["diagnostic/build-deadbeef.logd"],
        password="test-password",
    )

    validate_report_shape(report, "synthetic success report")
    assert_true(report["total_modules"] == 2, "synthetic report total_modules mismatch")
    assert_true(report["passed"] == 1, "synthetic report passed count mismatch")
    assert_true(report["failed"] == 1, "synthetic report failed count mismatch")
    assert_true(
        report["modules"][0]["elapsed_seconds"] == 1.234,
        "synthetic report should round elapsed_seconds to three decimals",
    )
    assert_true(
        report["diagnostic_logd"] == "diagnostic/build-deadbeef.logd",
        "synthetic report should keep the .logd reference",
    )
    assert_true(
        report["decrypt_command"] == (
            "encryptly unpack diagnostic/build-deadbeef.logd <outdir> --password test-password"
        ),
        "synthetic report should include decrypt command when logd and password exist",
    )

    failure_report = build.build_diagnostic_report(
        results,
        "badc0de0",
        logd_error="simulated encryptly failure",
        message_blocker="simulated blocker",
    )
    validate_report_shape(failure_report, "synthetic failure report")
    assert_true(
        failure_report["diagnostic_logd"] is None,
        "failure report should not claim a .logd path",
    )
    assert_true(
        failure_report["diagnostic_logd_error"] == "simulated encryptly failure",
        "failure report should preserve logd creation errors",
    )


def validate_committed_artifacts() -> int:
    metadata_paths = sorted(DIAGNOSTIC_DIR.glob("build-*.json"))
    assert_true(metadata_paths, "expected at least one diagnostic/build-*.json file")

    checked = 0
    for metadata_path in metadata_paths:
        report = json.loads(metadata_path.read_text(encoding="utf-8"))
        label = str(metadata_path.relative_to(ROOT))
        validate_report_shape(report, label)
        for relpath in as_logd_list(report["diagnostic_logd"]):
            artifact_path = ROOT / relpath
            assert_true(artifact_path.exists(), f"{label}: missing artifact {relpath}")
        checked += 1
    return checked


def main() -> int:
    validate_builder_contract()
    checked = validate_committed_artifacts()
    print(f"build diagnostic verification passed; metadata files checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
