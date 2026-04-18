"""
Statistical tests for adjustment quality assessment.
"""

import numpy as np
from scipy import stats
from typing import Optional


def global_model_test(vPv: float, redundancy: int, 
                      sigma_0_apriori: float = 1.0,
                      significance_level: float = 0.05) -> tuple[bool, float, float, float]:
    """
    Performs the global model test (Chi-square test).
    
    Tests H0: sigma_0 = sigma_0_apriori against H1: sigma_0 != sigma_0_apriori
    
    Args:
        vPv: Weighted sum of squared residuals (v^T * P * v)
        redundancy: Degrees of freedom (n - u)
        sigma_0_apriori: A priori standard deviation of unit weight
        significance_level: Significance level (typically 0.05)
    
    Returns:
        Tuple of (test_passed, test_statistic, lower_bound, upper_bound)
    """
    if redundancy <= 0:
        return False, 0.0, 0.0, 0.0
    
    # Test statistic
    test_statistic = vPv / (sigma_0_apriori ** 2)
    
    # Critical values (two-sided test)
    alpha = significance_level
    lower_bound = stats.chi2.ppf(alpha / 2, redundancy)
    upper_bound = stats.chi2.ppf(1 - alpha / 2, redundancy)
    
    # Test decision
    test_passed = lower_bound <= test_statistic <= upper_bound
    
    return test_passed, test_statistic, lower_bound, upper_bound


def compute_sigma_0(vPv: float, redundancy: int) -> float:
    """
    Computes the a posteriori standard deviation of unit weight.
    
    Args:
        vPv: Weighted sum of squared residuals
        redundancy: Degrees of freedom
    
    Returns:
        sigma_0 (a posteriori)
    """
    if redundancy <= 0:
        return 0.0
    
    return np.sqrt(vPv / redundancy)


def normalized_residual(residual: float, sigma_0: float, 
                        qvv: float) -> float:
    """
    Computes the normalized residual for outlier detection.
    
    Args:
        residual: The residual v
        sigma_0: A posteriori standard deviation of unit weight
        qvv: Cofactor of the residual (diagonal element of Qvv)
    
    Returns:
        Normalized residual w = v / (sigma_0 * sqrt(qvv))
    """
    if qvv <= 0 or sigma_0 <= 0:
        return 0.0
    
    return residual / (sigma_0 * np.sqrt(qvv))
