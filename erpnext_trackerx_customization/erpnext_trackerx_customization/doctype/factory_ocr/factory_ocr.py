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
    users = frappe.get_all(
        "Has Role",
        filters={"role": FACTORY_MANAGER_ROLE},
        pluck="parent",
    ) or []

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
            frappe.log_error(
                title="Factory OCR Notification Log failed",
                message=frappe.get_traceback()
            )

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

    if doc.as_dict(no_nulls=False) != before.as_dict(no_nulls=False):
        frappe.throw(_("This document is locked in '{0}' state. Edits are not allowed.").format(doc.status))


def _get_relevant_factory_ocr_names(ocn: str, exclude_factory_ocr: str | None = None) -> list[str]:
    """
    Which Factory OCR docs should consume shipment qty?
    - count Pending for Approval + Approved
    - ignore Rejected
    """
    if not ocn:
        return []

    filters = {
        "ocn": ocn,
        "docstatus": ["<", 2],
        "status": ["in", ["Pending for Approval", "Approved"]],
    }
    if exclude_factory_ocr:
        filters["name"] = ["!=", exclude_factory_ocr]

    return frappe.get_all("Factory OCR", filters=filters, pluck="name") or []


def _get_shipped_qty_map(ocn: str, exclude_factory_ocr: str | None = None) -> dict[str, float]:
    """
    Map:
      key = style||colour||line_item  ->  SUM(ship_quantity)

    Counts ship_quantity from Factory OCR Item for relevant OCR docs of that OCN.
    """
    ocr_names = _get_relevant_factory_ocr_names(ocn, exclude_factory_ocr=exclude_factory_ocr)
    if not ocr_names:
        return {}

    # NOTE: assumes child doctype is "Factory OCR Item" and fieldnames:
    # style, colour, line_item, ship_quantity
    rows = frappe.db.sql("""
        SELECT
            COALESCE(style, '') AS style,
            COALESCE(colour, '') AS colour,
            COALESCE(line_item, '') AS line_item,
            COALESCE(SUM(COALESCE(ship_quantity, 0)), 0) AS shipped_qty
        FROM `tabFactory OCR Item`
        WHERE parent IN %(parents)s
        GROUP BY style, colour, line_item
    """, {"parents": tuple(ocr_names)}, as_dict=1)

    shipped_map = {}
    for r in rows or []:
        key = f"{r.style}||{r.colour}||{r.line_item}"
        shipped_map[key] = float(r.shipped_qty or 0)

    return shipped_map


def _sales_order_has_remaining_groups(sales_order: str) -> bool:
    """
    A Sales Order should be selectable if ANY grouped key has remaining qty:
      remaining = order_qty(group) - shipped_qty(group)
      remaining > 0
    """
    if not sales_order:
        return False

    shipped_map = _get_shipped_qty_map(sales_order)

    so_items = frappe.db.sql("""
        SELECT custom_style, custom_color, custom_lineitem, qty
        FROM `tabSales Order Item`
        WHERE parent = %s
    """, (sales_order,), as_dict=1)

    if not so_items:
        return False

    grouped = defaultdict(lambda: 0.0)
    for row in so_items:
        style = row.custom_style or ""
        if not style:
            continue
        color = row.custom_color or ""
        lineitem = row.custom_lineitem or ""
        key = f"{style}||{color}||{lineitem}"
        grouped[key] += float(row.qty or 0)

    for key, order_qty in grouped.items():
        shipped_qty = float(shipped_map.get(key, 0))
        remaining = float(order_qty) - shipped_qty
        if remaining > 0:
            return True

    return False


class FactoryOCR(Document):
    def validate(self):
        if not self.status or self.status == "Draft":
            self.status = "Pending for Approval"

        _freeze_if_locked(self)

    def after_insert(self):
        _notify_factory_managers_on_pending(self)

    def before_submit(self):
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
    """
    Return Sales Orders for the given customer that:
      - are submitted (docstatus = 1)
      - match txt
      - AND have at least one grouped SOI row (style||color||lineitem) with remaining qty > 0
    """
    customer = filters.get("customer")
    if not customer:
        return []

    candidates = frappe.db.sql("""
        SELECT name, customer, transaction_date
        FROM `tabSales Order`
        WHERE docstatus = 1
          AND customer = %(customer)s
          AND name LIKE %(txt)s
        ORDER BY transaction_date DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """, {
        "customer": customer,
        "txt": "%" + (txt or "") + "%",
        "limit": int(page_len) * 5,
        "offset": int(start)
    }, as_dict=1)

    results = []
    for so in candidates:
        if _sales_order_has_remaining_groups(so.name):
            results.append((so.name, so.customer, so.transaction_date))
        if len(results) >= int(page_len):
            break

    return results


@frappe.whitelist()
def fetch_sales_order_items_for_factory_ocr(sales_order, factory_ocr=None):
    """
    Returns grouped rows for Factory OCR Item creation.

    Rule:
      A group (style||color||lineitem) is allowed multiple times
      as long as total shipped qty (sum of ship_quantity) across previous OCRs
      is < Sales Order grouped order qty.

    Returned:
      - order_quantity = FULL grouped SO qty
      - ship_quantity  = REMAINING qty (order_qty - shipped_qty)  ✅
    """
    if not sales_order:
        return []

    shipped_map = _get_shipped_qty_map(sales_order, exclude_factory_ocr=factory_ocr)

    so_items = frappe.db.sql("""
        SELECT custom_style, custom_color, qty, custom_lineitem
        FROM `tabSales Order Item`
        WHERE parent = %s
    """, (sales_order,), as_dict=1)

    if not so_items:
        return []

    # Group Sales Order qty by (style||color||lineitem)
    grouped = defaultdict(lambda: {"style": "", "custom_color": "", "custom_lineitem": "", "order_qty": 0.0})
    for row in so_items:
        style = row.custom_style or ""
        if not style:
            continue

        color = row.custom_color or ""
        lineitem = row.custom_lineitem or ""
        key = f"{style}||{color}||{lineitem}"

        grouped[key]["style"] = style
        grouped[key]["custom_color"] = color
        grouped[key]["custom_lineitem"] = lineitem
        grouped[key]["order_qty"] += float(row.qty or 0)

    # Keep only keys with remaining > 0
    filtered_groups = {}
    remaining_map = {}
    for key, g in grouped.items():
        shipped_qty = float(shipped_map.get(key, 0))
        remaining = float(g["order_qty"]) - shipped_qty
        if remaining > 0:
            filtered_groups[key] = g
            remaining_map[key] = remaining

    if not filtered_groups:
        return []

    unique_styles = list(set(g["style"] for g in filtered_groups.values() if g.get("style")))

    # 2. CUT qty per (style, color)  (Cut Docket field = style_no)
    cut_map = {}
    if unique_styles:
        cut_data = frappe.db.sql("""
            SELECT 
                cd.style_no AS style_no,
                cd.color AS color,
                SUM(cci.confirmed_quantity) AS cut_qty
            FROM `tabCut Confirmation Item` cci
            INNER JOIN `tabCut Confirmation` cc 
                ON cci.parent = cc.name AND cc.docstatus = 1
            INNER JOIN `tabCut Docket` cd 
                ON cc.cut_po_number = cd.name AND cd.docstatus = 1
            WHERE cci.sales_order = %s
            GROUP BY cd.style_no, cd.color
        """, (sales_order,), as_dict=1)

        for d in cut_data or []:
            style_no = d.style_no or ""
            color = d.color or ""
            cut_map[f"{style_no}||{color}"] = d.cut_qty or 0

    # 3. Scan qty per (style, color) using Item.custom_style_master and Item.custom_colour_name
    scan_map = {}
    if unique_styles:
        scan_data = frappe.db.sql("""
            SELECT 
                itm.custom_style_master AS style,
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
            GROUP BY itm.custom_style_master, itm.custom_colour_name
        """, (sales_order,), as_dict=1)

        for d in scan_data or []:
            style = d.style or ""
            color = d.color or ""
            scan_map[f"{style}||{color}"] = d.scan_qty or 0

    # 4. Rejected garments (main component) per (style, color)
    rejection_garments_map = {}
    if unique_styles:
        rejection_data = frappe.db.sql("""
            SELECT 
                itm.custom_style_master AS style,
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
            GROUP BY itm.custom_style_master, itm.custom_colour_name
        """, (sales_order,), as_dict=1)

        for d in rejection_data or []:
            style = d.style or ""
            color = d.color or ""
            rejection_garments_map[f"{style}||{color}"] = d.rejected_count or 0

    # 5. Build result (order_quantity = full, ship_quantity = remaining)
    result = []
    for key, g in filtered_groups.items():
        style = g["style"]
        color = g["custom_color"]
        lineitem = g["custom_lineitem"]

        full_order_qty = float(g["order_qty"])
        remaining_qty = float(remaining_map.get(key, 0))

        style_color_key = f"{style}||{color}"

        cut_qty = cut_map.get(style_color_key, 0.0)
        scan_qty = scan_map.get(style_color_key, 0.0)
        rejected_garments = float(rejection_garments_map.get(style_color_key, 0))

        cut_to_ship_percent = (scan_qty / cut_qty * 100) if cut_qty else 0.0

        result.append({
            "style": style,
            "colour": color,
            "lineitem": lineitem,
            "order_quantity": full_order_qty,
            "ship_quantity": remaining_qty,  
            "cut_quantity": frappe.utils.flt(cut_qty, 2),
            "scan_quantity": frappe.utils.flt(scan_qty, 2),
            "rejected_garments": frappe.utils.flt(rejected_garments, 2),
            "cut_to_ship": frappe.utils.flt(cut_to_ship_percent, 2)
        })

    return result
