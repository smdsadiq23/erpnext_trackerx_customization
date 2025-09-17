# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe

def get_context(context):
    """Set context for the warehouse capacity dashboard page"""
    
    # Check if user has permission to view warehouse data
    if not frappe.has_permission("Warehouse", "read"):
        frappe.throw("Insufficient permissions to view warehouse data", frappe.PermissionError)
    
    # Set page context
    context.page_title = "Warehouse Capacity Intelligence Dashboard"
    context.show_sidebar = False
    
    return context