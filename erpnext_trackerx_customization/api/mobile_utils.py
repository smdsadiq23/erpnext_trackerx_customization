import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, now_datetime
import json
from datetime import datetime, timedelta

# ===========================
# SHARED MOBILE UTILITIES
# ===========================

@frappe.whitelist()
def get_document_list(doctype, search=None, status=None, company=None, supplier=None,
                      date_from=None, date_to=None, page=1, limit=20, sort_by="creation", sort_order="desc"):
    """
    Generic function to get document list with filters/pagination
    Works for any doctype (Purchase Receipt, Goods Receipt Note, etc.)
    """
    try:
        page = cint(page) or 1
        limit = cint(limit) or 20
        offset = (page - 1) * limit

        # Build conditions
        conditions = [f"doc.docstatus != 2"]
        values = {}

        # Search functionality
        if search:
            conditions.append("(doc.name LIKE %(search)s OR doc.supplier LIKE %(search)s OR doc.supplier_name LIKE %(search)s)")
            values["search"] = f"%{search}%"

        # Status filter
        if status:
            if status.lower() == "draft":
                conditions.append("doc.docstatus = 0")
            elif status.lower() == "submitted":
                conditions.append("doc.docstatus = 1")
            elif status.lower() == "cancelled":
                conditions.append("doc.docstatus = 2")

        # Company filter
        if company:
            conditions.append("doc.company = %(company)s")
            values["company"] = company

        # Supplier filter
        if supplier:
            conditions.append("doc.supplier = %(supplier)s")
            values["supplier"] = supplier

        # Date range filter
        if date_from:
            conditions.append("doc.posting_date >= %(date_from)s")
            values["date_from"] = date_from

        if date_to:
            conditions.append("doc.posting_date <= %(date_to)s")
            values["date_to"] = date_to

        where_clause = " AND ".join(conditions)

        # Get child table name
        child_table = f"`tab{doctype} Item`"

        # Main query
        query = f"""
            SELECT
                doc.name as id,
                doc.title,
                doc.supplier,
                doc.supplier_name,
                doc.company,
                doc.posting_date as date,
                doc.grand_total,
                doc.currency,
                doc.docstatus,
                doc.remarks,
                doc.modified,
                doc.creation,
                CASE
                    WHEN doc.docstatus = 0 THEN 'Draft'
                    WHEN doc.docstatus = 1 AND doc.is_return = 1 THEN 'Return'
                    WHEN doc.docstatus = 1 THEN 'Submitted'
                    WHEN doc.docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END as status,
                COUNT(child.name) as total_items
            FROM `tab{doctype}` doc
            LEFT JOIN {child_table} child ON child.parent = doc.name
            WHERE {where_clause}
            GROUP BY doc.name
            ORDER BY doc.{sort_by} {sort_order.upper()}
            LIMIT %(limit)s OFFSET %(offset)s
        """

        values.update({"limit": limit, "offset": offset})
        doc_list = frappe.db.sql(query, values, as_dict=True)

        # Get total count
        count_query = f"SELECT COUNT(DISTINCT doc.name) as total FROM `tab{doctype}` doc WHERE {where_clause}"
        total_count = frappe.db.sql(count_query, values, as_dict=True)[0].total
        total_pages = (total_count + limit - 1) // limit

        # Format response
        for doc in doc_list:
            if doc.get("date"):
                doc["date"] = str(doc["date"])
            if doc.get("modified"):
                doc["modified"] = doc["modified"].isoformat() if doc["modified"] else None
            if doc.get("creation"):
                doc["creation"] = doc["creation"].isoformat() if doc["creation"] else None
            doc["grand_total"] = flt(doc.get("grand_total", 0), 2)

        return {
            "success": True,
            "data": doc_list,
            "pagination": {
                "page": page,
                "per_page": limit,
                "total": total_count,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }

    except Exception as e:
        frappe.log_error(f"Error in get_document_list for {doctype}: {str(e)}", "Mobile Utils Error")
        return {"success": False, "error": {"message": str(e), "code": "DOCUMENT_LIST_ERROR"}}

@frappe.whitelist()
def get_document_filters(doctype):
    """
    Generic function to get filter options for document list
    """
    try:
        # Get unique companies
        companies = frappe.db.sql(f"""
            SELECT DISTINCT company, company as label
            FROM `tab{doctype}`
            WHERE docstatus != 2
            ORDER BY company
        """, as_dict=True)

        # Get unique suppliers
        suppliers = frappe.db.sql(f"""
            SELECT DISTINCT supplier, supplier_name as label
            FROM `tab{doctype}`
            WHERE docstatus != 2 AND supplier IS NOT NULL
            ORDER BY supplier_name
        """, as_dict=True)

        # Get status options
        statuses = [
            {"value": "draft", "label": "Draft"},
            {"value": "submitted", "label": "Submitted"},
            {"value": "cancelled", "label": "Cancelled"}
        ]

        return {
            "success": True,
            "data": {
                "companies": companies,
                "suppliers": suppliers,
                "statuses": statuses
            }
        }

    except Exception as e:
        frappe.log_error(f"Error in get_document_filters for {doctype}: {str(e)}", "Mobile Utils Error")
        return {"success": False, "error": {"message": str(e), "code": "DOCUMENT_FILTERS_ERROR"}}

@frappe.whitelist()
def search_document(doctype, search_term, limit=10):
    """
    Generic function to search documents
    """
    try:
        if not search_term:
            return {"success": True, "data": [], "message": "Please provide a search term"}

        limit = cint(limit) or 10

        query = f"""
            SELECT
                doc.name as id,
                doc.title,
                doc.supplier,
                doc.supplier_name,
                doc.posting_date as date,
                doc.grand_total,
                doc.currency,
                CASE
                    WHEN doc.docstatus = 0 THEN 'Draft'
                    WHEN doc.docstatus = 1 AND doc.is_return = 1 THEN 'Return'
                    WHEN doc.docstatus = 1 THEN 'Submitted'
                    WHEN doc.docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END as status
            FROM `tab{doctype}` doc
            WHERE doc.docstatus != 2
            AND (
                doc.name LIKE %(search)s OR
                doc.supplier LIKE %(search)s OR
                doc.supplier_name LIKE %(search)s OR
                doc.supplier_delivery_note LIKE %(search)s OR
                doc.purchase_order LIKE %(search)s
            )
            ORDER BY doc.modified DESC
            LIMIT %(limit)s
        """

        results = frappe.db.sql(query, {
            "search": f"%{search_term}%",
            "limit": limit
        }, as_dict=True)

        # Format results
        for result in results:
            if result.get("date"):
                result["date"] = str(result["date"])
            result["grand_total"] = flt(result.get("grand_total", 0), 2)

        return {
            "success": True,
            "data": results,
            "search_term": search_term,
            "total_results": len(results)
        }

    except Exception as e:
        frappe.log_error(f"Error in search_document for {doctype}: {str(e)}", "Mobile Utils Error")
        return {"success": False, "error": {"message": str(e), "code": "DOCUMENT_SEARCH_ERROR"}}

@frappe.whitelist()
def get_companies():
    """
    Get companies list for dropdown - REUSABLE
    """
    try:
        companies = frappe.get_all("Company",
            fields=["name", "company_name", "abbr", "default_currency"],
            order_by="company_name asc"
        )

        # Format for mobile dropdown
        company_options = []
        for company in companies:
            company_options.append({
                "value": company.name,
                "label": company.company_name or company.name,
                "currency": company.default_currency,
                "abbr": company.abbr
            })

        return {
            "success": True,
            "data": {
                "companies": company_options,
                "total": len(company_options)
            }
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Companies Error", frappe.get_traceback())
        return {"success": False, "error": {"message": str(e), "code": "COMPANIES_ERROR"}}

@frappe.whitelist()
def get_purchase_orders(supplier=None, company=None, search=None):
    """
    Get purchase orders for dropdown - REUSABLE
    """
    try:
        # Build conditions
        conditions = ["docstatus = 1", "status != 'Closed'"]
        values = {}

        if supplier:
            conditions.append("supplier = %(supplier)s")
            values["supplier"] = supplier

        if company:
            conditions.append("company = %(company)s")
            values["company"] = company

        if search:
            conditions.append("(name LIKE %(search)s OR supplier_name LIKE %(search)s)")
            values["search"] = f"%{search}%"

        where_clause = " AND ".join(conditions)

        # Get purchase orders
        purchase_orders = frappe.db.sql(f"""
            SELECT
                name,
                supplier,
                supplier_name,
                company,
                transaction_date,
                grand_total,
                currency,
                status,
                per_received
            FROM `tabPurchase Order`
            WHERE {where_clause}
            ORDER BY transaction_date DESC
            LIMIT 50
        """, values, as_dict=True)

        # Format for mobile dropdown
        po_options = []
        for po in purchase_orders:
            po_options.append({
                "value": po.name,
                "label": f"{po.name} - {po.supplier_name}",
                "supplier": po.supplier,
                "supplier_name": po.supplier_name,
                "company": po.company,
                "date": str(po.transaction_date) if po.transaction_date else None,
                "grand_total": flt(po.grand_total, 2),
                "currency": po.currency,
                "status": po.status,
                "per_received": flt(po.per_received, 2)
            })

        return {
            "success": True,
            "data": {
                "purchase_orders": po_options,
                "total": len(po_options),
                "filters_applied": {
                    "supplier": supplier,
                    "company": company,
                    "search": search
                }
            }
        }

    except Exception as e:
        frappe.log_error("Mobile Utils PO Error", frappe.get_traceback())
        return {"success": False, "error": {"message": str(e), "code": "PURCHASE_ORDERS_ERROR"}}

@frappe.whitelist()
def get_warehouses(company=None):
    """
    Get list of warehouses for dropdown - REUSABLE
    """
    try:
        conditions = ["is_group = 0", "disabled = 0"]
        values = {}

        if company:
            conditions.append("company = %(company)s")
            values["company"] = company

        warehouses = frappe.db.sql(f"""
            SELECT
                name,
                warehouse_name,
                company
            FROM `tabWarehouse`
            WHERE {' AND '.join(conditions)}
            ORDER BY warehouse_name
        """, values, as_dict=True)

        formatted_warehouses = []
        for wh in warehouses:
            formatted_warehouses.append({
                "value": wh.name,
                "label": wh.warehouse_name,
                "company": wh.company
            })

        return {
            "success": True,
            "data": formatted_warehouses,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Warehouses Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to get warehouses", "code": "API_ERROR"}}

@frappe.whitelist()
def get_tax_templates():
    """
    Get available Purchase Taxes and Charges templates - REUSABLE
    """
    try:
        templates = frappe.db.sql("""
            SELECT
                name,
                title,
                company,
                disabled
            FROM `tabPurchase Taxes and Charges Template`
            WHERE disabled = 0
            ORDER BY title
        """, as_dict=True)

        formatted_templates = []
        for template in templates:
            formatted_templates.append({
                "value": template.name,
                "label": template.title or template.name,
                "company": template.company
            })

        return {
            "success": True,
            "data": formatted_templates,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Tax Templates Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to get tax templates", "code": "API_ERROR"}}

@frappe.whitelist()
def get_tax_accounts(company=None):
    """
    Get tax account heads for dropdown - REUSABLE
    """
    try:
        conditions = ["disabled = 0", "is_group = 0"]
        values = {"tax_pattern": "%Tax%"}

        if company:
            conditions.append("company = %(company)s")
            values["company"] = company

        # Get tax accounts
        accounts = frappe.db.sql("""
            SELECT
                name,
                account_name,
                account_type,
                company
            FROM `tabAccount`
            WHERE {}
            AND (account_type LIKE %(tax_pattern)s OR account_type IN ('Chargeable', 'Expense Account'))
            ORDER BY account_name
        """.format(' AND '.join(conditions)), values, as_dict=True)

        formatted_accounts = []
        for account in accounts:
            formatted_accounts.append({
                "value": account.name,
                "label": account.account_name,
                "account_type": account.account_type,
                "company": account.company
            })

        return {
            "success": True,
            "data": formatted_accounts,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Error in get_tax_accounts", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to get tax accounts", "code": "API_ERROR"}}


@frappe.whitelist()
def get_document_status_summary(doctype):
    """
    Get count of documents by status for dashboard display - REUSABLE
    """
    try:
        # Get count by status
        status_counts = frappe.db.sql(f"""
            SELECT
                CASE
                    WHEN docstatus = 0 THEN 'Draft'
                    WHEN docstatus = 1 AND is_return = 1 THEN 'Return'
                    WHEN docstatus = 1 THEN 'Submitted'
                    WHEN docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END as status,
                COUNT(*) as count,
                SUM(grand_total) as total_amount
            FROM `tab{doctype}`
            WHERE docstatus != 2
            GROUP BY
                CASE
                    WHEN docstatus = 0 THEN 'Draft'
                    WHEN docstatus = 1 AND is_return = 1 THEN 'Return'
                    WHEN docstatus = 1 THEN 'Submitted'
                    WHEN docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END
        """, as_dict=True)

        # Build response as array of key-value objects to match mobile_v1 format
        response_data = []
        total_count = 0

        for item in status_counts:
            status = item['status']
            count = item['count']

            response_data.append({
                "key": status,
                "value": count
            })
            total_count += count

        # Add total at the end
        response_data.append({
            "key": "Total",
            "value": total_count
        })

        return {
            "success": True,
            "data": response_data,
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Status Summary Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to get document status summary", "code": "API_ERROR"}}


@frappe.whitelist()
def get_naming_series(doctype):
    """
    Get available naming series for a doctype

    Args:
        doctype (str): The doctype to get naming series for

    Returns:
        dict: Available naming series
    """
    try:
        # Get naming series from doctype
        naming_series_field = frappe.get_meta(doctype).get_field("naming_series")

        if not naming_series_field or not naming_series_field.options:
            return {
                "success": False,
                "error": {
                    "message": f"No naming series configured for {doctype}",
                    "code": "NO_NAMING_SERIES"
                }
            }

        # Parse options
        options = []
        for series in naming_series_field.options.split('\n'):
            series = series.strip()
            if series:
                options.append({
                    "value": series,
                    "label": series
                })

        return {
            "success": True,
            "data": {
                "naming_series": options,
                "default": options[0]["value"] if options else None
            }
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Naming Series Error", frappe.get_traceback())
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "NAMING_SERIES_ERROR"
            }
        }


@frappe.whitelist()
def search_items(search_term, supplier=None, company=None, limit=10):
    """
    Search items for adding to documents

    Args:
        search_term (str): Item code or name to search
        supplier (str): Filter by supplier (optional)
        company (str): Filter by company (optional)
        limit (int): Maximum results to return

    Returns:
        dict: List of matching items
    """
    try:
        limit = cint(limit) or 10

        # Build search conditions
        conditions = ["i.disabled = 0", "i.is_purchase_item = 1"]
        values = {"limit": limit}

        if search_term:
            conditions.append("(i.item_code LIKE %(search)s OR i.item_name LIKE %(search)s)")
            values["search"] = f"%{search_term}%"

        # Filter by supplier if provided
        supplier_condition = ""
        if supplier:
            supplier_condition = """
            AND EXISTS (
                SELECT 1 FROM `tabItem Supplier`
                WHERE parent = i.name AND supplier = %(supplier)s
            )
            """
            values["supplier"] = supplier

        query = f"""
            SELECT
                i.item_code,
                i.item_name,
                i.description,
                i.stock_uom,
                i.purchase_uom,
                i.item_group,
                i.has_batch_no,
                i.has_serial_no,
                i.maintain_stock,
                COALESCE(ip.price_list_rate, 0) as rate
            FROM `tabItem` i
            LEFT JOIN `tabItem Price` ip ON i.item_code = ip.item_code
                AND ip.price_list = 'Standard Buying'
            WHERE {' AND '.join(conditions)}
            {supplier_condition}
            ORDER BY
                CASE WHEN i.item_code LIKE %(search)s THEN 1 ELSE 2 END,
                i.item_name
            LIMIT %(limit)s
        """

        items = frappe.db.sql(query, values, as_dict=True)

        # Format for mobile display
        formatted_items = []
        for item in items:
            formatted_item = {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "stock_uom": item.stock_uom,
                "purchase_uom": item.purchase_uom,
                "item_group": item.item_group,
                "has_batch_no": item.has_batch_no,
                "has_serial_no": item.has_serial_no,
                "maintain_stock": item.maintain_stock,
                "rate": flt(item.rate),
                "display_name": f"{item.item_code} - {item.item_name}",
                "rate_display": f"{flt(item.rate):,.2f}"
            }
            formatted_items.append(formatted_item)

        return {
            "success": True,
            "data": formatted_items,
            "total": len(formatted_items),
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error searching items: {str(e)}", "Mobile Utils Search Items Error")
        return {"success": False, "error": {"message": "Failed to search items", "code": "API_ERROR"}}


@frappe.whitelist()
def get_document_items(doctype, doc_id):
    """
    Get all items in a document for the Items tab

    Args:
        doctype (str): Document type
        doc_id (str): Document ID

    Returns:
        dict: List of document items with details
    """
    try:
        # Check if document exists
        if not frappe.db.exists(doctype, doc_id):
            return {"success": False, "error": {"message": f"{doctype} not found", "code": "DOCUMENT_NOT_FOUND"}}

        # Get child table name
        child_table = f"`tab{doctype} Item`"

        # Get document items
        items = frappe.db.sql(f"""
            SELECT
                pri.name,
                pri.item_code,
                pri.item_name,
                pri.description,
                pri.qty,
                pri.received_qty,
                pri.uom,
                pri.warehouse,
                pri.batch_no,
                pri.serial_no,
                pri.rate,
                pri.amount,
                pri.conversion_factor,
                pri.stock_uom,
                pri.stock_qty,
                pri.custom_color,
                i.item_group,
                i.stock_uom as item_stock_uom,
                i.has_batch_no,
                i.has_serial_no
            FROM {child_table} pri
            LEFT JOIN `tabItem` i ON pri.item_code = i.name
            WHERE pri.parent = %(doc_id)s
            ORDER BY pri.idx
        """, {"doc_id": doc_id}, as_dict=True)

        # Format items for mobile display
        formatted_items = []
        for item in items:
            formatted_item = {
                "name": item.name,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "qty": flt(item.qty),
                "received_qty": flt(item.received_qty),
                "uom": item.uom,
                "warehouse": item.warehouse,
                "batch_no": item.batch_no,
                "serial_no": item.serial_no,
                "rate": flt(item.rate),
                "amount": flt(item.amount),
                "conversion_factor": flt(item.conversion_factor),
                "stock_uom": item.stock_uom,
                "stock_qty": flt(item.stock_qty),
                "custom_color": item.custom_color,
                "custom_roll_box_no": item.custom_roll_box_no,
                "custom_composition": item.custom_composition,
                "item_group": item.item_group,
                "item_stock_uom": item.item_stock_uom,
                "has_batch_no": item.has_batch_no,
                "has_serial_no": item.has_serial_no,
                "display_name": f"{item.item_code} - {item.item_name}",
                "amount_display": f"{flt(item.amount):,.2f}",
                "rate_display": f"{flt(item.rate):,.2f}"
            }
            formatted_items.append(formatted_item)

        return {
            "success": True,
            "data": formatted_items,
            "total": len(formatted_items),
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Get Items Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to get items", "code": "API_ERROR"}}


@frappe.whitelist()
def add_document_item(doctype, doc_id, item_code, warehouse, qty=1, received_qty=None, no_of_boxes=None,
                     batch_no=None, serial_no=None, rate=None):
    """
    Add a new item to document

    Args:
        doctype (str): Document type
        doc_id (str): Document ID
        item_code (str): Item code to add
        warehouse (str): Warehouse for the item
        qty (float): Ordered quantity
        received_qty (float): Actually received quantity
        no_of_boxes (float): Number of boxes/rolls
        batch_no (str): Batch number if applicable
        serial_no (str): Serial number if applicable
        rate (float): Item rate

    Returns:
        dict: Added item details
    """
    try:
        # Validate inputs
        if not doc_id or not item_code or not warehouse:
            return {"success": False, "error": {"message": "Document ID, Item Code, and Warehouse are required", "code": "MISSING_REQUIRED_FIELDS"}}

        # Check if document exists and is editable
        doc = frappe.get_doc(doctype, doc_id)
        if doc.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted document", "code": "INVALID_STATE"}}

        # Get item details
        if not frappe.db.exists("Item", item_code):
            return {"success": False, "error": {"message": "Item not found", "code": "ITEM_NOT_FOUND"}}

        item = frappe.get_doc("Item", item_code)

        # Get default rate if not provided
        if not rate:
            rate = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": "Standard Buying"}, "price_list_rate") or 0

        # Calculate quantities
        qty = flt(qty) or 1
        received_qty = flt(received_qty) or qty
        rate = flt(rate)

        # Create new item row
        item_row = doc.append("items", {})
        item_row.item_code = item_code
        item_row.item_name = item.item_name
        item_row.description = item.description
        item_row.qty = qty
        item_row.received_qty = received_qty
        item_row.uom = item.purchase_uom or item.stock_uom
        item_row.warehouse = warehouse
        item_row.rate = rate
        item_row.amount = received_qty * rate
        item_row.conversion_factor = 1
        item_row.stock_uom = item.stock_uom
        item_row.stock_qty = received_qty

        # Add optional fields
        if batch_no:
            item_row.batch_no = batch_no
        if serial_no:
            item_row.serial_no = serial_no
        if no_of_boxes:
            item_row.custom_no_of_boxes = flt(no_of_boxes)

        # Save the document
        doc.save()

        return {
            "success": True,
            "message": "Item added successfully",
            "data": {
                "name": item_row.name,
                "item_code": item_row.item_code,
                "item_name": item_row.item_name,
                "qty": flt(item_row.qty),
                "received_qty": flt(item_row.received_qty),
                "rate": flt(item_row.rate),
                "amount": flt(item_row.amount),
                "warehouse": item_row.warehouse
            },
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Add Item Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to add item", "code": "API_ERROR"}}


@frappe.whitelist()
def update_document_item(doctype, item_id, **kwargs):
    """
    Update an existing document item

    Args:
        doctype (str): Document type
        item_id (str): Item ID
        **kwargs: Fields to update (qty, received_qty, warehouse, rate, etc.)

    Returns:
        dict: Updated item details
    """
    try:
        # Get child table name
        child_table = f"{doctype} Item"

        # Check if item exists
        if not frappe.db.exists(child_table, item_id):
            return {"success": False, "error": {"message": "Item not found", "code": "ITEM_NOT_FOUND"}}

        # Get the item and parent document
        item_doc = frappe.get_doc(child_table, item_id)
        doc = frappe.get_doc(doctype, item_doc.parent)

        if doc.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted document", "code": "INVALID_STATE"}}

        # Update allowed fields
        allowed_fields = ['qty', 'received_qty', 'warehouse', 'rate', 'batch_no', 'serial_no', 'custom_no_of_boxes']
        updated_fields = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field in ['qty', 'received_qty', 'rate', 'custom_no_of_boxes']:
                    setattr(item_doc, field, flt(value))
                else:
                    setattr(item_doc, field, value)
                updated_fields.append(field)

        # Recalculate amount if qty or rate changed
        if 'received_qty' in updated_fields or 'rate' in updated_fields:
            item_doc.amount = item_doc.received_qty * item_doc.rate
            item_doc.stock_qty = item_doc.received_qty * item_doc.conversion_factor

        # Save the document
        doc.save()

        return {
            "success": True,
            "message": "Item updated successfully",
            "data": {
                "name": item_doc.name,
                "item_code": item_doc.item_code,
                "qty": flt(item_doc.qty),
                "received_qty": flt(item_doc.received_qty),
                "rate": flt(item_doc.rate),
                "amount": flt(item_doc.amount),
                "warehouse": item_doc.warehouse,
                "updated_fields": updated_fields
            },
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Update Item Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to update item", "code": "API_ERROR"}}


@frappe.whitelist()
def delete_document_item(doctype, item_id):
    """
    Delete a document item

    Args:
        doctype (str): Document type
        item_id (str): Item ID

    Returns:
        dict: Success confirmation
    """
    try:
        # Get child table name
        child_table = f"{doctype} Item"

        # Check if item exists
        if not frappe.db.exists(child_table, item_id):
            return {"success": False, "error": {"message": "Item not found", "code": "ITEM_NOT_FOUND"}}

        # Get the item and parent document
        item_doc = frappe.get_doc(child_table, item_id)
        doc = frappe.get_doc(doctype, item_doc.parent)

        if doc.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted document", "code": "INVALID_STATE"}}

        # Remove the item from document
        for i, row in enumerate(doc.items):
            if row.name == item_id:
                del doc.items[i]
                break

        # Save the document
        doc.save()

        return {
            "success": True,
            "message": "Item deleted successfully",
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile Utils Delete Item Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to delete item", "code": "API_ERROR"}}


@frappe.whitelist()
def validate_document_items(doctype, doc_id):
    """
    Validate document items before moving to next tab

    Args:
        doctype (str): Document type
        doc_id (str): Document ID

    Returns:
        dict: Validation results
    """
    try:
        doc = frappe.get_doc(doctype, doc_id)
        validation_results = {"is_valid": True, "can_proceed": True, "issues": []}

        # Check if there are any items
        if not doc.items:
            validation_results["is_valid"] = False
            validation_results["can_proceed"] = False
            validation_results["issues"].append("At least one item is required")

        # Validate each item
        for item in doc.items:
            item_issues = []

            # Check required fields
            if not item.item_code:
                item_issues.append("Item code is required")
            if not item.warehouse:
                item_issues.append("Warehouse is required")
            if flt(item.received_qty) <= 0:
                item_issues.append("Received quantity must be greater than 0")

            # Check batch requirement
            if item.item_code:
                has_batch = frappe.db.get_value("Item", item.item_code, "has_batch_no")
                if has_batch and not item.batch_no:
                    item_issues.append("Batch number is required for this item")

            if item_issues:
                validation_results["is_valid"] = False
                validation_results["issues"].extend([f"Item {item.item_code}: {issue}" for issue in item_issues])

        # Final validation
        if validation_results["issues"]:
            validation_results["can_proceed"] = False

        message = "Items validation successful" if validation_results["is_valid"] else "Items validation failed"

        return {"success": True, "data": validation_results, "message": message}

    except Exception as e:
        frappe.log_error("Mobile Utils Validate Items Error", frappe.get_traceback())
        return {"success": False, "error": {"message": "Items validation failed", "code": "VALIDATION_ERROR"}}
