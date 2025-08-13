# -*- coding: utf-8 -*-
"""
AQL Grid Web Page

Displays AQL tables in an editable spreadsheet-like format.
"""

import frappe
from frappe import _

def get_context(context):
    """Get context data for AQL grid page"""
    
    context.title = _("AQL Grid - Editable Table")
    
    # Get URL parameters for regime and level selection
    default_regime = frappe.form_dict.get("regime", "Normal")
    default_level = frappe.form_dict.get("level", "2")
    
    # Validate regime and level
    valid_regimes = ["Normal", "Tightened", "Reduced"]
    if default_regime not in valid_regimes:
        default_regime = "Normal"
    
    # Get AQL values for column headers
    aql_standards = frappe.get_all("AQL Standard", 
                                 fields=["aql_value", "description"],
                                 order_by="CAST(aql_value AS DECIMAL)")
    
    # Get all sample codes and their sizes (for rows)
    sample_codes_data = [
        {"code": "A", "size": 2},
        {"code": "B", "size": 3}, 
        {"code": "C", "size": 5},
        {"code": "D", "size": 8},
        {"code": "E", "size": 13},
        {"code": "F", "size": 20},
        {"code": "G", "size": 32},
        {"code": "H", "size": 50},
        {"code": "J", "size": 80},
        {"code": "K", "size": 125},
        {"code": "L", "size": 200},
        {"code": "M", "size": 315},
        {"code": "N", "size": 500},
        {"code": "P", "size": 800},
        {"code": "Q", "size": 1250},
        {"code": "R", "size": 2000}
    ]
    
    # Get inspection levels and regimes
    inspection_levels = frappe.get_all("AQL Level",
                                     fields=["level_code", "level_type", "description"],
                                     order_by="level_code")
    
    inspection_regimes = ["Normal", "Tightened", "Reduced"]
    
    # Get all AQL table entries for the default view
    try:
        aql_entries = frappe.get_all(
            "AQL Table",
            fields=["name", "sample_code_letter", "aql_value", "acceptance_number", 
                   "rejection_number", "sample_size", "lot_size_range"],
            filters={
                "inspection_regime": default_regime,
                "inspection_level": default_level,
                "is_active": 1
            },
            order_by="sample_code_letter, CAST(aql_value AS DECIMAL)"
        )
    except:
        aql_entries = []  # Empty if no data exists yet
    
    # Organize data in grid format - flatten for easier template access
    aql_grid_data = {}
    aql_flat_data = {}
    
    # Create sample data if no real data exists
    if not aql_entries:
        # Create mock data for demonstration
        for code_data in sample_codes_data[:5]:  # First 5 codes only
            code = code_data["code"]
            aql_grid_data[code] = {
                "sample_size": code_data["size"],
                "lot_size_range": f"Sample range for {code}"
            }
            # Add some mock AQL values
            for aql_val in ["0.065", "0.10", "0.15"]:
                flat_key = f"{code}_{aql_val}"
                aql_flat_data[flat_key] = {
                    "acceptance": 0,
                    "rejection": 1,
                    "doc_name": f"mock_{flat_key}"
                }
    else:
        # Process real data
        for entry in aql_entries:
            code = entry.sample_code_letter
            aql_value = entry.aql_value
            
            if code not in aql_grid_data:
                aql_grid_data[code] = {
                    "sample_size": entry.sample_size,
                    "lot_size_range": entry.lot_size_range
                }
            
            # Create flattened key for template access
            flat_key = f"{code}_{aql_value}"
            aql_flat_data[flat_key] = {
                "acceptance": entry.acceptance_number,
                "rejection": entry.rejection_number,
                "doc_name": entry.name
            }
    
    context.aql_standards = aql_standards
    context.sample_codes_data = sample_codes_data
    context.inspection_levels = inspection_levels
    context.inspection_regimes = inspection_regimes
    context.aql_grid_data = aql_grid_data
    context.aql_flat_data = aql_flat_data
    context.default_regime = default_regime
    context.default_level = default_level
    
    return context