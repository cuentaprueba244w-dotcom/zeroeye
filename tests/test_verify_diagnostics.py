import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_diagnostics import validate_report


class DiagnosticVerifierTests(unittest.TestCase):
    def test_validates_complete_report_with_failed_module(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostic = root / "diagnostic"
            diagnostic.mkdir()
            (diagnostic / "build-deadbeef.logd").write_bytes(b"encrypted diagnostic")
            metadata = diagnostic / "build-deadbeef.json"
            metadata.write_text(
                json.dumps(
                    {
                        "commit": "deadbeef",
                        "diagnostic_logd": "diagnostic/build-deadbeef.logd",
                        "total_modules": 2,
                        "passed": 1,
                        "failed": 1,
                        "modules": [
                            {
                                "name": "backend",
                                "status": "PASS",
                                "elapsed_seconds": 1.25,
                                "artifact": "backend/target",
                                "output": "",
                            },
                            {
                                "name": "frailbox",
                                "status": "FAIL",
                                "elapsed_seconds": 0.5,
                                "artifact": None,
                                "output": "make failed",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual(validate_report(metadata, root), [])

    def test_reports_missing_logd_and_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostic = root / "diagnostic"
            diagnostic.mkdir()
            metadata = diagnostic / "build-bad.json"
            metadata.write_text(
                json.dumps(
                    {
                        "commit": "bad",
                        "diagnostic_logd": "diagnostic/build-bad.logd",
                        "total_modules": 1,
                        "passed": 1,
                        "failed": 0,
                        "modules": [
                            {
                                "name": "backend",
                                "status": "FAIL",
                                "elapsed_seconds": 0.2,
                                "output": "failed",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            errors = validate_report(metadata, root)

        self.assertTrue(any("passed count" in error for error in errors))
        self.assertTrue(any("failed count" in error for error in errors))
        self.assertTrue(any("missing diagnostic artifact" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
