import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def save_process_map(map_name, process_map_number, select_fg, nodes, edges, description=None):
    """
    Save or update a Process Map.
    - If a map with the given map_name already exists → update it.
    - Otherwise → insert a new one.
    """
    try:
        # Input validation
        if not map_name:
            frappe.throw(_("Map name is required"))
        if not process_map_number:
            frappe.throw(_("Process map number is required"))
        if not select_fg:
            frappe.throw(_("Finished goods item selection is required"))
        if not nodes:
            frappe.throw(_("Process map nodes are required"))
        if not edges:
            frappe.throw(_("Process map edges are required"))

        # Validate JSON data
        try:
            import json
            if isinstance(nodes, str):
                json.loads(nodes)
            if isinstance(edges, str):
                json.loads(edges)
        except json.JSONDecodeError as e:
            frappe.throw(_("Invalid JSON data in nodes or edges: {0}").format(str(e)))

        existing = frappe.db.exists("Process Map", {"map_name": map_name})

        if existing:
            # Update existing map
            doc = frappe.get_doc("Process Map", existing)
            doc.process_map_number = process_map_number
            doc.select_fg = select_fg
            doc.nodes = nodes
            doc.edges = edges
            doc.description = description or ""
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            return {"success": True, "message": "Map updated successfully", "docname": doc.name}
        else:
            # Create new map
            doc = frappe.get_doc({
                "doctype": "Process Map",
                "process_map_number": process_map_number,
                "map_name": map_name,
                "select_fg": select_fg,
                "nodes": nodes,
                "edges": edges,
                "description": description or ""
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return {"success": True, "message": "Map saved successfully", "docname": doc.name}

    except Exception as e:
        frappe.log_error(f"Error saving process map: {str(e)}", "Process Map Save Error")
        return {"success": False, "message": str(e)}
