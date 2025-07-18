# apps/customize_erpnext_app/customize_erpnext_app/item_group_hooks.py

import frappe
from frappe import _

# Define the list of protected Item Group names that should not be deleted
PROTECTED_ITEM_GROUPS = ["All Item Groups","Trims","Raw Materials","Fabrics","Knitted Fabrics","Single Jersey","Rib Knit","Interlock","Pique Knit","Fleece","Jacquard Knit","Mesh Knit","French Terry","Finished Goods"]

def prevent_item_group_deletion(doc, method):
    """
    This function is hooked to the 'before_delete' event of the Item Group DocType.
    It checks if the Item Group being deleted is one of the protected groups.
    If it is, it raises a PermissionError to prevent the deletion.
    """
    frappe.log_error("Item Group Deletion Check", f"Attempting to delete Item Group: {doc.name}")

    if doc.name in PROTECTED_ITEM_GROUPS:
        frappe.throw(_(f"Deletion of Item Group '{doc.name}' is not allowed as it is a protected system group."),
                     frappe.PermissionError)
    else:
        frappe.msgprint(_(f"Item Group '{doc.name}' is allowed to be deleted."))




def get_item_permission_query_conditions(user):
    """
    Applies row-level security for the Item DocType based on user roles
    and the 'custom_select_master' field.

    Args:
        user (str): The username of the currently logged-in user.

    Returns:
        str: A SQL WHERE clause fragment to filter Item records,
             or an empty string if no additional filtering is needed.
    """
    if not user:
        user = frappe.session.user

    # Get roles of the current user
    user_roles = frappe.get_roles(user)
    frappe.log_error("Item Permission Check", f"User: {user}, Roles: {user_roles}")

    conditions = []

    finished_goods_roles = ["Finished Goods Manager", "Finished Goods", "FG Manager", "Finished Goods User", "FG User", "FG Supervisor", "Finished Goods Supervisor"]
    fabrics_roles = ["Fabrics Manager", "Fabrics", "Fabrics Supervisor", "Fabrics User","Fabric Manager", "Fabric", "Fabric Supervisor", "Fabric User"]
    trims_roles = ["Trims Manager", "Trims", "Trims Supervisor", "Trims User"]
    accessories_roles = ["Accessories Manager", "Accessories", "Accessories Supervisor", "Accessories User"]
    machine_roles = ["Machine Manager", "Machine", "Machine User", "Machine Supervisor"]



    # Rule 1: Finished Goods Manager sees only 'Finished Goods'
    if any(role in finished_goods_roles for role in user_roles):
        conditions.append("`tabItem`.`custom_select_master` = 'Finished Goods'")
        frappe.log_error("Item Permission Check", "Applied filter for Finished Goods Manager.")

    # Rule 2: Fabrics Manager sees only 'Fabrics' (Example, add if you have this role)
    if any(role in fabrics_roles for role in user_roles):
        conditions.append("`tabItem`.`custom_select_master` = 'Fabrics'")

    # Rule 3: Trims Manager sees only 'Trims' (Example)
    if any(role in trims_roles for role in user_roles):
        conditions.append("`tabItem`.`custom_select_master` = 'Trims'")

    # Rule 4: Machine Manager sees only 'Machine' (Example)
    if any(role in machine_roles for role in user_roles):
        conditions.append("`tabItem`.`custom_select_master` = 'Machine'")

    # Rule 5: Accessories Manager sees only 'Accessories' (Example)
    if any(role in accessories_roles for role in user_roles):
        conditions.append("`tabItem`.`custom_select_master` = 'Accessories'")



    # Add more rules for other specific roles and custom_select_master values

    # Important: If a user has a role that should see ALL items (e.g., System Manager, Administrator)
    # then we should return an empty string to not apply any additional filter.
    # This check should typically come *after* specific role checks.
    if "System Manager" in user_roles or "Administrator" in user_roles:
        frappe.log_error("Item Permission Check", "System Manager/Administrator - No additional filter applied.")
        return ""

    # Combine all applicable conditions with 'AND'
    if conditions:
        # Use ' AND ' to combine multiple conditions.
        # Ensure the table name is explicitly mentioned for custom fields if they exist on standard DocTypes.
        # `tabItem` is the standard table name for the Item DocType.
        return " AND ".join(conditions)
    else:
        # If no specific role-based filter applies, you might want to:
        # 1. Return "" to show all items (if default permission allows)
        # 2. Return "1=0" to show no items (if no specific permission is granted)
        # For now, let's return "" to allow standard role permissions to take over.
        # If you want to restrict access to *only* those with specific roles,
        # you might return "1=0" here.
        frappe.log_error("Item Permission Check", "No specific role-based filter applied. Returning empty string.")
        return ""
