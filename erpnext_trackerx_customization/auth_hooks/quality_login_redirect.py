import frappe
from frappe import _

def redirect_quality_users_on_login():
    """Redirect Quality users to Quality Dashboard on login"""
    
    try:
        user_roles = frappe.get_roles(frappe.session.user)
        
        # Check if user has quality roles
        is_quality_inspector = "Quality Inspector" in user_roles
        is_quality_manager = "Quality Manager" in user_roles
        
        if is_quality_inspector or is_quality_manager:
            # Redirect to Quality Dashboard
            frappe.local.response["location"] = "/app/quality_dashboard"
            frappe.local.response["type"] = "redirect"
            
    except Exception as e:
        # Don't block login if there's an error
        frappe.log_error(f"Error in quality login redirect: {str(e)}")
        pass