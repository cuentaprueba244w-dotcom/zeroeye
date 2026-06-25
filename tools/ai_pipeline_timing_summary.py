#!/usr/bin/env python3
"""
AI Pipeline Timing Budget Summary

Records per-stage timing data for the AI training pipeline and generates
text and JSON summaries with optional budget threshold enforcement.

Usage:
    python3 tools/ai_pipeline_timing_summary.py --input timing_data.json
    python3 tools/ai_pipeline_timing_summary.py --input timing_data.json --threshold 30
    python3 tools/ai_pipeline_timing_summary.py --input timing_data.json --output-dir metrics/

The --threshold flag or AI_STAGE_BUDGET_SECS env var sets the over-budget
threshold (default: no threshold). Stages exceeding this limit are flagged.
"""

import argparse
import json
import os
import sys
from datetime import datetime


def load_timing_data(path):
    """Load stage timing records from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_summary(data, budget_secs=None):
    """Build a structured summary from timing data.

    The summary includes:
      - Pipeline-wide totals (duration, stage count)
      - Per-stage elapsed times
      - Slowest stage
      - Over-budget stages (if threshold is set)
      - Redacted metadata (no raw prompts or secrets)
    """
    stages = data.get("stages", [])
    pipeline_name = data.get("pipeline", "ai_pipeline")
    started_at = data.get("started_at", "")

    if not stages:
        return {
            "pipeline": pipeline_name,
            "started_at": started_at,
            "finished_at": datetime.utcnow().isoformat() + "Z",
            "total_duration_secs": 0.0,
            "stage_count": 0,
            "stages": [],
            "slowest_stage": None,
            "over_budget_stages": [],
            "status": "EMPTY",
        }

    total_duration = 0.0
    parsed_stages = []

    for stage in stages:
        name = stage.get("name", "unknown")
        elapsed = stage.get("elapsed_secs", 0.0)
        status = stage.get("status", "unknown")
        total_duration += elapsed

        parsed_stages.append({
            "name": name,
            "elapsed_secs": round(elapsed, 3),
            "status": status,
        })

    # Sort by elapsed descending to find slowest
    sorted_stages = sorted(parsed_stages, key=lambda s: s["elapsed_secs"], reverse=True)
    slowest = sorted_stages[0] if sorted_stages else None

    # Check budget
    over_budget = []
    if budget_secs is not None:
        for stage in parsed_stages:
            if stage["elapsed_secs"] > budget_secs:
                over_budget.append(stage)

    return {
        "pipeline": pipeline_name,
        "started_at": started_at,
        "finished_at": datetime.utcnow().isoformat() + "Z",
        "total_duration_secs": round(total_duration, 3),
        "stage_count": len(parsed_stages),
        "stages": parsed_stages,
        "slowest_stage": slowest,
        "over_budget_stages": over_budget,
        "budget_secs": budget_secs,
        "status": "OVER_BUDGET" if over_budget else ("PASS" if parsed_stages else "EMPTY"),
    }


def format_text_summary(summary):
    """Format the summary as human-readable text."""

    lines = []
    lines.append("=" * 60)
    lines.append(f"  AI Pipeline Timing Summary")
    lines.append(f"  Pipeline: {summary['pipeline']}")
    lines.append(f"  Status:   {summary['status']}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Started:           {summary['started_at']}")
    lines.append(f"  Finished:          {summary['finished_at']}")
    lines.append(f"  Total Duration:    {summary['total_duration_secs']:.2f}s")
    lines.append(f"  Stage Count:       {summary['stage_count']}")
    lines.append("")

    if summary['slowest_stage']:
        slow = summary['slowest_stage']
        lines.append(f"  Slowest Stage:     {slow['name']} ({slow['elapsed_secs']:.2f}s)")
    lines.append("")

    lines.append("  Per-Stage Breakdown:")
    lines.append("  " + "-" * 50)
    for stage in summary['stages']:
        budget_flag = ""
        if summary['budget_secs'] is not None and stage['elapsed_secs'] > summary['budget_secs']:
            budget_flag = "  *** OVER BUDGET ***"
        lines.append(f"    {stage['name']:<35s} {stage['elapsed_secs']:>8.2f}s  [{stage['status']}]{budget_flag}")
    lines.append("")

    if summary['over_budget_stages']:
        lines.append(f"  Stages Over Budget (threshold: {summary['budget_secs']}s):")
        for stage in summary['over_budget_stages']:
            lines.append(f"    - {stage['name']} ({stage['elapsed_secs']:.2f}s)")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI pipeline timing budget summary"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to timing data JSON file (from ai_pipeline.sh)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Directory for summary output files (default: stdout only)"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=None,
        help="Budget threshold in seconds (overrides AI_STAGE_BUDGET_SECS)"
    )
    args = parser.parse_args()

    # Determine budget threshold: CLI flag > env var > no limit
    budget_secs = args.threshold
    if budget_secs is None:
        env_threshold = os.environ.get("AI_STAGE_BUDGET_SECS")
        if env_threshold is not None:
            try:
                budget_secs = float(env_threshold)
            except (ValueError, TypeError):
                print(
                    f"Warning: Invalid AI_STAGE_BUDGET_SECS={env_threshold}, "
                    f"ignoring",
                    file=sys.stderr,
                )
                budget_secs = None

    try:
        data = load_timing_data(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Cannot load timing data: {e}", file=sys.stderr)
        return 1

    summary = build_summary(data, budget_secs)

    # Text output
    text = format_text_summary(summary)
    print(text)

    # JSON output
    json_summary = json.dumps(summary, indent=2)

    # Write files if output directory specified
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)

        text_path = os.path.join(args.output_dir, "timing_summary.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
            f.write("\n")
        print(f"\nText summary written to: {text_path}")

        json_path = os.path.join(args.output_dir, "timing_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_summary)
            f.write("\n")
        print(f"JSON summary written to: {json_path}")

    print(json_summary)

    return 0 if summary["status"] != "ERROR" else 1


if __name__ == "__main__":
    sys.exit(main())
