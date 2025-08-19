# -*- coding: utf-8 -*-
"""
AQL Table View DocType

Manages different views and formats for displaying AQL tables.
"""

import frappe
from frappe.model.document import Document
from frappe import _

class AQLTableView(Document):
    def validate(self):
        if self.is_default_view:
            # Ensure only one default view exists
            existing_default = frappe.get_all("AQL Table View", 
                                            filters={"is_default_view": 1, "name": ["!=", self.name]},
                                            limit=1)
            if existing_default:
                frappe.throw(_("Another view is already set as default. Please uncheck that first."))
        
        if self.aql_values_selection == "Custom Selection" and not self.selected_aql_values:
            frappe.throw(_("Please specify AQL values for custom selection"))
    
    def get_aql_data(self):
        """Generate AQL data based on view configuration"""
        
        # Parse selected AQL values
        if self.aql_values_selection == "Common Values Only":
            aql_values = ["0.065", "0.10", "0.15", "0.25", "0.40", "0.65", "1.0", "1.5", "2.5", "4.0", "6.5"]
        elif self.aql_values_selection == "All Values":
            aql_values = frappe.get_all("AQL Standard", pluck="aql_value", order_by="CAST(aql_value AS DECIMAL)")
        else:  # Custom Selection
            aql_values = [val.strip() for val in (self.selected_aql_values or "").split(",")]
        
        # Build filters
        filters = {"is_active": 1}
        if self.inspection_regime != "All":
            filters["inspection_regime"] = self.inspection_regime
        
        # Get inspection levels
        if self.inspection_levels:
            levels = frappe.get_all("AQL Level", pluck="level_code", order_by="level_code")
        else:
            levels = ["2"]  # Default to Level 2
        
        # Build table data
        table_data = {}
        
        for level in levels:
            level_data = {}
            
            # Get all entries for this level
            level_filters = dict(filters)
            level_filters["inspection_level"] = level
            
            entries = frappe.get_all(
                "AQL Table",
                fields=["lot_size_range", "sample_code_letter", "sample_size", 
                       "aql_value", "acceptance_number", "rejection_number", "inspection_regime"],
                filters=level_filters,
                order_by="lot_size_range, aql_value"
            )
            
            # Group by lot size range and sample code
            for entry in entries:
                if entry.aql_value not in aql_values:
                    continue
                
                range_key = entry.lot_size_range
                if range_key not in level_data:
                    level_data[range_key] = {
                        "sample_code": entry.sample_code_letter,
                        "sample_size": entry.sample_size,
                        "aql_data": {}
                    }
                
                level_data[range_key]["aql_data"][entry.aql_value] = {
                    "acceptance": entry.acceptance_number,
                    "rejection": entry.rejection_number,
                    "regime": entry.inspection_regime
                }
            
            if level_data:
                table_data[level] = level_data
        
        return {
            "aql_values": aql_values,
            "levels": levels,
            "table_data": table_data,
            "view_config": {
                "show_lot_size_ranges": self.show_lot_size_ranges,
                "show_sample_sizes": self.show_sample_sizes,
                "show_acceptance_rejection": self.show_acceptance_rejection,
                "table_style": self.table_style,
                "inspection_regime": self.inspection_regime
            }
        }