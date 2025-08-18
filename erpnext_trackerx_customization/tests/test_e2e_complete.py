#!/usr/bin/env python3
"""
Complete End-to-End Test for Trims Inspection Workflow
Combines GRN creation, inspection workflow, and purchase receipt verification
"""

import frappe
from frappe.utils import today, add_days
from .setup_test_data import create_all_dummy_data
from .create_test_grn import run_grn_workflow_test
from .test_defects_calculations import run_calculation_tests
from .test_status_transitions import run_status_transition_tests
from .test_grn_workflow import run_grn_to_pr_tests


def run_complete_e2e_test():
    """Run the complete end-to-end test suite"""
    print("=" * 90)
    print("RUNNING COMPLETE END-TO-END TRIMS INSPECTION WORKFLOW TEST")
    print("=" * 90)
    
    test_results = {
        "setup_data": False,
        "defects_calculations": False,
        "status_transitions": False,
        "grn_workflow": False,
        "real_grn_creation": False
    }
    
    try:
        # Step 1: Setup test data
        print("\n🔧 STEP 1: SETTING UP TEST DATA")
        print("-" * 50)
        test_results["setup_data"] = create_all_dummy_data()
        
        if not test_results["setup_data"]:
            print("❌ Test data setup failed - aborting E2E test")
            return False
        
        # Step 2: Test defects calculations
        print("\n🧮 STEP 2: TESTING DEFECTS CALCULATIONS")
        print("-" * 50)
        test_results["defects_calculations"] = run_calculation_tests()
        
        # Step 3: Test status transitions
        print("\n🔄 STEP 3: TESTING STATUS TRANSITIONS")
        print("-" * 50)
        test_results["status_transitions"] = run_status_transition_tests()
        
        # Step 4: Test GRN workflow logic
        print("\n📦 STEP 4: TESTING GRN WORKFLOW LOGIC")
        print("-" * 50)
        test_results["grn_workflow"] = run_grn_to_pr_tests()
        
        # Step 5: Test real GRN creation and workflow
        print("\n🏭 STEP 5: TESTING REAL GRN CREATION")
        print("-" * 50)
        grn_result = run_grn_workflow_test()
        test_results["real_grn_creation"] = bool(grn_result)
        
        # Summary
        print("\n" + "=" * 90)
        print("🎉 COMPLETE E2E TEST SUMMARY")
        print("=" * 90)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n📊 TEST RESULTS: {passed_tests}/{total_tests} PASSED")
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   • {test_name.replace('_', ' ').title()}: {status}")
        
        if passed_tests == total_tests:
            print(f"\n🎯 ALL TESTS PASSED! Trims Inspection E2E workflow is fully functional.")
            
            print(f"\n✅ VERIFIED CAPABILITIES:")
            print(f"   • Defects calculation with cross-contamination prevention")
            print(f"   • All 7 status transitions working correctly")
            print(f"   • GRN workflow properly separating inspection/non-inspection items")
            print(f"   • Real GRN creation with mixed items")
            print(f"   • Purchase Receipt creation for non-inspection items")
            print(f"   • Inspection document creation for inspection items")
            
            print(f"\n🔄 CONFIRMED WORKFLOW:")
            print(f"   GRN → [Inspection Items → Inspections] + [Non-Inspection Items → PRs]")
            
            print("=" * 90)
            return True
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check logs above for details.")
            return False
        
    except Exception as e:
        print(f"\n❌ E2E TEST FAILED WITH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Setup Frappe environment
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    # Run complete E2E test
    success = run_complete_e2e_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)