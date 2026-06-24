#!/usr/bin/env python3
"""Unit tests for health_check.py retry/backoff mechanism."""
import socket, sys, time
from unittest.mock import MagicMock, patch
import pytest
sys.path.insert(0, "tools")
from health_check import (
    RETRY_MAX_ATTEMPTS, RETRYABLE_EXCEPTIONS,
    check_cpu_health, check_disk_usage, check_http_service,
    check_load_average, check_memory_usage, check_system_health,
    check_tcp_port, retry_with_backoff,
)

class TestRetryDecorator:
    def test_successful_call_no_retry(self):
        call_count = [0]
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def ok_func(x): call_count[0] += 1; return "OK", f"r_{x}", x
        result = ok_func(42)
        assert result == ("OK", "r_42", 42); assert call_count[0] == 1

    def test_retry_on_socket_timeout(self):
        call_count = [0]
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky():
            call_count[0] += 1
            if call_count[0] < 3: raise socket.timeout("timed out")
            return "OK", "ok", 200
        result = flaky()
        assert result == ("OK", "ok", 200); assert call_count[0] == 3

    def test_retry_on_oserror(self):
        call_count = [0]
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky():
            call_count[0] += 1
            if call_count[0] < 2: raise OSError("io error")
            return "OK", "recovered", 1
        result = flaky()
        assert result == ("OK", "recovered", 1); assert call_count[0] == 2

    def test_retry_on_connection_error(self):
        call_count = [0]
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky():
            call_count[0] += 1
            if call_count[0] < 3: raise ConnectionError("fail")
            return "OK", "connected", 1
        assert flaky() == ("OK", "connected", 1); assert call_count[0] == 3

    def test_no_retry_on_value_error(self):
        call_count = [0]
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def bad(): call_count[0] += 1; raise ValueError("nope")
        with pytest.raises(ValueError): bad()
        assert call_count[0] == 1

    def test_max_attempts_exhausted(self):
        call_count = [0]
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def always(): call_count[0] += 1; raise socket.timeout("always")
        with pytest.raises(socket.timeout): always()
        assert call_count[0] == 3

    def test_exponential_backoff_timing(self):
        call_count = [0]; sleep_times = []
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def flaky():
            call_count[0] += 1
            if call_count[0] < 3: raise socket.timeout("t")
            return "OK", "ok", 1
        with patch("health_check.time.sleep", side_effect=lambda t: sleep_times.append(t)):
            flaky()
        assert len(sleep_times) == 2
        assert abs(sleep_times[0] - 0.1) < 0.01; assert abs(sleep_times[1] - 0.2) < 0.01

class TestCheckFunctionsHaveRetry:
    def test_all_have_retry(self):
        for fn in [check_http_service, check_tcp_port, check_disk_usage,
                   check_memory_usage, check_load_average, check_cpu_health,
                   check_system_health]:
            assert hasattr(fn, "__wrapped__"), f"{fn.__name__} missing retry"

class TestRetryableExceptions:
    def test_retryable(self):
        assert socket.timeout in RETRYABLE_EXCEPTIONS
        assert ConnectionError in RETRYABLE_EXCEPTIONS
        assert OSError in RETRYABLE_EXCEPTIONS

class TestCpuHealthCheck:
    def test_returns_tuple(self):
        r = check_cpu_health()
        assert isinstance(r, tuple); assert len(r) == 3
        _, _, d = r
        assert "cpu_count" in d; assert d["cpu_count"] > 0
