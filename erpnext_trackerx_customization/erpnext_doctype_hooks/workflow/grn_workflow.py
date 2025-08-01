import frappe

def on_submit_grn(doc, method):
    """
    For every item in GRN:
    - Create Material Inspection Report (MIR)
    - If Fabric, create Fabric Roll and link to MIR
    """
    for item in doc.items:
        # Create MIR
        mir = frappe.new_doc("Material Inspection Report")
        mir.grn = doc.name
        mir.grn_item = item.name
        mir.item_code = item.item_code
        mir.qty = item.qty
        mir.supplier = doc.supplier
        mir.status = "Draft"
        mir.save(ignore_permissions=True)

        # If item is Fabric, create Fabric Roll
        item_group = frappe.db.get_value("Item", item.item_code, "item_group")
        if item_group and item_group.lower() == "fabric":
            roll = frappe.new_doc("Fabric Roll")
            roll.item_code = item.item_code
            roll.supplier = doc.supplier
            roll.length = item.qty
            roll.width = getattr(item, "width", None)
            roll.grn = doc.name
            roll.mir = mir.name
            roll.status = "Pending Inspection"
            roll.save(ignore_permissions=True)
    frappe.msgprint("Inspection Reports (and Fabric Rolls for fabric) have been created.")



def on_submit_mir(doc, method):
    """
    After all MIRs for a GRN are submitted:
    - Create Purchase Receipt, split accepted/rejected
    """
    grn = doc.grn
    if not grn:
        return
    # Check if all MIRs for this GRN are submitted
    mirs = frappe.get_all("Material Inspection Report", filters={"grn": grn}, fields=["name", "docstatus"])
    if not mirs or any(m['docstatus'] != 1 for m in mirs):
        return  # Wait until all are submitted

    grn_doc = frappe.get_doc("Goods Receipt Note", grn)
    pr = frappe.new_doc("Purchase Receipt")
    pr.supplier = grn_doc.supplier
    pr.company = grn_doc.company
    pr.linked_grn = grn_doc.name
    pr.posting_date = frappe.utils.nowdate()

    for mir_row in mirs:
        mir_doc = frappe.get_doc("Material Inspection Report", mir_row["name"])
        if mir_doc.accepted_qty and mir_doc.accepted_qty > 0:
            pr.append("items", {
                "item_code": mir_doc.item_code,
                "qty": mir_doc.accepted_qty,
                "rate": get_purchase_rate_from_grn_item(grn_doc, mir_doc.grn_item),
                "mir": mir_doc.name,
                "grn": grn_doc.name,
            })
        if mir_doc.rejected_qty and mir_doc.rejected_qty > 0:
            pr.append("rejected_items", {
                "item_code": mir_doc.item_code,
                "qty": mir_doc.rejected_qty,
                "mir": mir_doc.name,
                "reason": mir_doc.remarks or ""
            })
    pr.insert(ignore_permissions=True)
    frappe.msgprint(f"Purchase Receipt {pr.name} created from GRN {grn_doc.name} and all MIRs.")

def get_purchase_rate_from_grn_item(grn_doc, grn_item_name):
    for item in grn_doc.items:
        if item.name == grn_item_name:
            return getattr(item, "rate", 0)
    return 0
