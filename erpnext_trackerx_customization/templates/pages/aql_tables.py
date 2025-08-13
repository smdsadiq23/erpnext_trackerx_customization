# -*- coding: utf-8 -*-
"""
AQL Tables Web Page

Displays AQL tables for different inspection regimes in a structured format.
"""

import frappe
from frappe import _

def get_context(context):
    """Get context data for AQL tables page"""
    
    context.title = _("AQL Tables - Inspection Regimes")
    
    # Get all inspection regimes
    regimes = ["Normal", "Tightened", "Reduced"]
    
    # Get all inspection levels
    levels = frappe.get_all("AQL Level", 
                          fields=["level_code", "level_type", "description"],
                          order_by="level_code")
    
    # Get all AQL standards
    standards = frappe.get_all("AQL Standard",
                             fields=["aql_value", "description"],
                             order_by="CAST(aql_value AS DECIMAL)")
    
    # Get sample codes and their sizes
    sample_codes = {
        'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20,
        'G': 32, 'H': 50, 'J': 80, 'K': 125, 'L': 200,
        'M': 315, 'N': 500, 'P': 800, 'Q': 1250, 'R': 2000
    }
    
    # Build AQL table data for each regime
    aql_tables = {}
    
    for regime in regimes:
        # Get all entries for this regime
        entries = frappe.get_all(
            "AQL Table",
            fields=["inspection_level", "lot_size_range", "sample_code_letter", 
                   "sample_size", "aql_value", "acceptance_number", "rejection_number"],
            filters={"inspection_regime": regime, "is_active": 1},
            order_by="inspection_level, lot_size_range, aql_value"
        )
        
        # Organize data by inspection level and lot size range
        regime_data = {}
        for entry in entries:
            level = entry.inspection_level
            lot_range = entry.lot_size_range
            
            if level not in regime_data:
                regime_data[level] = {}
            
            if lot_range not in regime_data[level]:
                regime_data[level][lot_range] = {
                    'sample_code': entry.sample_code_letter,
                    'sample_size': entry.sample_size,
                    'aql_values': {}
                }
            
            regime_data[level][lot_range]['aql_values'][entry.aql_value] = {
                'acceptance': entry.acceptance_number,
                'rejection': entry.rejection_number
            }
        
        aql_tables[regime] = regime_data
    
    context.regimes = regimes
    context.levels = levels
    context.standards = standards
    context.sample_codes = sample_codes
    context.aql_tables = aql_tables
    
    return context