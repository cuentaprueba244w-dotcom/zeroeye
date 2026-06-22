"""Tests for build.py diagnostic generation"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

try:
    from build import (
        diagnostic_paths_for_commit,
        build_diagnostic_report,
        write_diagnostic_report,
        ROOT,
        DIAGNOSTIC_DIR,
        MODULES,
    )
    HAS_BUILD_MODULE = True
except ImportError as e:
    HAS_BUILD_MODULE = False
    _import_error = str(e)


class TestDiagnosticPaths(unittest.TestCase):
    def test_diagnostic_paths_create_dir(self):
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        import build
        with tempfile.TemporaryDirectory() as tmp:
            orig = build.DIAGNOSTIC_DIR
            build.DIAGNOSTIC_DIR = Path(tmp) / "diagnostic"
            try:
                logd_path, metadata_path, commit_id = build.diagnostic_paths_for_commit()
                self.assertTrue(build.DIAGNOSTIC_DIR.exists())
                self.assertIn("build-", str(logd_path))
                self.assertEqual(metadata_path.suffix, ".json")
            finally:
                build.DIAGNOSTIC_DIR = orig


class TestDiagnosticReport(unittest.TestCase):
    def test_report_structure(self):
        """Report includes all required fields"""
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        results = [
            ("backend", True, 12.5, "Build output", "/path/to/binary"),
            ("frontend", False, 8.2, "Error: build failed", None),
        ]
        report = build_diagnostic_report(results, "abc12345")
        required = {"generated_at", "commit", "total_modules", "passed", "failed", "modules"}
        self.assertTrue(required.issubset(set(report.keys())),
                        f"Missing: {required - set(report.keys())}")

    def test_report_module_counts(self):
        """Report correctly counts pass/fail"""
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        results = [
            ("backend", True, 5.0, "ok", None),
            ("frontend", True, 3.0, "ok", None),
            ("market", False, 2.0, "fail", None),
        ]
        report = build_diagnostic_report(results, "abc12345")
        self.assertEqual(report["total_modules"], 3)
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 1)

    def test_report_module_details(self):
        """Each module entry has status, elapsed_seconds, and output"""
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        results = [("test-module", True, 10.5, "Build successful", None)]
        report = build_diagnostic_report(results, "abc12345")
        module = report["modules"][0]
        required = {"name", "status", "elapsed_seconds", "output"}
        self.assertTrue(required.issubset(set(module.keys())),
                        f"Missing: {required - set(module.keys())}")
        self.assertEqual(module["name"], "test-module")
        self.assertEqual(module["status"], "PASS")
        self.assertEqual(module["elapsed_seconds"], 10.5)

    def test_report_error_scenario(self):
        """Error details recorded when logd fails"""
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        results = [("encryptly-preflight", False, 13.0, "encryptly not available", None)]
        report = build_diagnostic_report(
            results, "abc12345",
            logd_error="encryptly binary not found",
            message_blocker="You need to fix your environment"
        )
        self.assertEqual(report["failed"], 1)
        self.assertIsNotNone(report.get("message_blocker"))

    def test_empty_results(self):
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        report = build_diagnostic_report([], "abc12345")
        self.assertEqual(report["total_modules"], 0)
        self.assertEqual(report["passed"], 0)
        self.assertEqual(report["failed"], 0)


class TestWriteDiagnosticReport(unittest.TestCase):
    def test_write_and_read_report(self):
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        report = {
            "generated_at": "test",
            "commit": "abc12345",
            "total_modules": 1,
            "passed": 1,
            "failed": 0,
            "modules": [{"name": "test", "status": "PASS", "elapsed_seconds": 1.0, "output": "ok"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            write_diagnostic_report(path, report)
            self.assertTrue(path.exists())
            with open(path, "r") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["commit"], "abc12345")
            self.assertEqual(loaded["total_modules"], 1)


class TestModuleDefinitions(unittest.TestCase):
    def test_modules_have_required_fields(self):
        if not HAS_BUILD_MODULE:
            self.skipTest(f"Cannot import build.py: {_import_error}")
        for module in MODULES:
            for field in ["name", "language", "dir", "build_cmd", "clean_cmd"]:
                self.assertTrue(hasattr(module, field),
                                f"Module {module.name} missing field {field}")


if __name__ == "__main__":
    unittest.main()
