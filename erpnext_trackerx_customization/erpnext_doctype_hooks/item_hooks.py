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
        return "1=1" # do not restrict if the role doesnt have any item types (empty)


## ITS PART OF BELOW autonam_item method now
# def set_item_code_before_insert(doc, method):
#     """
#     Auto-generate item_code before validation
#     Only runs for new documents
#     """
#     frappe.log_error(f"before_insert hook called for Item: {doc.name}", "Item Code Generation")

#     if not doc.custom_select_master:
#         frappe.throw("custom_select_master is required to generate item_code")

#     doc.item_code = generate_item_code(doc)


def autoname(doc, method=None):
    if doc.get("custom_manual_item_code"):
        if not doc.item_code:
            frappe.throw("Item Code is mandatory when 'Manual Item Code' is enabled.")
        doc.name = doc.item_code
    else:
        try:
            doc.item_code = generate_item_code(doc)
        except Exception as e:
            frappe.log_error(f"Item autoname error: {str(e)}", "Item autoname")
            frappe.throw(f"Failed to generate item code: {str(e)}")
        doc.name = doc.item_code


def generate_item_code(doc):
    """
    Generate item_code with custom logic.
    For 'Fabrics', include standard fields + GSM, Width, and Finish.
    For 'Yarns', use: Y-{count}-{type}-{shade}
    """
    master = doc.custom_select_master
    prefix_map = {
        "Finished Goods": "FG",
        "Fabrics": "FAB",
        "Trims": "TRM",
        "Accessories": "ACC",
        "Labels": "LBL",
        "Machines": "MC",
        "Packing Materials": "PM",
        "Spare Parts": "SP",
        "Semi Finished Goods": "SFG",
        "Yarns": "YRN"
    }

    prefix = prefix_map.get(master)
    if not prefix:
        prefix = "ITEM"

    # Special handling for Yarns
    if master == "Yarns":
        yarn_count = str(doc.custom_yarn_count).strip() if doc.custom_yarn_count else ""
        yarn_type = str(doc.custom_yarn_type).strip() if doc.custom_yarn_type else ""
        # Handle Yarn Shade (Link to Colour Master)
        yarn_shade = ""
        if doc.custom_yarn_shade:
            try:
                shade_doc = frappe.get_doc("Colour Master", doc.custom_yarn_shade)
                yarn_shade = shade_doc.colour_name or shade_doc.name  # Use 'colour_name' field as title
            except Exception as e:
                frappe.log_error(f"Error fetching Colour Master: {doc.custom_yarn_shade}", "Yarn Code Generation")
                yarn_shade = doc.custom_yarn_shade  # fallback to name

        parts = [prefix]
        if yarn_count:
            parts.append(yarn_count)
        if yarn_type:
            parts.append(yarn_type)
        if yarn_shade:
            parts.append(yarn_shade)

        base_code = "-".join(parts)
    else:
        # === Original logic for all other types ===
        # Format item_group conditionally
        item_group = doc.item_group or ""
        item_group_code = ""

        is_machine = master == 'Machines'
        is_spare_parts = master == 'Spare Parts'
        is_fabrics = master == 'Fabrics'

        if item_group:
            if master == "Accessories":
                item_group_code = item_group  # full name
            else:
                words = item_group.split()
                if len(words) == 1:
                    item_group_code = words[0][:3].upper()
                else:
                    item_group_code = ''.join(word[0].upper() for word in words)

        # Standard fields (used for most types, including Fabrics)
        item_name = doc.item_name or ""
        color_name = doc.custom_colour_name or ""
        color_code = doc.custom_colour_code or ""

        # Machine / Spare Parts fields
        machine_type = doc.custom_machineequipment_type or ''
        machine_model_no = doc.custom_model_no or ''
        sp_category = doc.custom_spare_part_category or ''
        sp_type = doc.custom_spare_part_type or ''

        # Fabric-specific fields (only used when master == 'Fabrics')
        fabric_width = str(doc.custom_width).strip() if doc.custom_width else ""
        fabric_gsm = str(doc.custom_gsm).strip() if doc.custom_gsm else ""
        fabric_finish = str(doc.custom_type_of_finish).strip() if doc.custom_type_of_finish else ""

        # Build parts list
        if item_group_code == prefix:
            prefix = ""
            parts = []
        else:
            parts = [prefix]

        if is_machine or is_spare_parts:
            if machine_type:
                parts.append(machine_type)
            if machine_model_no:
                parts.append(machine_model_no)
            if sp_category:
                parts.append(sp_category)
            if sp_type:
                parts.append(sp_type)

        else:
            # This block now includes Fabrics AND other standard types
            if item_group_code:
                parts.append(item_group_code)
            if item_name:
                parts.append(item_name)
            if color_name:
                parts.append(color_name)
            if color_code:
                parts.append(color_code)

            # ➕ Extra: Append fabric specs ONLY for Fabrics
            if is_fabrics:
                fabric_attrs = [fabric_width, fabric_gsm, fabric_finish]
                fabric_attrs = [attr for attr in fabric_attrs if attr]  # skip empty
                if fabric_attrs:
                    parts.append("-".join(fabric_attrs))

        base_code = "-".join(parts)

    # Get next sequence number
    last_doc = frappe.db.sql("""
        SELECT item_code FROM `tabItem`
        WHERE custom_select_master = %s
        ORDER BY creation DESC LIMIT 1
    """, master, as_dict=True)

    if last_doc:
        item_code_parts = last_doc[0].item_code.rsplit('-', 1)
        if len(item_code_parts) > 1 and item_code_parts[1].isdigit():
            last_seq = int(item_code_parts[1])
        else:
            last_seq = 0
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"{base_code}-{next_seq:06d}"


def validate_item(doc, method):
    if doc.custom_select_master == "Yarns":
        if not doc.custom_yarn_count:
            frappe.throw("Yarn Count is required for Yarn items.")
        if not doc.custom_yarn_type:
            frappe.throw("Yarn Type is required for Yarn items.")
        # Shade can be optional if business allows


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
