# File Organization Structure

This document describes the organized file structure for the ERPNext TrackerX Customization project.

## Directory Structure

### `/tests/` - Test Files
Contains all test files, examples, and verification scripts:
- **Unit Tests**: `test_*.py` files for individual components
- **Integration Tests**: End-to-end testing scripts  
- **Examples**: `fabric_inspection_example.py` and other examples
- **Verification**: Data verification and debug scripts
- **HTML Templates**: Test HTML files and previews

### `/erpnext_trackerx_customization/data/` - Data Files
Contains data scripts and master data:
- `complete_fabric_defects.py` - Fabric defect definitions
- `defect_master_data.py` - Master defect data
- `import_aql_data.py` - AQL data import script

### `/erpnext_trackerx_customization/setup/` - Setup Files
Contains setup and installation scripts:
- `generate_aql_table.py` - AQL table generation
- `generate_aql_table_with_ranges.py` - AQL table with ranges
- `setup_aql_views.py` - AQL view setup
- `purchase_receipt_custom_fields.py` - Custom field setup
- `warehouse_structure.py` - Warehouse structure setup

### `/docs/` - Documentation
Contains all documentation files:
- Project summaries and README files
- API documentation
- Setup guides and examples
- Technical specifications

## Files Moved

### From Root to `/tests/`:
- `aql_doctype_assessment.py`
- `fabric_inspection_preview.html` 
- `run_tests.py`

### From Main Module to `/tests/`:
- All `test_*.py` files from various doctypes
- `fabric_inspection_example.py`
- Test template files

### From Root `/setup/` to `/erpnext_trackerx_customization/setup/`:
- `generate_aql_table.py`
- `generate_aql_table_with_ranges.py`
- `setup_aql_views.py`

### From Nested `/data/data/` to `/erpnext_trackerx_customization/data/`:
- `complete_fabric_defects.py`
- `defect_master_data.py`
- `import_aql_data.py` (moved from inner module)

## Benefits of This Organization

1. **Clear Separation**: Tests, setup, and data files are properly separated
2. **Easy Navigation**: Developers can quickly find relevant files
3. **Maintainability**: Better code organization for long-term maintenance
4. **Best Practices**: Follows Python/Frappe project structure conventions
5. **Scalability**: Easy to add new files in appropriate locations

## Running Tests

All test files are now located in the `/tests/` directory. To run tests:

```bash
# Run all tests
python tests/run_tests.py

# Run specific test
python tests/test_fabric_inspection.py

# Run verification scripts
python tests/verify_aql_data.py
```

## Data Import

Data-related scripts are in `/erpnext_trackerx_customization/data/`:

```bash
# Import AQL data
python -m erpnext_trackerx_customization.data.import_aql_data

# Import defect master data  
python -m erpnext_trackerx_customization.data.defect_master_data
```

## Setup Scripts

Setup scripts are in `/erpnext_trackerx_customization/setup/`:

```bash
# Generate AQL tables
python -m erpnext_trackerx_customization.setup.generate_aql_table

# Setup warehouse structure
python -m erpnext_trackerx_customization.setup.warehouse_structure
```

This organization ensures a clean, maintainable codebase that follows industry best practices.