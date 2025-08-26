import frappe

def create_doctypes():
    def create_if_not_exists(doctype_dict):
        if not frappe.db.exists("DocType", doctype_dict["name"]):
            doc = frappe.get_doc(doctype_dict)
            doc.insert()
            doc.save()
            frappe.db.commit()
            print(f"✅ Created DocType: {doctype_dict['name']}")
        else:
            print(f"⚠️ DocType already exists: {doctype_dict['name']}")

    # Process Type
    create_if_not_exists({
        "doctype": "DocType",
        "name": "Process Type",
        "module": "Custom",
        "custom": 1,
        "fields": [
            {"fieldname": "type_name", "fieldtype": "Data", "label": "Process Type", "reqd": 1},
            {"fieldname": "description", "fieldtype": "Small Text", "label": "Description"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
    })

    # Process Group
    create_if_not_exists({
        "doctype": "DocType",
        "name": "Process Group",
        "module": "Custom",
        "custom": 1,
        "fields": [
            {"fieldname": "group_name", "fieldtype": "Data", "label": "Process Group Name", "reqd": 1},
            {"fieldname": "description", "fieldtype": "Small Text", "label": "Description"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
    })

    # Operation Process (Updated with Process Group)
    create_if_not_exists({
        "doctype": "DocType",
        "name": "Operation Process",
        "module": "Custom",
        "custom": 1,
        "fields": [
            {"fieldname": "process_name", "fieldtype": "Data", "label": "Process Name", "reqd": 1},
            {"fieldname": "process_type", "fieldtype": "Link", "options": "Process Type", "label": "Process Type", "reqd": 1},
            {"fieldname": "process_group", "fieldtype": "Link", "options": "Process Group", "label": "Process Group", "reqd": 1},
            {"fieldname": "description", "fieldtype": "Small Text", "label": "Description"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
    })

    # Stream
    create_if_not_exists({
        "doctype": "DocType",
        "name": "Stream",
        "module": "Custom",
        "custom": 1,
        "fields": [
            {"fieldname": "stream_name", "fieldtype": "Data", "label": "Stream Name", "reqd": 1},
            {"fieldname": "process_group", "fieldtype": "Link", "options": "Process Group", "label": "Process Group (Optional)", "reqd": 0},
            {"fieldname": "description", "fieldtype": "Small Text", "label": "Description"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
    })

    # Stream Process (Child Table)
    create_if_not_exists({
        "doctype": "DocType",
        "name": "Stream Process",
        "module": "Custom",
        "custom": 1,
        "istable": 1,
        "fields": [
            {"fieldname": "operation_process", "fieldtype": "Link", "options": "Operation Process", "label": "Operation Process", "reqd": 1}
        ],
        "permissions": [{"role": "System Manager", "read": 1}]
    })

    # Add Child Table to Stream if not exists
    stream_meta = frappe.get_doc("DocType", "Stream")
    if not any(f.fieldname == "stream_processes" for f in stream_meta.fields):
        stream_meta.append("fields", {
            "fieldname": "stream_processes",
            "fieldtype": "Table",
            "label": "Processes",
            "options": "Stream Process"
        })
        stream_meta.save()
        frappe.db.commit()
        print("✅ Added Stream Process child table to Stream")

    # Process Node Connection
    create_if_not_exists({
        "doctype": "DocType",
        "name": "Process Node Connection",
        "module": "Custom",
        "custom": 1,
        "fields": [
            {"fieldname": "from_process", "fieldtype": "Link", "options": "Operation Process", "label": "From Process", "reqd": 1},
            {"fieldname": "to_process", "fieldtype": "Link", "options": "Operation Process", "label": "To Process", "reqd": 1},
            {"fieldname": "connection_label", "fieldtype": "Data", "label": "Connection Label"},
            {"fieldname": "stream", "fieldtype": "Link", "options": "Stream", "label": "Stream"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
    })

def create():
    create_doctypes()
