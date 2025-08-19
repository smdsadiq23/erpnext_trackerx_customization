#!/usr/bin/env python3
"""
Test Runner for Trims Inspection Test Suite
Provides easy way to run individual tests or complete test suite
"""

import frappe
import sys


def run_individual_test(test_name):
    """Run a specific test by name"""
    test_functions = {
        "defects": "erpnext_trackerx_customization.tests.test_defects_calculations.run_calculation_tests",
        "status": "erpnext_trackerx_customization.tests.test_status_transitions.run_status_transition_tests", 
        "grn": "erpnext_trackerx_customization.tests.test_grn_workflow.run_grn_to_pr_tests",
        "e2e": "erpnext_trackerx_customization.tests.test_e2e_complete.run_complete_e2e_test",
        "setup": "erpnext_trackerx_customization.tests.setup_test_data.create_all_dummy_data"
    }
    
    if test_name not in test_functions:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_functions.keys())}")
        return False
    
    try:
        # Import and run the test function
        module_path, function_name = test_functions[test_name].rsplit('.', 1)
        module = frappe.get_module(module_path)
        test_function = getattr(module, function_name)
        return test_function()
    except Exception as e:
        print(f"❌ Test {test_name} failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests in sequence"""
    print("=" * 80)
    print("RUNNING ALL TRIMS INSPECTION TESTS")
    print("=" * 80)
    
    tests = [
        ("setup", "Test Data Setup"),
        ("defects", "Defects Calculations"),
        ("status", "Status Transitions"),
        ("grn", "GRN Workflow"),
        ("e2e", "Complete E2E Test")
    ]
    
    results = {}
    
    for test_key, test_name in tests:
        print(f"\n🔄 Running: {test_name}")
        print("-" * 50)
        
        try:
            result = run_individual_test(test_key)
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"Result: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ FAILED: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 ALL TESTS SUMMARY")
    print("=" * 80)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nPASSED: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    return passed == total


def show_help():
    """Show help information"""
    print("Trims Inspection Test Runner")
    print("=" * 40)
    print("\nUsage:")
    print("  bench execute erpnext_trackerx_customization.tests.test_runner.run_all_tests")
    print("  bench execute erpnext_trackerx_customization.tests.test_runner.run_individual_test --args \"['test_name']\"")
    print("\nAvailable individual tests:")
    print("  • setup   - Create test data")
    print("  • defects - Test defects calculations") 
    print("  • status  - Test status transitions")
    print("  • grn     - Test GRN workflow")
    print("  • e2e     - Complete end-to-end test")
    print("\nExamples:")
    print("  bench execute erpnext_trackerx_customization.tests.test_runner.run_individual_test --args \"['defects']\"")
    print("  bench execute erpnext_trackerx_customization.tests.test_runner.run_individual_test --args \"['e2e']\"")


if __name__ == "__main__":
    # Setup Frappe environment
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            show_help()
        else:
            test_name = sys.argv[1]
            success = run_individual_test(test_name)
            exit(0 if success else 1)
    else:
        success = run_all_tests()
        exit(0 if success else 1)