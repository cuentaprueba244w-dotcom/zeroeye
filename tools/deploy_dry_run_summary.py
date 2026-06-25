#!/usr/bin/env python3
"""
Deploy Dry-Run Rollback Summary Export

Generates structured text and JSON summaries for dry-run rollback
operations. Supports filtering by service and environment, and
redacts secret-looking values from exported summaries.

Usage:
    python3 tools/deploy_dry_run_summary.py \
        --service backend --env staging --version v3.1.0
    python3 tools/deploy_dry_run_summary.py \
        --service all --env production --version v3.2.0 \
        --output-dir metrics/
    python3 tools/deploy_dry_run_summary.py \
        --service market --env production --version v3.0.0 \
        --filter-secrets
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# SECRET REDACTION
# ---------------------------------------------------------------------------

SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|auth|authorization|bearer|cookie|credential|password"
    r"|secret|token|private[_-]?key|certificate[_-]?key|signing[_-]?key"
    r"|db[_-]?url|database[_-]?url|connection[_-]?string|jwt)",
    re.IGNORECASE,
)

SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|password|secret|token"
    r"|private[_-]?key|signing[_-]?key)\s*[:=]?\s*(?:bearer\s+)?\S+"
)


def _redact_scalar(value: Any) -> str:
    """Redact a scalar if it looks like a secret value."""
    if isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        return "[REDACTED]"
    return str(value)


def redact_summary(data: Any) -> Any:
    """Recursively redact secret-looking keys and values from a summary dict.

    Scans dictionary keys matching known secret patterns and replaces their
    values with '[REDACTED]'. Also scans string values for embedded secrets.
    """
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for key, value in data.items():
            str_key = str(key)
            if SECRET_KEY_PATTERN.search(str_key):
                cleaned[str_key] = "[REDACTED]"
            elif isinstance(value, (dict, list)):
                cleaned[str_key] = redact_summary(value)
            elif isinstance(value, str):
                cleaned[str_key] = _redact_scalar(value)
            else:
                cleaned[str_key] = value
        return cleaned
    if isinstance(data, list):
        return [redact_summary(item) for item in data]
    if isinstance(data, str):
        return _redact_scalar(data)
    return data


# ---------------------------------------------------------------------------
# SERVICE ENVIRONMENT CONFIGURATION (mirrors deploy.py)
# ---------------------------------------------------------------------------

SERVICES = {
    "backend": {
        "name": "backend-api",
        "language": "rust",
        "port": 8080,
        "replicas": {"development": 1, "staging": 2, "production": 4},
    },
    "frontend": {
        "name": "frontend-web",
        "language": "typescript",
        "port": 3000,
        "replicas": {"development": 1, "staging": 1, "production": 2},
    },
    "market": {
        "name": "market-engine",
        "language": "go",
        "port": 8081,
        "replicas": {"development": 1, "staging": 2, "production": 3},
    },
    "frailbox": {
        "name": "frailbox-runtime",
        "language": "c",
        "port": 8082,
        "replicas": {"development": 1, "staging": 1, "production": 2},
    },
}

ENVIRONMENTS = {
    "development": {
        "host": "dev.example.com",
        "namespace": "tent-dev",
        "kube_context": "dev-cluster",
        "auto_approve": True,
    },
    "staging": {
        "host": "staging.example.com",
        "namespace": "tent-staging",
        "kube_context": "staging-cluster",
        "auto_approve": False,
    },
    "production": {
        "host": "api.example.com",
        "namespace": "tent-production",
        "kube_context": "prod-cluster",
        "auto_approve": False,
    },
}


# ---------------------------------------------------------------------------
# ROLLBACK PLAN BUILDER
# ---------------------------------------------------------------------------

_RISK_NOTES = {
    "development": "Low risk: development environment, no real traffic",
    "staging": "Medium risk: staging environment, synthetic traffic only",
    "production": "High risk: production environment, real user traffic",
}

_ROLLBACK_STEPS = [
    {
        "step": 1,
        "action": "Identify the target version from deployment history",
        "command": (
            "python3 tools/deploy.py --rollback "
            "--env {env} --service {service} --version {version}"
        ),
    },
    {
        "step": 2,
        "action": "Scale down the current deployment to zero replicas",
        "command": (
            "kubectl scale deployment/{deployment} --replicas=0 "
            "-n {namespace} --context {kube_context}"
        ),
    },
    {
        "step": 3,
        "action": "Deploy the target version directly",
        "command": (
            "kubectl set image deployment/{deployment} "
            "{container}=registry.example.com/tent/{service}:{version} "
            "-n {namespace} --context {kube_context}"
        ),
    },
    {
        "step": 4,
        "action": "Scale up the deployment to the required replica count",
        "command": (
            "kubectl scale deployment/{deployment} "
            "--replicas={replicas} "
            "-n {namespace} --context {kube_context}"
        ),
    },
    {
        "step": 5,
        "action": "Wait for rollout to complete",
        "command": (
            "kubectl rollout status deployment/{deployment} "
            "-n {namespace} --context {kube_context} --timeout=300s"
        ),
    },
    {
        "step": 6,
        "action": "Verify health check endpoint",
        "command": (
            "curl -s -o /dev/null -w '%{{http_code}}' "
            "http://{host}:{port}/health"
        ),
    },
    {
        "step": 7,
        "action": "Run smoke tests on the restored service",
        "command": (
            "python3 tools/health_check.py "
            "--service {service} --env {env}"
        ),
    },
]

_PLANNED_ACTIONS = [
    "Halt current deployment",
    "Execute rollback sequence (7 steps)",
    "Re-deploy previous stable version",
    "Restore database to pre-deployment state (if migration run)",
    "Verify service health after rollback",
    "Run post-rollback smoke tests",
    "Notify stakeholders of rollback completion",
]


def build_rollback_plan(
    service: str,
    env: str,
    version: str,
    services: Optional[Dict[str, Any]] = None,
    envs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a structured rollback plan for a single service.

    Args:
        service: Service name (e.g., 'backend', 'frontend').
        env: Environment name.
        version: Target version/tag to rollback to.
        services: Optional service config (defaults to module SERVICES).
        envs: Optional environment config (defaults to module ENVIRONMENTS).

    Returns:
        Dict containing the complete rollback plan.
    """
    svc_cfg = (services or SERVICES).get(service)
    env_cfg = (envs or ENVIRONMENTS).get(env)

    if not svc_cfg or not env_cfg:
        return {}

    deployment = svc_cfg["name"]
    replicas = svc_cfg["replicas"].get(env, 1)

    steps = []
    for s in _ROLLBACK_STEPS:
        step = dict(s)
        step["command"] = step["command"].format(
            env=env,
            service=service,
            version=version,
            deployment=deployment,
            namespace=env_cfg["namespace"],
            kube_context=env_cfg["kube_context"],
            registry="registry.example.com",
            replicas=replicas,
            host=env_cfg["host"],
            port=svc_cfg["port"],
            container=service,
        )
        steps.append(step)

    return {
        "service": service,
        "deployment": deployment,
        "environment": env,
        "target_version": version,
        "language": svc_cfg["language"],
        "namespace": env_cfg["namespace"],
        "kube_context": env_cfg["kube_context"],
        "risk_note": _RISK_NOTES.get(env, "Unknown risk level"),
        "planned_actions": list(_PLANNED_ACTIONS),
        "rollback_steps": steps,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def auto_approve(env_name: str) -> bool:
    """Check whether the given environment supports auto-approve."""
    env_cfg = ENVIRONMENTS.get(env_name, {})
    return env_cfg.get("auto_approve", False)


def build_summary(
    rollback_plans: List[Dict[str, Any]],
    filter_secrets: bool = True,
    env: Optional[str] = None,
    service_opt: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a structured summary from one or more rollback plans.

    Args:
        rollback_plans: List of rollback plan dicts.
        filter_secrets: Whether to redact secret-looking values (default: True).
        env: Optional environment filter.
        service_opt: Optional service filter.

    Returns:
        A structured summary dict.
    """
    plans = list(rollback_plans)

    total_services = len(plans)
    total_steps = sum(len(p.get("rollback_steps", [])) for p in plans)
    environments = sorted({
        p["environment"] for p in plans if "environment" in p
    })

    warnings = []
    for p in plans:
        env_name = p.get("environment", "")
        if env_name == "production":
            warnings.append(
                f"PRODUCTION ROLLBACK: {p['service']} — "
                f"requires CAB approval and 48-hour stakeholder notice"
            )
        if not auto_approve(env_name):
            warnings.append(
                f"Manual approval required for "
                f"{p['service']} in {p['environment']}"
            )

    summary: Dict[str, Any] = {
        "summary_type": "dry_run_rollback",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "filter": {
            "service": service_opt or "all",
            "environment": env or "all",
        },
        "totals": {
            "services_included": total_services,
            "total_rollback_steps": total_steps,
            "environments_affected": environments,
        },
        "plans": plans,
        "warnings": warnings,
    }

    if filter_secrets:
        summary = redact_summary(summary)

    return summary


# ---------------------------------------------------------------------------
# SUMMARY FORMATTERS
# ---------------------------------------------------------------------------

def format_text_summary(summary: Dict[str, Any]) -> str:
    """Format a dry-run rollback summary as human-readable text.

    Produces a structured report with environment info, per-service
    rollback plans, risk notes, and detailed rollback steps.
    """
    lines: List[str] = []
    lines.append("=" * 72)
    lines.append("  DRY-RUN ROLLBACK SUMMARY")
    lines.append("=" * 72)
    lines.append(f"  Generated: {summary.get('generated_at', 'unknown')}")
    lines.append(
        f"  Filter: service={summary['filter']['service']}, "
        f"env={summary['filter']['environment']}"
    )
    lines.append(
        f"  Services: {summary['totals']['services_included']}"
    )
    lines.append(
        f"  Total steps: {summary['totals']['total_rollback_steps']}"
    )
    lines.append(
        "  Environments: "
        f"{', '.join(summary['totals']['environments_affected'])}"
    )
    lines.append("=" * 72)

    # Warnings
    warnings = summary.get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("\u26a0\ufe0f  WARNINGS:")
        for w in warnings:
            lines.append(f"  \u26a0  {w}")
        lines.append("")

    # Per-service plans
    for idx, plan in enumerate(summary.get("plans", []), 1):
        lines.append("-" * 72)
        lines.append(
            f"  [{idx}] {plan.get('service', '?').upper()} "
            f"\u2192 {plan.get('environment', '?').upper()}"
        )
        lines.append("-" * 72)
        lines.append(f"  Deployment:     {plan.get('deployment', '?')}")
        lines.append(f"  Language:       {plan.get('language', '?')}")
        lines.append(
            f"  Target version: {plan.get('target_version', '?')}"
        )
        lines.append(
            f"  Namespace:      {plan.get('namespace', '?')}"
        )
        lines.append(
            f"  Kube context:   {plan.get('kube_context', '?')}"
        )
        lines.append(
            f"  Risk:           {plan.get('risk_note', 'Unknown')}"
        )

        actions = plan.get("planned_actions", [])
        if actions:
            lines.append(
                f"\n  Planned actions ({len(actions)}):"
            )
            for action in actions:
                lines.append(f"    \u2022 {action}")

        steps = plan.get("rollback_steps", [])
        if steps:
            lines.append(f"\n  Rollback steps ({len(steps)}):")
            for step in steps:
                lines.append("")
                lines.append(
                    f"    Step {step['step']}: {step['action']}"
                )
                lines.append(f"      $ {step['command']}")

        lines.append("")

    lines.append("=" * 72)
    lines.append("  END OF SUMMARY")
    lines.append("=" * 72)

    return "\n".join(lines)


def export_summary(
    summary: Dict[str, Any],
    output_dir: str = ".",
    base_name: str = "rollback_dry_run",
) -> Dict[str, str]:
    """Export a dry-run rollback summary as text and JSON files.

    Args:
        summary: The structured summary dict.
        output_dir: Directory to write output files.
        base_name: Base filename (without extension).

    Returns:
        Dict mapping format names to file paths.
    """
    os.makedirs(output_dir, exist_ok=True)

    # JSON export
    json_path = os.path.join(output_dir, f"{base_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"JSON summary exported: {json_path}")

    # Text export
    text_path = os.path.join(output_dir, f"{base_name}.txt")
    text_content = format_text_summary(summary)
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text_content)
    print(f"Text summary exported: {text_path}")

    return {"json": json_path, "text": text_path}


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export dry-run rollback summary (text + JSON)",
    )
    parser.add_argument(
        "--service", "-s",
        default="all",
        help="Service name (default: all)",
    )
    parser.add_argument(
        "--env", "-e",
        default="staging",
        choices=list(ENVIRONMENTS.keys()),
        help="Target environment (default: staging)",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Target version/tag to rollback to",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Output directory for summary files",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Disable secret redaction (not recommended)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for standalone usage."""
    args = parse_args(argv)

    if args.service == "all":
        services = list(SERVICES.keys())
    elif args.service in SERVICES:
        services = [args.service]
    else:
        print(f"Unknown service: {args.service}")
        print(f"Available: {', '.join(SERVICES.keys())}")
        return 1

    if args.env not in ENVIRONMENTS:
        print(f"Unknown environment: {args.env}")
        print(f"Available: {', '.join(ENVIRONMENTS.keys())}")
        return 1

    plans = []
    for svc in services:
        plan = build_rollback_plan(svc, args.env, args.version)
        if plan:
            plans.append(plan)
        else:
            print(f"Warning: could not build plan for {svc} in {args.env}")

    if not plans:
        print("No rollback plans generated.")
        return 1

    summary = build_summary(
        plans,
        filter_secrets=not args.no_redact,
        env=args.env,
        service_opt=args.service,
    )

    exported = export_summary(summary, output_dir=args.output_dir)

    print(f"\nRollback dry-run summary exported:")
    for fmt, path in exported.items():
        print(f"  {fmt}: {path}")

    warnings = summary.get("warnings", [])
    if warnings:
        print(
            f"\n\u26a0\ufe0f  {len(warnings)} warning(s) "
            f"\u2014 review text output for details"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())