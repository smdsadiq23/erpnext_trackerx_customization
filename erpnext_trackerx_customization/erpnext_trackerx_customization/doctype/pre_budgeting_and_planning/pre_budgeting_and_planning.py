# Copyright (c) 2026, CognitionX and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, getdate


class PreBudgetingandPlanning(Document):
    def before_submit(self):
        """
        Prevent submission unless status is 'Approved'
        """
        if self.status != "Approved":
            frappe.throw(
                _("Cannot submit Pre-Budgeting document. Status must be 'Approved' to submit."),
                title=_("Submission Blocked")
            )


@frappe.whitelist()
def get_sales_orders_not_in_pre_budgeting(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
    """
    Get Sales Orders NOT already used in non-cancelled Pre-Budgeting documents
    - Excludes SOs used in Draft/Submitted Pre-Budgeting docs
    - Includes SOs used only in Cancelled Pre-Budgeting docs (allowed to recreate)
    """
    # Get SOs used in non-cancelled Pre-Budgeting docs (Draft=0, Submitted=1)
    used_sos = frappe.db.sql_list("""
        SELECT DISTINCT sales_order 
        FROM `tabPre-Budgeting and Planning` 
        WHERE docstatus < 2  -- Draft (0) or Submitted (1), NOT Cancelled (2)
          AND sales_order IS NOT NULL 
          AND sales_order != ''
    """)
    
    conditions = ["so.docstatus = 1"]  # Only submitted SOs
    params = {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    }
    
    if txt:
        conditions.append("(so.name LIKE %(txt)s OR so.customer LIKE %(txt)s)")
    
    # CRITICAL FIX: Removed extra closing parenthesis AND conditionally add param
    if used_sos:
        conditions.append("so.name NOT IN %(used_sos)s")  # ✅ FIXED: No extra ")"
        params["used_sos"] = tuple(used_sos)  # Only add param if condition exists
    
    query = """
        SELECT so.name, so.customer, so.transaction_date, so.grand_total
        FROM `tabSales Order` so
        WHERE {conditions}
        ORDER BY so.transaction_date DESC, so.name DESC
        LIMIT %(start)s, %(page_len)s
    """.format(conditions=" AND ".join(conditions))
    
    return frappe.db.sql(query, params, as_dict=as_dict)


@frappe.whitelist()
def get_styles_for_sales_order(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
    """
    Get distinct custom_style values from Sales Order Items for selected Sales Order
    """
    # Handle filters (could be string or dict)
    if isinstance(filters, str):
        import json
        filters = json.loads(filters)
    
    sales_order = filters.get("sales_order") if isinstance(filters, dict) else None
    if not sales_order:
        return []
    
    # CRITICAL FIX: Handle case where Style Master might not exist OR custom_style is not linked
    # Try to get styles directly from SO Items first (without Style Master join)
    try:
        # First attempt: Join with Style Master (for validation)
        return frappe.db.sql("""
            SELECT DISTINCT soi.custom_style AS name, soi.custom_style AS label
            FROM `tabSales Order Item` soi
            INNER JOIN `tabStyle Master` sm ON sm.name = soi.custom_style
            WHERE soi.parent = %(sales_order)s
              AND soi.custom_style IS NOT NULL
              AND soi.custom_style != ''
              AND (soi.custom_style LIKE %(txt)s OR sm.style_name LIKE %(txt)s)
            ORDER BY soi.custom_style
            LIMIT %(start)s, %(page_len)s
        """, {
            "sales_order": sales_order,
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_dict=as_dict)
    except Exception:
        # Fallback: Get styles directly from SO Items (if Style Master doesn't exist)
        return frappe.db.sql("""
            SELECT DISTINCT soi.custom_style AS name, soi.custom_style AS label
            FROM `tabSales Order Item` soi
            WHERE soi.parent = %(sales_order)s
              AND soi.custom_style IS NOT NULL
              AND soi.custom_style != ''
              AND soi.custom_style LIKE %(txt)s
            ORDER BY soi.custom_style
            LIMIT %(start)s, %(page_len)s
        """, {
            "sales_order": sales_order,
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_dict=as_dict)


@frappe.whitelist()
def get_so_totals(sales_order, style):
    """
    Get total quantity and amount from Sales Order Items for the given style
    Returns: { "total_qty": float, "actual_sales_amount": float }
    """
    if not sales_order or not style:
        return {"total_qty": 0, "actual_sales_amount": 0}
    
    try:
        result = frappe.db.sql("""
            SELECT 
                SUM(soi.qty) as total_qty,
                SUM(soi.amount) as actual_sales_amount
            FROM `tabSales Order Item` soi
            WHERE soi.parent = %s 
                AND soi.docstatus = 1
                AND soi.custom_style = %s
        """, (sales_order, style), as_dict=True)
        
        if result and result[0]:
            return {
                "total_qty": flt(result[0].total_qty),
                "actual_sales_amount": flt(result[0].actual_sales_amount)
            }
        return {"total_qty": 0, "actual_sales_amount": 0}
        
    except Exception as e:
        frappe.log_error(
            title="SO Totals Fetch Error",
            message=f"Sales Order: {sales_order}, Style: {style}, Error: {str(e)}"
        )
        return {"total_qty": 0, "actual_sales_amount": 0}


@frappe.whitelist()
def fetch_yarn_accessories_from_sales_order(sales_order, style=None):
    """
    Fetch yarn/accessories data from Sales Order to populate Pre-Budget - Yarn and Accessories child table
    
    Logic:
    1. Get FG items from Sales Order Item filtered by custom_style (if provided)
    2. For each FG item, get default/active BOM
    3. For each BOM item:
       - bom_qty (from BOM)
       - fg_qty (sum from SO Item)
       - total_qty = bom_qty × fg_qty
       - rate = fetched from Item Price (Standard Buying price list)
       - amount = total_qty × rate
    
    Returns:
        List of dicts compatible with Pre-Budget - Yarn and Accessories child table
    """
    if not sales_order:
        return []

    try:
        # Build query to get FG items from SO, optionally filtered by custom_style
        query = """
            SELECT soi.item_code, SUM(soi.qty) as total_fg_qty
            FROM `tabSales Order Item` soi
            WHERE soi.parent = %s 
                AND soi.docstatus = 1
        """
        params = [sales_order]
        
        if style:
            query += " AND soi.custom_style = %s"
            params.append(style)
        
        query += " GROUP BY soi.item_code ORDER BY soi.item_code"
        
        so_items = frappe.db.sql(query, params, as_dict=True)

        if not so_items:
            msg = _("No items found in Sales Order {0}").format(frappe.bold(sales_order))
            if style:
                msg += _(" matching Style {0}").format(frappe.bold(style))
            frappe.throw(msg)

        # Get default buying price list from Buying Settings
        default_buying_price_list = frappe.db.get_single_value("Buying Settings", "buying_price_list") or "Standard Buying"
        
        child_table_data = []

        for so_item in so_items:
            fg_item = so_item.item_code
            fg_qty = flt(so_item.total_fg_qty)

            # Get active BOM for FG item (prefer default, then latest created)
            bom = frappe.db.get_value("BOM", {
                "item": fg_item,
                "is_active": 1,
                "docstatus": 1
            }, "name", order_by="is_default DESC, creation DESC")

            if not bom:
                frappe.log_error(
                    f"No active BOM found for FG Item: {fg_item} in Sales Order: {sales_order}"
                )
                continue

            # Get BOM components with item_type from Item master
            bom_items = frappe.db.sql("""
                SELECT 
                    bi.item_code as component_item,
                    bi.custom_item_type as item_type,
                    bi.qty as bom_qty,                    
                    i.item_name as item_name,
                    i.stock_uom as uom
                FROM `tabBOM Item` bi
                INNER JOIN `tabItem` i ON i.name = bi.item_code
                WHERE bi.parent = %s 
                    AND bi.parentfield = 'items'
                    AND bi.docstatus < 2
                ORDER BY bi.idx
            """, bom, as_dict=True)

            for bom_item in bom_items:
                total_qty = flt(bom_item.bom_qty) * fg_qty
                
                # Fetch latest valid price from Item Price for this component
                rate = get_item_price(
                    item_code=bom_item.component_item,
                    price_list=default_buying_price_list,
                    uom=bom_item.uom
                )

                amount = total_qty * rate if rate else 0

                child_table_data.append({
                    "fg_item": fg_item,
                    "item_type": bom_item.item_type or "",
                    "item_code": bom_item.component_item,
                    "bom_qty": bom_item.bom_qty,
                    "fg_qty": fg_qty,
                    "total_qty": total_qty,
                    "rate": flt(rate, 2) if rate else 0,
                    "currency": flt(amount, 2)
                })

        return child_table_data

    except Exception as e:
        frappe.log_error(
            title="Pre-Budget Yarn/Accessories Fetch Error",
            message=f"Sales Order: {sales_order}, Style: {style}, Error: {str(e)}"
        )
        frappe.throw(_("Error loading yarn/accessories data: {0}").format(str(e)))


def get_item_price(item_code, price_list="Standard Buying", uom=None):
    """
    Fetch the latest valid price for an item from Item Price doctype
    
    Rules:
    1. Filter by item_code, price_list, and buying=1
    2. Consider valid_from/valid_upto dates (today must be within range)
    3. Prefer prices with matching uom, fallback to any uom
    4. Return latest price by valid_from date
    
    Returns:
        Float price or None if no valid price found
    """
    today_date = today()
    
    # First try: exact match with uom
    price = frappe.db.sql("""
        SELECT ip.price_list_rate
        FROM `tabItem Price` ip
        WHERE ip.item_code = %s
            AND ip.price_list = %s
            AND ip.buying = 1
            AND (ip.valid_from IS NULL OR ip.valid_from <= %s)
            AND (ip.valid_upto IS NULL OR ip.valid_upto >= %s)
            AND (ip.uom IS NULL OR ip.uom = %s OR %s IS NULL)
        ORDER BY ip.valid_from DESC, ip.creation DESC
        LIMIT 1
    """, (item_code, price_list, today_date, today_date, uom, uom), as_dict=True)
    
    if price:
        return flt(price[0].price_list_rate)
    
    # Second try: any uom (fallback)
    price = frappe.db.sql("""
        SELECT ip.price_list_rate
        FROM `tabItem Price` ip
        WHERE ip.item_code = %s
            AND ip.price_list = %s
            AND ip.buying = 1
            AND (ip.valid_from IS NULL OR ip.valid_from <= %s)
            AND (ip.valid_upto IS NULL OR ip.valid_upto >= %s)
        ORDER BY ip.valid_from DESC, ip.creation DESC
        LIMIT 1
    """, (item_code, price_list, today_date, today_date), as_dict=True)
    
    if price:
        return flt(price[0].price_list_rate)
    
    # No valid price found
    frappe.log_error(f"No valid price found for item {item_code} in price list {price_list}")
    return 0


@frappe.whitelist()
def fetch_process_from_cmt_planning(style, sales_order, category):
    """
    Fetch process data from CMT Planning and distribute across FG items
    
    Logic:
    1. Get unique FG items with quantities from Sales Order (filtered by style)
    2. Get CMT process rows for the category
    3. For EACH FG item, repeat ALL process rows with:
       - fg_item = FG item code
       - qty = FG item quantity (CMT stores per-piece rates, so qty = FG qty)
       - rate = CMT price (per-piece rate)
       - amount = qty × rate
    
    Args:
        style (str): REQUIRED - Style code to filter Sales Order Items
        sales_order (str): Sales Order name
        category (str): CMT Planning category for process lookup
    
    Returns:
        List of dicts for Pre-Budget - Process child table with fg_item populated
    """
    if not style or not sales_order or not category:
        return []

    try:
        # Get FG items with quantities from Sales Order (filtered by style)
        fg_items = frappe.db.sql("""
            SELECT soi.item_code as fg_item, SUM(soi.qty) as fg_qty
            FROM `tabSales Order Item` soi
            WHERE soi.parent = %s 
                AND soi.docstatus = 1
                AND soi.custom_style = %s
            GROUP BY soi.item_code
            ORDER BY soi.item_code
        """, (sales_order, style), as_dict=True)
        
        if not fg_items:
            frappe.log_error(
                title="No FG Items Found",
                message=f"Style: {style}, Sales Order: {sales_order}"
            )
            return []

        # Find CMT Planning record matching the category EXACTLY (submitted only)
        cmt_planning = frappe.db.get_value("CMT Planning", {
            "category": category,
            "docstatus": 1  # Only submitted CMT Planning
        }, "name")

        if not cmt_planning:
            frappe.log_error(
                title="CMT Planning Not Found",
                message=f"Category: {category} (must be submitted)"
            )
            return []

        # Get CMT process costing rows
        cmt_processes = frappe.db.get_all("CMT Process Costing", 
            filters={"parent": cmt_planning, "parenttype": "CMT Planning"},
            fields=["operation", "pcs", "price"],
            order_by="idx"
        )

        if not cmt_processes:
            frappe.log_error(
                title="No CMT Processes Found",
                message=f"CMT Planning: {cmt_planning}"
            )
            return []

        child_table_data = []
        
        # For EACH FG item, repeat ALL process rows
        for fg_item in fg_items:
            fg_item_code = fg_item.fg_item
            fg_qty = flt(fg_item.fg_qty)
            
            for process in cmt_processes:
                # CMT stores PER-PIECE rates (pcs=1 is default)
                # So qty = FG item quantity, rate = price per piece
                process_qty = fg_qty  # Direct FG quantity
                rate = flt(process.price or 0)
                amount = process_qty * rate

                child_table_data.append({
                    "fg_item": fg_item_code,  # ✅ POPULATED
                    "operations": process.operation or "",
                    "qty": flt(process_qty, 2),
                    "rate": flt(rate, 2),
                    "amount": flt(amount, 2)
                })

        return child_table_data

    except Exception as e:
        frappe.log_error(
            title="CMT Process Fetch Error",
            message=f"Style: {style}, Sales Order: {sales_order}, Category: {category}, Error: {str(e)}"
        )
        return []