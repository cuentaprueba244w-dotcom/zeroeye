#!/usr/bin/env python3
"""Tests for ai_pipeline_timing_summary.py"""

import json
import os
import sys
import tempfile
import unittest

# Add the tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from ai_pipeline_timing_summary import build_summary, format_text_summary


class TestTimingSummary(unittest.TestCase):
    """Verify timing summary generation and budget threshold enforcement."""

    def setUp(self):
        self.sample_data = {
            "pipeline": "ai_pipeline",
            "started_at": "2026-06-21T10:00:00Z",
            "stages": [
                {"name": "data_preparation", "elapsed_secs": 3.512, "status": "done"},
                {"name": "backend_training", "elapsed_secs": 5.234, "status": "done"},
                {"name": "market_training", "elapsed_secs": 7.891, "status": "done"},
                {"name": "frontend_training", "elapsed_secs": 3.100, "status": "done"},
                {"name": "tools_training", "elapsed_secs": 4.200, "status": "done"},
                {"name": "frailbox_training", "elapsed_secs": 5.500, "status": "done"},
                {"name": "evaluation", "elapsed_secs": 4.000, "status": "done"},
                {"name": "deployment", "elapsed_secs": 4.800, "status": "done"},
            ],
        }

    def test_summary_structure(self):
        """Verify the summary contains all required fields."""
        summary = build_summary(self.sample_data)
        self.assertIn("pipeline", summary)
        self.assertIn("total_duration_secs", summary)
        self.assertIn("stage_count", summary)
        self.assertIn("stages", summary)
        self.assertIn("slowest_stage", summary)
        self.assertIn("status", summary)
        self.assertEqual(summary["pipeline"], "ai_pipeline")
        self.assertEqual(summary["stage_count"], 8)
        self.assertIsNotNone(summary["slowest_stage"])

    def test_total_duration(self):
        """Verify total duration equals sum of all stage elapsed times."""
        summary = build_summary(self.sample_data)
        expected = sum(s["elapsed_secs"] for s in self.sample_data["stages"])
        self.assertAlmostEqual(summary["total_duration_secs"], expected, places=2)

    def test_slowest_stage_detected(self):
        """Verify the slowest stage is correctly identified."""
        summary = build_summary(self.sample_data)
        self.assertEqual(summary["slowest_stage"]["name"], "market_training")
        self.assertAlmostEqual(summary["slowest_stage"]["elapsed_secs"], 7.891, places=2)

    def test_over_budget_threshold(self):
        """Verify over-budget stages are flagged when threshold is set."""
        # Set a tight threshold of 5 seconds
        summary = build_summary(self.sample_data, budget_secs=5.0)
        self.assertEqual(summary["status"], "OVER_BUDGET")
        over_budget_names = [s["name"] for s in summary["over_budget_stages"]]
        self.assertIn("market_training", over_budget_names)  # 7.891s > 5s
        self.assertIn("frailbox_training", over_budget_names)  # 5.5s > 5s
        self.assertIn("backend_training", over_budget_names)  # 5.234s > 5s
        self.assertNotIn("data_preparation", over_budget_names)  # 3.512s <= 5s

    def test_no_budget_threshold(self):
        """Verify no over-budget stages when threshold is not set."""
        summary = build_summary(self.sample_data, budget_secs=None)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(len(summary["over_budget_stages"]), 0)

    def test_generous_budget(self):
        """Verify PASS status when all stages are within budget."""
        summary = build_summary(self.sample_data, budget_secs=10.0)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(len(summary["over_budget_stages"]), 0)

    def test_empty_stages(self):
        """Verify graceful handling of empty stage list."""
        empty_data = {"pipeline": "ai_pipeline", "started_at": "", "stages": []}
        summary = build_summary(empty_data)
        self.assertEqual(summary["status"], "EMPTY")
        self.assertEqual(summary["stage_count"], 0)
        self.assertIsNone(summary["slowest_stage"])
        self.assertAlmostEqual(summary["total_duration_secs"], 0.0)

    def test_single_stage(self):
        """Verify summary works with a single stage."""
        single_data = {
            "pipeline": "ai_pipeline",
            "started_at": "2026-06-21T10:00:00Z",
            "stages": [
                {"name": "quick_stage", "elapsed_secs": 0.500, "status": "done"},
            ],
        }
        summary = build_summary(single_data)
        self.assertEqual(summary["stage_count"], 1)
        self.assertEqual(summary["slowest_stage"]["name"], "quick_stage")
        self.assertAlmostEqual(summary["total_duration_secs"], 0.5, places=2)

    def test_text_output_contains_keys(self):
        """Verify the text summary contains expected sections."""
        summary = build_summary(self.sample_data)
        text = format_text_summary(summary)
        self.assertIn("AI Pipeline Timing Summary", text)
        self.assertIn("Total Duration", text)
        self.assertIn("Slowest Stage", text)
        self.assertIn("market_training", text)
        self.assertIn("Per-Stage Breakdown", text)

    def test_text_over_budget_marker(self):
        """Verify over-budget stages are marked in text output."""
        summary = build_summary(self.sample_data, budget_secs=5.0)
        text = format_text_summary(summary)
        self.assertIn("OVER BUDGET", text)

    def test_load_timing_data(self):
        """Verify timing data can be loaded from a JSON file."""
        from ai_pipeline_timing_summary import load_timing_data, build_summary
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(self.sample_data, f)
            temp_path = f.name

        try:
            loaded = load_timing_data(temp_path)
            self.assertEqual(len(loaded["stages"]), 8)
            self.assertEqual(loaded["pipeline"], "ai_pipeline")

            summary = build_summary(loaded)
            self.assertEqual(summary["stage_count"], 8)
        finally:
            os.unlink(temp_path)

    def test_secret_redaction(self):
        """Verify the summary does not include raw prompt or secret content."""
        data_with_inputs = {
            "pipeline": "ai_pipeline",
            "started_at": "2026-06-21T10:00:00Z",
            "stages": [
                {"name": "inference", "elapsed_secs": 2.0, "status": "done",
                 "prompt": "my_secret_api_key_12345"},
            ],
        }
        summary = build_summary(data_with_inputs)
        text = format_text_summary(summary)
        # The summary module should only output stage name, elapsed, status
        # Not the raw prompt content
        self.assertNotIn("secret_api_key", text)
        # Stage name should appear
        self.assertIn("inference", text)


if __name__ == "__main__":
    unittest.main()
