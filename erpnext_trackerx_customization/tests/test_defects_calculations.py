#!/usr/bin/env python3
"""
Isolated Tests for Trims Inspection Calculation Functions
Tests only the calculation logic without creating documents
"""

import frappe
import json
from erpnext_trackerx_customization.api.trims_inspection import (
    clean_defects_data, clean_count_value, determine_inspection_result, 
    get_defect_severity, get_quality_grade
)


def test_defects_data_cleaning():
    """Test the defects data cleaning function"""
    print("\n=== TESTING DEFECTS DATA CLEANING ===")
    
    # Test malformed data
    dirty_data = {
        "001": {
            "critical_BROKEN": "5abc",      # Should become 5
            "major_SCRATCH": 3,             # Should remain 3
            "minor_STAIN": "0",             # Should be removed (zero)
            "invalid_KEY": "",              # Should be removed (empty)
            "another_DEFECT": None,         # Should be removed (null)
            "good_DEFECT": "10"             # Should become 10
        },
        "002": {
            "critical_BROKEN": "abc123def", # Should become 123
            "major_SCRATCH": "7xyz",        # Should become 7
            "empty_ITEM": 0                 # Should be removed
        },
        "003": {
            # Empty item - should be removed entirely
        }
    }
    
    cleaned = clean_defects_data(dirty_data)
    
    print("Before cleaning:", json.dumps(dirty_data, indent=2))
    print("After cleaning:", json.dumps(cleaned, indent=2))
    
    # Test assertions
    assert cleaned["001"]["critical_BROKEN"] == 5, "Should extract 5 from '5abc'"
    assert cleaned["001"]["major_SCRATCH"] == 3, "Should preserve clean integer"
    assert "minor_STAIN" not in cleaned["001"], "Should remove zero values"
    assert "invalid_KEY" not in cleaned["001"], "Should remove empty values"
    assert cleaned["001"]["good_DEFECT"] == 10, "Should convert string number"
    
    assert cleaned["002"]["critical_BROKEN"] == 123, "Should extract 123 from 'abc123def'"
    assert cleaned["002"]["major_SCRATCH"] == 7, "Should extract 7 from '7xyz'"
    assert "empty_ITEM" not in cleaned["002"], "Should remove zero values"
    
    assert "003" not in cleaned, "Should remove empty items"
    
    print("✅ Defects data cleaning test PASSED")


def test_count_value_cleaning():
    """Test individual count value cleaning"""
    print("\n=== TESTING COUNT VALUE CLEANING ===")
    
    test_cases = [
        # (input, expected_output)
        ("5abc", 5),           # Extract number from beginning
        ("abc5def", 5),        # Will extract any number (current behavior)
        ("123def", 123),       # Multiple digits
        ("", 0),               # Empty string
        (None, 0),             # None value
        (0, 0),                # Integer zero
        (15, 15),              # Clean integer
        ("0", 0),              # String zero
        ("   ", 0),            # Whitespace
        ("abc", 0),            # No numbers
        (-5, 0),               # Negative (should become 0)
        (5.7, 5),              # Float (should become int)
    ]
    
    for input_val, expected in test_cases:
        result = clean_count_value(input_val)
        print(f"   {repr(input_val):15} → {result:3} (expected: {expected})")
        assert result == expected, f"Failed for {repr(input_val)}: got {result}, expected {expected}"
    
    print("✅ Count value cleaning test PASSED")


def test_defect_severity_determination():
    """Test defect severity classification"""
    print("\n=== TESTING DEFECT SEVERITY DETERMINATION ===")
    
    test_cases = [
        # (defect_code, expected_severity)
        ("BROKEN", "Critical"),
        ("broken", "Critical"),     # Case insensitive
        ("WRONG_COLOR", "Critical"),
        ("MISSING", "Critical"),
        ("CONTAMINATION", "Critical"),
        
        ("SCRATCH", "Major"),
        ("scratch", "Major"),       # Case insensitive
        ("DENT", "Major"),
        ("DISCOLORATION", "Major"),
        ("ASSEMBLY_ERROR", "Major"),
        
        ("TINY_SPOT", "Minor"),     # Doesn't match critical/major patterns
        ("SMALL_SPOT", "Minor"),
        ("UNKNOWN_DEFECT", "Minor"), # Default to minor
        ("", "Minor"),              # Empty string
    ]
    
    for defect_code, expected in test_cases:
        result = get_defect_severity(defect_code)
        print(f"   {defect_code:15} → {result:8} (expected: {expected})")
        assert result == expected, f"Failed for '{defect_code}': got {result}, expected {expected}"
    
    print("✅ Defect severity determination test PASSED")


def test_inspection_result_logic():
    """Test inspection result determination logic"""
    print("\n=== TESTING INSPECTION RESULT LOGIC ===")
    
    test_cases = [
        # (critical, major, minor, has_mandatory_failures, expected_result)
        (0, 0, 0, False, "Accepted"),           # Perfect quality
        (1, 0, 0, False, "Rejected"),           # Any critical = reject
        (0, 0, 0, True, "Rejected"),            # Mandatory failure = reject
        (0, 6, 0, False, "Conditional Accept"), # Too many major defects
        (0, 0, 11, False, "Conditional Accept"), # Too many minor defects
        (0, 5, 10, False, "Accepted"),           # At thresholds (not over)
        (0, 4, 9, False, "Accepted"),           # Under thresholds
        (0, 2, 5, False, "Accepted"),           # Low defect counts
        (5, 10, 20, True, "Rejected"),          # Multiple issues - critical wins
    ]
    
    for critical, major, minor, has_failures, expected in test_cases:
        # Create mock checklist data
        checklist_data = []
        if has_failures:
            checklist_data = [{
                "is_mandatory": True,
                "results": {"status": "Fail"}
            }]
        
        result = determine_inspection_result(critical, major, minor, checklist_data)
        
        print(f"   C:{critical:2} M:{major:2} m:{minor:2} Fail:{str(has_failures):5} → {result:18} (expected: {expected})")
        assert result == expected, f"Failed for C:{critical} M:{major} m:{minor} F:{has_failures} - got '{result}', expected '{expected}'"
    
    print("✅ Inspection result logic test PASSED")


def test_quality_grade_logic():
    """Test quality grade determination"""
    print("\n=== TESTING QUALITY GRADE LOGIC ===")
    
    test_cases = [
        # (critical, major, minor, expected_grade)
        (0, 0, 0, "A - Excellent"),        # Perfect
        (0, 1, 2, "A - Excellent"),        # Very low defects
        (0, 2, 5, "A - Excellent"),        # At threshold for excellent
        (0, 3, 6, "B - Good"),             # Over excellent threshold
        (0, 5, 10, "B - Good"),            # At good threshold
        (0, 6, 11, "C - Conditional"),     # Over good threshold
        (1, 0, 0, "F - Rejected"),         # Any critical defects
        (2, 10, 20, "F - Rejected"),       # Multiple critical defects
        (0, 10, 5, "C - Conditional"),     # Many major defects
        (0, 2, 15, "C - Conditional"),     # Many minor defects
    ]
    
    for critical, major, minor, expected in test_cases:
        result = get_quality_grade(critical, major, minor)
        print(f"   C:{critical:2} M:{major:2} m:{minor:2} → {result:15} (expected: {expected})")
        assert result == expected, f"Failed for C:{critical} M:{major} m:{minor} - got '{result}', expected '{expected}'"
    
    print("✅ Quality grade logic test PASSED")


def test_complex_defects_scenario():
    """Test a complex real-world defects scenario"""
    print("\n=== TESTING COMPLEX DEFECTS SCENARIO ===")
    
    # Simulate complex trims inspection data with multiple items and defect types
    complex_data = {
        "BATCH_001": {
            "critical_BROKEN": "3dirty",        # 3 critical
            "major_SCRATCH": 5,                 # 5 major
            "minor_STAIN": "2abc",              # 2 minor
            "empty_defect": "",                 # Should be ignored
        },
        "BATCH_002": {
            "critical_MISSING": 2,              # 2 critical
            "major_DENT": "4xyz",               # 4 major
            "minor_MARK": 8,                    # 8 minor
            "zero_defect": 0,                   # Should be ignored
        },
        "BATCH_003": {
            "minor_SPOT": 1,                    # 1 minor only
        }
    }
    
    cleaned = clean_defects_data(complex_data)
    
    # Calculate totals manually to verify
    total_critical = 0
    total_major = 0
    total_minor = 0
    
    for item_number, item_defects in cleaned.items():
        for defect_key, count in item_defects.items():
            severity = "Minor"  # Default
            if defect_key.startswith("critical_"):
                severity = "Critical"
            elif defect_key.startswith("major_"):
                severity = "Major"
            elif defect_key.startswith("minor_"):
                severity = "Minor"
            
            if severity == "Critical":
                total_critical += count
            elif severity == "Major":
                total_major += count
            else:
                total_minor += count
    
    print(f"   Complex scenario totals:")
    print(f"   Critical: {total_critical} (expected: 5)")
    print(f"   Major: {total_major} (expected: 9)")
    print(f"   Minor: {total_minor} (expected: 11)")
    
    assert total_critical == 5, f"Expected 5 critical, got {total_critical}"
    assert total_major == 9, f"Expected 9 major, got {total_major}"
    assert total_minor == 11, f"Expected 11 minor, got {total_minor}"
    
    # Test the final result
    result = determine_inspection_result(total_critical, total_major, total_minor, [])
    expected_result = "Rejected"  # Due to critical defects
    assert result == expected_result, f"Expected {expected_result}, got {result}"
    
    print(f"   Final result: {result} ✓")
    print("✅ Complex defects scenario test PASSED")


def run_calculation_tests():
    """Run all calculation tests"""
    print("=" * 70)
    print("RUNNING TRIMS INSPECTION CALCULATION TESTS")
    print("=" * 70)
    
    try:
        test_defects_data_cleaning()
        test_count_value_cleaning()
        test_defect_severity_determination()
        test_inspection_result_logic()
        test_quality_grade_logic()
        test_complex_defects_scenario()
        
        print("\n" + "=" * 70)
        print("🎉 ALL CALCULATION TESTS PASSED!")
        print("   ✅ Defects data cleaning works correctly")
        print("   ✅ Count value cleaning handles malformed data")
        print("   ✅ Defect severity classification is accurate")
        print("   ✅ Inspection result logic follows business rules")
        print("   ✅ Quality grade determination is correct")
        print("   ✅ Complex scenarios are handled properly")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ CALCULATION TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Setup Frappe environment
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    # Run tests
    success = run_calculation_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)