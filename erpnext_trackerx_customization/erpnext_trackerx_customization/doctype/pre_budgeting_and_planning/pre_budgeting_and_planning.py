# Copyright (c) 2026, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PreBudgetingandPlanning(Document):
	pass



@frappe.whitelist()
def get_sales_orders_by_style(doctype, txt, searchfield, start, page_len, filters):
    style = filters.get("style")
    if not style:
        return []

    return frappe.db.sql("""
        SELECT DISTINCT so.name
        FROM `tabSales Order` so
        INNER JOIN `tabSales Order Item` soi
            ON soi.parent = so.name
        WHERE soi.custom_style = %s
        AND so.name LIKE %s
        ORDER BY so.modified DESC
        LIMIT %s, %s
    """, (style, f"%{txt}%", start, page_len))


@frappe.whitelist()
def fetch_pre_budget_items(pre_budget_doc):
    doc = frappe.get_doc("Pre-Budgeting and Planning", pre_budget_doc)

    if not doc.sales_order:
        frappe.throw("Please select Sales Order first")

    # Clear existing rows
    doc.set("table_itma", [])

    # 1. Get Sales Order Items
    so_items = frappe.get_all(
        "Sales Order Item",
        filters={"parent": doc.sales_order},
        fields=["item_code", "qty"]
    )

    unique_items = {}
    for i in so_items:
        unique_items[i.item_code] = i.qty   # FG Qty

    for fg_item, fg_qty in unique_items.items():

        # 2. Get BOM
        bom = frappe.get_value(
            "BOM",
            {"item": fg_item, "is_active": 1, "is_default": 1},
            "name"
        )

        if not bom:
            continue

        # 3. Get BOM Items
        bom_items = frappe.get_all(
            "BOM Item",
            filters={
                "parent": bom,
                "parentfield": "items"
            },
            fields=[
                "item_code",
                "qty",
                "custom_item_type"
            ]
        )

        for bi in bom_items:
            total_qty = bi.qty * fg_qty

            row = doc.append("table_itma", {
                "fg_item": fg_item,
                "item_type": bi.custom_item_type,
                "item_code": bi.item_code,
                "bom_qty": bi.qty,
                "fg_qty": fg_qty,
                "total_qty": total_qty
            })

    doc.save()
    return {"status": "success"}
