#!/usr/bin/env python3
"""
Status Transitions Test for Trims Inspection
Focus on testing all status transitions without complex document creation
"""

import frappe
import json
from erpnext_trackerx_customization.api.trims_inspection import (
    is_valid_trims_status_transition, determine_inspection_result
)


def test_status_transition_matrix():
    """Test complete status transition matrix"""
    print("\n=== TESTING STATUS TRANSITION MATRIX ===")
    
    # Define all valid transitions
    valid_transitions = {
        'Draft': ['In Progress', 'Hold'],
        'In Progress': ['Hold', 'Submitted'],
        'Hold': ['In Progress', 'Submitted'],
        'Submitted': ['Accepted', 'Rejected', 'Conditional Accept'],
        'Accepted': [],      # Terminal status
        'Rejected': [],      # Terminal status  
        'Conditional Accept': []  # Terminal status
    }
    
    print("VALID TRANSITIONS:")
    total_valid = 0
    # Test all valid transitions
    for current_status, allowed_next_statuses in valid_transitions.items():
        for next_status in allowed_next_statuses:
            result = is_valid_trims_status_transition(current_status, next_status)
            assert result == True, f"Should allow {current_status} → {next_status}"
            print(f"   ✓ {current_status:18} → {next_status}")
            total_valid += 1
    
    print(f"\nINVALID TRANSITIONS (should be blocked):")
    total_invalid = 0
    # Test all possible invalid transitions
    all_statuses = ['Draft', 'In Progress', 'Hold', 'Submitted', 'Accepted', 'Rejected', 'Conditional Accept']
    
    for current_status in all_statuses:
        for next_status in all_statuses:
            if current_status == next_status:
                continue  # Skip self-transitions
            
            is_valid_transition = next_status in valid_transitions.get(current_status, [])
            if not is_valid_transition:
                result = is_valid_trims_status_transition(current_status, next_status)
                assert result == False, f"Should NOT allow {current_status} → {next_status}"
                print(f"   ✗ {current_status:18} ✗ {next_status} (correctly blocked)")
                total_invalid += 1
    
    print(f"\n   Total valid transitions: {total_valid}")
    print(f"   Total invalid transitions blocked: {total_invalid}")
    print("✅ Status transition matrix validation passed")


def test_inspection_result_scenarios():
    """Test all inspection result determination scenarios"""
    print("\n=== TESTING INSPECTION RESULT SCENARIOS ===")
    
    scenarios = [
        # Perfect quality
        {
            "name": "Perfect Quality",
            "critical": 0, "major": 0, "minor": 0,
            "mandatory_failures": False,
            "expected": "Accepted"
        },
        
        # Critical defects always reject
        {
            "name": "Critical Defects",
            "critical": 1, "major": 0, "minor": 0,
            "mandatory_failures": False,
            "expected": "Rejected"
        },
        {
            "name": "Multiple Critical Defects",
            "critical": 5, "major": 10, "minor": 20,
            "mandatory_failures": False,
            "expected": "Rejected"
        },
        
        # Mandatory checklist failures always reject
        {
            "name": "Mandatory Checklist Failure",
            "critical": 0, "major": 0, "minor": 0,
            "mandatory_failures": True,
            "expected": "Rejected"
        },
        {
            "name": "Good Quality + Mandatory Failure",
            "critical": 0, "major": 2, "minor": 3,
            "mandatory_failures": True,
            "expected": "Rejected"
        },
        
        # Too many major defects → Conditional Accept
        {
            "name": "Too Many Major Defects",
            "critical": 0, "major": 6, "minor": 0,
            "mandatory_failures": False,
            "expected": "Conditional Accept"
        },
        {
            "name": "At Major Threshold",
            "critical": 0, "major": 5, "minor": 0,
            "mandatory_failures": False,
            "expected": "Accepted"  # At threshold, not over
        },
        
        # Too many minor defects → Conditional Accept
        {
            "name": "Too Many Minor Defects",
            "critical": 0, "major": 0, "minor": 11,
            "mandatory_failures": False,
            "expected": "Conditional Accept"
        },
        {
            "name": "At Minor Threshold",
            "critical": 0, "major": 0, "minor": 10,
            "mandatory_failures": False,
            "expected": "Accepted"  # At threshold, not over
        },
        
        # Combined defects
        {
            "name": "Both Major and Minor Over Threshold",
            "critical": 0, "major": 8, "minor": 15,
            "mandatory_failures": False,
            "expected": "Conditional Accept"
        },
        {
            "name": "Under All Thresholds",
            "critical": 0, "major": 3, "minor": 7,
            "mandatory_failures": False,
            "expected": "Accepted"
        },
        
        # Edge cases
        {
            "name": "Exactly At Both Thresholds",
            "critical": 0, "major": 5, "minor": 10,
            "mandatory_failures": False,
            "expected": "Accepted"  # At thresholds, not over
        }
    ]
    
    for scenario in scenarios:
        print(f"   Testing: {scenario['name']}")
        
        # Create mock checklist data
        checklist_data = []
        if scenario['mandatory_failures']:
            checklist_data = [{
                "is_mandatory": True,
                "results": {"status": "Fail"}
            }]
        else:
            checklist_data = [{
                "is_mandatory": True,
                "results": {"status": "Pass"}
            }]
        
        result = determine_inspection_result(
            scenario['critical'], 
            scenario['major'], 
            scenario['minor'], 
            checklist_data
        )
        
        expected = scenario['expected']
        assert result == expected, f"Expected {expected}, got {result} for scenario: {scenario['name']}"
        
        print(f"     C:{scenario['critical']:2} M:{scenario['major']:2} m:{scenario['minor']:2} " + 
              f"Fail:{scenario['mandatory_failures']:5} → {result:18} ✓")
    
    print("✅ All inspection result scenarios passed")


def test_complete_workflow_paths():
    """Test complete workflow paths from Draft to final status"""
    print("\n=== TESTING COMPLETE WORKFLOW PATHS ===")
    
    # Define possible workflow paths
    workflow_paths = [
        {
            "name": "Draft → In Progress → Submitted → Accepted",
            "path": ["Draft", "In Progress", "Submitted", "Accepted"],
            "description": "Normal workflow with good quality"
        },
        {
            "name": "Draft → In Progress → Submitted → Rejected", 
            "path": ["Draft", "In Progress", "Submitted", "Rejected"],
            "description": "Normal workflow with poor quality"
        },
        {
            "name": "Draft → In Progress → Submitted → Conditional Accept",
            "path": ["Draft", "In Progress", "Submitted", "Conditional Accept"],
            "description": "Normal workflow with moderate quality"
        },
        {
            "name": "Draft → Hold → In Progress → Submitted → Accepted",
            "path": ["Draft", "Hold", "In Progress", "Submitted", "Accepted"],
            "description": "Workflow with hold for clarification"
        },
        {
            "name": "Draft → In Progress → Hold → Submitted → Rejected",
            "path": ["Draft", "In Progress", "Hold", "Submitted", "Rejected"],
            "description": "Workflow with hold during inspection"
        },
        {
            "name": "Draft → Hold → Submitted → Conditional Accept",
            "path": ["Draft", "Hold", "Submitted", "Conditional Accept"],
            "description": "Direct submission from hold"
        }
    ]
    
    for workflow in workflow_paths:
        print(f"   Testing path: {workflow['name']}")
        path = workflow['path']
        
        # Test each transition in the path
        for i in range(len(path) - 1):
            current_status = path[i]
            next_status = path[i + 1]
            
            is_valid = is_valid_trims_status_transition(current_status, next_status)
            assert is_valid, f"Invalid transition in path: {current_status} → {next_status}"
        
        # Create visual path representation
        path_visual = " → ".join(path)
        print(f"     {path_visual} ✓")
    
    print("✅ All workflow paths validated")


def test_terminal_status_behavior():
    """Test that terminal statuses cannot transition"""
    print("\n=== TESTING TERMINAL STATUS BEHAVIOR ===")
    
    terminal_statuses = ['Accepted', 'Rejected', 'Conditional Accept']
    all_statuses = ['Draft', 'In Progress', 'Hold', 'Submitted', 'Accepted', 'Rejected', 'Conditional Accept']
    
    for terminal_status in terminal_statuses:
        print(f"   Testing terminal status: {terminal_status}")
        
        # Test that terminal status cannot transition to any other status
        for target_status in all_statuses:
            if target_status == terminal_status:
                continue  # Skip self-transition
            
            is_valid = is_valid_trims_status_transition(terminal_status, target_status)
            assert is_valid == False, f"Terminal status {terminal_status} should not transition to {target_status}"
        
        print(f"     ✓ {terminal_status} correctly blocks all outgoing transitions")
    
    print("✅ Terminal status behavior validated")


def test_business_rules_compliance():
    """Test compliance with business rules"""
    print("\n=== TESTING BUSINESS RULES COMPLIANCE ===")
    
    print("   Rule 1: Critical defects always cause rejection")
    for critical_count in [1, 5, 10]:
        result = determine_inspection_result(critical_count, 0, 0, [])
        assert result == "Rejected", f"Critical defects should always reject"
        print(f"     ✓ {critical_count} critical defects → Rejected")
    
    print("   Rule 2: Mandatory checklist failures always cause rejection")
    checklist_fail = [{"is_mandatory": True, "results": {"status": "Fail"}}]
    result = determine_inspection_result(0, 0, 0, checklist_fail)
    assert result == "Rejected", f"Mandatory failures should always reject"
    print(f"     ✓ Mandatory checklist failure → Rejected")
    
    print("   Rule 3: Major defects > 5 cause conditional acceptance")
    result = determine_inspection_result(0, 6, 0, [])
    assert result == "Conditional Accept", f"Too many major defects should cause conditional accept"
    print(f"     ✓ 6 major defects → Conditional Accept")
    
    print("   Rule 4: Minor defects > 10 cause conditional acceptance")
    result = determine_inspection_result(0, 0, 11, [])
    assert result == "Conditional Accept", f"Too many minor defects should cause conditional accept"
    print(f"     ✓ 11 minor defects → Conditional Accept")
    
    print("   Rule 5: At threshold values are accepted")
    result = determine_inspection_result(0, 5, 10, [])
    assert result == "Accepted", f"At threshold should be accepted"
    print(f"     ✓ 5 major + 10 minor (at thresholds) → Accepted")
    
    print("   Rule 6: Low defect counts are accepted")
    result = determine_inspection_result(0, 2, 5, [])
    assert result == "Accepted", f"Low defects should be accepted"
    print(f"     ✓ 2 major + 5 minor → Accepted")
    
    print("✅ All business rules compliance validated")


def run_status_transition_tests():
    """Run all status transition tests"""
    print("=" * 80)
    print("RUNNING TRIMS INSPECTION STATUS TRANSITION TESTS")
    print("=" * 80)
    
    try:
        # Test 1: Complete status transition matrix
        test_status_transition_matrix()
        
        # Test 2: Inspection result scenarios
        test_inspection_result_scenarios()
        
        # Test 3: Complete workflow paths
        test_complete_workflow_paths()
        
        # Test 4: Terminal status behavior
        test_terminal_status_behavior()
        
        # Test 5: Business rules compliance
        test_business_rules_compliance()
        
        print("\n" + "=" * 80)
        print("🎉 ALL STATUS TRANSITION TESTS PASSED!")
        print("   ✅ Complete status transition matrix validated (7 statuses)")
        print("   ✅ All inspection result scenarios tested (13 scenarios)")
        print("   ✅ Complete workflow paths verified (6 paths)")
        print("   ✅ Terminal status behavior confirmed")
        print("   ✅ Business rules compliance validated")
        print("\n📋 STATUS SUMMARY:")
        print("   • Draft → In Progress, Hold")
        print("   • In Progress → Hold, Submitted")  
        print("   • Hold → In Progress, Submitted")
        print("   • Submitted → Accepted, Rejected, Conditional Accept")
        print("   • Accepted, Rejected, Conditional Accept → [Terminal]")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ STATUS TRANSITION TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Setup Frappe environment
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    # Run tests
    success = run_status_transition_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)