import frappe

def create_process_map_doctype():
    module = "ERPNext TrackerX Customization"  # change to your module

    doctype = {
        "doctype": "DocType",
        "name": "Process Map",
        "module": module,
        "custom": 1,
        "fields": [
            {"fieldname": "map_name", "fieldtype": "Data", "label": "Map Name", "reqd": 1},
            {"fieldname": "description", "fieldtype": "Small Text", "label": "Description"},
            {"fieldname": "nodes", "fieldtype": "Long Text", "label": "Nodes (JSON)", "description": "Stores nodes from React Flow"},
            {"fieldname": "edges", "fieldtype": "Long Text", "label": "Edges (JSON)", "description": "Stores connections between nodes"}
        ],
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}
        ]
    }

    if not frappe.db.exists("DocType", doctype["name"]):
        doc = frappe.get_doc(doctype)
        doc.insert()
        frappe.db.commit()
        print("✅ Created DocType: Process Map")
    else:
        print("⚡ Process Map DocType already exists")


def run():
    create_process_map_doctype()
