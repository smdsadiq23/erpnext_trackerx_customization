# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict


class FactoryOCR(Document):
	pass


@frappe.whitelist()
def sales_order_query_for_factory_ocr(doctype, txt, searchfield, start, page_len, filters):
    """
    Returns Sales Orders for the given customer that:
    - Are submitted (docstatus = 1)
    - Are NOT used in any Factory OCR (Draft or Submitted)
    """
    customer = filters.get("customer")
    if not customer:
        return []

    # Get all OCNs already used in Factory OCR (Draft + Submitted)
    used_ocns = frappe.get_all(
        "Factory OCR",
        filters={"docstatus": ["<", 2], "ocn": ["is", "set"]},
        pluck="ocn"
    )
    # Ensure it's a tuple (even if empty) for SQL safety
    used_ocns = tuple(set(used_ocns)) if used_ocns else ("__none__",)

    # Main query: Sales Orders for this customer, not used, matching search text
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

    # 1. Fetch Sales Order Items (source of truth for (style, color) combos)
    so_items = frappe.db.sql("""
        SELECT item_code, custom_color, qty
        FROM `tabSales Order Item`
        WHERE parent = %s AND docstatus = 1
    """, (sales_order,), as_dict=1)

    if not so_items:
        return []

    # Build lookup of all (item_code, custom_color) combinations
    grouped = defaultdict(lambda: {"item_code": "", "custom_color": "", "order_qty": 0})
    for row in so_items:
        if not row.item_code:
            continue
        key = f"{row.item_code}||{row.custom_color or ''}"
        grouped[key]["item_code"] = row.item_code
        grouped[key]["custom_color"] = row.custom_color or ""
        grouped[key]["order_qty"] += row.qty

    unique_styles = list(set(g["item_code"] for g in grouped.values()))

    # 2. Fetch CUT quantity per (style, color) from Cut Docket
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
            cut_map[f"{d.style}||{color}"] = d.cut_qty

    # 3. Fetch Pack quantity per (style, color) from Tracking
    pack_map = {}
    if unique_styles:
        pack_data = frappe.db.sql("""
            SELECT 
                itm.name AS item_code,
                itm.custom_colour_name AS color,
                COALESCE(SUM(pi.quantity), 0) AS pack_qty
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
        for d in pack_data:
            color = d.color or ""
            pack_map[f"{d.item_code}||{color}"] = d.pack_qty

    # 4. Fetch REJECTION count per (style, color) — MAIN COMPONENT ONLY (garments)
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
            AND tbc.sales_order = %s   -- ✅ Safe in WHERE
            GROUP BY itm.name, itm.custom_colour_name
        """, (sales_order,), as_dict=1)
        for d in rejection_data:
            color = d.color or ""
            rejection_garments_map[f"{d.item_code}||{color}"] = d.rejected_count

    # # 5. Fetch REJECTED PANELS count per (style, color) — ALL COMPONENTS
    # rejection_panels_map = {}
    # if unique_styles:
    #     rejection_panels_data = frappe.db.sql("""
    #         SELECT 
    #             itm.name AS item_code,
    #             itm.custom_colour_name AS color,
    #             COUNT(isl.name) AS rejected_count
    #         FROM `tabTracking Order` tor
    #         INNER JOIN `tabTracking Order Bundle Configuration` tbc
    #             ON tbc.parent = tor.name
    #             AND tbc.parentfield = 'component_bundle_configurations'
    #         INNER JOIN `tabItem` itm
    #             ON itm.name = tor.item
    #         INNER JOIN `tabProduction Item` pi
    #             ON pi.tracking_order = tor.name
    #             AND pi.bundle_configuration = tbc.name
    #         -- NO is_main filter here → all panels/components
    #         INNER JOIN `tabItem Scan Log` isl
    #             ON isl.production_item = pi.name
    #             AND isl.status LIKE '%%Reject%%'
    #         WHERE tor.item IS NOT NULL
    #           AND tbc.sales_order = %s
    #         GROUP BY itm.name, itm.custom_colour_name
    #     """, (sales_order,), as_dict=1)
    #     for d in rejection_panels_data:
    #         color = d.color or ""
    #         rejection_panels_map[f"{d.item_code}||{color}"] = d.rejected_count            

    # 6. Fetch style master for mapping
    item_style_map = {}
    if unique_styles:
        items = frappe.db.get_all("Item", 
            filters={"name": ["in", unique_styles]},
            fields=["name", "custom_style_master"]
        )
        item_style_map = {item.name: item.custom_style_master for item in items}

    # 7. Build final result — all quantities now EXACT per (style, color)
    result = []
    for group in grouped.values():
        item_code = group["item_code"]
        color = group["custom_color"]
        order_qty = group["order_qty"]
        key = f"{item_code}||{color}"

        cut_qty = cut_map.get(key, 0.0)
        pack_qty = pack_map.get(key, 0.0)
        rejected_garments = float(rejection_garments_map.get(key, 0))
        # rejected_panels = float(rejection_panels_map.get(key, 0))

        cut_to_ship_percent = (pack_qty / cut_qty * 100) if cut_qty else 0.0

        result.append({
            "style": item_style_map.get(item_code) or "",
            "colour": color,
            "order_quantity": order_qty,
            "cut_quantity": frappe.utils.flt(cut_qty, 2),
            "pack_quantity": frappe.utils.flt(pack_qty, 2),
            "rejected_garments": frappe.utils.flt(rejected_garments, 2),
            # "rejected_panels": frappe.utils.flt(rejected_panels, 2),
            "cut_to_ship": frappe.utils.flt(cut_to_ship_percent, 2)
        })

    return result