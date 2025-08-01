import frappe
from frappe.utils import nowdate
from frappe import _

# --- 1. On GRN submit: create MIR and Fabric Rolls ---
def on_submit_grn(doc, method):
    """Create MIR and Fabric Rolls when GRN is submitted"""
    try:
        # 1. Create Material Inspection Report
        mir = frappe.new_doc("Material Inspection Report")
        mir.goods_receipt_note = doc.name
        mir.supplier = doc.supplier
        mir.inspection_status = "Pending"
        
        for item in doc.items:
            mir_item = mir.append("mir_items", {
                "item_code": item.item_code,
                "uom": item.uom,
                "received_quantity": item.received_quantity,
                "accepted_qty": item.received_quantity,  # Default all accepted
                "rejected_qty": 0,
                "material_type": item.material_type,
                "accepted_warehouse": item.accepted_warehouse or doc.set_warehouse
            })
            
            # Copy additional fields if they exist
            for field in ["color", "composition", "roll_no", "fabric_length", 
                         "fabric_width", "shade", "batch_no", "lot_no", "remarks"]:
                if hasattr(item, field):
                    setattr(mir_item, field, getattr(item, field))

            # Create Fabric Roll for fabric items
            if (item.material_type or "").lower() in ["fabric", "fabrics"]:
                create_fabric_roll(doc, item, mir.name)

        mir.insert(ignore_permissions=True)
        frappe.msgprint(_("Material Inspection Report {0} created").format(mir.name))
        
    except Exception as e:
        frappe.log_error(_("GRN Submit Error"), f"GRN: {doc.name}\nError: {str(e)}")
        frappe.throw(_("Failed to create MIR. See error log for details."))

def create_fabric_roll(grn_doc, item, mir_name=None):
    """Create Fabric Roll document"""
    try:
        roll = frappe.new_doc("Fabric Roll")
        roll.update({
            "item_code": item.item_code,
            "supplier": grn_doc.supplier,
            "width": item.fabric_width,
            "length": item.fabric_length,
            "shade_code": item.shade,
            "lot_no": item.lot_no,
            "inspection_status": "Pending",
            "current_warehouse": item.accepted_warehouse or grn_doc.set_warehouse,
            "grn": grn_doc.name,
            "mir": mir_name
        })
        roll.insert(ignore_permissions=True)
        return roll.name
    except Exception as e:
        frappe.log_error(_("Fabric Roll Creation Error"), f"Item: {item.item_code}\nError: {str(e)}")
        raise e

# --- 2. On MIR submit: update rolls, generate PR ---
def on_submit_mir(doc, method):
    """Handle MIR submission workflow"""
    try:
        validate_mir_items(doc)
        update_mir_status(doc)
        update_fabric_rolls(doc)
        create_purchase_receipt(doc)
    except Exception as e:
        frappe.log_error(_("MIR Submit Error"), f"MIR: {doc.name}\nError: {str(e)}")
        raise

def validate_mir_items(doc):
    """Validate MIR items before submission"""
    for item in doc.mir_items:
        if (item.accepted_qty or 0) + (item.rejected_qty or 0) != item.received_quantity:
            frappe.throw(_("Row {0}: Accepted + Rejected must equal Received Quantity").format(item.idx))

def update_mir_status(doc):
    """Update MIR status based on inspection results"""
    all_accepted = all(item.accepted_qty == item.received_quantity for item in doc.mir_items)
    all_rejected = all(item.rejected_qty == item.received_quantity for item in doc.mir_items)
    
    doc.inspection_status = "Accepted" if all_accepted else \
                           "Rejected" if all_rejected else "Partial"
    doc.save(ignore_permissions=True)

def update_fabric_rolls(doc):
    """Update Fabric Roll status based on MIR results"""
    for item in doc.mir_items:
        if (item.material_type or "").lower() in ["fabric", "fabrics"]:
            status = "Passed" if item.accepted_qty == item.received_quantity else \
                    "Rejected" if item.rejected_qty == item.received_quantity else "Partial"
            
            frappe.db.sql("""
                UPDATE `tabFabric Roll`
                SET inspection_status = %s, mir = %s
                WHERE grn = %s AND item_code = %s
                AND ifnull(lot_no,'') = %s AND ifnull(shade_code,'') = %s
            """, (status, doc.name, doc.goods_receipt_note, item.item_code, 
                 item.lot_no or '', item.shade or ''))

# def create_purchase_receipt(doc):
#     """Create Purchase Receipt from accepted items in MIR"""
#     grn_doc = frappe.get_doc("Goods Receipt Note", doc.goods_receipt_note)
    
#     try:
#         pr = frappe.new_doc("Purchase Receipt")
#         pr.update({
#             "supplier": grn_doc.supplier,
#             "company": grn_doc.company,
#             "posting_date": nowdate(),
#             "set_posting_time": 1,
#             "linked_grn": grn_doc.name,
#             "linked_mir": doc.name,
#             "set_warehouse": grn_doc.set_warehouse or get_default_warehouse()
#         })

#         # Add accepted items
#         for item in doc.mir_items:
#             if item.accepted_qty > 0:
#                 pr.append("items", {
#                     "doctype": "Purchase Receipt Item",
#                     "item_code": item.item_code,
#                     "qty": item.accepted_qty,
#                     "uom": item.uom,
#                     "rate": get_grn_item_rate(grn_doc, item.item_code),
#                     "warehouse": item.accepted_warehouse or pr.set_warehouse,
#                     "batch_no": item.batch_no,
#                     "lot_no": item.lot_no
#                 })

#         # Add rejected items if table exists
#         if frappe.db.exists("DocType", "Purchase Receipt Rejected Item"):
#             for item in doc.mir_items:
#                 if item.rejected_qty > 0:
#                     pr.append("rejected_items", {
#                         "doctype": "Purchase Receipt Rejected Item",
#                         "item_code": item.item_code,
#                         "qty": item.rejected_qty,
#                         "mir": doc.name,
#                         "reason": item.reason_for_rejection
#                     })

#         pr.flags.ignore_permissions = True
#         pr.insert()
#         pr.submit()
        
#         # Update Fabric Rolls with PR reference
#         frappe.db.sql("""
#             UPDATE `tabFabric Roll`
#             SET linked_purchase_receipt = %s
#             WHERE mir = %s
#         """, (pr.name, doc.name))
        
#         frappe.msgprint(_("Purchase Receipt {0} created").format(pr.name))
        
#     except Exception as e:
#         frappe.log_error(_("PR Creation Error"), f"MIR: {doc.name}\nError: {str(e)}")
#         raise

def create_purchase_receipt(doc):
    """Create Purchase Receipt from accepted items in MIR"""
    grn_doc = frappe.get_doc("Goods Receipt Note", doc.goods_receipt_note)
    pr = frappe.new_doc("Purchase Receipt")
    pr.supplier = grn_doc.supplier
    pr.company = grn_doc.company
    pr.posting_date = nowdate()
    pr.set_posting_time = 1
    pr.linked_grn = grn_doc.name
    pr.linked_mir = doc.name   # Link field!
    pr.set_warehouse = grn_doc.set_warehouse or get_default_warehouse()

    # Main PR Items (Accepted)
    for item in doc.mir_items:
        if item.accepted_qty > 0:
            pr.append("items", {
                "item_code": item.item_code,
                "qty": item.accepted_qty,
                "uom": item.uom,
                "rate": get_grn_item_rate(grn_doc, item.item_code),
                "warehouse": item.accepted_warehouse or pr.set_warehouse,
                # "batch_no": item.batch_no,
                # "lot_no": item.lot_no
            })

    # Rejected Items
    if frappe.db.exists("DocType", "Purchase Receipt Rejected Item"):
        for item in doc.mir_items:
            if item.rejected_qty > 0:
                pr.append("rejected_items", {
                    "item_code": item.item_code,
                    "qty": item.rejected_qty,
                    "mir": doc.name,
                    "reason": getattr(item, "reason_for_rejection", "") or ""
                })

    pr.flags.ignore_permissions = True
    pr.insert()

    # Update Fabric Roll PR ref
    frappe.db.sql("""
        UPDATE `tabFabric Roll`
        SET linked_purchase_receipt = %s
        WHERE mir = %s
    """, (pr.name, doc.name))

    frappe.msgprint(_("Purchase Receipt {0} created").format(pr.name))


# --- GRN Cancellation Handlers ---
def before_cancel_grn(doc, method):
    """Validate if GRN can be cancelled"""
    check_processed_mirs(doc.name)
    check_submitted_prs(doc.name)

def on_cancel_grn(doc, method):
    """Handle GRN cancellation cleanup"""
    cancel_linked_documents(doc.name)
    cleanup_fabric_rolls(doc.name)
    frappe.db.set_value("Goods Receipt Note", doc.name, "status", "Cancelled")
    frappe.msgprint(_("GRN {0} cancelled successfully").format(doc.name))

def check_processed_mirs(grn_name):
    """Check for processed MIRs"""
    if frappe.db.exists("Material Inspection Report", {
        "goods_receipt_note": grn_name,
        "docstatus": 1,
        "inspection_status": ["!=", "Pending"]
    }):
        frappe.throw(_("Cannot cancel GRN with processed MIRs"))

def check_submitted_prs(grn_name):
    """Check for submitted PRs"""
    prs = frappe.db.sql("""
        SELECT pr.name 
        FROM `tabPurchase Receipt` pr
        JOIN `tabMaterial Inspection Report` mir ON pr.linked_mir = mir.name
        WHERE mir.goods_receipt_note = %s AND pr.docstatus = 1
    """, grn_name)
    
    if prs:
        frappe.throw(_("Cannot cancel GRN with submitted Purchase Receipts"))

def cancel_linked_documents(grn_name):
    """Cancel all linked MIRs and PRs"""
    # Cancel MIRs first
    for mir in frappe.get_all("Material Inspection Report", 
                            {"goods_receipt_note": grn_name, "docstatus": 1}):
        mir_doc = frappe.get_doc("Material Inspection Report", mir.name)
        mir_doc.cancel()
    
    # PRs should be cancelled automatically via MIR cancellation

def cleanup_fabric_rolls(grn_name):
    """Delete Fabric Rolls linked to GRN"""
    frappe.db.sql("DELETE FROM `tabFabric Roll` WHERE grn = %s", grn_name)

# --- Helper Functions ---
def get_grn_item_rate(grn_doc, item_code):
    """Get item rate from GRN"""
    for item in grn_doc.items:
        if item.item_code == item_code:
            return item.rate
    return 0

def get_default_warehouse():
    """Get default warehouse from Stock Settings"""
    return frappe.db.get_single_value("Stock Settings", "default_warehouse") or _("Stores")

# --- API Endpoints ---
@frappe.whitelist()
def create_mir_for_grn(grn_name):
    """API endpoint to create MIR for GRN"""
    grn_doc = frappe.get_doc("Goods Receipt Note", grn_name)
    on_submit_grn(grn_doc, None)
    return True