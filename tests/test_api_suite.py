#!/usr/bin/env python3
"""
Comprehensive API test suite for the Tent of Trials platform tools.
Tests the health_check, benchmark, and config_generator modules.
"""

import json
import os
import socket
import ssl
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))


class TestHealthCheck:
    """Tests for health_check.py module."""

    @patch("health_check.socket.create_connection")
    def test_check_tcp_port_open(self, mock_connect):
        """Test TCP port check when port is open."""
        from health_check import check_tcp_port
        
        mock_connect.return_value = MagicMock()
        status, message, latency = check_tcp_port("localhost", 8080, timeout=5)
        
        assert status == "OK"
        assert "latency" in message.lower() or "ms" in message.lower()
        assert latency >= 0

    @patch("health_check.socket.create_connection")
    def test_check_tcp_port_closed(self, mock_connect):
        """Test TCP port check when port is closed."""
        from health_check import check_tcp_port
        
        mock_connect.side_effect = socket.timeout
        status, message, latency = check_tcp_port("localhost", 9999, timeout=1)
        
        assert status in ["CRITICAL", "WARNING"]
        assert "timeout" in message.lower() or "error" in message.lower()

    @patch("health_check.requests.get")
    def test_check_http_service_ok(self, mock_get):
        """Test HTTP service check when service is healthy."""
        from health_check import check_http_service
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        status, message, latency = check_http_service("localhost", 8080, "/health", 5)
        
        assert status == "OK"
        assert "200" in message or "ok" in message.lower()

    @patch("health_check.requests.get")
    def test_check_http_service_error(self, mock_get):
        """Test HTTP service check when service is unhealthy."""
        from health_check import check_http_service
        
        mock_get.side_effect = Exception("Connection refused")
        status, message, latency = check_http_service("localhost", 8080, "/health", 5)
        
        assert status in ["CRITICAL", "WARNING"]
        assert "error" in message.lower() or "connection" in message.lower()

    @patch("health_check.os.statvfs")
    def test_check_disk_usage_normal(self, mock_statvfs):
        """Test disk usage check when usage is normal."""
        from health_check import check_disk_usage
        
        mock_stat = MagicMock()
        mock_stat.f_blocks = 1000000
        mock_stat.f_bavail = 500000
        mock_stat.f_frsize = 4096
        mock_statvfs.return_value = mock_stat
        
        status, message, usage = check_disk_usage("/")
        
        assert status == "OK"
        assert usage == 50.0

    @patch("health_check.os.statvfs")
    def test_check_disk_usage_high(self, mock_statvfs):
        """Test disk usage check when usage is high."""
        from health_check import check_disk_usage
        
        mock_stat = MagicMock()
        mock_stat.f_blocks = 1000000
        mock_stat.f_bavail = 10000
        mock_stat.f_frsize = 4096
        mock_statvfs.return_value = mock_stat
        
        status, message, usage = check_disk_usage("/")
        
        assert status in ["WARNING", "CRITICAL"]
        assert usage > 90

    @patch("health_check.psutil.virtual_memory")
    def test_check_memory_usage_normal(self, mock_memory):
        """Test memory usage check when usage is normal."""
        from health_check import check_memory_usage
        
        mock_memory.return_value = MagicMock(percent=50.0)
        
        status, message, usage = check_memory_usage()
        
        assert status == "OK"
        assert usage == 50.0

    @patch("health_check.psutil.virtual_memory")
    def test_check_memory_usage_high(self, mock_memory):
        """Test memory usage check when usage is high."""
        from health_check import check_memory_usage
        
        mock_memory.return_value = MagicMock(percent=95.0)
        
        status, message, usage = check_memory_usage()
        
        assert status in ["WARNING", "CRITICAL"]
        assert usage > 90


class TestConfigGenerator:
    """Tests for config_generator.py module."""

    def test_merge_config_simple(self):
        """Test simple config merging."""
        from config_generator import merge_config
        
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge_config(base, override)
        
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_config_nested(self):
        """Test nested config merging."""
        from config_generator import merge_config
        
        base = {"db": {"host": "localhost", "port": 5432}}
        override = {"db": {"port": 5433}}
        result = merge_config(base, override)
        
        assert result == {"db": {"host": "localhost", "port": 5433}}

    def test_merge_config_no_mutation(self):
        """Test that merge_config does not mutate original dicts."""
        from config_generator import merge_config
        
        base = {"a": {"x": 1}}
        override = {"a": {"y": 2}}
        original_base = base.copy()
        result = merge_config(base, override)
        
        assert base == original_base
        assert result == {"a": {"x": 1, "y": 2}}

    def test_mask_sensitive(self):
        """Test sensitive value masking."""
        from config_generator import mask_sensitive
        
        config = {
            "database": {"password": "secret123"},
            "redis": {"password": "redis_pass"},
            "auth": {"jwt_secret": "jwt_secret_value"},
            "server": {"host": "localhost"}
        }
        masked = mask_sensitive(config)
        
        assert masked["database"]["password"] == "***REDACTED***"
        assert masked["redis"]["password"] == "***REDACTED***"
        assert masked["auth"]["jwt_secret"] == "***REDACTED***"
        assert masked["server"]["host"] == "localhost"

    def test_generate_config_development(self):
        """Test config generation for development environment."""
        from config_generator import generate_config
        
        config = generate_config("development")
        
        assert config["app"]["environment"] == "development"
        assert config["app"]["debug"] is True
        assert config["app"]["log_level"] == "debug"

    def test_generate_config_production(self):
        """Test config generation for production environment."""
        from config_generator import generate_config
        
        config = generate_config("production")
        
        assert config["app"]["environment"] == "production"
        assert config["app"]["debug"] is False
        assert config["app"]["log_level"] == "info"

    def test_generate_config_with_overrides(self):
        """Test config generation with custom overrides."""
        from config_generator import generate_config
        
        overrides = {"server": {"port": 9000}}
        config = generate_config("development", overrides)
        
        assert config["server"]["port"] == 9000


class TestBenchmark:
    """Tests for benchmark.py module."""

    def test_benchmark_latency_parser(self):
        """Test latency benchmark argument parsing."""
        from benchmark import parse_args
        
        args = parse_args(["latency", "--endpoint", "http://localhost:8080", "--requests", "100"])
        
        assert args.mode == "latency"
        assert args.endpoint == "http://localhost:8080"
        assert args.requests == 100

    def test_benchmark_throughput_parser(self):
        """Test throughput benchmark argument parsing."""
        from benchmark import parse_args
        
        args = parse_args(["throughput", "--endpoint", "http://localhost:8080", "--duration", "30"])
        
        assert args.mode == "throughput"
        assert args.duration == 30


class TestIntegration:
    """Integration tests for tool interactions."""

    def test_health_check_json_output(self):
        """Test health check with JSON output format."""
        from health_check import run_health_checks
        
        with patch("health_check.check_tcp_port") as mock_tcp:
            mock_tcp.return_value = ("OK", "Port open", 0.5)
            results = run_health_checks(json_output=True)
            
            assert isinstance(results, dict)
            assert "timestamp" in results or "services" in results

    def test_config_roundtrip(self):
        """Test config generation and masking roundtrip."""
        from config_generator import generate_config, mask_sensitive
        
        config = generate_config("development")
        masked = mask_sensitive(config)
        
        # Sensitive values should be redacted
        assert masked["database"]["password"] == "***REDACTED***"
        # Non-sensitive values should remain
        assert masked["server"]["host"] == "localhost"
