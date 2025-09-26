# production_target_manager.py - Frappe Page Python
import frappe

def get_context(context):
    # This function is called when the page is accessed
    context.no_cache = 1
    
    # Add any server-side data processing here if needed
    # For this page, we'll handle data loading via AJAX calls
    
    return context