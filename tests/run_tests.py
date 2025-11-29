#!/usr/bin/env python3
"""
Main test runner for ERPNext TrackerX Customization tests

Usage:
    python3 tests/run_tests.py [test_name]

Available tests:
    - supervisor_workflow: Tests supervisor rejection workflow
    - verification: Code verification only
    - all: Run all tests
"""

import sys
import os
import subprocess
from pathlib import Path

def run_supervisor_workflow_test():
    """Run supervisor workflow tests"""
    print("🚀 Running Supervisor Workflow Tests...")

    bench_path = Path(__file__).parent.parent.parent.parent.parent
    cmd = [
        "bench", "--site", "all", "execute",
        "trackerx_live.tests.supervisor_workflow.test_supervisor_workflow.test_supervisor_rejection_workflow"
    ]

    try:
        result = subprocess.run(cmd, cwd=bench_path, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run test: {e}")
        return False

def run_code_verification():
    """Run code verification to check if fixes are properly applied"""
    print("🔍 Running Code Verification...")

    bench_path = Path(__file__).parent.parent.parent.parent.parent

    verification_code = '''
def verify_fixes():
    print("🧪 Verifying Code Fixes...")

    # Check scan_item.py fix
    with open("apps/trackerx_live/trackerx_live/trackerx_live/api/scan_item.py", "r") as f:
        content = f.read()

    if "last_scan_log_doc.current_operation" in content:
        print("❌ scan_item.py: Field reference NOT fixed")
        return False
    elif "last_scan_log_doc.operation" in content:
        print("✅ scan_item.py: Field reference fixed")
    else:
        print("⚠️  scan_item.py: Could not verify field reference")

    # Check defect_classification.py fix
    with open("apps/trackerx_live/trackerx_live/trackerx_live/api/defect_classification.py", "r") as f:
        content = f.read()

    expected_features = [
        'if final_status in ("SP Rejected", "SP Recut")',
        'prod_item.status = "Completed"',
        'prod_item.tracking_status = "Unlinked"',
        'UPDATE `tabProduction Item Tag Map`'
    ]

    all_found = True
    for feature in expected_features:
        if feature in content:
            print(f"   ✅ {feature}")
        else:
            print(f"   ❌ Missing: {feature}")
            all_found = False

    return all_found

if verify_fixes():
    print("\\n🎉 All code fixes verified successfully!")
    exit(0)
else:
    print("\\n❌ Some code fixes are missing!")
    exit(1)
'''

    try:
        result = subprocess.run(
            ["python3", "-c", verification_code],
            cwd=bench_path,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr and "exit" not in result.stderr:
            print(f"Errors: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run verification: {e}")
        return False

def main():
    """Main test runner"""
    print("🧪 ERPNext TrackerX Customization - Test Runner")
    print("=" * 50)

    if len(sys.argv) > 1:
        test_name = sys.argv[1]
    else:
        test_name = "verification"  # Default to verification only

    success = True

    if test_name in ("all", "verification"):
        success &= run_code_verification()

    if test_name in ("all", "supervisor_workflow"):
        success &= run_supervisor_workflow_test()

    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()