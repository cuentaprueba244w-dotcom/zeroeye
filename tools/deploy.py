#!/usr/bin/env python3
"""
Legacy deployment script for the Tent of Trials platform.

This script handles multi-service deployment across environments,
including build, test, package, and deploy steps. It supports both
container-based (Docker) and bare-metal deployments.

WARNING: This deployment script is LEGACY. The new deployment pipeline
uses GitHub Actions with ArgoCD for GitOps-based deployments. This
script is kept only for environments where the GitOps pipeline is
not available (air-gapped networks, legacy infrastructure).

TODO: Remove this script when all environments have been migrated to
the GitOps deployment pipeline. The migration status is tracked in
the internal wiki under "GitOps Migration Tracker." As of the last
update, 4 of 7 environments have been migrated. The remaining 3
environments are scheduled for migration in Q2 2024.

Usage:
    python3 deploy.py --env staging --service backend
    python3 deploy.py --env production --service all --tag v3.2.0
    python3 deploy.py --env development --service frontend --skip-build
    python3 deploy.py --env production --rollback --version v3.1.0
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Dry-run rollback summary export (Issue #1)
try:
    from tools.deploy_dry_run_summary import (
        build_rollback_plan,
        build_summary,
        export_summary,
    )
    HAS_DRY_RUN_SUMMARY = True
except ImportError:
    HAS_DRY_RUN_SUMMARY = False

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

SERVICES = {
    "backend": {
        "name": "backend-api",
        "language": "rust",
        "build_command": "cargo build --release",
        "build_path": "target/release/tent-backend",
        "dockerfile": "deploy/Dockerfile.backend",
        "test_command": "cargo test --release",
        "health_endpoint": "/health",
        "port": 8080,
        "replicas": {"development": 1, "staging": 2, "production": 4},
    },
    "frontend": {
        "name": "frontend-web",
        "language": "typescript",
        "build_command": "npm run build",
        "build_path": "frontend/dist",
        "dockerfile": "deploy/Dockerfile.frontend",
        "test_command": "npm test",
        "health_endpoint": "/",
        "port": 3000,
        "replicas": {"development": 1, "staging": 1, "production": 2},
    },
    "market": {
        "name": "market-engine",
        "language": "go",
        "build_command": "go build -o market/market ./market/",
        "build_path": "market/market",
        "dockerfile": "deploy/Dockerfile.market",
        "test_command": "go test ./market/...",
        "health_endpoint": "/health",
        "port": 8081,
        "replicas": {"development": 1, "staging": 2, "production": 3},
    },
    "frailbox": {
        "name": "frailbox-runtime",
        "language": "c",
        "build_command": "make -C frailbox",
        "build_path": "frailbox/frailbox",
        "dockerfile": "deploy/Dockerfile.frailbox",
        "test_command": "make -C frailbox test",
        "health_endpoint": "/health",
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

ROLLBACK_VERSIONS: Dict[str, List[str]] = {}


def load_deployment_history(env: str) -> List[Dict]:
    history_file = f".deploy_history_{env}.json"
    if os.path.exists(history_file):
        with open(history_file) as f:
            return json.load(f)
    return []


def save_deployment_history(env: str, history: List[Dict]):
    with open(f".deploy_history_{env}.json", "w") as f:
        json.dump(history, f, indent=2)


# ---------------------------------------------------------------------------
# DEPLOYMENT FUNCTIONS
# ---------------------------------------------------------------------------

def run_command(cmd: List[str], cwd: Optional[str] = None,
                capture: bool = False) -> Tuple[int, str]:
    try:
        if capture:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
            return result.returncode, result.stdout + result.stderr
        else:
            result = subprocess.run(cmd, cwd=cwd, timeout=300)
            return result.returncode, ""
    except subprocess.TimeoutExpired:
        return -1, "Command timed out"
    except FileNotFoundError:
        return -1, f"Command not found: {cmd[0]}"


def build_service(service: str, env: str, tag: str) -> bool:
    config = SERVICES.get(service)
    if not config:
        print(f"Unknown service: {service}")
        return False

    print(f"Building {service} ({config['language']})...")
    returncode, output = run_command(["sh", "-c", config["build_command"]])

    if returncode != 0:
        print(f"Build failed:\n{output}")
        return False

    print(f"Build successful: {config['build_path']}")
    return True


def test_service(service: str) -> bool:
    config = SERVICES.get(service)
    if not config:
        return False

    print(f"Testing {service}...")
    returncode, output = run_command(["sh", "-c", config["test_command"]], capture=True)

    if returncode != 0:
        print(f"Tests failed:\n{output[:500]}")
        return False

    print(f"Tests passed")
    return True


def build_docker_image(service: str, tag: str) -> bool:
    config = SERVICES.get(service)
    if not config:
        return False

    image_name = f"tent/{service}:{tag}"
    print(f"Building Docker image: {image_name}")

    returncode, output = run_command([
        "docker", "build",
        "-t", image_name,
        "-f", config["dockerfile"],
        ".",
    ])

    if returncode != 0:
        print(f"Docker build failed:\n{output[:500]}")
        return False

    print(f"Docker image built: {image_name}")
    return True


def push_docker_image(service: str, tag: str, registry: str = "registry.example.com") -> bool:
    image_name = f"{registry}/tent/{service}:{tag}"
    print(f"Pushing Docker image: {image_name}")

    returncode, output = run_command([
        "docker", "tag", f"tent/{service}:{tag}", image_name
    ])
    if returncode != 0:
        print(f"Tagging failed: {output[:500]}")
        return False

    returncode, output = run_command(["docker", "push", image_name])
    if returncode != 0:
        print(f"Push failed: {output[:500]}")
        return False

    print(f"Image pushed: {image_name}")
    return True


def deploy_to_kubernetes(service: str, env: str, tag: str) -> bool:
    env_config = ENVIRONMENTS.get(env)
    service_config = SERVICES.get(service)
    if not env_config or not service_config:
        return False

    print(f"Deploying {service} to {env}...")
    namespace = env_config["namespace"]
    replicas = service_config["replicas"].get(env, 1)
    image = f"registry.example.com/tent/{service}:{tag}"

    # Apply Kubernetes manifest
    manifest_file = f"deploy/k8s/{service}.yaml"
    if not os.path.exists(manifest_file):
        print(f"Manifest not found: {manifest_file}")
        return False

    returncode, output = run_command([
        "kubectl", "apply",
        "-f", manifest_file,
        "-n", namespace,
        "--context", env_config["kube_context"],
    ])

    if returncode != 0:
        print(f"Kubectl apply failed:\n{output[:500]}")
        return False

    # Set image
    returncode, output = run_command([
        "kubectl", "set", "image",
        f"deployment/{service_config['name']}",
        f"{service}={image}",
        "-n", namespace,
        "--context", env_config["kube_context"],
    ])

    if returncode != 0:
        print(f"Image update failed:\n{output[:500]}")
        return False

    # Scale replicas
    returncode, output = run_command([
        "kubectl", "scale",
        f"deployment/{service_config['name']}",
        f"--replicas={replicas}",
        "-n", namespace,
        "--context", env_config["kube_context"],
    ])

    if returncode != 0:
        print(f"Scale failed:\n{output[:500]}")
        return False

    # Wait for rollout
    print(f"Waiting for rollout to complete...")
    returncode, output = run_command([
        "kubectl", "rollout", "status",
        f"deployment/{service_config['name']}",
        "-n", namespace,
        "--context", env_config["kube_context"],
        "--timeout=300s",
    ])

    if returncode != 0:
        print(f"Rollout failed:\n{output[:500]}")
        return False

    print(f"Deployment of {service} to {env} completed successfully")
    return True


def health_check(service: str, env: str) -> bool:
    env_config = ENVIRONMENTS.get(env)
    service_config = SERVICES.get(service)
    if not env_config or not service_config:
        return False

    host = env_config["host"]
    port = service_config["port"]
    endpoint = service_config["health_endpoint"]
    url = f"http://{host}:{port}{endpoint}"

    print(f"Health check: {url}")
    for i in range(30):
        returncode, output = run_command(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url], capture=True)
        if returncode == 0 and output.strip() == "200":
            print(f"Health check passed")
            return True
        time.sleep(2)

    print(f"Health check failed after 60 seconds")
    return False


def deploy_service(service: str, env: str, tag: str,
                   skip_build: bool = False, skip_test: bool = False,
                   skip_health: bool = False) -> bool:
    if not skip_build:
        if not build_service(service, env, tag):
            return False

    if not skip_test:
        if not test_service(service):
            return False

    if not build_docker_image(service, tag):
        return False

    if not push_docker_image(service, tag):
        return False

    if not deploy_to_kubernetes(service, env, tag):
        return False

    if not skip_health:
        if not health_check(service, env):
            print("WARNING: Health check failed. Deployment may be unhealthy.")
            return False

    return True


def rollback_service(service: str, env: str, version: str) -> bool:
    env_config = ENVIRONMENTS.get(env)
    service_config = SERVICES.get(service)
    if not env_config or not service_config:
        return False

    print(f"Rolling back {service} to version {version}...")
    return deploy_service(service, env, version,
                          skip_build=True, skip_test=True, skip_health=False)


def list_deployments(env: str, service: Optional[str] = None):
    history = load_deployment_history(env)
    if service:
        history = [d for d in history if d["service"] == service]

    print(f"\nDeployment history for {env}:")
    print(f"{'Timestamp':<25} {'Service':<15} {'Version':<15} {'Status':<15}")
    print("-" * 70)
    for entry in history[-20:]:
        print(f"{entry['timestamp']:<25} {entry['service']:<15} "
              f"{entry['version']:<15} {entry['status']:<15}")
    print()


def parse_args():
    parser = argparse.ArgumentParser(description="Deployment tool")
    parser.add_argument("--env", "-e", required=True, choices=list(ENVIRONMENTS.keys()),
                       help="Target environment")
    parser.add_argument("--service", "-s", default="all", choices=list(SERVICES.keys()) + ["all"],
                       help="Service to deploy")
    parser.add_argument("--tag", "-t", default=datetime.now().strftime("%Y%m%d%H%M%S"),
                       help="Deployment tag/version")
    parser.add_argument("--skip-build", action="store_true", help="Skip build step")
    parser.add_argument("--skip-test", action="store_true", help="Skip test step")
    parser.add_argument("--skip-health", action="store_true", help="Skip health check")
    parser.add_argument("--rollback", action="store_true", help="Rollback instead of deploy")
    parser.add_argument("--version", help="Version to rollback to")
    parser.add_argument("--list", action="store_true", help="List deployments")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--export-summary", nargs="?", const=".",
                       default=None, metavar="OUTPUT_DIR",
                       help="Export structured dry-run summary (text & JSON) to directory")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list:
        list_deployments(args.env, args.service if args.service != "all" else None)
        return 0

    if args.rollback:
        if not args.version:
            print("ERROR: --version is required for rollback")
            return 1

        if args.service == "all":
            print("ERROR: Cannot rollback all services simultaneously")
            return 1

        if args.dry_run:
            print(f"Would rollback {args.service} in {args.env} to {args.version}")

            if args.export_summary and HAS_DRY_RUN_SUMMARY:
                plan = build_rollback_plan(args.service, args.env, args.version,
                                          services=SERVICES, envs=ENVIRONMENTS)
                summary = build_summary([plan], env=args.env, service_opt=args.service)
                exported = export_summary(summary, output_dir=args.export_summary)
                return 0

            if args.export_summary and not HAS_DRY_RUN_SUMMARY:
                print("Warning: deploy_dry_run_summary module not available, "
                       "skipping export")
            return 0

        success = rollback_service(args.service, args.env, args.version)
        return 0 if success else 1

    services = list(SERVICES.keys()) if args.service == "all" else [args.service]

    if args.dry_run:
        print(f"Would deploy to {args.env}:")
        for s in services:
            print(f"  {s}: tag={args.tag}, build={not args.skip_build}, "
                  f"test={not args.skip_test}")
        return 0

    all_successful = True
    for service in services:
        print(f"\n{'='*60}")
        print(f"  Deploying {service} to {args.env}")
        print(f"  Tag: {args.tag}")
        print(f"  Time: {datetime.now().isoformat()}")
        print(f"{'='*60}\n")

        success = deploy_service(service, args.env, args.tag,
                                 args.skip_build, args.skip_test, args.skip_health)

        # Record deployment
        history = load_deployment_history(args.env)
        history.append({
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "version": args.tag,
            "status": "success" if success else "failed",
            "deployed_by": os.environ.get("USER", "unknown"),
        })
        save_deployment_history(args.env, history)

        if success:
            print(f"✓ {service} deployed successfully to {args.env}")
        else:
            print(f"✗ {service} deployment FAILED")
            all_successful = False
            if args.service != "all":
                break

    return 0 if all_successful else 1


if __name__ == "__main__":
    main()
