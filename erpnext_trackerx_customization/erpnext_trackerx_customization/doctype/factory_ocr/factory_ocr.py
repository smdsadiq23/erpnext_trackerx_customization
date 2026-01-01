# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict
from frappe.utils import cint, get_url_to_form

FACTORY_MANAGER_ROLE = "Factory Manager"


def _is_factory_manager(user=None) -> bool:
    user = user or getattr(frappe.session, "user", None) or "Guest"
    try:
        return FACTORY_MANAGER_ROLE in (frappe.get_roles(user) or [])
    except Exception:
        return frappe.get_user(user).has_role(FACTORY_MANAGER_ROLE)


def _ensure_factory_manager():
    if not _is_factory_manager():
        frappe.throw(_("Only Factory Manager can approve/reject Factory OCR."))


def _get_factory_manager_users_and_emails():
    """
    Returns:
      - users: list[str]
      - emails: list[str]
    """
    # Users mapped to role are stored in Has Role (parent = User)
    users = frappe.get_all(
        "Has Role",
        filters={"role": FACTORY_MANAGER_ROLE},
        pluck="parent",
    ) or []

    # Filter only enabled system users and collect emails
    if not users:
        return [], []

    user_rows = frappe.get_all(
        "User",
        filters={"name": ["in", users], "enabled": 1},
        fields=["name", "email"],
    ) or []

    enabled_users = [u.name for u in user_rows if u.name]
    emails = list({u.email for u in user_rows if u.email})  # unique emails

    return enabled_users, emails


def _notify_factory_managers_on_pending(doc: Document):
    """
    Send:
      1) In-app notification (Notification Log)
      2) Email
    Trigger condition:
      - called only on after_insert
      - doc.status == "Pending for Approval"
    """
    if (doc.status or "") != "Pending for Approval":
        return

    users, emails = _get_factory_manager_users_and_emails()
    if not users and not emails:
        return

    url = get_url_to_form(doc.doctype, doc.name)
    subject = f"Factory OCR Pending for Approval: {doc.name}"

    buyer = doc.buyer or "-"
    ocn = doc.ocn or "-"
    requester = doc.owner or "-"

    message = f"""
        <p><b>Factory OCR</b> is pending for approval.</p>
        <p>
          <b>ID:</b> {doc.name}<br>
          <b>Buyer:</b> {buyer}<br>
          <b>OCN:</b> {ocn}<br>
          <b>Requested By:</b> {requester}<br>
        </p>
        <p>
          Open: <a href="{url}">{url}</a>
        </p>
    """

    # 1) In-app notifications
    for u in users:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": u,
                "type": "Alert",
                "document_type": doc.doctype,
                "document_name": doc.name
            }).insert(ignore_permissions=True)
        except Exception:
            # don't block creation if notification fails for one user
            frappe.log_error(
                title="Factory OCR Notification Log failed",
                message=frappe.get_traceback()
            )

    # 2) Email notifications
    if emails:
        try:
            frappe.sendmail(
                recipients=emails,
                subject=subject,
                message=message,
                reference_doctype=doc.doctype,
                reference_name=doc.name,
            )
        except Exception:
            frappe.log_error(
                title="Factory OCR Email notification failed",
                message=frappe.get_traceback()
            )


def _freeze_if_locked(doc: Document):
    """
    Blocks edits once doc is in Pending/Approved/Rejected.
    Only allow changes via approve/reject methods (flagged).
    """
    if getattr(doc.flags, "allow_approval_update", False):
        return

    if doc.get("__islocal"):
        return

    if (doc.status or "") not in ("Pending for Approval", "Approved", "Rejected"):
        return

    before = doc.get_doc_before_save()
    if not before:
        return

    # Compare all normal fields + child tables (strict freeze)
    if doc.as_dict(no_nulls=False) != before.as_dict(no_nulls=False):
        frappe.throw(_("This document is locked in '{0}' state. Edits are not allowed.").format(doc.status))


class FactoryOCR(Document):
    def validate(self):
        # Ensure initial flow
        if not self.status or self.status == "Draft":
            self.status = "Pending for Approval"

        _freeze_if_locked(self)

    def after_insert(self):
        # ✅ Send notification + email once the document is created and pending
        _notify_factory_managers_on_pending(self)

    def before_submit(self):
        # If Factory OCR is still marked as Submittable, prevent manual submit completely.
        # (Recommended: turn OFF 'Is Submittable' in DocType to get Can Cut style header badge)
        frappe.throw(_("Manual Submit is not allowed for Factory OCR. Use Approve/Reject only."))


@frappe.whitelist()
def approve(docname, approver_remarks=None, with_replenishment=0):
    _ensure_factory_manager()

    if not docname:
        frappe.throw(_("Missing document name."))

    doc = frappe.get_doc("Factory OCR", docname)

    if (doc.status or "") != "Pending for Approval":
        frappe.throw(_("Only documents in 'Pending for Approval' can be approved."))

    remarks = (approver_remarks or "").strip()
    if not remarks:
        frappe.throw(_("Approver Remarks is mandatory to approve."))

    doc.flags.ignore_permissions = True
    doc.flags.allow_approval_update = True

    doc.status = "Approved"
    doc.approver_remarks = remarks
    doc.with_replenishment = cint(with_replenishment)

    doc.save()
    return {"status": doc.status}


@frappe.whitelist()
def reject(docname, reason=None, with_replenishment=0):
    _ensure_factory_manager()

    if not docname:
        frappe.throw(_("Missing document name."))

    doc = frappe.get_doc("Factory OCR", docname)

    if (doc.status or "") != "Pending for Approval":
        frappe.throw(_("Only documents in 'Pending for Approval' can be rejected."))

    remarks = (reason or "").strip()
    if not remarks:
        frappe.throw(_("Remarks is mandatory to reject."))

    doc.flags.ignore_permissions = True
    doc.flags.allow_approval_update = True

    doc.status = "Rejected"
    doc.approver_remarks = remarks
    doc.with_replenishment = cint(with_replenishment)

    doc.save()
    return {"status": doc.status}


@frappe.whitelist()
def sales_order_query_for_factory_ocr(doctype, txt, searchfield, start, page_len, filters):
    customer = filters.get("customer")
    if not customer:
        return []

    used_ocns = frappe.get_all(
        "Factory OCR",
        filters={"docstatus": ["<", 2], "ocn": ["is", "set"]},
        pluck="ocn"
    )
    used_ocns = tuple(set(used_ocns)) if used_ocns else ("__none__",)

    return frappe.db.sql("""
        SELECT name, customer, transaction_date
        FROM `tabSales Order`
        WHERE docstatus = 1
          AND customer = %(customer)s
          AND name LIKE %(txt)s
          AND name NOT IN %(used_ocns)s
        ORDER BY transaction_date DESC
        LIMIT %(start)s, %(page_len)s
    """, {
        "customer": customer,
        "txt": "%" + txt + "%",
        "used_ocns": used_ocns,
        "start": int(start),
        "page_len": int(page_len)
    })


@frappe.whitelist()
def fetch_sales_order_items_for_factory_ocr(sales_order):
    if not sales_order:
        return []

    so_items = frappe.db.sql("""
        SELECT item_code, custom_color, qty, custom_lineitem
        FROM `tabSales Order Item`
        WHERE parent = %s
    """, (sales_order,), as_dict=1)

    if not so_items:
        return []

    grouped = defaultdict(lambda: {"item_code": "", "custom_color": "", "custom_lineitem": "", "order_qty": 0})
    for row in so_items:
        if not row.item_code:
            continue
        key = f"{row.item_code}||{row.custom_color or ''}||{row.custom_lineitem or ''}"
        grouped[key]["item_code"] = row.item_code
        grouped[key]["custom_color"] = row.custom_color or ""
        grouped[key]["custom_lineitem"] = row.custom_lineitem or ""
        grouped[key]["order_qty"] += row.qty or 0

    unique_styles = list(set(g["item_code"] for g in grouped.values()))

    cut_map = {}
    if unique_styles:
        cut_data = frappe.db.sql("""
            SELECT 
                cd.style,
                cd.color,
                SUM(cci.confirmed_quantity) AS cut_qty
            FROM `tabCut Confirmation Item` cci
            INNER JOIN `tabCut Confirmation` cc 
                ON cci.parent = cc.name AND cc.docstatus = 1
            INNER JOIN `tabCut Docket` cd 
                ON cc.cut_po_number = cd.name AND cd.docstatus = 1
            WHERE cci.sales_order = %s
            GROUP BY cd.style, cd.color
        """, (sales_order,), as_dict=1)
        for d in cut_data:
            color = d.color or ""
            cut_map[f"{d.style}||{color}"] = d.cut_qty or 0

    scan_map = {}
    if unique_styles:
        scan_data = frappe.db.sql("""
            SELECT 
                itm.name AS item_code,
                itm.custom_colour_name AS color,
                COALESCE(SUM(pi.quantity), 0) AS scan_qty
            FROM `tabTracking Order Bundle Configuration` tbc
            INNER JOIN `tabTracking Order` tor
                ON tor.name = tbc.parent
                AND tor.item IS NOT NULL
                AND tor.last_operation IS NOT NULL
            INNER JOIN `tabItem` itm
                ON itm.name = tor.item
            INNER JOIN `tabProduction Item` pi
                ON pi.tracking_order = tor.name
                AND pi.bundle_configuration = tbc.name
            INNER JOIN `tabTracking Component` tc 
                ON tc.name = pi.component AND tc.is_main = 1
            INNER JOIN `tabItem Scan Log` isl
                ON isl.production_item = pi.name
                AND isl.operation = tor.last_operation
                AND isl.log_status = 'Completed'
                AND isl.status IN ('Counted', 'Activated', 'Pass')
            WHERE tbc.sales_order = %s
            GROUP BY itm.name, itm.custom_colour_name
        """, (sales_order,), as_dict=1)
        for d in scan_data:
            color = d.color or ""
            scan_map[f"{d.item_code}||{color}"] = d.scan_qty or 0

    rejection_garments_map = {}
    if unique_styles:
        rejection_data = frappe.db.sql("""
            SELECT 
                itm.name AS item_code,
                itm.custom_colour_name AS color,
                COUNT(isl.name) AS rejected_count
            FROM `tabTracking Order` tor
            INNER JOIN `tabTracking Order Bundle Configuration` tbc
                ON tbc.parent = tor.name
                AND tbc.parentfield = 'component_bundle_configurations'
            INNER JOIN `tabItem` itm
                ON itm.name = tor.item
            INNER JOIN `tabProduction Item` pi
                ON pi.tracking_order = tor.name
                AND pi.bundle_configuration = tbc.name
            INNER JOIN `tabTracking Component` tc 
                ON tc.name = pi.component AND tc.is_main = 1
            INNER JOIN `tabItem Scan Log` isl
                ON isl.production_item = pi.name
                AND isl.status LIKE '%%Reject%%'
            WHERE tor.item IS NOT NULL
              AND tbc.sales_order = %s
            GROUP BY itm.name, itm.custom_colour_name
        """, (sales_order,), as_dict=1)
        for d in rejection_data:
            color = d.color or ""
            rejection_garments_map[f"{d.item_code}||{color}"] = d.rejected_count or 0

    item_style_map = {}
    if unique_styles:
        items = frappe.db.get_all(
            "Item",
            filters={"name": ["in", unique_styles]},
            fields=["name", "custom_style_master"]
        )
        item_style_map = {item.name: item.custom_style_master for item in items}

    result = []
    for group in grouped.values():
        item_code = group["item_code"]
        color = group["custom_color"]
        lineitem = group["custom_lineitem"]
        order_qty = group["order_qty"]
        key = f"{item_code}||{color}"

        cut_qty = cut_map.get(key, 0.0)
        scan_qty = scan_map.get(key, 0.0)
        rejected_garments = float(rejection_garments_map.get(key, 0))

        cut_to_ship_percent = (scan_qty / cut_qty * 100) if cut_qty else 0.0

        result.append({
            "style": item_style_map.get(item_code) or "",
            "colour": color,
            "lineitem": lineitem,
            "order_quantity": order_qty,
            "cut_quantity": frappe.utils.flt(cut_qty, 2),
            "scan_quantity": frappe.utils.flt(scan_qty, 2),
            "rejected_garments": frappe.utils.flt(rejected_garments, 2),
            "cut_to_ship": frappe.utils.flt(cut_to_ship_percent, 2)
        })

    return result
