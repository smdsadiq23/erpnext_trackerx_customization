# -*- coding: utf-8 -*-
"""
AQL Validation Utilities

Validation functions for AQL-related data and operations.
"""

from __future__ import unicode_literals
import frappe
from .constants import (
    STANDARD_AQL_VALUES, 
    GENERAL_INSPECTION_LEVELS, 
    SPECIAL_INSPECTION_LEVELS,
    INSPECTION_REGIMES,
    SAMPLE_SIZE_MAPPING
)


def validate_aql_value(aql_value):
    """
    Validate that AQL value is within industry standards
    
    Args:
        aql_value (str): AQL value to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If AQL value is invalid
    """
    if aql_value not in STANDARD_AQL_VALUES:
        frappe.throw(f"AQL value '{aql_value}' is not a standard value. "
                    f"Valid values are: {', '.join(STANDARD_AQL_VALUES)}")
    return True


def validate_inspection_level(level_code, level_type):
    """
    Validate inspection level code matches its type
    
    Args:
        level_code (str): Level code (1, 2, 3, S1, S2, S3, S4)
        level_type (str): Level type (General or Special)
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If level code/type combination is invalid
    """
    if level_type == "General":
        if level_code not in GENERAL_INSPECTION_LEVELS:
            frappe.throw(f"For General inspection, level code must be one of: "
                        f"{', '.join(GENERAL_INSPECTION_LEVELS)}")
    
    elif level_type == "Special":
        if level_code not in SPECIAL_INSPECTION_LEVELS:
            frappe.throw(f"For Special inspection, level code must be one of: "
                        f"{', '.join(SPECIAL_INSPECTION_LEVELS)}")
    
    else:
        frappe.throw(f"Level type must be either 'General' or 'Special', got '{level_type}'")
    
    return True


def validate_inspection_regime(regime):
    """
    Validate inspection regime
    
    Args:
        regime (str): Inspection regime
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If regime is invalid
    """
    if regime not in INSPECTION_REGIMES:
        frappe.throw(f"Inspection regime must be one of: {', '.join(INSPECTION_REGIMES)}")
    return True


def validate_sample_code_letter(code_letter):
    """
    Validate sample code letter
    
    Args:
        code_letter (str): Sample code letter
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If code letter is invalid
    """
    if code_letter not in SAMPLE_SIZE_MAPPING:
        valid_codes = ', '.join(sorted(SAMPLE_SIZE_MAPPING.keys()))
        frappe.throw(f"Sample code letter '{code_letter}' is invalid. "
                    f"Valid codes are: {valid_codes}")
    return True


def validate_acceptance_rejection_numbers(acceptance_number, rejection_number):
    """
    Validate acceptance and rejection numbers relationship
    
    Args:
        acceptance_number (int): Maximum acceptable defects
        rejection_number (int): Minimum defects for rejection
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If numbers are invalid
    """
    if not isinstance(acceptance_number, int) or acceptance_number < 0:
        frappe.throw("Acceptance number must be a non-negative integer")
    
    if not isinstance(rejection_number, int) or rejection_number < 1:
        frappe.throw("Rejection number must be a positive integer")
    
    if rejection_number <= acceptance_number:
        frappe.throw("Rejection number must be greater than acceptance number")
    
    return True


def validate_sample_size(sample_size, code_letter):
    """
    Validate sample size matches code letter
    
    Args:
        sample_size (int): Sample size
        code_letter (str): Sample code letter
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If sample size doesn't match code
    """
    expected_size = SAMPLE_SIZE_MAPPING.get(code_letter)
    
    if expected_size and sample_size != expected_size:
        frappe.throw(f"Sample size for code letter '{code_letter}' should be {expected_size}, "
                    f"got {sample_size}")
    
    return True


def validate_defects_count(defects_found, sample_size):
    """
    Validate defects count is reasonable for sample size
    
    Args:
        defects_found (int): Number of defects found
        sample_size (int): Total sample size
        
    Returns:
        bool: True if valid
        
    Raises:
        frappe.ValidationError: If defects count is invalid
    """
    if not isinstance(defects_found, int) or defects_found < 0:
        frappe.throw("Defects found must be a non-negative integer")
    
    if defects_found > sample_size:
        frappe.throw(f"Defects found ({defects_found}) cannot be greater than "
                    f"sample size ({sample_size})")
    
    return True