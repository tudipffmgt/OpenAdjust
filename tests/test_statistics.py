"""
Tests for statistical functions.
"""
import pytest
from openadjust.core.statistics import global_model_test, compute_sigma_0


class TestStatistics:
    """Test cases for statistical functions."""

    def test_compute_sigma_0(self):
        """Test sigma_0 calculation."""
        vPv = 10.0
        redundancy = 10

        sigma_0 = compute_sigma_0(vPv, redundancy)
        assert sigma_0 == pytest.approx(1.0)

    def test_global_model_test_pass(self):
        """Test global model test - should pass."""
        vPv = 10.0  # Exactly at expected value
        redundancy = 10

        passed, stat, lower, upper = global_model_test(vPv, redundancy)
        # Mit == statt is, damit NumPy-Booleans korrekt verglichen werden
        assert passed == True  # oder einfach: assert passed
