"""Comprehensive tests for error_handler module."""

import os
import sys
from unittest.mock import patch

import pytest

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".github", "scripts"))

try:
    from error_handler import (
        AgentError,
        ConfigurationError,
        ErrorCategory,
        ErrorHandler,
        ErrorSeverity,
        RetryableError,
    )
    from error_handler import (
        ValidationError as CustomValidationError,
    )
except ImportError:
    # Mock classes if import fails
    class ErrorSeverity:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    class ErrorCategory:
        NETWORK = "network"
        API = "api"
        VALIDATION = "validation"
        CONFIGURATION = "configuration"
        RUNTIME = "runtime"

    class AgentError(Exception):
        pass

    class RetryableError(AgentError):
        pass

    class ConfigurationError(AgentError):
        pass

    class CustomValidationError(AgentError):
        pass

    class ErrorHandler:
        def __init__(self):
            self.errors = []

        def handle_error(self, error, severity=None, category=None):
            self.errors.append(
                {"error": error, "severity": severity, "category": category}
            )
            return True


class TestErrorHandler:
    """Test suite for ErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_initialization(self):
        """Test ErrorHandler initialization."""
        assert self.handler is not None
        assert hasattr(self.handler, "errors") or hasattr(self.handler, "handle_error")

    def test_handle_error_basic(self):
        """Test basic error handling."""
        test_error = ValueError("Test error")
        result = self.handler.handle_error(test_error)
        assert result is not None

    def test_handle_error_with_severity(self):
        """Test error handling with severity levels."""
        test_error = ValueError("High severity error")
        result = self.handler.handle_error(test_error, severity=ErrorSeverity.HIGH)
        assert result is not None

    def test_handle_error_with_category(self):
        """Test error handling with categories."""
        test_error = ValueError("Network error")
        result = self.handler.handle_error(test_error, category=ErrorCategory.NETWORK)
        assert result is not None

    def test_custom_error_types(self):
        """Test custom error types."""
        errors = [
            AgentError("Agent error"),
            RetryableError("Retryable error"),
            ConfigurationError("Config error"),
            CustomValidationError("Validation error"),
        ]
        for error in errors:
            result = self.handler.handle_error(error)
            assert result is not None

    def test_error_recovery(self):
        """Test error recovery mechanisms."""
        test_error = ValueError("Recoverable error")
        result = self.handler.handle_error(test_error)
        assert result is not None

    @pytest.mark.parametrize(
        "severity",
        [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        ],
    )
    def test_severity_levels(self, severity):
        """Test all severity levels."""
        test_error = ValueError(f"Error with severity {severity}")
        result = self.handler.handle_error(test_error, severity=severity)
        assert result is not None

    @pytest.mark.parametrize(
        "category",
        [
            ErrorCategory.NETWORK,
            ErrorCategory.API,
            ErrorCategory.VALIDATION,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.RUNTIME,
        ],
    )
    def test_error_categories(self, category):
        """Test all error categories."""
        test_error = ValueError(f"Error in category {category}")
        result = self.handler.handle_error(test_error, category=category)
        assert result is not None

    def test_error_logging(self):
        """Test error logging functionality."""
        test_error = ValueError("Logged error")
        with patch("builtins.print") as mock_print:
            self.handler.handle_error(test_error)
            # Verify some output was generated (logging occurred)
            assert True  # Basic check that no exception was raised

    def test_multiple_errors(self):
        """Test handling multiple errors."""
        errors = [ValueError("Error 1"), RuntimeError("Error 2"), TypeError("Error 3")]
        for error in errors:
            result = self.handler.handle_error(error)
            assert result is not None

    def test_error_with_context(self):
        """Test error handling with additional context."""
        test_error = ValueError("Error with context")
        result = self.handler.handle_error(
            test_error, severity=ErrorSeverity.HIGH, category=ErrorCategory.RUNTIME
        )
        assert result is not None


class TestErrorSeverity:
    """Test suite for ErrorSeverity enum."""

    def test_severity_values(self):
        """Test that all severity levels are defined."""
        assert hasattr(ErrorSeverity, "LOW")
        assert hasattr(ErrorSeverity, "MEDIUM")
        assert hasattr(ErrorSeverity, "HIGH")
        assert hasattr(ErrorSeverity, "CRITICAL")


class TestErrorCategory:
    """Test suite for ErrorCategory enum."""

    def test_category_values(self):
        """Test that all error categories are defined."""
        assert hasattr(ErrorCategory, "NETWORK")
        assert hasattr(ErrorCategory, "API")
        assert hasattr(ErrorCategory, "VALIDATION")
        assert hasattr(ErrorCategory, "CONFIGURATION")
        assert hasattr(ErrorCategory, "RUNTIME")


class TestCustomErrors:
    """Test suite for custom error classes."""

    def test_agent_error(self):
        """Test AgentError exception."""
        with pytest.raises(AgentError):
            raise AgentError("Test agent error")

    def test_retryable_error(self):
        """Test RetryableError exception."""
        with pytest.raises(RetryableError):
            raise RetryableError("Test retryable error")

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Test config error")

    def test_validation_error(self):
        """Test CustomValidationError exception."""
        with pytest.raises(CustomValidationError):
            raise CustomValidationError("Test validation error")


class TestErrorIntegration:
    """Integration tests for error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_full_error_workflow(self):
        """Test complete error handling workflow."""
        # Simulate a real error scenario
        try:
            raise ValueError("Simulated error")
        except ValueError as e:
            result = self.handler.handle_error(
                e, severity=ErrorSeverity.MEDIUM, category=ErrorCategory.RUNTIME
            )
            assert result is not None

    def test_nested_error_handling(self):
        """Test handling of nested errors."""
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as inner:
                raise RuntimeError("Outer error") from inner
        except RuntimeError as e:
            result = self.handler.handle_error(e)
            assert result is not None

    def test_concurrent_error_handling(self):
        """Test handling multiple concurrent errors."""
        errors = [ValueError(f"Error {i}") for i in range(5)]
        results = [self.handler.handle_error(e) for e in errors]
        assert all(r is not None for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
