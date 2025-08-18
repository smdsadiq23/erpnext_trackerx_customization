# Trims Inspection Test Suite

This directory contains comprehensive tests for the Trims Inspection workflow, covering the complete E2E process from GRN to Purchase Receipt creation.

## Test Structure

### Core Tests (Essential)
- `test_defects_calculations.py` - Tests defects calculation logic and cross-contamination prevention
- `test_status_transitions.py` - Tests all 7 status transitions and workflow validation  
- `test_grn_workflow.py` - Tests GRN to Inspection/Purchase Receipt workflow
- `test_e2e_complete.py` - Complete end-to-end workflow testing

### Setup & Data
- `setup_test_data.py` - Creates master data for testing (suppliers, items, defects, AQL levels)

### Utilities
- `test_runner.py` - Runs all tests in sequence

## Running Tests

### Run All Tests
```bash
bench execute erpnext_trackerx_customization.tests.test_runner.run_all_tests
```

### Run Individual Tests
```bash
# Test defects calculations
bench execute erpnext_trackerx_customization.tests.test_defects_calculations.run_defects_tests

# Test status transitions  
bench execute erpnext_trackerx_customization.tests.test_status_transitions.run_status_tests

# Test GRN workflow
bench execute erpnext_trackerx_customization.tests.test_grn_workflow.run_grn_tests

# Test complete E2E
bench execute erpnext_trackerx_customization.tests.test_e2e_complete.run_e2e_tests
```

### Setup Test Data
```bash
bench execute erpnext_trackerx_customization.tests.setup_test_data.create_all_test_data
```

## Test Coverage

- ✅ Defects calculation with cross-contamination prevention
- ✅ All 7 status transitions (Draft, In Progress, Hold, Submitted, Accepted, Rejected, Conditional Accept)
- ✅ AQL sample size calculations
- ✅ GRN workflow separation (inspection vs non-inspection items)
- ✅ Purchase Receipt creation for non-inspection items
- ✅ Inspection document creation for inspection items
- ✅ Complete E2E workflow from GRN to final status
- ✅ Business rules validation
- ✅ Terminal status behavior
- ✅ Real data integration testing

## Status Transitions Tested

```
Draft → In Progress, Hold
In Progress → Hold, Submitted  
Hold → In Progress, Submitted
Submitted → Accepted, Rejected, Conditional Accept
Accepted, Rejected, Conditional Accept → [Terminal - no outgoing transitions]
```

## Workflow Confirmed

```
GRN Submission → Decision Point
├── Inspection Items → Inspection Documents → Status Workflow
└── Non-Inspection Items → Purchase Receipts → Direct Processing
```