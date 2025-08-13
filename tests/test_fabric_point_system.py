#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Fabric Defect Point System

Tests the enhanced point calculation system for fabric defects with actual measurements.

Usage:
    bench execute erpnext_trackerx_customization.test_fabric_point_system.test_point_calculations
"""

import frappe

def test_point_calculations():
    """Test the fabric defect point calculation system"""
    
    print("🧪 TESTING FABRIC DEFECT POINT CALCULATION SYSTEM")
    print("=" * 60)
    
    # Test cases with different defect types and measurements
    test_cases = [
        {
            "defect_code": "YD001",  # Thick Yarn
            "defect_name": "Thick Yarn",
            "test_measurements": [
                {"measurement": "2.5", "expected_points": 1, "description": "2.5 inches (≤ 3\")"},
                {"measurement": "4.2", "expected_points": 2, "description": "4.2 inches (3\" to 6\")"},
                {"measurement": "7.8", "expected_points": 3, "description": "7.8 inches (6\" to 9\")"},
                {"measurement": "12", "expected_points": 4, "description": "12 inches (> 9\")"},
                {"measurement": "3", "expected_points": 1, "description": "3 inches (boundary case ≤ 3\")"},
                {"measurement": "6", "expected_points": 2, "description": "6 inches (boundary case 3\" to 6\")"},
                {"measurement": "9", "expected_points": 3, "description": "9 inches (boundary case 6\" to 9\")"}
            ]
        },
        {
            "defect_code": "YD004",  # Nep/Foreign Fiber  
            "defect_name": "Nep/Foreign Fiber",
            "test_measurements": [
                {"measurement": "0.2", "expected_points": 1, "description": "0.2 inches (≤ 1/4\" = 0.25)"},
                {"measurement": "0.375", "expected_points": 2, "description": "0.375 inches (1/4\" to 1/2\")"},
                {"measurement": "0.75", "expected_points": 3, "description": "0.75 inches (1/2\" to 1\")"},
                {"measurement": "1.5", "expected_points": 4, "description": "1.5 inches (> 1\")"},
                {"measurement": "1/4", "expected_points": 1, "description": "1/4 inch (boundary case ≤ 1/4\")"},
                {"measurement": "1/2", "expected_points": 2, "description": "1/2 inch (boundary case 1/4\" to 1/2\")"}
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in test_cases:
        defect_code = test_case["defect_code"]
        defect_name = test_case["defect_name"]
        
        print(f"\n🔍 Testing Defect: {defect_code} - {defect_name}")
        print("-" * 50)
        
        try:
            # Get the defect master record
            defect_doc = frappe.get_doc("Defect Master", defect_code)
            
            print(f"   Criteria:")
            print(f"   • 1 Point: {defect_doc.point_1_criteria}")
            print(f"   • 2 Points: {defect_doc.point_2_criteria}")
            print(f"   • 3 Points: {defect_doc.point_3_criteria}")
            print(f"   • 4 Points: {defect_doc.point_4_criteria}")
            print()
            
            for test_measurement in test_case["test_measurements"]:
                measurement = test_measurement["measurement"]
                expected_points = test_measurement["expected_points"]
                description = test_measurement["description"]
                
                # Calculate actual points
                actual_points = defect_doc.get_point_value(measurement)
                
                # Test result
                total_tests += 1
                if actual_points == expected_points:
                    passed_tests += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                print(f"   {status} | {description}")
                print(f"          Expected: {expected_points} points, Got: {actual_points} points")
                
        except Exception as e:
            print(f"   ❌ ERROR: Could not test {defect_code} - {str(e)}")
    
    print(f"\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    # Test different input formats
    print(f"\n🧪 TESTING INPUT FORMAT PARSING")
    print("-" * 40)
    
    try:
        defect_doc = frappe.get_doc("Defect Master", "YD001")
        
        format_tests = [
            {"input": "2.5", "description": "Decimal string"},
            {"input": 3.7, "description": "Float number"},
            {"input": "4 inches", "description": "With unit"},
            {"input": "1/4", "description": "Fraction"},
            {"input": "2 1/2", "description": "Mixed number"},
            {"input": "3.5\"", "description": "With quotes"},
            {"input": "5 in", "description": "With 'in' unit"}
        ]
        
        for test in format_tests:
            try:
                points = defect_doc.get_point_value(test["input"])
                print(f"   ✅ {test['description']}: '{test['input']}' → {points} points")
            except Exception as e:
                print(f"   ❌ {test['description']}: '{test['input']}' → Error: {str(e)}")
                
    except Exception as e:
        print(f"   ❌ Could not test input formats: {str(e)}")
    
    return passed_tests == total_tests

def demo_point_calculation():
    """Demonstrate point calculation for different scenarios"""
    
    print(f"\n🎯 FABRIC DEFECT POINT CALCULATION DEMO")
    print("=" * 50)
    
    scenarios = [
        {
            "scenario": "Quality Inspector finds a Thick Yarn defect",
            "defect_code": "YD001",
            "measurements": ["2.1", "4.5", "7.0", "10.2"]
        },
        {
            "scenario": "Quality Inspector finds Foreign Fiber contamination",
            "defect_code": "YD004", 
            "measurements": ["0.2", "0.3", "0.8", "1.2"]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['scenario']}")
        print(f"   Defect Code: {scenario['defect_code']}")
        print("   Measurements and Points:")
        
        try:
            defect_doc = frappe.get_doc("Defect Master", scenario["defect_code"])
            
            for measurement in scenario["measurements"]:
                points = defect_doc.get_point_value(measurement)
                print(f"   • {measurement}\" defect = {points} points")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def create_point_calculation_report():
    """Create a comprehensive report of all fabric defects and their point systems"""
    
    print(f"\n📄 FABRIC DEFECT POINT SYSTEM REPORT")
    print("=" * 70)
    
    try:
        # Get all fabric defects
        fabric_defects = frappe.get_all(
            "Defect Master",
            fields=["defect_code", "defect_name", "point_1_criteria", "point_2_criteria", 
                   "point_3_criteria", "point_4_criteria"],
            filters={
                "inspection_type": "Fabric Inspection",
                "is_active": 1
            },
            order_by="defect_code"
        )
        
        print(f"Found {len(fabric_defects)} active fabric defects with point systems:")
        print()
        
        for defect in fabric_defects:
            print(f"🔸 {defect.defect_code} - {defect.defect_name}")
            print(f"   1 Point:  {defect.point_1_criteria or 'Not defined'}")
            print(f"   2 Points: {defect.point_2_criteria or 'Not defined'}")
            print(f"   3 Points: {defect.point_3_criteria or 'Not defined'}")
            print(f"   4 Points: {defect.point_4_criteria or 'Not defined'}")
            print()
            
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")

def main():
    """Run all tests and demonstrations"""
    
    print("🎯 COMPREHENSIVE FABRIC DEFECT POINT SYSTEM TESTING")
    print("=" * 70)
    
    # Run point calculation tests
    test_success = test_point_calculations()
    
    # Run demonstration
    demo_point_calculation()
    
    # Generate report
    create_point_calculation_report()
    
    print(f"\n🎉 TESTING COMPLETE!")
    if test_success:
        print("✅ All tests passed - Point calculation system is working correctly!")
    else:
        print("❌ Some tests failed - Please review the implementation")
    
    return test_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)