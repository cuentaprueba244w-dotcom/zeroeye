import json
import tempfile
import unittest
from pathlib import Path

import build


class BuildDiagnosticReportTests(unittest.TestCase):
    def test_failed_module_is_recorded_with_counts_and_elapsed_time(self):
        report = build.build_diagnostic_report(
            [("frontend", False, 1.2345, "npm build failed", None)],
            "deadbeef",
            logd_error="encryptly unavailable",
        )

        self.assertEqual(report["total_modules"], 1)
        self.assertEqual(report["passed"], 0)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["modules"][0]["name"], "frontend")
        self.assertEqual(report["modules"][0]["status"], "FAIL")
        self.assertEqual(report["modules"][0]["elapsed_seconds"], 1.234)
        self.assertEqual(report["modules"][0]["output"], "npm build failed")

    def test_successful_module_records_artifact_and_logd_path(self):
        report = build.build_diagnostic_report(
            [("backend", True, 0.5, "", "backend/target/debug/backend")],
            "deadbeef",
            logd_relpaths=["diagnostic/build-deadbeef.logd"],
            password="test-password",
        )

        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["diagnostic_logd"], "diagnostic/build-deadbeef.logd")
        self.assertEqual(report["modules"][0]["artifact"], "backend/target/debug/backend")
        self.assertIn("encryptly unpack diagnostic/build-deadbeef.logd", report["decrypt_command"])

    def test_chunked_logd_report_records_all_parts(self):
        relpaths = [
            "diagnostic/build-deadbeef-part001.logd",
            "diagnostic/build-deadbeef-part002.logd",
        ]
        report = build.build_diagnostic_report(
            [("backend", True, 0.5, "", None)],
            "deadbeef",
            logd_relpaths=relpaths,
            password="test-password",
            chunked=True,
        )

        self.assertEqual(report["diagnostic_logd"], relpaths)
        self.assertTrue(report["chunked"])
        self.assertEqual(report["chunk_size_bytes"], build.DIAGNOSTIC_CHUNK_SIZE)
        self.assertIn("diagnostic/build-deadbeef-part001.logd", report["pr_note"])

    def test_write_diagnostic_report_creates_json_file(self):
        report = build.build_diagnostic_report(
            [("encryptly-preflight", False, 0.25, "preflight failed", None)],
            "00000000",
            logd_error="preflight failed",
        )

        with tempfile.TemporaryDirectory() as tmp:
            diag_dir = Path(tmp) / "diagnostic"
            diag_dir.mkdir()
            path = diag_dir / "build-00000000.json"
            original_root = build.ROOT
            build.ROOT = Path(tmp)
            try:
                build.write_diagnostic_report(path, report)
            finally:
                build.ROOT = original_root
            written = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(written["commit"], "00000000")
        self.assertIsNone(written["diagnostic_logd"])
        self.assertEqual(written["diagnostic_logd_error"], "preflight failed")
        self.assertEqual(written["modules"][0]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
