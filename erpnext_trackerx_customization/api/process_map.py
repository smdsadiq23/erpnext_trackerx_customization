import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def save_process_map(map_name, process_map_number, select_fg, nodes, edges, description=None):
    """
    Save or update a Process Map.
    - If a map with the given map_name already exists → update it.
    - Otherwise → insert a new one.
    """
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
        return {"message": "Map updated", "docname": doc.name}
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
        return {"message": "Map saved", "docname": doc.name}
