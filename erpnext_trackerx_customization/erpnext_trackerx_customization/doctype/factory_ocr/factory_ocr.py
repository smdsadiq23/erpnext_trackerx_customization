# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict


class FactoryOCR(Document):
	pass


@frappe.whitelist()
def get_sales_orders_by_brand(brand):
    # Get customers linked to this brand
    customers = frappe.get_all('Customer', filters={'brand': brand}, pluck='name')
    if not customers:
        return []
    # Get sales orders for those customers
    orders = frappe.get_all('Sales Order', 
        filters={'customer': ['in', customers], 'docstatus': 1},
        pluck='name'
    )
    return orders


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

    # 3. Fetch SHIP quantity per (style, color) from Tracking
    ship_map = {}
    if unique_styles:
        ship_data = frappe.db.sql("""
            SELECT 
                itm.name AS item_code,
                itm.custom_colour_name AS color,
                COALESCE(SUM(pi.quantity), 0) AS ship_qty
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
        for d in ship_data:
            color = d.color or ""
            ship_map[f"{d.item_code}||{color}"] = d.ship_qty

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
            rejection_map[f"{d.item_code}||{color}"] = d.rejected_count

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
        ship_qty = ship_map.get(key, 0.0)
        rejected_garments = float(rejection_garments_map.get(key, 0))
        rejected_panels = float(rejection_panels_map.get(key, 0))

        cut_to_ship_percent = (ship_qty / cut_qty * 100) if cut_qty else 0.0

        result.append({
            "style": item_style_map.get(item_code) or "",
            "colour": color,
            "order_quantity": order_qty,
            "cut_quantity": frappe.utils.flt(cut_qty, 2),
            "ship_quantity": frappe.utils.flt(ship_qty, 2),
            "rejected_garments": frappe.utils.flt(rejected_garments, 2),
            "rejected_panels": frappe.utils.flt(rejected_panels, 2),
            "cut_to_ship": frappe.utils.flt(cut_to_ship_percent, 2)
        })

    return result