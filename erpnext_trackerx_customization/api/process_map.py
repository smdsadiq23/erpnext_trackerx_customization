import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def save_process_map(map_name, nodes, edges, description=None):
    doc = frappe.get_doc({
        "doctype": "Process Map",               # Target DocType
        "map_name": map_name,                   # Custom name field
        "nodes": nodes,                    # Serialized JSON string of all nodes
        "edges": edges,                    # Serialized JSON string of all edges
        "description": description or ""        # Optional description
    })
    
    doc.insert(ignore_permissions=True)         # Save to DB, bypassing user permissions
    return {"message": "Map saved", "docname": doc.name}  # Return success response
