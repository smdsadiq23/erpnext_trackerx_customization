# AQL System API Reference

Complete API documentation for the industry-standard AQL (Accepted Quality Level) system implementation.

## Overview

The AQL system implements ISO 2859-1 (MIL-STD-105E) standard for acceptance sampling inspection by attributes. It provides:

- **7 Inspection Levels**: General (1,2,3) and Special (S1,S2,S3,S4)
- **18 AQL Values**: From 0.065% (extremely strict) to 150% (screening only)
- **588 AQL Table Entries**: Complete acceptance/rejection criteria
- **3 Inspection Regimes**: Normal, Tightened, Reduced

## Master Data Structure

### AQL Level
Defines inspection levels for different quality requirements.

```json
{
  "doctype": "AQL Level",
  "level_code": "2",
  "level_type": "General", 
  "description": "General Inspection Level II - Standard discrimination",
  "is_active": 1
}
```

**Fields:**
- `level_code`: String - Level identifier (1,2,3,S1,S2,S3,S4)
- `level_type`: String - "General" or "Special"
- `description`: Text - Detailed description of usage
- `is_active`: Boolean - Whether level is active

### AQL Standard
Defines acceptable quality levels.

```json
{
  "doctype": "AQL Standard",
  "aql_value": "2.5",
  "description": "2.5% defective - Standard quality level",
  "is_active": 1
}
```

**Fields:**
- `aql_value`: String - AQL percentage (0.065 to 150)
- `description`: Text - Usage guidelines
- `is_active`: Boolean - Whether standard is active

### AQL Table
Contains acceptance/rejection criteria for each combination.

```json
{
  "doctype": "AQL Table",
  "sample_code_letter": "H",
  "sample_size": 50,
  "aql_value": "2.5",
  "inspection_regime": "Normal",
  "acceptance_number": 3,
  "rejection_number": 4,
  "is_active": 1
}
```

**Fields:**
- `sample_code_letter`: String - Sample code (A-R)
- `sample_size`: Integer - Actual sample size
- `aql_value`: Link - Links to AQL Standard
- `inspection_regime`: String - Normal/Tightened/Reduced
- `acceptance_number`: Integer - Maximum acceptable defects
- `rejection_number`: Integer - Minimum defects for rejection
- `is_active`: Boolean - Whether entry is active

## AQL Calculator API

### Core Functions

#### `get_sample_size_code(quantity, inspection_level)`
Returns sample size code based on lot quantity and inspection level.

**Parameters:**
- `quantity` (int): Lot quantity
- `inspection_level` (str): Inspection level (1,2,3,S1,S2,S3,S4)

**Returns:**
- `str`: Sample code letter (A-R)

**Example:**
```python
from erpnext_trackerx_customization.utils.aql import AQLCalculator

code = AQLCalculator.get_sample_size_code(500, "2")  # Returns "H"
```

#### `get_sample_size(code_letter)`
Returns actual sample size for a given code letter.

**Parameters:**
- `code_letter` (str): Sample code letter (A-R)

**Returns:**
- `int`: Sample size

**Example:**
```python
size = AQLCalculator.get_sample_size("H")  # Returns 50
```

#### `calculate_aql_criteria(item_code, quantity)`
Calculates complete AQL criteria for an item.

**Parameters:**
- `item_code` (str): Item code with AQL configuration
- `quantity` (int): Received quantity

**Returns:**
- `dict`: Complete AQL criteria

**Example:**
```python
criteria = AQLCalculator.calculate_aql_criteria("ITEM-001", 500)
# Returns:
# {
#   "sample_code_letter": "H",
#   "sample_size": 50,
#   "acceptance_number": 3,
#   "rejection_number": 4,
#   "inspection_level": "2",
#   "aql_value": "2.5",
#   "inspection_regime": "Normal"
# }
```

#### `determine_inspection_result(defects_found, acceptance_number, rejection_number)`
Determines inspection result based on defects found.

**Parameters:**
- `defects_found` (int): Number of defects found in sample
- `acceptance_number` (int): Maximum acceptable defects
- `rejection_number` (int): Minimum defects for rejection

**Returns:**
- `str`: "Accepted", "Rejected", or "Re-inspect"

**Example:**
```python
result = AQLCalculator.determine_inspection_result(2, 3, 4)  # Returns "Accepted"
```

## Integration Points

### Item Configuration
Items must be configured with AQL parameters:

```python
# Required Item fields
item.custom_aql_inspection_level = "2"          # Link to AQL Level
item.custom_inspection_regime = "Normal"        # Inspection regime
item.custom_accepted_quality_level = "2.5"     # Link to AQL Standard
```

### Material Inspection Item
Enhanced with automatic AQL calculations:

```python
# Auto-calculated fields
mir_item.sample_size = 50                   # From AQL calculation
mir_item.acceptance_number = 3              # From AQL table lookup
mir_item.rejection_number = 4               # From AQL table lookup
mir_item.inspection_result = "Accepted"     # Based on defects found
```

## Sample Size Code Mapping

| Code | Sample Size | Code | Sample Size | Code | Sample Size | Code | Sample Size |
|------|-------------|------|-------------|------|-------------|------|-------------|
| A    | 2           | E    | 13          | J    | 80          | N    | 500         |
| B    | 3           | F    | 20          | K    | 125         | P    | 800         |
| C    | 5           | G    | 32          | L    | 200         | Q    | 1250        |
| D    | 8           | H    | 50          | M    | 315         | R    | 2000        |

## AQL Value Classifications

| Strictness Level | AQL Values | Usage |
|------------------|------------|-------|
| Extremely Strict | 0.065, 0.10, 0.15 | Safety-critical, high-precision |
| Very Strict | 0.25, 0.40, 0.65 | Critical components, premium quality |
| Standard | 1.0, 1.5, 2.5 | General manufacturing, consumer products |
| Lenient | 4.0, 6.5, 10 | Non-critical, cost-sensitive |
| Very Lenient | 15, 25, 40 | Basic quality, rough materials |
| Extremely Lenient | 65, 100, 150 | Material classification, screening |

## Error Handling

The system provides comprehensive error handling:

### Common Errors

**"Item does not have complete AQL configuration"**
- Cause: Missing AQL fields on Item
- Solution: Configure all three AQL fields on Item

**"No AQL table entry found"**
- Cause: Missing AQL table entry for combination
- Solution: Import complete AQL table data

**"AQL value must be one of the standard values"**
- Cause: Invalid AQL value used
- Solution: Use only standard ISO 2859-1 values

### Validation Functions

```python
from erpnext_trackerx_customization.utils.aql.validators import (
    validate_aql_value,
    validate_inspection_level,
    validate_sample_code_letter
)

# Validate AQL value
validate_aql_value("2.5")  # Returns True or raises exception

# Validate inspection level
validate_inspection_level("2", "General")  # Returns True or raises exception
```

## Data Import

### Import Complete AQL Master Data

```bash
# Import all AQL master data
bench execute erpnext_trackerx_customization.erpnext_trackerx_customization.import_aql_data.import_aql_master_data
```

This imports:
- **7 AQL Levels** (1,2,3,S1,S2,S3,S4)
- **18 AQL Standards** (0.065% to 150%)
- **588 AQL Table Entries** (all combinations)

### Validation

The import script includes comprehensive validation:
- Checks all expected levels are present
- Verifies sample code coverage (A-R)
- Confirms regime coverage (Normal/Tightened/Reduced)
- Validates data relationships

## Performance Considerations

- **AQL Table Lookups**: Optimized with database indexes
- **Batch Processing**: Import processes data in batches
- **Caching**: Calculation results can be cached
- **Memory Usage**: Minimal memory footprint for calculations

## Testing

The system includes comprehensive test coverage:

```bash
# Run AQL unit tests
python -m pytest erpnext_trackerx_customization/tests/unit/aql/

# Run AQL integration tests  
python -m pytest erpnext_trackerx_customization/tests/integration/test_aql_workflow.py

# Run complete system test
python erpnext_trackerx_customization/tests/functional/final_aql_test.py
```

## Standards Compliance

✅ **ISO 2859-1 Compliant**: Fully implements international standard
✅ **MIL-STD-105E Compatible**: Military standard compatibility
✅ **Industry Standard**: Used across manufacturing industries
✅ **Quality Assurance**: Comprehensive validation and testing