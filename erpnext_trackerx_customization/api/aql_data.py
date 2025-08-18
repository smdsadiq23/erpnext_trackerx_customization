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
