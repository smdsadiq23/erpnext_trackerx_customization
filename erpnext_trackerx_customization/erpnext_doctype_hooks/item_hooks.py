# apps/erpnext_trackerx_customization/erpnext_trackerx_customization/item_hooks.py

import frappe
from erpnext_trackerx_customization.utils.constants import get_constants 

def get_item_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    constants = get_constants()

    role_map = constants.get("item_master_role_map", {})
    item_types_allowed = set()

    # Build a set of allowed item types based on role match
    for item_type, roles in role_map.items():
        if any(role in roles for role in user_roles):
            item_types_allowed.add(item_type)
    

    # Allow System Manager or Administrator to bypass
    if "System Manager" in user_roles or "Administrator" in user_roles:
        frappe.log_error("Item Permission Check", "System Manager/Administrator – full access allowed.")
        return ""

    # Build SQL conditions for allowed item types
    if item_types_allowed:
        formatted = "', '".join(item_types_allowed)
        condition = f"`tabItem`.`custom_select_master` IN ('{formatted}')"
        frappe.log_error("Item Permission Check", f"Filtered items where custom_select_master in: {item_types_allowed}")
        return condition
    else:
        frappe.log_error("Item Permission Check", "No matching roles found — access restricted (1=0)")
        return "1=0"


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
        "Accessories": "ACC",
        "Lables": "LBL",
        "Machines": "MC",
        "Packing Materials": "PCK_MTL"
    }

    prefix = prefix_map.get(master)
    if not prefix:
        #frappe.throw(f"Invalid custom_select_master value: {master}")
        prefix = "ITEM"

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
