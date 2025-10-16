import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, now_datetime
import json
import re
from datetime import datetime, timedelta

# ===========================
# SECURITY CONSTANTS
# ===========================

# Whitelist of allowed doctypes for security
ALLOWED_DOCTYPES = {
    'Purchase Receipt', 'Goods Receipt Note', 'Purchase Order', 
    'Material Request', 'Stock Entry', 'Delivery Note', 'Sales Invoice'
}

# Allowed sort fields to prevent injection
ALLOWED_SORT_FIELDS = {
    'creation', 'modified', 'name', 'posting_date', 'transaction_date', 
    'grand_total', 'supplier', 'supplier_name'
}

# Allowed sort orders
ALLOWED_SORT_ORDERS = {'asc', 'desc', 'ASC', 'DESC'}

# CONFIGURABLE VALIDATION RULES
VALIDATION_CONFIG = {
    "received_qty_min": 0,
    "require_item_codes": True,
    "require_batch_for_batch_items": True,
    "allow_zero_qty": False,
    "min_items_required": 1,
    "validate_rates": True,
    "rate_min": 0
}

def get_validation_config():
    """
    Get validation configuration from Mobile API Settings or use defaults
    """
    try:
        # Try to get from Mobile API Settings
        settings = frappe.get_single("Mobile API Settings")
        if settings:
            return {
                "received_qty_min": getattr(settings, 'minimum_rate_allowed', 0),
                "require_item_codes": getattr(settings, 'require_item_codes', True),
                "require_batch_for_batch_items": getattr(settings, 'require_batch_numbers_for_batch_items', True),
                "allow_zero_qty": getattr(settings, 'allow_zero_quantities', False),
                "min_items_required": getattr(settings, 'minimum_items_required', 1),
                "validate_rates": getattr(settings, 'validate_item_rates', True),
                "rate_min": getattr(settings, 'minimum_rate_allowed', 0)
            }
    except:
        pass
    
    # Fallback to default configuration
    return VALIDATION_CONFIG

# Configurable fields per doctype for better flexibility
DOCTYPE_FIELDS = {
    "Purchase Receipt": {
        "title": "title",
        "supplier": "supplier", 
        "supplier_name": "supplier_name",
        "grand_total": "grand_total",
        "currency": "currency",
        "posting_date": "posting_date",
        "company": "company",
        "remarks": "remarks"
    },
    "Goods Receipt Note": {
        "title": "title",
        "supplier": "supplier",
        "supplier_name": "supplier_name", 
        "grand_total": "grand_total",
        "currency": "currency",
        "posting_date": "posting_date",
        "company": "company",
        "remarks": "remarks"
    },
    "Purchase Order": {
        "title": "title",
        "supplier": "supplier",
        "supplier_name": "supplier_name",
        "grand_total": "grand_total", 
        "currency": "currency",
        "posting_date": "transaction_date",
        "company": "company",
        "remarks": "remarks"
    }
}


def secure_api_call(func):
    """
    Decorator to add security validation to API calls
    """
    def wrapper(*args, **kwargs):
        try:
            # Rate limiting check (basic implementation)
            user = frappe.session.user
            if user == "Guest":
                raise frappe.PermissionError("Guest users not allowed")
            
            # Remove Frappe's internal parameters that utility functions don't expect
            kwargs.pop('cmd', None)
            kwargs.pop('method', None)
            kwargs.pop('args', None)
            kwargs.pop('kwargs', None)
            
            # Input validation for common parameters
            if 'doctype' in kwargs:
                validate_doctype(kwargs['doctype'])
            if 'search' in kwargs and kwargs['search']:
                kwargs['search'] = sanitize_search_term(kwargs['search'])
            if 'search_term' in kwargs and kwargs['search_term']:
                kwargs['search_term'] = sanitize_search_term(kwargs['search_term'])
            
            return func(*args, **kwargs)
        except frappe.ValidationError:
            raise
        except Exception as e:
            frappe.log_error(f"Security error in {func.__name__}: {str(e)}", "Security Error")
            raise frappe.ValidationError("Invalid request")
    
    return wrapper

def validate_doctype(doctype):
    """Validate doctype against whitelist to prevent SQL injection"""
    if not doctype or doctype not in ALLOWED_DOCTYPES:
        raise frappe.ValidationError(f"Invalid doctype: {doctype}. Allowed types: {', '.join(ALLOWED_DOCTYPES)}")
    return doctype

def sanitize_search_term(search_term):
    """Sanitize search terms to prevent SQL injection"""
    if not search_term:
        return ""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[^\w\s\-\.@]', '', str(search_term))
    return sanitized.strip()

def validate_sort_params(sort_by, sort_order):
    """Validate sort parameters to prevent SQL injection"""
    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = 'creation'  # Default safe value
    
    if sort_order.upper() not in ALLOWED_SORT_ORDERS:
        sort_order = 'DESC'  # Default safe value
    
    return sort_by, sort_order.upper()

def validate_pagination_params(page, limit):
    """Validate pagination parameters"""
    page = max(1, cint(page) or 1)
    limit = max(1, min(100, cint(limit) or 20))  # Cap at 100 for performance
    return page, limit

def safe_table_name(doctype):
    """Generate safe table name after validation"""
    validated_doctype = validate_doctype(doctype)
    return f"`tab{validated_doctype}`"

def safe_child_table_name(doctype):
    """Generate safe child table name after validation"""
    validated_doctype = validate_doctype(doctype)
    return f"`tab{validated_doctype} Item`"

def get_doctype_fields(doctype):
    """Get field mappings for a specific doctype"""
    validated_doctype = validate_doctype(doctype)
    return DOCTYPE_FIELDS.get(validated_doctype, DOCTYPE_FIELDS["Purchase Receipt"])

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
        # SECURITY: Validate and sanitize all inputs
        validate_doctype(doctype)
        search = sanitize_search_term(search) if search else None
        sort_by, sort_order = validate_sort_params(sort_by, sort_order)
        page, limit = validate_pagination_params(page, limit)
        
        offset = (page - 1) * limit

        # Build conditions with parameterized queries
        conditions = ["doc.docstatus != 2"]
        values = {}

        # Get doctype-specific field mappings for search
        fields = get_doctype_fields(doctype)
        
        # Search functionality with sanitized input using dynamic fields
        if search:
            search_conditions = [
                f"doc.name LIKE %(search)s",
                f"doc.{fields['supplier']} LIKE %(search)s", 
                f"doc.{fields['supplier_name']} LIKE %(search)s"
            ]
            conditions.append(f"({' OR '.join(search_conditions)})")
            values["search"] = f"%{search}%"

        # Status filter with validation
        if status:
            status = status.lower()
            if status == "draft":
                conditions.append("doc.docstatus = 0")
            elif status == "submitted":
                conditions.append("doc.docstatus = 1")
            elif status == "cancelled":
                conditions.append("doc.docstatus = 2")

        # Company filter with validation
        if company:
            # Validate company exists
            if frappe.db.exists("Company", company):
                conditions.append("doc.company = %(company)s")
                values["company"] = company

        # Supplier filter with validation
        if supplier:
            # Validate supplier exists
            if frappe.db.exists("Supplier", supplier):
                conditions.append("doc.supplier = %(supplier)s")
                values["supplier"] = supplier

        # Date range filter with validation
        if date_from:
            try:
                getdate(date_from)  # Validate date format
                conditions.append("doc.posting_date >= %(date_from)s")
                values["date_from"] = date_from
            except:
                pass  # Skip invalid dates

        if date_to:
            try:
                getdate(date_to)  # Validate date format
                conditions.append("doc.posting_date <= %(date_to)s")
                values["date_to"] = date_to
            except:
                pass  # Skip invalid dates

        where_clause = " AND ".join(conditions)

        # SECURITY: Use safe table names
        table_name = safe_table_name(doctype)
        child_table = safe_child_table_name(doctype)
        
        # Get doctype-specific field mappings
        fields = get_doctype_fields(doctype)

        # OPTIMIZED: Use SQL_CALC_FOUND_ROWS for better performance with dynamic fields
        # Performance hint: Use index on docstatus, company, supplier for faster filtering
        query = f"""
            SELECT SQL_CALC_FOUND_ROWS
                doc.name as id,
                doc.{fields['title']} as title,
                doc.{fields['supplier']} as supplier,
                doc.{fields['supplier_name']} as supplier_name,
                doc.{fields['company']} as company,
                doc.{fields['posting_date']} as date,
                doc.{fields['grand_total']} as grand_total,
                doc.{fields['currency']} as currency,
                doc.docstatus,
                doc.{fields['remarks']} as remarks,
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
            FROM {table_name} doc
            LEFT JOIN {child_table} child ON child.parent = doc.name
            WHERE {where_clause}
            GROUP BY doc.name
            ORDER BY doc.{sort_by} {sort_order}
            LIMIT %(limit)s OFFSET %(offset)s
        """

        values.update({"limit": limit, "offset": offset})
        doc_list = frappe.db.sql(query, values, as_dict=True)

        # Get total count using FOUND_ROWS() - much more efficient
        total_count = frappe.db.sql("SELECT FOUND_ROWS() as total", as_dict=True)[0].total
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

    except frappe.ValidationError as ve:
        return {"success": False, "error": {"message": str(ve), "code": "VALIDATION_ERROR"}}
    except Exception as e:
        frappe.log_error(f"Error in get_document_list for {doctype}: {str(e)}", "Mobile Utils Error")
        return {"success": False, "error": {"message": "An error occurred while fetching documents", "code": "DOCUMENT_LIST_ERROR"}}

@frappe.whitelist()
def get_document_filters(doctype):
    """
    Generic function to get filter options for document list
    """
    try:
        # SECURITY: Validate doctype
        validate_doctype(doctype)
        table_name = safe_table_name(doctype)

        # Get unique companies with safe table name
        companies = frappe.db.sql(f"""
            SELECT DISTINCT company, company as label
            FROM {table_name}
            WHERE docstatus != 2
            ORDER BY company
        """, as_dict=True)

        # Get unique suppliers with safe table name
        suppliers = frappe.db.sql(f"""
            SELECT DISTINCT supplier, supplier_name as label
            FROM {table_name}
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

    except frappe.ValidationError as ve:
        return {"success": False, "error": {"message": str(ve), "code": "VALIDATION_ERROR"}}
    except Exception as e:
        frappe.log_error(f"Error in get_document_filters for {doctype}: {str(e)}", "Mobile Utils Error")
        return {"success": False, "error": {"message": "An error occurred while fetching filters", "code": "DOCUMENT_FILTERS_ERROR"}}

@frappe.whitelist()
def search_document(doctype, search_term, limit=10):
    """
    Generic function to search documents
    """
    try:
        # SECURITY: Validate doctype and sanitize inputs
        validate_doctype(doctype)
        search_term = sanitize_search_term(search_term)
        
        if not search_term:
            return {"success": True, "data": [], "message": "Please provide a search term"}

        limit = max(1, min(50, cint(limit) or 10))  # Cap at 50 for performance
        table_name = safe_table_name(doctype)
        
        # Get doctype-specific field mappings
        fields = get_doctype_fields(doctype)

        query = f"""
            SELECT
                doc.name as id,
                doc.{fields['title']} as title,
                doc.{fields['supplier']} as supplier,
                doc.{fields['supplier_name']} as supplier_name,
                doc.{fields['posting_date']} as date,
                doc.{fields['grand_total']} as grand_total,
                doc.{fields['currency']} as currency,
                CASE
                    WHEN doc.docstatus = 0 THEN 'Draft'
                    WHEN doc.docstatus = 1 AND doc.is_return = 1 THEN 'Return'
                    WHEN doc.docstatus = 1 THEN 'Submitted'
                    WHEN doc.docstatus = 2 THEN 'Cancelled'
                    ELSE 'Unknown'
                END as status
            FROM {table_name} doc
            WHERE doc.docstatus != 2
            AND (
                doc.name LIKE %(search)s OR
                doc.{fields['supplier']} LIKE %(search)s OR
                doc.{fields['supplier_name']} LIKE %(search)s OR
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

    except frappe.ValidationError as ve:
        return {"success": False, "error": {"message": str(ve), "code": "VALIDATION_ERROR"}}
    except Exception as e:
        frappe.log_error(f"Error in search_document for {doctype}: {str(e)}", "Mobile Utils Error")
        return {"success": False, "error": {"message": "An error occurred while searching documents", "code": "DOCUMENT_SEARCH_ERROR"}}

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
        frappe.log_error(f"Mobile Utils Companies Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch companies: {str(e)}", "code": "COMPANIES_ERROR"}}

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
        frappe.log_error(f"Mobile Utils PO Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch purchase orders: {str(e)}", "code": "PURCHASE_ORDERS_ERROR"}}

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
        frappe.log_error(f"Mobile Utils Warehouses Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch warehouses: {str(e)}", "code": "WAREHOUSES_ERROR"}}

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
        frappe.log_error(f"Mobile Utils Tax Templates Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch tax templates: {str(e)}", "code": "TAX_TEMPLATES_ERROR"}}

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
        frappe.log_error(f"Error in get_tax_accounts: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch tax accounts: {str(e)}", "code": "TAX_ACCOUNTS_ERROR"}}


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
        frappe.log_error(f"Mobile Utils Status Summary Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch document status summary: {str(e)}", "code": "STATUS_SUMMARY_ERROR"}}


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
        frappe.log_error(f"Mobile Utils Naming Series Error: {str(e)}", frappe.get_traceback())
        return {
            "success": False,
            "error": {
                "message": f"Failed to fetch naming series: {str(e)}",
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
        return {"success": False, "error": {"message": f"Failed to search items: {str(e)}", "code": "SEARCH_ITEMS_ERROR"}}


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
        # SECURITY: Validate doctype and sanitize doc_id
        validate_doctype(doctype)
        if not doc_id or not isinstance(doc_id, str):
            return {"success": False, "error": {"message": "Invalid document ID", "code": "INVALID_DOC_ID"}}
        
        # Sanitize doc_id to prevent injection
        doc_id = re.sub(r'[^\w\-\.]', '', str(doc_id))
        if not doc_id:
            return {"success": False, "error": {"message": "Invalid document ID format", "code": "INVALID_DOC_ID"}}

        # Check if document exists
        if not frappe.db.exists(doctype, doc_id):
            return {"success": False, "error": {"message": "Document not found", "code": "DOCUMENT_NOT_FOUND"}}

        # SECURITY: Use safe child table name
        child_table = safe_child_table_name(doctype)

        # Get document items with safe table names
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

    except frappe.ValidationError as ve:
        return {"success": False, "error": {"message": str(ve), "code": "VALIDATION_ERROR"}}
    except Exception as e:
        frappe.log_error(f"Mobile Utils Get Items Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch document items: {str(e)}", "code": "GET_ITEMS_ERROR"}}


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
        frappe.log_error(f"Mobile Utils Add Item Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to add item to document: {str(e)}", "code": "ADD_ITEM_ERROR"}}


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
        frappe.log_error(f"Mobile Utils Update Item Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to update document item: {str(e)}", "code": "UPDATE_ITEM_ERROR"}}


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
        frappe.log_error(f"Mobile Utils Delete Item Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to delete document item: {str(e)}", "code": "DELETE_ITEM_ERROR"}}


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
        config = get_validation_config()
        frappe.log_error(f"Validation Config", config)

        if not doc.items:
            validation_results["issues"].append("At least one item is required")
        elif len(doc.items) < config.get("min_items_required", 1):
            validation_results["issues"].append(f"At least {config.get('min_items_required', 1)} item(s) required")
        else:
            for item in doc.items:
                # Configurable item code validation
                if config.get("require_item_codes", True) and not item.item_code:
                    validation_results["issues"].append("All items must have item codes")
                
                # Configurable quantity validation
                received_qty = flt(item.received_qty)
                if not config.get("allow_zero_qty", False) and received_qty <= 0:
                    validation_results["issues"].append("All items must have received quantity greater than 0")
                elif received_qty < config.get("received_qty_min", 0):
                    validation_results["issues"].append(f"Received quantity must be at least {config.get('received_qty_min', 0)}")

                # Configurable batch requirements
                if config.get("require_batch_for_batch_items", True) and item.item_code:
                    has_batch = frappe.db.get_value("Item", item.item_code, "has_batch_no")
                    if has_batch and not item.batch_no:
                        validation_results["issues"].append(f"Batch number required for item {item.item_code}")
                
                # Configurable rate validation
                if config.get("validate_rates", True):
                    rate = flt(item.rate)
                    if rate < config.get("rate_min", 0):
                        validation_results["issues"].append(f"Rate must be at least {config.get('rate_min', 0)} for item {item.item_code}")

        # Final validation
        if validation_results["issues"]:
            validation_results["can_proceed"] = False

        message = "Items validation successful" if validation_results["is_valid"] else "Items validation failed"

        return {"success": True, "data": validation_results, "message": message}

    except Exception as e:
        frappe.log_error(f"Mobile Utils Validate Items Error: {str(e)}", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to validate document items: {str(e)}", "code": "VALIDATE_ITEMS_ERROR"}}
