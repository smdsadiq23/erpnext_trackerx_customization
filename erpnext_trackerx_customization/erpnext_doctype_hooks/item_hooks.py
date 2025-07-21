# apps/customize_erpnext_app/customize_erpnext_app/item_hooks.py

import frappe

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

    finished_goods_roles = ["Finished Goods Manager", "Finished Goods", "FG Manager", "Finished Goods User", "FG User", "FG Supervisor", "Finished Goods Supervisor", "Style Master", "Style User", "Style Manager", "Style User", "Style Master Manager"]
    fabrics_roles = ["Fabrics Manager", "Fabrics", "Fabrics Supervisor", "Fabrics User","Fabric Manager", "Fabric", "Fabric Supervisor", "Fabric User", "Fabrics Master"]
    trims_roles = ["Trims Manager", "Trims", "Trims Supervisor", "Trims User", "Trims Master"]
    accessories_roles = ["Accessories Manager", "Accessories", "Accessories Supervisor", "Accessories User", "Accessories Master"]
    machine_roles = ["Machine Manager", "Machine", "Machine User", "Machine Supervisor", "Machine Master"]



    # Rule 1: Finished Goods Manager sees only 'Finished Goods'
    if any(role in finished_goods_roles for role in user_roles):
        conditions.append("`tabItem`.`custom_select_master` = 'Style'")
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

def set_item_code_before_insert(doc, method):
    """
    Auto-generate item_code before validation
    Only runs for new documents
    """
    frappe.log_error(f"before_insert hook called for Item: {doc.name}", "Item Code Generation")

    if not doc.custom_select_master:
        frappe.throw("custom_select_master is required to generate item_code")

    doc.item_code = generate_item_code(doc)



def generate_item_code(doc):
    """
    Your custom logic to generate item_code
    """
    master = doc.custom_select_master
    prefix_map = {
        "Style": "FG",
        "Fabrics": "FAB",
        "Trims": "TRM",
        "Accessories": "ACC"
    }

    prefix = prefix_map.get(master)
    if not prefix:
        frappe.throw(f"Invalid custom_select_master value: {master}")

    # Format item_group conditionally
    item_group = doc.item_group or ""
    item_group_code = ""

    if item_group:
        if master == "Accessories":
            # Use full item_group name for Accessories
            item_group_code = item_group
        else:
            # Use abbreviation for other types
            words = item_group.split()
            if len(words) == 1:
                item_group_code = words[0][:3].upper()
            else:
                item_group_code = ''.join([word[0].upper() for word in words])

    item_name = doc.item_name or ""
    color_name = doc.custom_colour_name or ""
    color_code = doc.custom_colour_code or ""

    parts = [prefix]
    if item_group_code:
        parts.append(item_group_code)
    if item_name:
        parts.append(item_name)
    if color_name:
        parts.append(color_name)
    if color_code:
        parts.append(color_code)

    base_code = "-".join(parts)

    # Get next sequence number
    last_doc = frappe.db.sql("""
        SELECT item_code FROM `tabItem`
        WHERE custom_select_master = %s
        ORDER BY creation DESC LIMIT 1
    """, master, as_dict=True)

    if last_doc:
        last_seq = int(last_doc[0].item_code.rsplit('-', 1)[1])
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"{base_code}-{next_seq:06d}"

def validate_item(doc, method):
    if doc.custom_select_master == "Style":
        validate_for_fg_components(doc, method)


def validate_for_fg_components(doc, method):
    components = doc.custom_fg_components or []

    # 1. At least one row should be present
    if not components:
        frappe.throw("At least one FG Component must be added.")

    # Mapping
    leaf_rows = set()
    parent_map = {}
    main_found = None
    fg_root_found = None
    parent_references = set()

    # Build maps
    for row in components:
        parent_map[row.name] = row.parent_component
        if row.parent_component:
            parent_references.add(row.parent_component)

    # 2. Only one row should have parent_component as None (FG root)
    roots = [row for row in components if not row.parent_component]
    if len(roots) != 1:
        frappe.throw("Exactly one FG Component must have no parent (i.e., the Finished Good root).")

    fg_root = roots[0]
    fg_root_found = fg_root.name

    # 4.a FG (root) must have tracking_required = True
    if not fg_root.tracking_required:
        frappe.throw("FG Component (root without parent) must have Tracking Required checked.")

    # Identify leaves (those not parent of any other)
    for row in components:
        if row.name not in parent_references:
            leaf_rows.add(row.name)

    # 3. Only one component can be marked as main
    mains = [row for row in components if row.is_main_component]
    if len(mains) != 1:
        frappe.throw("Exactly one FG Component must be marked as Main Component.")

    main_row = mains[0]

    # 3.a Main must be a leaf
    if main_row.name in parent_references:
        frappe.throw("Main Component must be a leaf component (cannot have children).")

    # 4.b Main must have tracking_required = True
    if not main_row.tracking_required:
        frappe.throw("Main Component must have Tracking Required checked.")

    # 4.c For any leaf with tracking_required = True, all ancestors must also have it
    name_to_row = {row.name: row for row in components}

    for row in components:
        if row.name in leaf_rows and row.tracking_required:
            current = row
            visited = set()
            while current.parent_component:
                if current.parent_component in visited:
                    frappe.throw("Cycle detected in parent_component references.")
                visited.add(current.parent_component)

                parent = name_to_row.get(current.parent_component)
                if not parent:
                    frappe.throw(f"Parent component '{current.parent_component}' not found.")
                if not parent.tracking_required:
                    frappe.throw(f"Tracking Required must be checked for all ancestors of leaf component '{row.component_name}'.")
                current = parent
