"""
Utility functions for ERPNext TrackerX Customization
"""

import frappe
import json
import os


def get_material_types():
    """
    Get material types from constants.json
    """
    try:
        constants_path = os.path.join(
            frappe.get_app_path('erpnext_trackerx_customization'), 
            'config', 
            'constants.json'
        )
        
        if os.path.exists(constants_path):
            with open(constants_path, 'r') as f:
                constants = json.load(f)
            return constants.get('item_master', [])
        else:
            # Fallback if constants file doesn't exist
            return ["Finished Goods", "Fabrics", "Trims", "Accessories", "Machines", "Labels", "Packing Materials"]
            
    except Exception as e:
        frappe.log_error(f"Error reading material types from constants: {str(e)}")
        # Return fallback values
        return ["Finished Goods", "Fabrics", "Trims", "Accessories", "Machines", "Labels", "Packing Materials"]


def get_material_type_options():
    """
    Get material types formatted as options string for Select fields
    """
    material_types = get_material_types()
    return '\n'.join(material_types)


@frappe.whitelist()
def get_material_types_for_api():
    """
    API endpoint to get material types
    """
    return {
        'success': True,
        'material_types': get_material_types()
    }