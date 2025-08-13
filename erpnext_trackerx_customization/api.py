import frappe
import json
from frappe import _
import os

import frappe
from erpnext_trackerx_customization.utils.constants import get_constants

@frappe.whitelist()
def get_item_constants():
    return get_constants()

@frappe.whitelist()
def update_aql_table_entries(changes):
    """
    Update multiple AQL table entries in batch
    
    Args:
        changes: List of dictionaries with name, acceptance_number, rejection_number
    """
    try:
        if not isinstance(changes, list):
            frappe.throw(_("Changes must be a list"))
        
        updated_count = 0
        
        for change in changes:
            if not all(key in change for key in ['name', 'acceptance_number', 'rejection_number']):
                continue
                
            # Get and update the document
            doc = frappe.get_doc('AQL Table', change['name'])
            doc.acceptance_number = int(change['acceptance_number'])
            doc.rejection_number = int(change['rejection_number'])
            doc.save()
            
            updated_count += 1
        
        frappe.db.commit()
        
        return {
            'success': True,
            'updated_count': updated_count,
            'message': _('Successfully updated {0} AQL table entries').format(updated_count)
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error updating AQL table entries: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def get_aql_grid_data(regime="Normal", level="2"):
    """
    Get AQL grid data for specific regime and level
    
    Args:
        regime: Inspection regime (Normal, Tightened, Reduced)
        level: Inspection level code
    """
    try:
        # Get AQL table entries
        aql_entries = frappe.get_all(
            "AQL Table",
            fields=["name", "sample_code_letter", "aql_value", "acceptance_number", 
                   "rejection_number", "sample_size", "lot_size_range"],
            filters={
                "inspection_regime": regime,
                "inspection_level": level,
                "is_active": 1
            },
            order_by="sample_code_letter, CAST(aql_value AS DECIMAL)"
        )
        
        # Get AQL standards for column headers
        aql_standards = frappe.get_all("AQL Standard", 
                                     fields=["aql_value", "description"],
                                     order_by="CAST(aql_value AS DECIMAL)")
        
        # Organize data in grid format
        aql_grid_data = {}
        for entry in aql_entries:
            code = entry.sample_code_letter
            aql_value = entry.aql_value
            
            if code not in aql_grid_data:
                aql_grid_data[code] = {
                    "sample_size": entry.sample_size,
                    "lot_size_range": entry.lot_size_range,
                    "values": {}
                }
            
            aql_grid_data[code]["values"][aql_value] = {
                "acceptance": entry.acceptance_number,
                "rejection": entry.rejection_number,
                "doc_name": entry.name
            }
        
        return {
            'success': True,
            'aql_grid_data': aql_grid_data,
            'aql_standards': aql_standards,
            'regime': regime,
            'level': level
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting AQL grid data: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }