#!/usr/bin/env python3
"""Tests for deploy_dry_run_summary.py — dry-run rollback summary export."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from deploy_dry_run_summary import (
    SERVICES,
    ENVIRONMENTS,
    SECRET_KEY_PATTERN,
    SECRET_VALUE_PATTERN,
    build_rollback_plan,
    build_summary,
    export_summary,
    format_text_summary,
    redact_summary,
)


class TestSecretRedaction(unittest.TestCase):
    """Verify secret-looking values are redacted from summaries."""

    def test_redact_api_key_in_dict(self):
        data = {"api_key": "sk-abc123", "name": "backend"}
        result = redact_summary(data)
        self.assertEqual(result["api_key"], "[REDACTED]")
        self.assertEqual(result["name"], "backend")

    def test_redact_password_in_dict(self):
        data = {"password": "hunter2", "env": "production"}
        result = redact_summary(data)
        self.assertEqual(result["password"], "[REDACTED]")

    def test_redact_token_key_casing(self):
        data = {"TOKEN": "ghp_xxx", "ApiKey": "abc123"}
        result = redact_summary(data)
        self.assertEqual(result["TOKEN"], "[REDACTED]")
        self.assertEqual(result["ApiKey"], "[REDACTED]")

    def test_redact_bearer_in_string_value(self):
        data = {"authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.dGVzdA"}
        result = redact_summary(data)
        self.assertEqual(result["authorization"], "[REDACTED]")

    def test_nested_redaction(self):
        data = {"config": {"connection_string": "postgres://user:pass@host/db"}, "name": "test"}
        result = redact_summary(data)
        self.assertEqual(result["config"]["connection_string"], "[REDACTED]")
        self.assertEqual(result["name"], "test")

    def test_innocent_values_not_redacted(self):
        data = {"service": "backend", "environment": "staging", "port": 8080}
        result = redact_summary(data)
        self.assertEqual(result["service"], "backend")
        self.assertEqual(result["port"], 8080)

    def test_list_redaction(self):
        data = [{"name": "backend", "api_key": "secret"}, {"name": "frontend"}]
        result = redact_summary(data)
        self.assertEqual(result[0]["api_key"], "[REDACTED]")
        self.assertEqual(result[1]["name"], "frontend")


class TestBuildRollbackPlan(unittest.TestCase):
    """Verify rollback plans contain all required fields."""

    def test_build_plan_backend_staging(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        self.assertEqual(plan["service"], "backend")
        self.assertEqual(plan["deployment"], "backend-api")
        self.assertEqual(plan["environment"], "staging")
        self.assertEqual(plan["target_version"], "v3.1.0")
        self.assertEqual(plan["language"], "rust")
        self.assertEqual(plan["namespace"], "tent-staging")
        self.assertEqual(plan["kube_context"], "staging-cluster")
        self.assertIn("risk_note", plan)
        self.assertIn("planned_actions", plan)
        self.assertIn("rollback_steps", plan)

    def test_build_plan_production(self):
        plan = build_rollback_plan("frontend", "production", "v3.2.0")
        self.assertEqual(plan["environment"], "production")
        self.assertEqual(plan["risk_note"], "High risk: production environment, real user traffic")

    def test_build_plan_development(self):
        plan = build_rollback_plan("market", "development", "v2.1.0")
        self.assertEqual(plan["environment"], "development")
        self.assertEqual(plan["namespace"], "tent-dev")

    def test_build_plan_unknown_service(self):
        plan = build_rollback_plan("unknown", "staging", "v1.0.0")
        self.assertEqual(plan, {})

    def test_build_plan_unknown_env(self):
        plan = build_rollback_plan("backend", "unknown", "v1.0.0")
        self.assertEqual(plan, {})

    def test_build_plan_rollback_actions_count(self):
        plan = build_rollback_plan("backend", "production", "v3.0.0")
        self.assertGreaterEqual(len(plan["rollback_steps"]), 6)
        self.assertGreaterEqual(len(plan["planned_actions"]), 5)

    def test_build_plan_custom_config(self):
        custom_services = {
            "test-svc": {
                "name": "test-deploy",
                "language": "python",
                "port": 9090,
                "replicas": {"staging": 1},
            }
        }
        custom_envs = {
            "staging": {
                "host": "test.example.com",
                "namespace": "test-ns",
                "kube_context": "test-ctx",
                "auto_approve": True,
            }
        }
        plan = build_rollback_plan(
            "test-svc", "staging", "v1.0.0",
            services=custom_services, envs=custom_envs,
        )
        self.assertEqual(plan["service"], "test-svc")
        self.assertEqual(plan["namespace"], "test-ns")


class TestBuildSummary(unittest.TestCase):
    """Verify summary aggregation and filtering."""

    def test_single_service_summary(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        summary = build_summary([plan], env="staging", service_opt="backend")
        self.assertEqual(summary["totals"]["services_included"], 1)
        self.assertEqual(summary["totals"]["total_rollback_steps"], 7)
        self.assertEqual(summary["filter"]["service"], "backend")
        self.assertEqual(summary["filter"]["environment"], "staging")

    def test_multi_service_summary(self):
        plans = [
            build_rollback_plan("backend", "staging", "v3.1.0"),
            build_rollback_plan("frontend", "staging", "v2.0.0"),
        ]
        summary = build_summary(plans, env="staging")
        self.assertEqual(summary["totals"]["services_included"], 2)
        self.assertEqual(summary["totals"]["total_rollback_steps"], 14)

    def test_production_warning(self):
        plan = build_rollback_plan("backend", "production", "v3.1.0")
        summary = build_summary([plan], env="production")
        warnings = summary.get("warnings", [])
        self.assertTrue(any("PRODUCTION ROLLBACK" in w for w in warnings))

    def test_manual_approval_warning(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        summary = build_summary([plan], env="staging")
        warnings = summary.get("warnings", [])
        self.assertTrue(any("Manual approval" in w for w in warnings))

    def test_secret_redaction_in_summary(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        summary = build_summary([plan], filter_secrets=True)
        self.assertIsNotNone(summary)

    def test_no_secret_redaction(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        summary = build_summary([plan], filter_secrets=False)
        self.assertEqual(summary["totals"]["services_included"], 1)

    def test_summary_has_required_keys(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        summary = build_summary([plan])
        required = ["summary_type", "generated_at", "filter", "totals", "plans"]
        for key in required:
            self.assertIn(key, summary)


class TestTextFormatter(unittest.TestCase):
    """Verify text output is structured and readable."""

    def test_text_contains_required_sections(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        summary = build_summary([plan])
        text = format_text_summary(summary)
        self.assertIn("DRY-RUN ROLLBACK SUMMARY", text)
        self.assertIn("BACKEND", text)
        self.assertIn("STAGING", text)
        self.assertIn("v3.1.0", text)
        self.assertIn("Step 1", text)
        self.assertIn("Step 7", text)

    def test_text_shows_warnings(self):
        plan = build_rollback_plan("backend", "production", "v3.1.0")
        summary = build_summary([plan], env="production")
        text = format_text_summary(summary)
        self.assertIn("PRODUCTION", text)
        self.assertIn("WARNINGS", text)

    def test_text_shows_all_actions(self):
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        summary = build_summary([plan])
        text = format_text_summary(summary)
        self.assertIn("Planned actions (7)", text)
        self.assertIn("Rollback steps (7)", text)

    def test_text_multi_service(self):
        plans = [
            build_rollback_plan("backend", "staging", "v3.1.0"),
            build_rollback_plan("market", "production", "v2.0.0"),
        ]
        summary = build_summary(plans)
        text = format_text_summary(summary)
        self.assertIn("BACKEND", text)
        self.assertIn("MARKET", text)


class TestExport(unittest.TestCase):
    """Verify file export produces valid text and JSON."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        plan = build_rollback_plan("backend", "staging", "v3.1.0")
        self.summary = build_summary([plan])

    def test_export_json_and_text(self):
        result = export_summary(self.summary, output_dir=self.temp_dir)
        self.assertIn("json", result)
        self.assertIn("text", result)
        self.assertTrue(os.path.exists(result["json"]))
        self.assertTrue(os.path.exists(result["text"]))

    def test_json_is_valid(self):
        result = export_summary(self.summary, output_dir=self.temp_dir)
        with open(result["json"]) as f:
            data = json.load(f)
        self.assertEqual(data["summary_type"], "dry_run_rollback")
        self.assertIn("plans", data)

    def test_export_custom_base_name(self):
        result = export_summary(
            self.summary, output_dir=self.temp_dir, base_name="my_summary"
        )
        self.assertIn("my_summary.json", result["json"])
        self.assertIn("my_summary.txt", result["text"])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestEnvironmentFilter(unittest.TestCase):
    """Verify environment-specific configurations are correct."""

    def test_all_envs_have_required_keys(self):
        for env_name, cfg in ENVIRONMENTS.items():
            with self.subTest(env=env_name):
                self.assertIn("host", cfg)
                self.assertIn("namespace", cfg)
                self.assertIn("kube_context", cfg)
                self.assertIn("auto_approve", cfg)

    def test_production_not_auto_approve(self):
        self.assertFalse(ENVIRONMENTS["production"]["auto_approve"])

    def test_development_is_auto_approve(self):
        self.assertTrue(ENVIRONMENTS["development"]["auto_approve"])


class TestServiceConfig(unittest.TestCase):
    """Verify service configurations are correct."""

    def test_all_services_have_required_keys(self):
        for svc_name, cfg in SERVICES.items():
            with self.subTest(service=svc_name):
                self.assertIn("name", cfg)
                self.assertIn("language", cfg)
                self.assertIn("port", cfg)
                self.assertIn("replicas", cfg)

    def test_all_services_have_replicas_for_all_envs(self):
        for svc_name, cfg in SERVICES.items():
            for env_name in ENVIRONMENTS:
                with self.subTest(service=svc_name, env=env_name):
                    self.assertIn(env_name, cfg["replicas"])


if __name__ == "__main__":
    unittest.main()