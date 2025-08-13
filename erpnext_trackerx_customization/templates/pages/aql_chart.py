# -*- coding: utf-8 -*-
"""
AQL Chart Web Page

Displays AQL charts in a traditional tabular format similar to industry standard AQL cards.
"""

import frappe
from frappe import _

def get_context(context):
    """Get context data for AQL chart page"""
    
    context.title = _("AQL Chart - Industry Standard")
    
    # Common AQL values used in industry
    common_aql_values = ["0.065", "0.10", "0.15", "0.25", "0.40", "0.65", "1.0", "1.5", "2.5", "4.0", "6.5"]
    
    # Sample size codes and their corresponding sample sizes
    sample_codes_info = [
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
    
    # Build AQL chart data for Normal inspection
    aql_chart_data = {}
    
    for code_info in sample_codes_info:
        code = code_info["code"]
        size = code_info["size"]
        
        # Get AQL data for this sample code in Normal regime
        entries = frappe.get_all(
            "AQL Table",
            fields=["aql_value", "acceptance_number", "rejection_number"],
            filters={
                "sample_code_letter": code,
                "inspection_regime": "Normal",
                "is_active": 1
            },
            order_by="CAST(aql_value AS DECIMAL)"
        )
        
        # Organize by AQL value
        code_data = {"size": size, "aql_values": {}}
        for entry in entries:
            if entry.aql_value in common_aql_values:
                code_data["aql_values"][entry.aql_value] = {
                    "ac": entry.acceptance_number,
                    "re": entry.rejection_number
                }
        
        if code_data["aql_values"]:  # Only include codes that have data
            aql_chart_data[code] = code_data
    
    # Get lot size ranges for General Level II (most common)
    lot_ranges = frappe.db.sql("""
        SELECT DISTINCT lot_size_range, sample_code_letter
        FROM `tabAQL Table`
        WHERE inspection_level = '2' AND inspection_regime = 'Normal'
        ORDER BY sample_code_letter
    """, as_dict=True)
    
    # Create lot size to sample code mapping
    lot_size_mapping = {}
    for range_info in lot_ranges:
        lot_size_mapping[range_info.lot_size_range] = range_info.sample_code_letter
    
    context.common_aql_values = common_aql_values
    context.sample_codes_info = sample_codes_info
    context.aql_chart_data = aql_chart_data
    context.lot_size_mapping = lot_size_mapping
    
    return context