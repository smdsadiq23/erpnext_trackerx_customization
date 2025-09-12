import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def save_process_map(map_name, process_map_number, select_fg, nodes, edges, description=None):
    # Create new Process Map document
    doc = frappe.get_doc({
        "doctype": "Process Map",
        "process_map_number": process_map_number,   # ✅ mandatory field
        "map_name": map_name,
        "select_fg": select_fg,                     # ✅ mandatory field
        "nodes": nodes,                             # JSON string of nodes
        "edges": edges,                             # JSON string of edges
        "description": description or ""
    })
    
    doc.insert(ignore_permissions=True)
    return {"message": "Map saved", "docname": doc.name}
