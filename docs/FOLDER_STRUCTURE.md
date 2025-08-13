# Industry Standard Folder Structure

This document outlines the organized folder structure for the ERPNext TrackerX Customization app, following Python and Frappe framework best practices.

## Root Directory Structure

```
erpnext_trackerx_customization/
├── README.md                           # Project overview and setup
├── license.txt                         # License information  
├── pyproject.toml                      # Python project configuration
├── FOLDER_STRUCTURE.md                 # This document
│
├── docs/                               # Documentation
│   ├── README.md                       # Documentation index
│   ├── api/                           # API documentation
│   │   ├── aql_system.md              # AQL system APIs
│   │   └── quality_management.md     # Quality APIs
│   ├── examples/                      # Examples and tutorials
│   │   ├── aql_setup.md               # AQL setup guide
│   │   └── integration_examples.py   # Code examples
│   └── guides/                        # User guides
│       ├── aql_workflow.md            # Workflow documentation
│       └── quality_control.md        # QC processes
│
└── erpnext_trackerx_customization/    # Main app package
    ├── __init__.py                     # Package initialization
    ├── hooks.py                        # Frappe hooks configuration
    ├── modules.txt                     # Module definitions
    ├── patches.txt                     # Database patches
    │
    ├── api/                           # External API endpoints
    │   ├── __init__.py
    │   └── item_groups_filter.py
    │
    ├── config/                        # Configuration files
    │   ├── __init__.py
    │   └── constants.json
    │
    ├── erpnext_doctype_hooks/         # ERPNext doctype hooks
    │   ├── bom.py
    │   ├── item_hooks.py
    │   ├── material_request_hooks.py
    │   └── workflow/
    │       └── grn_workflow.py
    │
    ├── erpnext_trackerx_customization/ # Core app module
    │   ├── __init__.py
    │   │
    │   ├── doctype/                   # Custom DocTypes
    │   │   ├── __init__.py
    │   │   │
    │   │   ├── aql_level/             # AQL Level DocType
    │   │   │   ├── __init__.py
    │   │   │   ├── aql_level.json
    │   │   │   └── aql_level.py
    │   │   │
    │   │   ├── aql_standard/          # AQL Standard DocType  
    │   │   │   ├── __init__.py
    │   │   │   ├── aql_standard.json
    │   │   │   └── aql_standard.py
    │   │   │
    │   │   ├── aql_table/             # AQL Table DocType
    │   │   │   ├── __init__.py
    │   │   │   ├── aql_table.json
    │   │   │   └── aql_table.py
    │   │   │
    │   │   ├── material_inspection_item/ # Enhanced MIR Item
    │   │   │   ├── __init__.py
    │   │   │   ├── material_inspection_item.json
    │   │   │   └── material_inspection_item.py
    │   │   │
    │   │   └── [other_doctypes]/      # Other business DocTypes
    │   │
    │   ├── fixtures/                  # Master data fixtures
    │   │   ├── aql_level.json
    │   │   ├── aql_standard.json
    │   │   └── aql_table.json
    │   │
    │   ├── import_aql_data.py         # AQL master data import script
    │   │
    │   └── utils/                     # Utility modules
    │       ├── __init__.py
    │       ├── constants.py           # General constants
    │       │
    │       ├── aql/                   # AQL utilities
    │       │   ├── __init__.py
    │       │   ├── calculator.py      # Core AQL calculations
    │       │   ├── constants.py       # AQL-specific constants
    │       │   └── validators.py      # AQL validation utilities
    │       │
    │       ├── quality/               # Quality management utilities
    │       │   ├── __init__.py
    │       │   └── inspection_utils.py
    │       │
    │       └── helpers/               # General helper functions
    │           ├── __init__.py
    │           └── data_utils.py
    │
    ├── fixtures/                      # App-level fixtures
    │   ├── custom_field.json          # Custom field definitions
    │   ├── custom_docperm.json        # Custom permissions
    │   ├── item_group.json            # Master data
    │   └── property_setter.json       # Property customizations
    │
    ├── overrides/                     # DocType overrides
    │   ├── __init__.py
    │   └── bom.py
    │
    ├── patches/                       # Database migration patches
    │   └── [version_patches]/
    │
    ├── public/                        # Frontend assets
    │   └── js/
    │       ├── bom.js
    │       ├── item.js
    │       └── material_request.js
    │
    ├── scripts/                       # Utility scripts
    │   └── [setup_scripts]/
    │
    ├── setup/                         # Setup utilities
    │   ├── purchase_receipt_custom_fields.py
    │   └── warehouse_structure.py
    │
    ├── templates/                     # Web templates
    │   ├── __init__.py
    │   └── pages/
    │       └── __init__.py
    │
    ├── tests/                         # Test suite
    │   ├── __init__.py                # Test package init
    │   │
    │   ├── fixtures/                  # Test data fixtures
    │   │   ├── test_items.json
    │   │   └── test_aql_data.json
    │   │
    │   ├── unit/                      # Unit tests
    │   │   ├── __init__.py
    │   │   │
    │   │   ├── aql/                   # AQL unit tests
    │   │   │   ├── __init__.py
    │   │   │   ├── test_aql_calculator.py
    │   │   │   ├── test_aql_level.py
    │   │   │   ├── test_aql_standard.py
    │   │   │   ├── test_aql_table.py
    │   │   │   └── test_aql_standalone.py
    │   │   │
    │   │   ├── quality/               # Quality unit tests
    │   │   │   ├── __init__.py
    │   │   │   └── test_inspection_utils.py
    │   │   │
    │   │   ├── warehouse/             # Warehouse unit tests
    │   │   │   ├── __init__.py
    │   │   │   └── test_warehouse_utils.py
    │   │   │
    │   │   └── inventory/             # Inventory unit tests
    │   │       ├── __init__.py
    │   │       └── test_inventory_utils.py
    │   │
    │   ├── integration/               # Integration tests
    │   │   ├── __init__.py
    │   │   ├── test_aql_workflow.py   # AQL end-to-end tests
    │   │   └── test_quality_workflow.py
    │   │
    │   └── functional/                # Functional/E2E tests
    │       ├── __init__.py
    │       ├── final_aql_test.py      # Complete AQL system test
    │       └── test_user_workflows.py
    │
    └── utils/                         # App-level utilities
        ├── __init__.py
        └── constants.py
```

## Key Organization Principles

### 1. **Separation of Concerns**
- **DocTypes**: Business logic and data models
- **Utils**: Reusable utility functions and calculations  
- **Tests**: Comprehensive test coverage organized by type
- **Fixtures**: Master data and setup data
- **API**: External interfaces and endpoints

### 2. **Modular Structure**
- **AQL System**: Self-contained in `utils/aql/` with calculator, constants, validators
- **Quality Management**: Separate module for quality-specific utilities
- **Test Organization**: Unit, integration, and functional tests clearly separated

### 3. **Industry Standards**
- **Python Package Structure**: Proper `__init__.py` files and module organization
- **Test Categories**: Unit tests for individual components, integration for interactions, functional for workflows
- **Documentation**: API docs, examples, and user guides
- **Configuration Management**: Centralized constants and configuration files

### 4. **Scalability**
- **Modular Utils**: Easy to extend with new utility modules
- **Test Structure**: Simple to add new test categories and modules
- **Documentation**: Organized for different user types (developers, users, administrators)
- **Clean Dependencies**: Clear import paths and module relationships

## Benefits of This Structure

1. **Maintainability**: Clear separation makes code easy to find and modify
2. **Testability**: Comprehensive test structure ensures quality
3. **Scalability**: Easy to add new features without structural changes
4. **Documentation**: Well-documented for different audiences
5. **Industry Compliance**: Follows Python and Frappe best practices
6. **Team Collaboration**: Clear structure makes it easy for teams to work together

## Migration Notes

Files have been moved from their previous locations to this organized structure:
- `aql_calculator.py` → `utils/aql/calculator.py`
- Test files → `tests/unit/aql/`, `tests/integration/`, `tests/functional/`
- Documentation → `docs/` with proper categorization

All import statements have been updated to reflect the new structure.