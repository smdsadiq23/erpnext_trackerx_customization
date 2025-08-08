import frappe

def insert_sampling_plan():
    plan = frappe.get_doc({
        "doctype": "Sampling Plan",
        "title": "ANSI/ASQ Z1.4 - 2008",
        "description": "Standard sampling plan for inspection by attributes.",
        "is_active": 1
    }).insert(ignore_permissions=True)
    return plan.name

def insert_inspection_levels(plan_name):
    levels = [
        ("General I", "I", "General"),
        ("General II", "II", "General"),
        ("General III", "III", "General"),
        ("Special S1", "S1", "Special"),
        ("Special S2", "S2", "Special"),
        ("Special S3", "S3", "Special"),
        ("Special S4", "S4", "Special")
    ]
    inserted = {}
    for title, code, typ in levels:
        doc = frappe.get_doc({
            "doctype": "Inspection Level",
            "title": title,
            "code": code,
            "inspection_type": typ,
            "sampling_plan": plan_name
        }).insert(ignore_permissions=True)
        inserted[title] = doc.name
    return inserted

def insert_lot_sizes(plan_name, inspection_levels):
    ranges = [
        (2, 8, "A"), (9, 15, "B"), (16, 25, "C"), (26, 50, "D"),
        (51, 90, "E"), (91, 150, "F"), (151, 280, "G"), (281, 500, "H"),
        (501, 1200, "J"), (1201, 3200, "K"), (3201, 10000, "L"), (10001, 35000, "M")
    ]
    for fqty, tqty, code_letter in ranges:
        lot_range = frappe.get_doc({
            "doctype": "Lot Size Range",
            "from_qty": fqty,
            "to_qty": tqty,
            "sampling_plan": plan_name,
            "lot_size_mappings": [
                {
                    "doctype": "Lot Size Inspection Level Mapping",
                    "inspection_level": inspection_levels["General II"],
                    "sample_code_letter": code_letter
                }
            ]
        })
        lot_range.insert(ignore_permissions=True)

def insert_sample_codes(plan_name):
    data = {
        "A": (2, [(0.65, 0, 1), (1.0, 0, 1), (1.5, 0, 1)]),
        "B": (3, [(0.65, 0, 1), (1.0, 0, 1), (1.5, 0, 1)]),
        "C": (5, [(0.65, 0, 1), (1.0, 0, 1), (1.5, 0, 1)]),
        "K": (125, [(0.65, 3, 4), (1.0, 5, 6), (1.5, 7, 8)])
    }
    for code, (size, aqls) in data.items():
        doc = frappe.get_doc({
            "doctype": "Sample Code Definition",
            "code_letter": code,
            "sample_size": size,
            "sampling_plan": plan_name,
            "aql_limits": [
                {
                    "doctype": "AQL Accept Reject Limits",
                    "aql_level": aql,
                    "accept": ac,
                    "reject": rc
                } for aql, ac, rc in aqls
            ]
        })
        doc.insert(ignore_permissions=True)

def run():
    # Create Sampling Plan
    plan_name = insert_sampling_plan()

    # Insert and fetch real Inspection Level names
    inspection_levels = insert_inspection_levels(plan_name)
    frappe.db.commit()

    # Use real Inspection Level names in Lot Size mappings
    insert_lot_sizes(plan_name, inspection_levels)

    # Add Sample Code definitions with AQL limits
    insert_sample_codes(plan_name)

    # Final DB commit
    frappe.db.commit()
