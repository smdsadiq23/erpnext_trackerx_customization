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
            filters={"disabled": 0},
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
        values = {}

        if company:
            conditions.append("company = %(company)s")
            values["company"] = company

        # Get tax accounts
        accounts = frappe.db.sql(f"""
            SELECT
                name,
                account_name,
                account_type,
                company
            FROM `tabAccount`
            WHERE {' AND '.join(conditions)}
            AND (account_type LIKE '%Tax%' OR account_type IN ('Chargeable', 'Expense Account'))
            ORDER BY account_name
        """, values, as_dict=True)

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
        frappe.log_error("Mobile Utils Tax Accounts Error", frappe.get_traceback())
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
        frappe.log_error(f"Error in get_document_status_summary for {doctype}: {str(e)}", "Mobile Utils Status Summary Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "DOCUMENT_STATUS_SUMMARY_ERROR"
            }
        }
