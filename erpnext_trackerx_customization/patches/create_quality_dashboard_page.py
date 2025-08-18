import frappe
from frappe import _

def execute():
    """
    Migration patch to create Quality Dashboard page
    This runs automatically with bench migrate
    """
    
    try:
        # Check if page already exists and is working
        if frappe.db.exists("Page", "quality_dashboard"):
            try:
                # Test if existing page is properly configured
                page = frappe.get_doc("Page", "quality_dashboard")
                if page.title and len(page.roles) > 0:
                    print("Quality Dashboard page already exists and is properly configured")
                    return
                else:
                    # Page exists but not properly configured, delete and recreate
                    frappe.delete_doc("Page", "quality_dashboard", force=True, ignore_permissions=True)
            except Exception:
                # Page record corrupted, force delete
                frappe.db.sql("DELETE FROM `tabPage` WHERE name = 'quality_dashboard'")
                frappe.db.commit()
        
        # Create the Quality Dashboard page
        page = frappe.new_doc("Page")
        page.name = "quality_dashboard"
        page.title = "Quality Dashboard"
        page.page_name = "quality_dashboard"
        page.module = "ERPNext TrackerX Customization"
        page.standard = "No"
        page.system_page = 0
        
        # Add required roles
        required_roles = [
            "Quality Inspector",
            "Quality Manager", 
            "System Manager",
            "Administrator"
        ]
        
        for role_name in required_roles:
            if frappe.db.exists("Role", role_name):
                page.append("roles", {"role": role_name})
        
        # Insert the page
        page.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print("✅ Quality Dashboard page created successfully via migration")
        
    except Exception as e:
        print(f"❌ Error creating Quality Dashboard page: {str(e)}")
        # Don't raise exception to prevent migration failure
        frappe.log_error(f"Quality Dashboard page creation failed: {str(e)}")