"""
AQL Data API
Provides access to AQL Level data for frontend components
"""

import frappe
from frappe import _

@frappe.whitelist()
def get_aql_levels():
    """Get all AQL levels for dropdown/selection"""
    try:
        aql_levels = frappe.get_list(
            "AQL Level",
            fields=["name", "level_code", "level_type", "description"],
            order_by="level_code"
        )
        
        return {
            "success": True,
            "data": aql_levels,
            "count": len(aql_levels)
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching AQL levels: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@frappe.whitelist()
def get_aql_level_details(level_code):
    """Get detailed information for a specific AQL level"""
    try:
        aql_level = frappe.get_doc("AQL Level", level_code)
        
        return {
            "success": True,
            "data": {
                "name": aql_level.name,
                "level_code": aql_level.level_code,
                "level_type": aql_level.level_type,
                "description": aql_level.description
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching AQL level {level_code}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

@frappe.whitelist()
def get_aql_standards():
    """Get all AQL standards/values for dropdown/selection"""
    try:
        aql_standards = frappe.get_list(
            "AQL Standard",
            fields=["name", "aql_value", "description"],
            filters={"is_active": 1},
            order_by="CAST(aql_value AS DECIMAL(10,2))"
        )
        
        return {
            "success": True,
            "data": aql_standards,
            "count": len(aql_standards)
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching AQL standards: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@frappe.whitelist()
def get_aql_options():
    """Get both AQL levels and standards in one call for efficiency"""
    try:
        # Get AQL Levels
        aql_levels = frappe.get_list(
            "AQL Level",
            fields=["name", "level_code", "level_type", "description"],
            filters={"is_active": 1},
            order_by="level_code"
        )
        
        # Get AQL Standards
        aql_standards = frappe.get_list(
            "AQL Standard", 
            fields=["name", "aql_value", "description"],
            filters={"is_active": 1},
            order_by="CAST(aql_value AS DECIMAL(10,2))"
        )
        
        return {
            "success": True,
            "data": {
                "aql_levels": aql_levels,
                "aql_standards": aql_standards
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching AQL options: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {"aql_levels": [], "aql_standards": []}
        }

@frappe.whitelist()
def calculate_aql_sampling(total_quantity, aql_level, aql_value, inspection_regime, total_rolls=None):
    """Calculate AQL sampling requirements based on AQL Table"""
    try:
        # Convert parameters
        total_quantity = float(total_quantity) if total_quantity else 0
        total_rolls = int(total_rolls) if total_rolls else 0
        
        if total_quantity <= 0:
            return {
                "success": False,
                "error": "Total quantity must be greater than 0",
                "data": {}
            }
        
        # Determine lot size range based on total quantity
        lot_size_range = get_lot_size_range(total_quantity)
        
        # Query AQL Table for matching entry
        aql_table_entry = frappe.get_list(
            "AQL Table",
            fields=["sample_size", "sample_code_letter", "acceptance_number", "rejection_number"],
            filters={
                "inspection_level": aql_level,
                "inspection_regime": inspection_regime,
                "lot_size_range": lot_size_range,
                "aql_value": aql_value,
                "is_active": 1
            },
            limit=1
        )
        
        if not aql_table_entry:
            # Return default calculation if no exact match
            sample_rolls = min(max(1, int(total_rolls * 0.1)), total_rolls) if total_rolls else 1
            return {
                "success": True,
                "data": {
                    "sample_size": sample_rolls,
                    "sample_rolls": sample_rolls,
                    "lot_size_range": lot_size_range,
                    "sample_code_letter": "N/A",
                    "acceptance_number": 0,
                    "rejection_number": 1,
                    "calculation_method": "default_fallback"
                }
            }
        
        entry = aql_table_entry[0]
        
        # Calculate roll sampling based on AQL sample size
        sample_size = entry.get("sample_size", 1)
        
        # For fabric inspection, sample size represents meters/units to inspect
        # Convert to rolls - assume even distribution across available rolls
        if total_rolls and total_rolls > 0:
            rolls_to_inspect = min(max(1, int(sample_size / (total_quantity / total_rolls))), total_rolls)
        else:
            rolls_to_inspect = 1
            
        return {
            "success": True,
            "data": {
                "sample_size": sample_size,
                "sample_rolls": rolls_to_inspect,
                "lot_size_range": lot_size_range,
                "sample_code_letter": entry.get("sample_code_letter"),
                "acceptance_number": entry.get("acceptance_number"),
                "rejection_number": entry.get("rejection_number"),
                "calculation_method": "aql_table"
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating AQL sampling: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {}
        }

def get_lot_size_range(total_quantity):
    """Determine lot size range based on quantity (ISO 2859-1 standard)"""
    if total_quantity <= 8:
        return "2-8"
    elif total_quantity <= 15:
        return "9-15"
    elif total_quantity <= 25:
        return "16-25"
    elif total_quantity <= 50:
        return "26-50"
    elif total_quantity <= 90:
        return "51-90"
    elif total_quantity <= 150:
        return "91-150"
    elif total_quantity <= 280:
        return "151-280"
    elif total_quantity <= 500:
        return "281-500"
    elif total_quantity <= 1200:
        return "501-1200"
    elif total_quantity <= 3200:
        return "1201-3200"
    elif total_quantity <= 10000:
        return "3201-10000"
    elif total_quantity <= 35000:
        return "10001-35000"
    elif total_quantity <= 150000:
        return "35001-150000"
    else:
        return "150001-500000"

@frappe.whitelist()
def test_aql_access():
    """Test AQL data accessibility"""
    try:
        count = frappe.db.count("AQL Level")
        sample_data = frappe.get_list("AQL Level", limit=3)
        
        return {
            "success": True,
            "total_records": count,
            "sample_count": len(sample_data),
            "sample_data": sample_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
