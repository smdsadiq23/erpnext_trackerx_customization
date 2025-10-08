import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, now_datetime
import json
from datetime import datetime, timedelta


# ===========================
# PAGE 1: GRN LIST APIs
# ===========================

@frappe.whitelist()
def get_grn_list(search=None, status=None, company=None, supplier=None,
                 date_from=None, date_to=None, page=1, limit=20, sort_by="creation", sort_order="desc"):
    """
    Get paginated GRN list with filters and search functionality

    Args:
        search (str): Search term for GRN ID, supplier name, or PO number
        status (str): Filter by GRN status (Draft, Submitted, Cancelled)
        company (str): Filter by company
        supplier (str): Filter by supplier
        date_from (str): Filter from date (YYYY-MM-DD)
        date_to (str): Filter to date (YYYY-MM-DD)
        page (int): Page number for pagination
        limit (int): Number of records per page
        sort_by (str): Field to sort by
        sort_order (str): Sort order (asc/desc)

    Returns:
        dict: Paginated GRN list with filters
    """
    try:
        page = cint(page) or 1
        limit = cint(limit) or 20
        offset = (page - 1) * limit

        # Build conditions
        conditions = ["pr.docstatus != 2"]  # Exclude deleted records
        values = {}

        # Search functionality
        if search:
            search_condition = """(
                pr.name LIKE %(search)s OR
                pr.supplier LIKE %(search)s OR
                pr.supplier_name LIKE %(search)s OR
                pr.remarks LIKE %(search)s
            )"""
            conditions.append(search_condition)
            values["search"] = f"%{search}%"

        # Status filter
        if status:
            if status.lower() == "draft":
                conditions.append("pr.docstatus = 0")
            elif status.lower() == "submitted":
                conditions.append("pr.docstatus = 1")
            elif status.lower() == "cancelled":
                conditions.append("pr.docstatus = 2")

        # Company filter
        if company:
            conditions.append("pr.company = %(company)s")
            values["company"] = company

        # Supplier filter
        if supplier:
            conditions.append("pr.supplier = %(supplier)s")
            values["supplier"] = supplier

        # Date range filter
        if date_from:
            conditions.append("pr.posting_date >= %(date_from)s")
            values["date_from"] = date_from

        if date_to:
            conditions.append("pr.posting_date <= %(date_to)s")
            values["date_to"] = date_to

        # Build WHERE clause
        where_clause = " AND ".join(conditions)

        # Validate sort fields
        allowed_sort_fields = ["creation", "modified", "posting_date", "name", "supplier", "grand_total"]
        if sort_by not in allowed_sort_fields:
            sort_by = "creation"

        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"

        # Main query for GRN list
        query = f"""
            SELECT
                pr.name as id,
                pr.title,
                pr.supplier,
                pr.supplier_name,
                pr.company,
                pr.posting_date as date,
                pr.grand_total,
                pr.currency,
                pr.docstatus,
                pr.status as workflow_status,
                pr.remarks,
                pr.is_return,
                pr.modified,
                pr.creation,
                CASE
                    WHEN pr.docstatus = 0 THEN 'Draft'
                    WHEN pr.docstatus = 1 AND pr.is_return = 1 THEN 'Return'
                    WHEN pr.docstatus = 1 THEN 'Submitted'
                    WHEN pr.docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END as status,
                COUNT(pri.name) as total_items
            FROM `tabPurchase Receipt` pr
            LEFT JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name
            WHERE {where_clause}
            GROUP BY pr.name
            ORDER BY pr.{sort_by} {sort_order.upper()}
            LIMIT %(limit)s OFFSET %(offset)s
        """

        values.update({"limit": limit, "offset": offset})

        # Execute query
        grn_list = frappe.db.sql(query, values, as_dict=True)

        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT pr.name) as total
            FROM `tabPurchase Receipt` pr
            WHERE {where_clause}
        """

        total_count = frappe.db.sql(count_query, values, as_dict=True)[0].total
        total_pages = (total_count + limit - 1) // limit

        # Format the response
        for grn in grn_list:
            # Format dates
            if grn.get("date"):
                grn["date"] = str(grn["date"])
            if grn.get("modified"):
                grn["modified"] = grn["modified"].isoformat() if grn["modified"] else None
            if grn.get("creation"):
                grn["creation"] = grn["creation"].isoformat() if grn["creation"] else None

            # Format amounts
            grn["grand_total"] = flt(grn.get("grand_total", 0), 2)

            # Add status color for mobile UI
            status_colors = {
                "Draft": "#6c757d",
                "Submitted": "#28a745",
                "Cancelled": "#dc3545",
                "Return": "#fd7e14"
            }
            grn["status_color"] = status_colors.get(grn.get("status"), "#6c757d")

        return {
            "success": True,
            "data": grn_list,
            "pagination": {
                "page": page,
                "per_page": limit,
                "total": total_count,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "filters_applied": {
                "search": search,
                "status": status,
                "company": company,
                "supplier": supplier,
                "date_from": date_from,
                "date_to": date_to
            },
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error in get_grn_list: {str(e)}", "Mobile GRN List Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_LIST_ERROR"
            }
        }

@frappe.whitelist()
def get_grn_filters():
    """
    Get available filter options for GRN list

    Returns:
        dict: Available filter options
    """
    try:
        # Get unique companies
        companies = frappe.db.sql("""
            SELECT DISTINCT company, company as label
            FROM `tabPurchase Receipt`
            WHERE docstatus != 2
            ORDER BY company
        """, as_dict=True)

        # Get unique suppliers
        suppliers = frappe.db.sql("""
            SELECT DISTINCT supplier, supplier_name as label
            FROM `tabPurchase Receipt`
            WHERE docstatus != 2 AND supplier IS NOT NULL
            ORDER BY supplier_name
        """, as_dict=True)

        # Get status options
        statuses = [
            {"value": "draft", "label": "Draft"},
            {"value": "submitted", "label": "Submitted"},
            {"value": "cancelled", "label": "Cancelled"}
        ]

        # Get date range (last 6 months of data)
        date_range = frappe.db.sql("""
            SELECT
                MIN(posting_date) as min_date,
                MAX(posting_date) as max_date
            FROM `tabPurchase Receipt`
            WHERE docstatus != 2
        """, as_dict=True)[0]

        return {
            "success": True,
            "data": {
                "companies": companies,
                "suppliers": suppliers,
                "statuses": statuses,
                "date_range": {
                    "min_date": str(date_range.min_date) if date_range.min_date else None,
                    "max_date": str(date_range.max_date) if date_range.max_date else None
                }
            }
        }

    except Exception as e:
        frappe.log_error(f"Error in get_grn_filters: {str(e)}", "Mobile GRN Filters Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_FILTERS_ERROR"
            }
        }

@frappe.whitelist()
def search_grn(search_term, limit=10):
    """
    Quick search GRNs by ID, supplier name, or PO number

    Args:
        search_term (str): Search term
        limit (int): Maximum number of results

    Returns:
        dict: Quick search results
    """
    try:
        if not search_term:
            return {
                "success": True,
                "data": [],
                "message": "Please provide a search term"
            }

        limit = cint(limit) or 10

        query = """
            SELECT
                pr.name as id,
                pr.title,
                pr.supplier,
                pr.supplier_name,
                pr.posting_date as date,
                pr.grand_total,
                pr.currency,
                CASE
                    WHEN pr.docstatus = 0 THEN 'Draft'
                    WHEN pr.docstatus = 1 AND pr.is_return = 1 THEN 'Return'
                    WHEN pr.docstatus = 1 THEN 'Submitted'
                    WHEN pr.docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END as status
            FROM `tabPurchase Receipt` pr
            WHERE pr.docstatus != 2
            AND (
                pr.name LIKE %(search)s OR
                pr.supplier LIKE %(search)s OR
                pr.supplier_name LIKE %(search)s OR
                pr.bill_no LIKE %(search)s OR
                pr.supplier_delivery_note LIKE %(search)s
            )
            ORDER BY pr.modified DESC
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
        frappe.log_error(f"Error in search_grn: {str(e)}", "Mobile GRN Search Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_SEARCH_ERROR"
            }
        }

@frappe.whitelist()
def get_grn_status_summary():
    """
    Get count of GRNs by status for dashboard display

    Returns:
        dict: Status-wise GRN counts
    """
    try:
        # Get count by status
        status_counts = frappe.db.sql("""
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
            FROM `tabPurchase Receipt`
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
        frappe.log_error(f"Error in get_grn_status_summary: {str(e)}", "Mobile GRN Status Summary Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_STATUS_SUMMARY_ERROR"
            }
        }

# ===========================
# PAGE 2: GRN DETAILS APIs
# ===========================

@frappe.whitelist()
def create_grn():
    """
    Create new GRN with default values

    Returns:
        dict: New GRN details with default values
    """
    try:
        # Get user defaults
        user_defaults = frappe.get_user_default_values()
        default_company = user_defaults.get("company") or frappe.db.get_single_value("Global Defaults", "default_company")

        # Create new Purchase Receipt document
        grn = frappe.new_doc("Purchase Receipt")

        # Set default values
        grn.posting_date = getdate()
        grn.posting_time = now_datetime().time()
        grn.set_posting_time = 0
        grn.company = default_company
        grn.is_return = 0
        grn.apply_putaway_rule = 0

        # Get default naming series
        naming_series = frappe.db.get_value("Purchase Receipt", {"company": default_company}, "naming_series")
        if not naming_series:
            naming_series = frappe.get_meta("Purchase Receipt").get_field("naming_series").options.split("\n")[0]

        grn.naming_series = naming_series

        # Insert document (save as draft)
        grn.insert(ignore_permissions=True)

        return {
            "success": True,
            "data": {
                "grn_id": grn.name,
                "series": grn.naming_series,
                "posting_date": str(grn.posting_date),
                "posting_time": str(grn.posting_time) if grn.posting_time else None,
                "company": grn.company,
                "is_return": grn.is_return,
                "apply_putaway_rule": grn.apply_putaway_rule,
                "set_posting_time": grn.set_posting_time,
                "docstatus": grn.docstatus,
                "workflow_state": grn.workflow_state,
                "creation": grn.creation.isoformat() if grn.creation else None,
                "modified": grn.modified.isoformat() if grn.modified else None
            },
            "message": "GRN created successfully"
        }

    except Exception as e:
        frappe.log_error(f"Error creating GRN: {str(e)}", "Mobile GRN Create Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_CREATE_ERROR"
            }
        }

@frappe.whitelist()
def get_grn(grn_id):
    """
    Get GRN details by ID

    Args:
        grn_id (str): GRN document name

    Returns:
        dict: GRN details
    """
    try:
        if not grn_id:
            return {
                "success": False,
                "error": {
                    "message": "GRN ID is required",
                    "code": "GRN_ID_REQUIRED"
                }
            }

        # Check if GRN exists
        if not frappe.db.exists("Purchase Receipt", grn_id):
            return {
                "success": False,
                "error": {
                    "message": f"GRN {grn_id} not found",
                    "code": "GRN_NOT_FOUND"
                }
            }

        # Get GRN document
        grn = frappe.get_doc("Purchase Receipt", grn_id)

        # Format response using getattr for safe access to potentially non-existent fields
        grn_data = {
            "grn_id": grn.name,
            "title": getattr(grn, "title", ""),
            "naming_series": getattr(grn, "naming_series", ""),
            "company": grn.company,
            "posting_date": str(grn.posting_date) if grn.posting_date else None,
            "posting_time": str(grn.posting_time) if grn.posting_time else None,
            "set_posting_time": getattr(grn, "set_posting_time", 0),
            "supplier": grn.supplier,
            "supplier_name": getattr(grn, "supplier_name", ""),
            "supplier_delivery_note": getattr(grn, "supplier_delivery_note", ""),
            "bill_no": getattr(grn, "bill_no", ""),
            "bill_date": str(getattr(grn, "bill_date", "")) if getattr(grn, "bill_date", None) else None,
            "is_return": getattr(grn, "is_return", 0),
            "apply_putaway_rule": getattr(grn, "apply_putaway_rule", 0),
            "is_subcontracted": getattr(grn, "is_subcontracted", 0),
            "purchase_order": getattr(grn, "purchase_order", None),
            "currency": getattr(grn, "currency", ""),
            "conversion_rate": flt(getattr(grn, "conversion_rate", 1), 4),
            "buying_price_list": getattr(grn, "buying_price_list", ""),
            "price_list_currency": getattr(grn, "price_list_currency", ""),
            "plc_conversion_rate": flt(getattr(grn, "plc_conversion_rate", 1), 4),
            "ignore_pricing_rule": getattr(grn, "ignore_pricing_rule", 0),
            "scan_barcode": getattr(grn, "scan_barcode", None),
            "docstatus": grn.docstatus,
            "workflow_state": getattr(grn, "workflow_state", ""),
            "status": getattr(grn, "status", ""),
            "per_billed": flt(getattr(grn, "per_billed", 0), 2),
            "total_qty": flt(getattr(grn, "total_qty", 0), 2),
            "total": flt(getattr(grn, "total", 0), 2),
            "net_total": flt(getattr(grn, "net_total", 0), 2),
            "total_taxes_and_charges": flt(getattr(grn, "total_taxes_and_charges", 0), 2),
            "discount_amount": flt(getattr(grn, "discount_amount", 0), 2),
            "grand_total": flt(getattr(grn, "grand_total", 0), 2),
            "rounded_total": flt(getattr(grn, "rounded_total", 0), 2),
            "in_words": getattr(grn, "in_words", ""),
            "creation": grn.creation.isoformat() if grn.creation else None,
            "modified": grn.modified.isoformat() if grn.modified else None,
            "owner": grn.owner,
            "modified_by": grn.modified_by
        }

        # Get related purchase order details if available
        if grn.items and grn.items[0].purchase_order:
            po_name = grn.items[0].purchase_order
            po_details = frappe.db.get_value("Purchase Order", po_name,
                ["supplier", "supplier_name", "transaction_date", "status"], as_dict=True)
            if po_details:
                grn_data["purchase_order_details"] = {
                    "name": po_name,
                    "supplier": po_details.supplier,
                    "supplier_name": po_details.supplier_name,
                    "date": str(po_details.transaction_date) if po_details.transaction_date else None,
                    "status": po_details.status
                }

        return {
            "success": True,
            "data": grn_data
        }

    except Exception as e:
        frappe.log_error(f"Error getting GRN {grn_id}: {str(e)}", "Mobile GRN Get Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_GET_ERROR"
            }
        }

@frappe.whitelist()
def update_grn_header(grn_id, **kwargs):
    """
    Update GRN header information

    Args:
        grn_id (str): GRN document name
        **kwargs: Fields to update

    Returns:
        dict: Update result
    """
    try:
        if not grn_id:
            return {
                "success": False,
                "error": {
                    "message": "GRN ID is required",
                    "code": "GRN_ID_REQUIRED"
                }
            }

        # Get GRN document
        grn = frappe.get_doc("Purchase Receipt", grn_id)

        # Check if GRN can be modified
        if grn.docstatus != 0:
            return {
                "success": False,
                "error": {
                    "message": f"Cannot modify {grn.status} GRN",
                    "code": "GRN_NOT_DRAFT"
                }
            }

        # Track changes
        changes = {}

        # Update allowed fields
        updatable_fields = [
            'posting_date', 'posting_time', 'set_posting_time', 'company',
            'supplier_delivery_note', 'bill_no', 'bill_date', 'is_return',
            'apply_putaway_rule', 'purchase_order', 'supplier', 'title'
        ]

        for field, value in kwargs.items():
            if field in updatable_fields and hasattr(grn, field):
                old_value = getattr(grn, field)

                # Handle date fields
                if field in ['posting_date', 'bill_date'] and value:
                    value = getdate(value)

                # Handle time fields
                if field == 'posting_time' and value:
                    from frappe.utils import get_time
                    value = get_time(value)

                # Handle boolean fields
                if field in ['set_posting_time', 'is_return', 'apply_putaway_rule']:
                    value = cint(value)

                # Handle float fields
                if field in ['conversion_rate', 'plc_conversion_rate']:
                    value = flt(value)

                if old_value != value:
                    setattr(grn, field, value)
                    changes[field] = {"old": old_value, "new": value}

        # If purchase order is updated, update supplier automatically
        if 'purchase_order' in changes and changes['purchase_order']['new']:
            po_name = changes['purchase_order']['new']
            po_supplier = frappe.db.get_value("Purchase Order", po_name, "supplier")
            if po_supplier and po_supplier != grn.supplier:
                grn.supplier = po_supplier
                changes['supplier'] = {"old": grn.supplier, "new": po_supplier}

        # Save document if changes were made
        if changes:
            grn.save(ignore_permissions=True)

        return {
            "success": True,
            "data": {
                "grn_id": grn.name,
                "changes_made": len(changes),
                "changes": changes,
                "modified": grn.modified.isoformat() if grn.modified else None
            },
            "message": f"GRN updated successfully. {len(changes)} field(s) changed."
        }

    except Exception as e:
        frappe.log_error(f"Error updating GRN {grn_id}: {str(e)}", "Mobile GRN Update Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_UPDATE_ERROR"
            }
        }

@frappe.whitelist()
def get_naming_series():
    """
    Get available naming series for Purchase Receipt

    Returns:
        dict: Available naming series
    """
    try:
        # Get naming series from Purchase Receipt doctype
        naming_series_field = frappe.get_meta("Purchase Receipt").get_field("naming_series")

        if not naming_series_field or not naming_series_field.options:
            return {
                "success": False,
                "error": {
                    "message": "No naming series configured for Purchase Receipt",
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
        frappe.log_error(f"Error getting naming series: {str(e)}", "Mobile GRN Naming Series Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "NAMING_SERIES_ERROR"
            }
        }

@frappe.whitelist()
def get_companies():
    """
    Get companies list for dropdown

    Returns:
        dict: Available companies
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
        frappe.log_error(f"Error getting companies: {str(e)}", "Mobile GRN Companies Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "COMPANIES_ERROR"
            }
        }

@frappe.whitelist()
def get_purchase_orders(supplier=None, company=None, search=None):
    """
    Get purchase orders for dropdown

    Args:
        supplier (str): Filter by supplier
        company (str): Filter by company
        search (str): Search term

    Returns:
        dict: Available purchase orders
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
        frappe.log_error(f"Error getting purchase orders: {str(e)}", "Mobile GRN PO Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "PURCHASE_ORDERS_ERROR"
            }
        }

@frappe.whitelist()
def validate_grn_header(grn_id):
    """
    Validate GRN header before moving to next tab

    Args:
        grn_id (str): GRN document name

    Returns:
        dict: Validation result
    """
    try:
        if not grn_id:
            return {
                "success": False,
                "error": {
                    "message": "GRN ID is required",
                    "code": "GRN_ID_REQUIRED"
                }
            }

        # Get GRN document
        grn = frappe.get_doc("Purchase Receipt", grn_id)

        # Validation rules
        errors = []
        warnings = []

        # Required field validations
        if not grn.company:
            errors.append("Company is required")

        if not grn.posting_date:
            errors.append("Posting date is required")

        # Business logic validations
        if grn.posting_date and getdate(grn.posting_date) > getdate():
            warnings.append("Posting date is in the future")

        if grn.is_return and not grn.return_against:
            warnings.append("Return against document is recommended for return entries")

        # Purchase order validations
        if grn.items:
            po_list = list(set([item.purchase_order for item in grn.items if item.purchase_order]))
            if len(po_list) > 1:
                warnings.append("Multiple purchase orders found in items")

        return {
            "success": True,
            "data": {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "can_proceed": len(errors) == 0,
                "grn_id": grn.name,
                "status": grn.status
            },
            "message": "Validation completed" if len(errors) == 0 else f"Validation failed with {len(errors)} error(s)"
        }

    except Exception as e:
        frappe.log_error(f"Error validating GRN {grn_id}: {str(e)}", "Mobile GRN Validation Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "GRN_VALIDATION_ERROR"
            }
        }


# ===========================
# PAGE 3: GRN ITEMS APIs
# ===========================

@frappe.whitelist()
def get_grn_items(grn_id):
    """
    Get all items in a GRN for the Items tab

    Args:
        grn_id (str): GRN document ID

    Returns:
        dict: List of GRN items with details
    """
    try:
        # Check if GRN exists and user has permission
        if not frappe.db.exists("Purchase Receipt", grn_id):
            return {"success": False, "error": {"message": "GRN not found", "code": "GRN_NOT_FOUND"}}

        # Get GRN items
        items = frappe.db.sql("""
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
                pri.custom_roll_box_no,
                pri.custom_composition,
                pri.custom_no_of_boxes,
                i.item_group,
                i.stock_uom as item_stock_uom,
                i.has_batch_no,
                i.has_serial_no,
                i.maintain_stock
            FROM `tabPurchase Receipt Item` pri
            LEFT JOIN `tabItem` i ON pri.item_code = i.name
            WHERE pri.parent = %(grn_id)s
            ORDER BY pri.idx
        """, {"grn_id": grn_id}, as_dict=True)

        # Format items for mobile display
        formatted_items = []
        for item in items:
            formatted_item = {
                "id": item.name,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "qty": flt(item.qty),
                "received_qty": flt(item.received_qty),
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "warehouse": item.warehouse,
                "batch_no": item.batch_no,
                "serial_no": item.serial_no,
                "rate": flt(item.rate),
                "amount": flt(item.amount),
                "conversion_factor": flt(item.conversion_factor),
                "stock_qty": flt(item.stock_qty),

                # Custom fields for mobile display
                "color": item.custom_color,
                "roll_box_no": item.custom_roll_box_no,
                "composition": item.custom_composition,
                "no_of_boxes": flt(item.custom_no_of_boxes),

                # Item master data
                "item_group": item.item_group,
                "has_batch_no": item.has_batch_no,
                "has_serial_no": item.has_serial_no,
                "maintain_stock": item.maintain_stock,

                # UI helpers
                "display_name": f"{item.item_code} - {item.item_name}",
                "qty_display": f"{flt(item.received_qty)} {item.uom}",
                "amount_display": f"{flt(item.amount):,.2f}"
            }
            formatted_items.append(formatted_item)

        return {
            "success": True,
            "data": formatted_items,
            "summary": {
                "total_items": len(formatted_items),
                "total_qty": sum(flt(item["received_qty"]) for item in formatted_items),
                "total_amount": sum(flt(item["amount"]) for item in formatted_items)
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error getting GRN items: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to get GRN items", "code": "API_ERROR"}}


@frappe.whitelist()
def add_grn_item(grn_id, item_code, warehouse, qty=1, received_qty=None, no_of_boxes=None,
                 batch_no=None, serial_no=None, rate=None):
    """
    Add a new item to GRN

    Args:
        grn_id (str): GRN document ID
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
        if not grn_id or not item_code or not warehouse:
            return {"success": False, "error": {"message": "GRN ID, Item Code, and Warehouse are required", "code": "MISSING_REQUIRED_FIELDS"}}

        # Check if GRN exists and is editable
        grn = frappe.get_doc("Purchase Receipt", grn_id)
        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Get item details
        item = frappe.get_doc("Item", item_code)
        if not item:
            return {"success": False, "error": {"message": "Item not found", "code": "ITEM_NOT_FOUND"}}

        # Get default rate if not provided
        if not rate:
            rate = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": "Standard Buying"}, "price_list_rate") or 0

        # Calculate quantities
        qty = flt(qty) or 1
        received_qty = flt(received_qty) or qty
        rate = flt(rate)

        # Create new item row
        item_row = grn.append("items", {})
        item_row.item_code = item_code
        item_row.item_name = item.item_name
        item_row.description = item.description
        item_row.qty = qty
        item_row.received_qty = received_qty
        item_row.uom = item.purchase_uom or item.stock_uom
        item_row.stock_uom = item.stock_uom
        item_row.conversion_factor = 1
        item_row.stock_qty = received_qty
        item_row.warehouse = warehouse
        item_row.rate = rate
        item_row.amount = received_qty * rate

        # Set custom fields
        if no_of_boxes:
            item_row.custom_no_of_boxes = flt(no_of_boxes)
        if batch_no and item.has_batch_no:
            item_row.batch_no = batch_no
        if serial_no and item.has_serial_no:
            item_row.serial_no = serial_no

        # Save the GRN
        grn.save()

        # Return the added item details
        added_item = {
            "id": item_row.name,
            "item_code": item_code,
            "item_name": item.item_name,
            "description": item.description,
            "qty": qty,
            "received_qty": received_qty,
            "uom": item_row.uom,
            "warehouse": warehouse,
            "batch_no": batch_no,
            "serial_no": serial_no,
            "rate": rate,
            "amount": item_row.amount,
            "no_of_boxes": flt(no_of_boxes),
            "display_name": f"{item_code} - {item.item_name}",
            "qty_display": f"{received_qty} {item_row.uom}",
            "amount_display": f"{item_row.amount:,.2f}"
        }

        return {
            "success": True,
            "data": added_item,
            "message": "Item added successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error adding GRN item: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to add item", "code": "API_ERROR"}}


@frappe.whitelist()
def update_grn_item(item_id, **kwargs):
    """
    Update an existing GRN item

    Args:
        item_id (str): Purchase Receipt Item ID
        **kwargs: Fields to update (qty, received_qty, warehouse, rate, etc.)

    Returns:
        dict: Updated item details
    """
    try:
        # Check if item exists
        if not frappe.db.exists("Purchase Receipt Item", item_id):
            return {"success": False, "error": {"message": "Item not found", "code": "ITEM_NOT_FOUND"}}

        # Get the item and parent GRN
        item_doc = frappe.get_doc("Purchase Receipt Item", item_id)
        grn = frappe.get_doc("Purchase Receipt", item_doc.parent)

        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

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

        # Save the GRN
        grn.save()

        return {
            "success": True,
            "data": {
                "id": item_id,
                "updated_fields": updated_fields,
                "qty": item_doc.qty,
                "received_qty": item_doc.received_qty,
                "warehouse": item_doc.warehouse,
                "rate": item_doc.rate,
                "amount": item_doc.amount,
                "batch_no": item_doc.batch_no,
                "serial_no": item_doc.serial_no,
                "no_of_boxes": item_doc.custom_no_of_boxes
            },
            "message": "Item updated successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error updating GRN item: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to update item", "code": "API_ERROR"}}


@frappe.whitelist()
def delete_grn_item(item_id):
    """
    Delete a GRN item

    Args:
        item_id (str): Purchase Receipt Item ID

    Returns:
        dict: Success confirmation
    """
    try:
        # Check if item exists
        if not frappe.db.exists("Purchase Receipt Item", item_id):
            return {"success": False, "error": {"message": "Item not found", "code": "ITEM_NOT_FOUND"}}

        # Get the item and parent GRN
        item_doc = frappe.get_doc("Purchase Receipt Item", item_id)
        grn = frappe.get_doc("Purchase Receipt", item_doc.parent)

        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Remove the item from GRN
        for i, row in enumerate(grn.items):
            if row.name == item_id:
                del grn.items[i]
                break

        # Save the GRN
        grn.save()

        return {
            "success": True,
            "message": "Item deleted successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error deleting GRN item: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to delete item", "code": "API_ERROR"}}


@frappe.whitelist()
def search_items(search_term, supplier=None, company=None, limit=10):
    """
    Search items for adding to GRN

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
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error searching items: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to search items", "code": "API_ERROR"}}


@frappe.whitelist()
def get_warehouses(company=None):
    """
    Get list of warehouses for dropdown

    Args:
        company (str): Filter by company (optional)

    Returns:
        dict: List of warehouses
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
        frappe.log_error(f"Error getting warehouses: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to get warehouses", "code": "API_ERROR"}}


@frappe.whitelist()
def get_batch_numbers(item_code, warehouse=None):
    """
    Get available batch numbers for an item

    Args:
        item_code (str): Item code
        warehouse (str): Warehouse to filter batches (optional)

    Returns:
        dict: List of batch numbers
    """
    try:
        if not item_code:
            return {"success": False, "error": {"message": "Item code is required", "code": "MISSING_REQUIRED_FIELDS"}}

        # Check if item has batch tracking
        has_batch = frappe.db.get_value("Item", item_code, "has_batch_no")
        if not has_batch:
            return {"success": True, "data": [], "message": "Item does not use batch tracking"}

        conditions = ["b.disabled = 0", "b.item = %(item_code)s"]
        values = {"item_code": item_code}

        if warehouse:
            conditions.append("sle.warehouse = %(warehouse)s")
            values["warehouse"] = warehouse

        # Get batches with available stock
        query = f"""
            SELECT DISTINCT
                b.name as batch_no,
                b.batch_id,
                b.manufacturing_date,
                b.expiry_date,
                COALESCE(SUM(sle.actual_qty), 0) as available_qty
            FROM `tabBatch` b
            LEFT JOIN `tabStock Ledger Entry` sle ON b.name = sle.batch_no
            WHERE {' AND '.join(conditions)}
            GROUP BY b.name
            HAVING available_qty > 0
            ORDER BY b.creation DESC
        """

        batches = frappe.db.sql(query, values, as_dict=True)

        formatted_batches = []
        for batch in batches:
            formatted_batch = {
                "value": batch.batch_no,
                "label": batch.batch_id or batch.batch_no,
                "manufacturing_date": batch.manufacturing_date,
                "expiry_date": batch.expiry_date,
                "available_qty": flt(batch.available_qty)
            }
            formatted_batches.append(formatted_batch)

        return {
            "success": True,
            "data": formatted_batches,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error getting batch numbers: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to get batch numbers", "code": "API_ERROR"}}


@frappe.whitelist()
def validate_grn_items(grn_id):
    """
    Validate GRN items before moving to next tab

    Args:
        grn_id (str): GRN document ID

    Returns:
        dict: Validation results
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)
        validation_results = {"is_valid": True, "can_proceed": True, "issues": []}

        # Check if there are any items
        if not grn.items:
            validation_results["is_valid"] = False
            validation_results["can_proceed"] = False
            validation_results["issues"].append("At least one item is required")

        # Validate each item
        for item in grn.items:
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
        frappe.log_error(f"Error validating GRN items: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Items validation failed", "code": "VALIDATION_ERROR"}}


# ===========================
# PAGE 4: TAX/CHARGES APIs
# ===========================

@frappe.whitelist()
def get_grn_taxes_and_charges(grn_id):
    """
    Get taxes and charges for a GRN

    Args:
        grn_id (str): GRN document ID

    Returns:
        dict: Tax and charge details
    """
    try:
        if not frappe.db.exists("Purchase Receipt", grn_id):
            return {"success": False, "error": {"message": "GRN not found", "code": "GRN_NOT_FOUND"}}

        grn = frappe.get_doc("Purchase Receipt", grn_id)

        # Get tax details
        taxes_and_charges = []
        for tax in grn.taxes:
            tax_detail = {
                "id": tax.name,
                "charge_type": tax.charge_type,
                "account_head": tax.account_head,
                "description": tax.description,
                "rate": flt(tax.rate),
                "tax_amount": flt(tax.tax_amount),
                "total": flt(tax.total),
                "base_tax_amount": flt(tax.base_tax_amount),
                "base_total": flt(tax.base_total),
                "cost_center": tax.cost_center
            }
            taxes_and_charges.append(tax_detail)

        # Get header tax information
        tax_info = {
            "tax_category": grn.tax_category,
            "shipping_rule": grn.shipping_rule,
            "incoterm": grn.incoterm,
            "taxes_and_charges_template": grn.taxes_and_charges,
            "taxes_and_charges": taxes_and_charges,
            "net_total": flt(grn.net_total),
            "total_taxes_and_charges": flt(grn.total_taxes_and_charges),
            "grand_total": flt(grn.grand_total),
            "rounded_total": flt(grn.rounded_total),
            "rounding_adjustment": flt(grn.rounding_adjustment),
            "disable_rounded_total": grn.disable_rounded_total or 0,
            "additional_discount_percentage": flt(grn.additional_discount_percentage),
            "discount_amount": flt(grn.discount_amount)
        }

        return {
            "success": True,
            "data": tax_info,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error getting GRN taxes: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to get tax details", "code": "API_ERROR"}}


@frappe.whitelist()
def get_tax_templates():
    """
    Get available Purchase Taxes and Charges templates

    Returns:
        dict: List of tax templates
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
        frappe.log_error(f"Error getting tax templates: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to get tax templates", "code": "API_ERROR"}}


@frappe.whitelist()
def get_tax_accounts(company=None):
    """
    Get tax account heads for dropdown

    Args:
        company (str): Filter by company

    Returns:
        dict: List of tax accounts
    """
    try:
        conditions = ["disabled = 0", "is_group = 0"]
        values = {}

        if company:
            conditions.append("company = %(company)s")
            values["company"] = company

        # Get tax accounts (both income and expense types relevant for purchase)
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
        frappe.log_error(f"Error getting tax accounts: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to get tax accounts", "code": "API_ERROR"}}


@frappe.whitelist()
def apply_tax_template(grn_id, template_name):
    """
    Apply tax template to GRN

    Args:
        grn_id (str): GRN document ID
        template_name (str): Tax template name

    Returns:
        dict: Updated tax information
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)
        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Clear existing taxes
        grn.taxes = []

        # Set the template
        grn.taxes_and_charges = template_name

        if template_name:
            # Get template taxes
            template = frappe.get_doc("Purchase Taxes and Charges Template", template_name)

            # Add template taxes to GRN
            for template_tax in template.taxes:
                tax_row = grn.append("taxes", {})
                tax_row.charge_type = template_tax.charge_type
                tax_row.account_head = template_tax.account_head
                tax_row.description = template_tax.description
                tax_row.rate = template_tax.rate
                tax_row.cost_center = template_tax.cost_center

        # Save and calculate
        grn.save()

        # Return updated tax information
        return get_grn_taxes_and_charges(grn_id)

    except Exception as e:
        frappe.log_error(f"Error applying tax template: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to apply tax template", "code": "API_ERROR"}}


@frappe.whitelist()
def add_tax_charge(grn_id, charge_type, account_head, rate=0, tax_amount=0, description=None):
    """
    Add individual tax/charge to GRN

    Args:
        grn_id (str): GRN document ID
        charge_type (str): Type of charge (On Net Total, Actual, etc.)
        account_head (str): Account head for the charge
        rate (float): Tax rate percentage
        tax_amount (float): Fixed tax amount
        description (str): Description of the charge

    Returns:
        dict: Added tax charge details
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)
        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Validate required fields
        if not charge_type or not account_head:
            return {"success": False, "error": {"message": "Charge type and account head are required", "code": "MISSING_REQUIRED_FIELDS"}}

        # Add new tax row
        tax_row = grn.append("taxes", {})
        tax_row.charge_type = charge_type
        tax_row.account_head = account_head
        tax_row.rate = flt(rate)
        tax_row.tax_amount = flt(tax_amount)
        tax_row.description = description or frappe.db.get_value("Account", account_head, "account_name")

        # Save and calculate
        grn.save()

        # Return the added tax details
        added_tax = {
            "id": tax_row.name,
            "charge_type": tax_row.charge_type,
            "account_head": tax_row.account_head,
            "description": tax_row.description,
            "rate": flt(tax_row.rate),
            "tax_amount": flt(tax_row.tax_amount),
            "total": flt(tax_row.total)
        }

        return {
            "success": True,
            "data": added_tax,
            "message": "Tax charge added successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error adding tax charge: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to add tax charge", "code": "API_ERROR"}}


@frappe.whitelist()
def update_tax_charge(tax_id, **kwargs):
    """
    Update existing tax charge

    Args:
        tax_id (str): Purchase Receipt Tax ID
        **kwargs: Fields to update

    Returns:
        dict: Updated tax details
    """
    try:
        if not frappe.db.exists("Purchase Taxes and Charges", tax_id):
            return {"success": False, "error": {"message": "Tax charge not found", "code": "TAX_NOT_FOUND"}}

        tax_doc = frappe.get_doc("Purchase Taxes and Charges", tax_id)
        grn = frappe.get_doc("Purchase Receipt", tax_doc.parent)

        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Update allowed fields
        allowed_fields = ['rate', 'tax_amount', 'description', 'cost_center']
        updated_fields = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field in ['rate', 'tax_amount']:
                    setattr(tax_doc, field, flt(value))
                else:
                    setattr(tax_doc, field, value)
                updated_fields.append(field)

        # Save and recalculate
        grn.save()

        return {
            "success": True,
            "data": {
                "id": tax_id,
                "updated_fields": updated_fields,
                "rate": tax_doc.rate,
                "tax_amount": tax_doc.tax_amount,
                "total": tax_doc.total,
                "description": tax_doc.description
            },
            "message": "Tax charge updated successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error updating tax charge: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to update tax charge", "code": "API_ERROR"}}


@frappe.whitelist()
def delete_tax_charge(tax_id):
    """
    Delete a tax charge from GRN

    Args:
        tax_id (str): Purchase Receipt Tax ID

    Returns:
        dict: Success confirmation
    """
    try:
        if not frappe.db.exists("Purchase Taxes and Charges", tax_id):
            return {"success": False, "error": {"message": "Tax charge not found", "code": "TAX_NOT_FOUND"}}

        tax_doc = frappe.get_doc("Purchase Taxes and Charges", tax_id)
        grn = frappe.get_doc("Purchase Receipt", tax_doc.parent)

        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Remove the tax from GRN
        for i, row in enumerate(grn.taxes):
            if row.name == tax_id:
                del grn.taxes[i]
                break

        # Save and recalculate
        grn.save()

        return {
            "success": True,
            "message": "Tax charge deleted successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error deleting tax charge: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to delete tax charge", "code": "API_ERROR"}}


@frappe.whitelist()
def update_grn_tax_settings(grn_id, **kwargs):
    """
    Update GRN tax-related settings

    Args:
        grn_id (str): GRN document ID
        **kwargs: Tax settings to update

    Returns:
        dict: Updated settings
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)
        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Update allowed tax settings
        allowed_fields = [
            'tax_category', 'shipping_rule', 'incoterm', 'disable_rounded_total',
            'additional_discount_percentage', 'discount_amount'
        ]
        updated_fields = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field in ['additional_discount_percentage', 'discount_amount']:
                    setattr(grn, field, flt(value))
                elif field == 'disable_rounded_total':
                    setattr(grn, field, cint(value))
                else:
                    setattr(grn, field, value)
                updated_fields.append(field)

        # Save and recalculate totals
        grn.save()

        return {
            "success": True,
            "data": {
                "grn_id": grn.name,
                "updated_fields": updated_fields,
                "net_total": flt(grn.net_total),
                "total_taxes_and_charges": flt(grn.total_taxes_and_charges),
                "grand_total": flt(grn.grand_total),
                "rounded_total": flt(grn.rounded_total)
            },
            "message": "Tax settings updated successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error updating tax settings: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to update tax settings", "code": "API_ERROR"}}


@frappe.whitelist()
def calculate_grn_totals(grn_id):
    """
    Calculate and return GRN totals

    Args:
        grn_id (str): GRN document ID

    Returns:
        dict: Calculated totals
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)

        # Force recalculation
        grn.save()

        totals = {
            "net_total": flt(grn.net_total),
            "total_taxes_and_charges": flt(grn.total_taxes_and_charges),
            "grand_total": flt(grn.grand_total),
            "rounded_total": flt(grn.rounded_total),
            "rounding_adjustment": flt(grn.rounding_adjustment),
            "discount_amount": flt(grn.discount_amount),
            "additional_discount_percentage": flt(grn.additional_discount_percentage),
            "currency": grn.currency,

            # Breakdown for display
            "totals_breakdown": {
                "items_total": flt(grn.net_total),
                "taxes_total": flt(grn.total_taxes_and_charges),
                "discount": flt(grn.discount_amount),
                "final_total": flt(grn.rounded_total) if not grn.disable_rounded_total else flt(grn.grand_total)
            }
        }

        return {
            "success": True,
            "data": totals,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error calculating totals: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to calculate totals", "code": "API_ERROR"}}


# ===========================
# PAGE 5: CHECKLIST APIs
# ===========================

@frappe.whitelist()
def get_grn_checklist(grn_id):
    """
    Get document checklist for GRN

    Args:
        grn_id (str): GRN document ID

    Returns:
        dict: Checklist items and status
    """
    try:
        if not frappe.db.exists("Purchase Receipt", grn_id):
            return {"success": False, "error": {"message": "GRN not found", "code": "GRN_NOT_FOUND"}}

        grn = frappe.get_doc("Purchase Receipt", grn_id)

        # Default checklist items for GRN
        default_checklist = [
            {
                "item_name": "Delivery Challan / Invoice",
                "description": "Invoice or delivery challan received from supplier",
                "is_required": 1,
                "priority": 1
            },
            {
                "item_name": "Packing List",
                "description": "Detailed packing list with item descriptions",
                "is_required": 1,
                "priority": 2
            },
            {
                "item_name": "Material Test Certificate (MTC)",
                "description": "Test certificate for material quality validation",
                "is_required": 0,
                "priority": 3
            }
        ]

        # Get existing checklist items from custom field or table
        checklist_items = []

        # Check if GRN has custom checklist field
        if hasattr(grn, 'custom_document_checklist') and grn.custom_document_checklist:
            for item in grn.custom_document_checklist:
                checklist_item = {
                    "id": item.name,
                    "item_name": item.checklist_item,
                    "description": item.description,
                    "status": item.status or "Not Received",
                    "received_date": item.received_date,
                    "remarks": item.remarks,
                    "is_required": cint(item.is_required),
                    "priority": cint(item.priority) or 99
                }
                checklist_items.append(checklist_item)
        else:
            # Create default checklist items
            for i, default_item in enumerate(default_checklist, 1):
                checklist_item = {
                    "id": f"default_{i}",
                    "item_name": default_item["item_name"],
                    "description": default_item["description"],
                    "status": "Not Received",
                    "received_date": None,
                    "remarks": "",
                    "is_required": default_item["is_required"],
                    "priority": default_item["priority"]
                }
                checklist_items.append(checklist_item)

        # Sort by priority
        checklist_items.sort(key=lambda x: x["priority"])

        # Calculate completion status
        total_items = len(checklist_items)
        completed_items = len([item for item in checklist_items if item["status"] == "Received"])
        required_items = len([item for item in checklist_items if item["is_required"]])
        required_completed = len([item for item in checklist_items if item["is_required"] and item["status"] == "Received"])

        checklist_summary = {
            "total_items": total_items,
            "completed_items": completed_items,
            "required_items": required_items,
            "required_completed": required_completed,
            "completion_percentage": (completed_items / total_items * 100) if total_items > 0 else 0,
            "required_completion_percentage": (required_completed / required_items * 100) if required_items > 0 else 0,
            "can_submit": required_completed == required_items,
            "status": "Complete" if required_completed == required_items else "Pending"
        }

        return {
            "success": True,
            "data": {
                "grn_id": grn_id,
                "checklist_items": checklist_items,
                "summary": checklist_summary
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error getting GRN checklist: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to get checklist", "code": "API_ERROR"}}


@frappe.whitelist()
def update_checklist_item(grn_id, item_id, status=None, received_date=None, remarks=None):
    """
    Update checklist item status

    Args:
        grn_id (str): GRN document ID
        item_id (str): Checklist item ID
        status (str): Received/Not Received
        received_date (str): Date when document was received
        remarks (str): Additional remarks

    Returns:
        dict: Updated item details
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)
        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        # Initialize checklist if not exists
        if not hasattr(grn, 'custom_document_checklist') or not grn.custom_document_checklist:
            _initialize_default_checklist(grn)

        # Find and update the checklist item
        item_updated = False
        for item in grn.custom_document_checklist:
            if item.name == item_id or str(item.idx) == str(item_id):
                if status:
                    item.status = status
                if received_date:
                    item.received_date = getdate(received_date)
                if remarks is not None:
                    item.remarks = remarks
                item_updated = True
                break

        if not item_updated and item_id.startswith('default_'):
            # Handle default items by creating them
            default_items = [
                "Delivery Challan / Invoice",
                "Packing List",
                "Material Test Certificate (MTC)"
            ]

            item_index = int(item_id.split('_')[1]) - 1
            if 0 <= item_index < len(default_items):
                new_item = grn.append("custom_document_checklist", {})
                new_item.checklist_item = default_items[item_index]
                new_item.status = status or "Not Received"
                new_item.received_date = getdate(received_date) if received_date else None
                new_item.remarks = remarks or ""
                new_item.is_required = 1 if item_index < 2 else 0
                new_item.priority = item_index + 1
                item_updated = True

        if not item_updated:
            return {"success": False, "error": {"message": "Checklist item not found", "code": "ITEM_NOT_FOUND"}}

        # Save the GRN
        grn.save()

        # Return updated item
        updated_item = {
            "id": item_id,
            "status": status,
            "received_date": received_date,
            "remarks": remarks,
            "updated": True
        }

        return {
            "success": True,
            "data": updated_item,
            "message": "Checklist item updated successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error updating checklist item: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to update checklist item", "code": "API_ERROR"}}


@frappe.whitelist()
def add_checklist_item(grn_id, item_name, description=None, is_required=0):
    """
    Add new checklist item to GRN

    Args:
        grn_id (str): GRN document ID
        item_name (str): Name of the checklist item
        description (str): Description of the item
        is_required (int): Whether item is required (1) or optional (0)

    Returns:
        dict: Added item details
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)
        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "Cannot modify submitted GRN", "code": "INVALID_STATE"}}

        if not item_name:
            return {"success": False, "error": {"message": "Item name is required", "code": "MISSING_REQUIRED_FIELDS"}}

        # Initialize checklist if not exists
        if not hasattr(grn, 'custom_document_checklist'):
            _initialize_default_checklist(grn)

        # Add new checklist item
        new_item = grn.append("custom_document_checklist", {})
        new_item.checklist_item = item_name
        new_item.description = description or ""
        new_item.status = "Not Received"
        new_item.is_required = cint(is_required)
        new_item.priority = len(grn.custom_document_checklist) + 1

        # Save the GRN
        grn.save()

        # Return added item
        added_item = {
            "id": new_item.name,
            "item_name": item_name,
            "description": description,
            "status": "Not Received",
            "received_date": None,
            "remarks": "",
            "is_required": cint(is_required),
            "priority": new_item.priority
        }

        return {
            "success": True,
            "data": added_item,
            "message": "Checklist item added successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error adding checklist item: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to add checklist item", "code": "API_ERROR"}}


@frappe.whitelist()
def validate_grn_for_submission(grn_id):
    """
    Validate GRN for final submission

    Args:
        grn_id (str): GRN document ID

    Returns:
        dict: Validation results and submission readiness
    """
    try:
        grn = frappe.get_doc("Purchase Receipt", grn_id)

        validation_results = {
            "is_valid": True,
            "can_submit": True,
            "issues": [],
            "warnings": []
        }

        # Header validation
        if not grn.supplier:
            validation_results["issues"].append("Supplier is required")
        if not grn.company:
            validation_results["issues"].append("Company is required")
        if not grn.posting_date:
            validation_results["issues"].append("Posting date is required")

        # Items validation
        if not grn.items:
            validation_results["issues"].append("At least one item is required")
        else:
            for item in grn.items:
                if not item.item_code:
                    validation_results["issues"].append("All items must have item codes")
                if flt(item.received_qty) <= 0:
                    validation_results["issues"].append("All items must have received quantity greater than 0")

                # Check batch requirements
                if item.item_code:
                    has_batch = frappe.db.get_value("Item", item.item_code, "has_batch_no")
                    if has_batch and not item.batch_no:
                        validation_results["issues"].append(f"Batch number required for item {item.item_code}")

        # Checklist validation
        checklist_response = get_grn_checklist(grn_id)
        if checklist_response["success"]:
            checklist_data = checklist_response["data"]
            if not checklist_data["summary"]["can_submit"]:
                validation_results["issues"].append("All required checklist items must be completed")
                validation_results["warnings"].append(f"Required checklist completion: {checklist_data['summary']['required_completed']}/{checklist_data['summary']['required_items']}")

        # Total validation
        if flt(grn.grand_total) <= 0:
            validation_results["warnings"].append("Grand total is zero - please verify calculations")

        # Set final validation status
        if validation_results["issues"]:
            validation_results["is_valid"] = False
            validation_results["can_submit"] = False

        # Submission checklist
        submission_checklist = [
            {
                "item": "Header Information",
                "status": "Complete" if grn.supplier and grn.company and grn.posting_date else "Incomplete",
                "required": True
            },
            {
                "item": "Items Added",
                "status": "Complete" if grn.items and len(grn.items) > 0 else "Incomplete",
                "required": True
            },
            {
                "item": "Quantities Entered",
                "status": "Complete" if all(flt(item.received_qty) > 0 for item in grn.items) else "Incomplete",
                "required": True
            },
            {
                "item": "Document Checklist",
                "status": checklist_data["summary"]["status"] if checklist_response["success"] else "Incomplete",
                "required": True
            },
            {
                "item": "Tax Calculations",
                "status": "Complete" if flt(grn.grand_total) > 0 else "Incomplete",
                "required": False
            }
        ]

        return {
            "success": True,
            "data": {
                "grn_id": grn_id,
                "validation_results": validation_results,
                "submission_checklist": submission_checklist,
                "ready_for_submission": validation_results["can_submit"]
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Error validating GRN for submission: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Validation failed", "code": "VALIDATION_ERROR"}}


@frappe.whitelist()
def submit_grn(grn_id):
    """
    Submit GRN after validation

    Args:
        grn_id (str): GRN document ID

    Returns:
        dict: Submission result
    """
    try:
        # First validate the GRN
        validation_response = validate_grn_for_submission(grn_id)
        if not validation_response["success"]:
            return validation_response

        if not validation_response["data"]["ready_for_submission"]:
            return {
                "success": False,
                "error": {
                    "message": "GRN validation failed",
                    "code": "VALIDATION_FAILED",
                    "details": validation_response["data"]["validation_results"]["issues"]
                }
            }

        # Get and submit the GRN
        grn = frappe.get_doc("Purchase Receipt", grn_id)

        if grn.docstatus == 1:
            return {"success": False, "error": {"message": "GRN is already submitted", "code": "ALREADY_SUBMITTED"}}

        if grn.docstatus == 2:
            return {"success": False, "error": {"message": "GRN is cancelled", "code": "CANCELLED_DOCUMENT"}}

        # Submit the document
        grn.submit()

        # Get final GRN details
        submitted_grn = {
            "grn_id": grn.name,
            "status": "Submitted",
            "docstatus": grn.docstatus,
            "submitted_by": frappe.session.user,
            "submission_date": now_datetime(),
            "grand_total": flt(grn.grand_total),
            "currency": grn.currency,
            "supplier": grn.supplier,
            "company": grn.company
        }

        return {
            "success": True,
            "data": submitted_grn,
            "message": "GRN submitted successfully",
            "timestamp": datetime.now().isoformat()
        }

    except frappe.ValidationError as e:
        frappe.log_error(f"Validation error during GRN submission: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": str(e), "code": "VALIDATION_ERROR"}}
    except Exception as e:
        frappe.log_error(f"Error submitting GRN: {str(e)}", "Mobile GRN API")
        return {"success": False, "error": {"message": "Failed to submit GRN", "code": "SUBMISSION_ERROR"}}


def _initialize_default_checklist(grn):
    """
    Initialize default checklist items for GRN

    Args:
        grn: GRN document object
    """
    default_items = [
        {
            "checklist_item": "Delivery Challan / Invoice",
            "description": "Invoice or delivery challan received from supplier",
            "is_required": 1,
            "priority": 1
        },
        {
            "checklist_item": "Packing List",
            "description": "Detailed packing list with item descriptions",
            "is_required": 1,
            "priority": 2
        },
        {
            "checklist_item": "Material Test Certificate (MTC)",
            "description": "Test certificate for material quality validation",
            "is_required": 0,
            "priority": 3
        }
    ]

    if not hasattr(grn, 'custom_document_checklist'):
        # If custom_document_checklist field doesn't exist, skip initialization
        return

    for item_data in default_items:
        item = grn.append("custom_document_checklist", {})
        item.checklist_item = item_data["checklist_item"]
        item.description = item_data["description"]
        item.status = "Not Received"
        item.is_required = item_data["is_required"]
        item.priority = item_data["priority"]