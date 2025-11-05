import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, now_datetime
import json
import re
from datetime import datetime, timedelta
import math

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
# ===========================
# SHARED MOBILE UTILITIES
# ===========================


@frappe.whitelist()
@secure_api_call
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
        frappe.log_error("Mobile Utils Error", f"Mobile Utils Companies Error: {str(e)}")
        return {"success": False, "error": {"message": f"Failed to fetch companies: {str(e)}", "code": "COMPANIES_ERROR"}}

@frappe.whitelist()
@secure_api_call
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
        frappe.log_error(f"Mobile Utils PO Error", frappe.get_traceback())
        return {"success": False, "error": {"message": f"Failed to fetch purchase orders: {str(e)}", "code": "PURCHASE_ORDERS_ERROR"}}

@frappe.whitelist()
@secure_api_call
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
@secure_api_call
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
@secure_api_call
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

# //////////////////////////////////////////
@frappe.whitelist()
@secure_api_call
def manage_document(doctype, action, doc_id=None, data=None):
    """
    Unified API for document management
    
    Args:
        doctype (str): Document type (Purchase Receipt, Goods Receipt Note, etc.)
        action (str): new, update
        doc_id (str): Document ID (required for update)
        data (dict): Document data including items
    
    Returns:
        dict: Operation result
    """
    try:
        # Validate doctype
        if doctype not in ALLOWED_DOCTYPES:
            return {"success": False, "error": {"message": f"Unsupported doctype: {doctype}", "code": "UNSUPPORTED_DOCTYPE"}}
        
        if action == "new":
            return _create_document(doctype, data)
        elif action == "update":
            return _update_document(doctype, doc_id, data)
        elif action == "submit":
            return _submit_document(doctype, doc_id)
        else:
            return {"success": False, "error": {"message": f"Invalid action: {action}", "code": "INVALID_ACTION"}}
            
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Document management error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "DOCUMENT_MANAGEMENT_ERROR"}}

def _create_document(doctype, data):
    """Create new document with all data and validation"""
    try:
        if not data:
            return {"success": False, "error": {"message": "Document data is required", "code": "MISSING_DATA"}}
        
        # Get user defaults
        default_company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        
        # Create new document
        doc = frappe.new_doc(doctype)
        
        # Set essential defaults only
        doc.posting_date = getdate(data.get('posting_date')) or getdate()
        doc.posting_time = now_datetime().time()
        doc.set_posting_time = 0
        doc.company = data.get('company') or default_company
        doc.is_return = 0
        
        # Map ALL fields from data to document (except 'items')
        # This will override defaults if the field is provided in data
        for field, value in data.items():
            if field != 'items' and hasattr(doc, field) and value is not None:
                setattr(doc, field, value)
        
        # Add items if provided - map all fields directly from item_data
        if data.get('items'):
            for item_data in data['items']:
                item_row = doc.append("items", {})
                # Map all fields from item_data to item_row
                for field, value in item_data.items():
                    if hasattr(item_row, field) and value is not None:
                        setattr(item_row, field, value)
        
        # Validate document before saving using Mobile API Settings
        validation_result = _validate_document_with_settings(doc)
        if not validation_result["is_valid"]:
            return {"success": False, "error": {"message": "Validation failed", "code": "VALIDATION_ERROR", "details": validation_result["issues"]}}
        
        # Save document
        doc.save()
        
        return {
            "success": True,
            "data": {
                "doc_id": doc.name,
                "action": "new",
                "changes_made": len(data.get('items', [])),
                "new_items": len(data.get('items', [])),
                "updated_items": 0,
                "deleted_items": 0
            },
            "message": f"{doctype} created successfully"
        }
    except frappe.MandatoryError as e:
        return {"success": False, "error": {"message": str(e), "code": "MANDATORY_ERROR"}}
    except frappe.ValidationError as e:
        return {"success": False, "error": {"message": str(e), "code": "VALIDATION_ERROR"}}
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Create document error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "CREATE_DOCUMENT_ERROR"}}

def _update_document(doctype, doc_id, data):
    """Update existing document with changed data and validation"""
    try:
        if not doc_id:
            return {"success": False, "error": {"message": "Document ID is required for update", "code": "MISSING_DOC_ID"}}
        
        if not data:
            return {"success": False, "error": {"message": "Update data is required", "code": "MISSING_DATA"}}
        
        # Get existing document
        doc = frappe.get_doc(doctype, doc_id)
        
        # Check if document can be modified
        if doc.docstatus != 0:
            return {"success": False, "error": {"message": f"Cannot modify {doc.status} document", "code": "INVALID_STATE"}}
        
        # Track changes
        changes_made = 0
        changed_fields = []
        new_items = 0
        updated_items = 0
        deleted_items = 0
        
        # Update document fields
        for field, value in data.items():
            if field != 'items' and hasattr(doc, field) and value is not None:
                old_value = getattr(doc, field)
                if old_value != value:
                    setattr(doc, field, value)
                    changed_fields.append(field)
                    changes_made += 1
        
        # Handle items
        if 'items' in data:
            item_changes = _update_document_items(doc, data['items'])
            new_items = item_changes['new_items']
            updated_items = item_changes['updated_items']
            deleted_items = item_changes['deleted_items']
            changes_made += new_items + updated_items + deleted_items
        
        # Validate document before saving using Mobile API Settings
        validation_result = _validate_document_with_settings(doc)
        if not validation_result["is_valid"]:
            return {"success": False, "error": {"message": "Validation failed", "code": "VALIDATION_ERROR", "details": validation_result["issues"]}}
        
        # Save document
        doc.save()
        
        return {
            "success": True,
            "data": {
                "doc_id": doc.name,
                "action": "update",
                "changes_made": changes_made,
                "changed_fields": changed_fields,
                "new_items": new_items,
                "updated_items": updated_items,
                "deleted_items": deleted_items
            },
            "message": f"{doctype} updated successfully"
        }
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Update document error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "UPDATE_DOCUMENT_ERROR"}}

def _validate_document_with_settings(doc):
    """Validate document using Mobile API Settings configuration"""
    try:
        validation_results = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Get validation configuration from Mobile API Settings
        config = get_validation_config()
        
        # Check items
        if not doc.items:
            validation_results["issues"].append("At least one item is required")
        elif len(doc.items) < config.get("min_items_required", 1):
            validation_results["issues"].append(f"At least {config.get('min_items_required', 1)} item(s) required")
        else:
            # Validate each item
            for item in doc.items:
                # Required fields validation
                if config.get("require_item_codes", True) and not item.item_code:
                    validation_results["issues"].append("All items must have item codes")
                
                # Quantity validation - ZERO QUANTITY CHECK
                received_qty = flt(item.received_qty)
                if not config.get("allow_zero_qty", False) and received_qty <= 0:
                    validation_results["issues"].append(f"Received quantity must be greater than 0 for item {item.item_code}")
                elif received_qty < config.get("received_qty_min", 0):
                    validation_results["issues"].append(f"Received quantity must be at least {config.get('received_qty_min', 0)} for item {item.item_code}")
                
                # Batch validation
                if config.get("require_batch_for_batch_items", True) and item.item_code:
                    has_batch = frappe.db.get_value("Item", item.item_code, "has_batch_no")
                    if has_batch and not item.batch_no:
                        validation_results["issues"].append(f"Batch number required for item {item.item_code}")
                
                # Rate validation
                if config.get("validate_rates", True):
                    rate = flt(item.rate)
                    if rate < config.get("rate_min", 0):
                        validation_results["issues"].append(f"Rate must be at least {config.get('rate_min', 0)} for item {item.item_code}")
        
        # Set final validation status
        if validation_results["issues"]:
            validation_results["is_valid"] = False
        
        return validation_results
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Document validation error: {str(e)}")
        return {"is_valid": False, "issues": [str(e)], "warnings": []}

def _add_item_to_document(doc, item_data):
    """Add item to document"""
    try:
        # Validate required fields
        required_fields = ["item_code"]
        for field in required_fields:
            if not item_data.get(field):
                raise ValueError(f"{field} is required")
        
        # Get item details
        if not frappe.db.exists("Item", item_data['item_code']):
            raise ValueError("Item not found")
        
        item = frappe.get_doc("Item", item_data['item_code'])
        
        # Map qty to received_qty if received_qty is not provided
        if 'received_qty' not in item_data and 'qty' in item_data:
            item_data['received_qty'] = item_data['qty']
        
        # Set default received_qty if not provided
        if not item_data.get('received_qty'):
            item_data['received_qty'] = flt(item_data.get('qty', 1))
        
        # Get default warehouse if not provided
        if not item_data.get('warehouse'):
            # Try to get default warehouse from item or company
            default_warehouse = (
                frappe.db.get_value("Item", item_data['item_code'], "default_warehouse") or
                frappe.db.get_value("Warehouse", {"company": doc.company, "is_group": 0}, "name") or
                None
            )
            if not default_warehouse:
                raise ValueError("warehouse is required and no default warehouse found")
            item_data['warehouse'] = default_warehouse
        
        # Get default rate if not provided
        if not item_data.get('rate'):
            item_data['rate'] = frappe.db.get_value("Item Price", {"item_code": item_data['item_code'], "price_list": "Standard Buying"}, "price_list_rate") or 0
        
        # Ensure rate is not None
        item_data['rate'] = flt(item_data.get('rate', 0))
        
        # Create new item row
        item_row = doc.append("items", {})
        item_row.item_code = item_data['item_code']
        # item_row.item_name = item.item_name
        # item_row.description = item.description
        item_row.qty = flt(item_data.get('qty', item_data['received_qty']))
        # item_row.received_qty = flt(item_data['received_qty'])
        # item_row.uom = item.purchase_uom or item.stock_uom
        # item_row.warehouse = item_data['warehouse']
        item_row.rate = flt(item_data['rate'])
        # item_row.amount = flt(item_row.received_qty) * flt(item_row.rate)
        # item_row.conversion_factor = 1
        # item_row.stock_uom = item.stock_uom
        # item_row.stock_qty = item_row.received_qty
        
        # Add optional fields
        # if item_data.get('batch_no'):
        #     item_row.batch_no = item_data['batch_no']
        # if item_data.get('serial_no'):
        #     item_row.serial_no = item_data['serial_no']
        # if item_data.get('no_of_boxes'):
        #     item_row.custom_no_of_boxes = flt(item_data['no_of_boxes'])
        
        return True
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Add item error: {str(e)}")
        raise e

def _update_document_items(doc, items_data):
    """Update document items based on provided data"""
    try:
        new_items = 0
        updated_items = 0
        deleted_items = 0
        
        # Get existing item IDs
        existing_item_ids = [item.name for item in doc.items]
        provided_item_ids = [item.get('item_id') for item in items_data if item.get('item_id')]
        
        # Find deleted items (items not in provided data)
        deleted_item_ids = [item_id for item_id in existing_item_ids if item_id not in provided_item_ids]
        deleted_items = len(deleted_item_ids)
        
        # Remove deleted items
        for item_id in deleted_item_ids:
            for i, row in enumerate(doc.items):
                if row.name == item_id:
                    del doc.items[i]
                    break
        
        # Process provided items
        for item_data in items_data:
            if item_data.get('item_id'):
                # Update existing item
                updated = _update_existing_item(doc, item_data)
                if updated:
                    updated_items += 1
            else:
                # Add new item
                _add_item_to_document(doc, item_data)
                new_items += 1
        
        return {
            "new_items": new_items,
            "updated_items": updated_items,
            "deleted_items": deleted_items
        }
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Update items error: {str(e)}")
        raise e

def _update_existing_item(doc, item_data):
    """Update existing item in document"""
    try:
        item_id = item_data.get('item_id')
        if not item_id:
            return False
        
        # Find the item
        for item in doc.items:
            if item.name == item_id:
                # Update allowed fields
                allowed_fields = ['qty', 'received_qty', 'warehouse', 'rate', 'batch_no', 'serial_no', 'custom_no_of_boxes']
                
                for field, value in item_data.items():
                    if field in allowed_fields and value is not None:
                        if field in ['qty', 'received_qty', 'rate', 'custom_no_of_boxes']:
                            setattr(item, field, flt(value))
                        else:
                            setattr(item, field, value)
                
                # Recalculate amount if qty or rate changed
                if 'received_qty' in item_data or 'rate' in item_data:
                    item.amount = item.received_qty * item.rate
                    item.stock_qty = item.received_qty * item.conversion_factor
                
                return True
        
        return False
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Update existing item error: {str(e)}")
        raise e

def _submit_document(doctype, doc_id):
    """Submit document after comprehensive validation"""
    try:
        if not doc_id:
            return {"success": False, "error": {"message": "Document ID is required for submit", "code": "MISSING_DOC_ID"}}
        
        # Get document
        doc = frappe.get_doc(doctype, doc_id)
        
        # Check if document can be submitted
        if doc.docstatus == 1:
            return {"success": False, "error": {"message": f"{doctype} is already submitted", "code": "ALREADY_SUBMITTED"}}
        
        if doc.docstatus == 2:
            return {"success": False, "error": {"message": f"{doctype} is cancelled", "code": "CANCELLED_DOCUMENT"}}
        
        # Comprehensive validation for submission
        validation_result = _validate_document_for_submission(doc, doctype)
        if not validation_result["is_valid"]:
            return {
                "success": False, 
                "error": {
                    "message": f"{doctype} validation failed", 
                    "code": "VALIDATION_FAILED", 
                    "details": validation_result["issues"]
                }
            }
        
        # Submit the document
        doc.submit()
        
        return {
            "success": True,
            "data": {
                "doc_id": doc.name,
                "action": "submit",
                "status": "Submitted",
                "docstatus": doc.docstatus,
                "submitted_by": frappe.session.user,
                "submission_date": now_datetime(),
                "grand_total": flt(doc.grand_total),
                "currency": getattr(doc, "currency", ""),
                "supplier": getattr(doc, "supplier", ""),
                "company": doc.company,
                "validation_results": validation_result,
                "submission_checklist": validation_result.get("submission_checklist", [])
            },
            "message": f"{doctype} submitted successfully"
        }
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Submit document error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "SUBMIT_DOCUMENT_ERROR"}}

def _validate_document_for_submission(doc, doctype):
    """Comprehensive validation for document submission"""
    try:
        validation_results = {
            "is_valid": True,
            "can_submit": True,
            "issues": [],
            "warnings": []
        }
        
        # Get validation configuration from Mobile API Settings
        config = get_validation_config()
        
        # Header validation
        if not getattr(doc, "supplier", None):
            validation_results["issues"].append("Supplier is required")
        if not getattr(doc, "company", None):
            validation_results["issues"].append("Company is required")
        if not getattr(doc, "posting_date", None):
            validation_results["issues"].append("Posting date is required")
        
        # Items validation
        if not doc.items:
            validation_results["issues"].append("At least one item is required")
        elif len(doc.items) < config.get("min_items_required", 1):
            validation_results["issues"].append(f"At least {config.get('min_items_required', 1)} item(s) required")
        else:
            # Validate each item
            for item in doc.items:
                # Required fields validation
                if config.get("require_item_codes", True) and not item.item_code:
                    validation_results["issues"].append("All items must have item codes")
                
                # Quantity validation - ZERO QUANTITY CHECK
                received_qty = flt(item.received_qty)
                if not config.get("allow_zero_qty", False) and received_qty <= 0:
                    validation_results["issues"].append(f"Received quantity must be greater than 0 for item {item.item_code}")
                elif received_qty < config.get("received_qty_min", 0):
                    validation_results["issues"].append(f"Received quantity must be at least {config.get('received_qty_min', 0)} for item {item.item_code}")
                
                # Batch validation
                if config.get("require_batch_for_batch_items", True) and item.item_code:
                    has_batch = frappe.db.get_value("Item", item.item_code, "has_batch_no")
                    if has_batch and not item.batch_no:
                        validation_results["issues"].append(f"Batch number required for item {item.item_code}")
                
                # Rate validation
                if config.get("validate_rates", True):
                    rate = flt(item.rate)
                    if rate < config.get("rate_min", 0):
                        validation_results["issues"].append(f"Rate must be at least {config.get('rate_min', 0)} for item {item.item_code}")
        
        # Total validation
        if flt(doc.grand_total) <= 0:
            validation_results["warnings"].append("Grand total is zero - please verify calculations")
        
        # Set final validation status
        if validation_results["issues"]:
            validation_results["is_valid"] = False
            validation_results["can_submit"] = False
        
        # Basic submission checklist (without document-specific checklist)
        submission_checklist = [
            {
                "item": "Header Information",
                "status": "Complete" if getattr(doc, "supplier", None) and getattr(doc, "company", None) and getattr(doc, "posting_date", None) else "Incomplete",
                "required": True
            },
            {
                "item": "Items Added",
                "status": "Complete" if doc.items and len(doc.items) > 0 else "Incomplete",
                "required": True
            },
            {
                "item": "Quantities Entered",
                "status": "Complete" if all(flt(item.received_qty) > 0 for item in doc.items) else "Incomplete",
                "required": True
            },
            {
                "item": "Tax Calculations",
                "status": "Complete" if flt(doc.grand_total) > 0 else "Incomplete",
                "required": False
            }
        ]
        
        validation_results["submission_checklist"] = submission_checklist
        
        return validation_results
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Document submission validation error: {str(e)}")
        return {"is_valid": False, "issues": [str(e)], "warnings": [], "submission_checklist": []}

@frappe.whitelist()
@secure_api_call
def get_document(doctype, doc_id):
    """
    Unified API to get document details
    
    Args:
        doctype (str): Document type (Purchase Receipt, Goods Receipt Note, etc.)
        doc_id (str): Document ID
    
    Returns:
        dict: Document details with items
    """
    try:
        # Validate doctype
        if doctype not in ALLOWED_DOCTYPES:
            return {"success": False, "error": {"message": f"Unsupported doctype: {doctype}", "code": "UNSUPPORTED_DOCTYPE"}}
        
        if not doc_id:
            return {"success": False, "error": {"message": "Document ID is required", "code": "DOC_ID_REQUIRED"}}
        
        # Check if document exists
        if not frappe.db.exists(doctype, doc_id):
            return {"success": False, "error": {"message": f"{doctype} {doc_id} not found", "code": "DOCUMENT_NOT_FOUND"}}
        
        # Get document
        doc = frappe.get_doc(doctype, doc_id)
        
        # Check permissions
        if not doc.has_permission("read"):
            return {"success": False, "error": {"message": f"Access denied to this {doctype}", "code": "PERMISSION_DENIED"}}
        
        # Format response based on doctype
        doc_data = _format_document_response(doc, doctype)
        
        return {"success": True, "data": doc_data}
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Get document error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "GET_DOCUMENT_ERROR"}}

def _format_document_response(doc, doctype):
    """Format document response based on doctype"""
    try:
        # Get doctype-specific field mappings
        fields = get_doctype_fields(doctype)
        
        # Base document data
        doc_data = {
            "doc_id": doc.name,
            "title": getattr(doc, fields.get("title_field", "title"), ""),
            "naming_series": getattr(doc, "naming_series", ""),
            "company": doc.company,
            "posting_date": str(getattr(doc, fields.get("date_field", "posting_date"))) if getattr(doc, fields.get("date_field", "posting_date")) else None,
            "posting_time": str(doc.posting_time) if getattr(doc, "posting_time", None) else None,
            "set_posting_time": getattr(doc, "set_posting_time", 0),
            "supplier": getattr(doc, fields.get("supplier_field", "supplier"), ""),
            "supplier_name": getattr(doc, "supplier_name", ""),
            "supplier_delivery_note": getattr(doc, "supplier_delivery_note", ""),
            "bill_no": getattr(doc, "bill_no", ""),
            "bill_date": str(getattr(doc, "bill_date", "")) if getattr(doc, "bill_date", None) else None,
            "is_return": getattr(doc, "is_return", 0),
            "purchase_order": getattr(doc, "purchase_order", None),
            "currency": getattr(doc, fields.get("currency_field", "currency"), ""),
            "conversion_rate": flt(getattr(doc, "conversion_rate", 1), 4),
            "docstatus": doc.docstatus,
            "workflow_state": getattr(doc, "workflow_state", ""),
            "status": getattr(doc, "status", ""),
            "total_qty": flt(getattr(doc, "total_qty", 0), 2),
            "total": flt(getattr(doc, "total", 0), 2),
            "net_total": flt(getattr(doc, "net_total", 0), 2),
            "total_taxes_and_charges": flt(getattr(doc, "total_taxes_and_charges", 0), 2),
            "grand_total": flt(getattr(doc, fields.get("total_field", "grand_total"), 0), 2),
            "creation": doc.creation.isoformat() if doc.creation else None,
            "modified": doc.modified.isoformat() if doc.modified else None,
            "owner": doc.owner,
            "modified_by": doc.modified_by
        }
        
        # Add doctype-specific fields
        if doctype == "Purchase Receipt":
            doc_data.update({
                "remarks": getattr(doc, "remarks", ""),
                "custom_fields": _get_custom_fields(doc, doctype)
            })
        elif doctype == "Goods Receipt Note":
            doc_data.update({
                "remarks": getattr(doc, "remarks", ""),
                "custom_fields": _get_custom_fields(doc, doctype)
            })
        
        # Get items
        items = []
        for item in doc.items:
            item_data = {
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
                "stock_qty": flt(item.stock_qty)
            }
            
            # Add custom item fields if any
            custom_item_fields = _get_custom_item_fields(item, doctype)
            if custom_item_fields:
                item_data.update(custom_item_fields)
            
            items.append(item_data)
        
        doc_data["items"] = items
        
        # Get taxes if available
        if hasattr(doc, "taxes") and doc.taxes:
            taxes = []
            for tax in doc.taxes:
                tax_data = {
                    "id": tax.name,
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "description": tax.description,
                    "rate": flt(tax.rate),
                    "tax_amount": flt(tax.tax_amount),
                    "total": flt(tax.total),
                    "cost_center": tax.cost_center
                }
                taxes.append(tax_data)
            doc_data["taxes"] = taxes
        
        return doc_data
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Format document response error: {str(e)}")
        return {}

def _get_custom_fields(doc, doctype):
    """Get custom fields for the document"""
    try:
        custom_fields = {}
        
        # Add any custom fields that might exist
        if hasattr(doc, "custom_color"):
            custom_fields["custom_color"] = doc.custom_color
        if hasattr(doc, "custom_remarks"):
            custom_fields["custom_remarks"] = doc.custom_remarks
        
        return custom_fields
        
    except:
        return {}

def _get_custom_item_fields(item, doctype):
    """Get custom fields for item"""
    try:
        custom_fields = {}
        
        # Add any custom item fields that might exist
        if hasattr(item, "custom_no_of_boxes"):
            custom_fields["custom_no_of_boxes"] = flt(item.custom_no_of_boxes)
        if hasattr(item, "custom_color"):
            custom_fields["custom_color"] = item.custom_color
        
        return custom_fields
        
    except:
        return {}

@frappe.whitelist()
@secure_api_call
def manage_document_checklist(doctype, action, doc_id, item_id=None, **kwargs):
    """
    Unified API for document checklist management
    
    Args:
        doctype (str): Document type (Purchase Receipt, Goods Receipt Note, etc.)
        action (str): get, update_item, add_item
        doc_id (str): Document ID
        item_id (str): Checklist item ID (for update_item)
        **kwargs: Additional parameters (status, received_date, remarks, item_name, description, is_required)
    
    Returns:
        dict: Operation result
    """
    try:
        # Validate doctype
        if doctype not in ALLOWED_DOCTYPES:
            return {"success": False, "error": {"message": f"Unsupported doctype: {doctype}", "code": "UNSUPPORTED_DOCTYPE"}}
        
        if not doc_id:
            return {"success": False, "error": {"message": "Document ID is required", "code": "MISSING_DOC_ID"}}
        
        if action == "get":
            return _get_document_checklist(doctype, doc_id)
        elif action == "update_item":
            return _update_checklist_item(doctype, doc_id, item_id, **kwargs)
        elif action == "add_item":
            return _add_checklist_item(doctype, doc_id, **kwargs)
        else:
            return {"success": False, "error": {"message": f"Invalid action: {action}", "code": "INVALID_ACTION"}}
            
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Checklist management error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "CHECKLIST_MANAGEMENT_ERROR"}}

def _get_document_checklist(doctype, doc_id):
    """Get document checklist"""
    try:
        # Check if document exists
        if not frappe.db.exists(doctype, doc_id):
            return {"success": False, "error": {"message": f"{doctype} not found", "code": "DOCUMENT_NOT_FOUND"}}
        
        doc = frappe.get_doc(doctype, doc_id)
        
        # Check if document has document_checklist field
        if not hasattr(doc, 'document_checklist'):
            return {"success": False, "error": {"message": f"{doctype} does not support document checklist", "code": "FEATURE_NOT_AVAILABLE"}}
        
        # Get default checklist items based on doctype
        default_checklist = _get_default_checklist(doctype)
        
        # Get existing checklist items
        checklist_items = []
        
        if doc.document_checklist:
            for item in doc.document_checklist:
                checklist_item = {
                    "id": item.name,
                    "item_name": item.document_type,
                    "description": item.document_type,
                    "status": "Received" if item.received else "Not Received",
                    "received_date": item.received_date,
                    "remarks": item.remarks,
                    "is_required": 1 if item.document_type in [item["item_name"] for item in default_checklist if item["is_required"]] else 0,
                    "priority": 99
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
                "doc_id": doc_id,
                "checklist_items": checklist_items,
                "summary": checklist_summary
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Get checklist error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "GET_CHECKLIST_ERROR"}}

def _update_checklist_item(doctype, doc_id, item_id, **kwargs):
    """Update checklist item"""
    try:
        if not item_id:
            return {"success": False, "error": {"message": "Item ID is required", "code": "MISSING_ITEM_ID"}}
        
        doc = frappe.get_doc(doctype, doc_id)
        
        # Check if document can be modified
        if doc.docstatus != 0:
            return {"success": False, "error": {"message": f"Cannot modify {doc.status} document", "code": "INVALID_STATE"}}
        
        # Check if document has document_checklist field
        if not hasattr(doc, 'document_checklist'):
            return {"success": False, "error": {"message": f"{doctype} does not support document checklist", "code": "FEATURE_NOT_AVAILABLE"}}
        
        # Initialize checklist if not exists
        if not doc.document_checklist:
            _initialize_default_checklist(doc, doctype)
        
        # Find and update the checklist item
        item_updated = False
        for item in doc.document_checklist:
            if item.name == item_id or str(item.idx) == str(item_id):
                if kwargs.get('status'):
                    item.received = 1 if kwargs['status'] == "Received" else 0
                if kwargs.get('received_date'):
                    item.received_date = getdate(kwargs['received_date'])
                if kwargs.get('remarks') is not None:
                    item.remarks = kwargs['remarks']
                item_updated = True
                break
        
        if not item_updated and item_id.startswith('default_'):
            # Handle default items by creating them
            default_items = [item["item_name"] for item in _get_default_checklist(doctype)]
            
            item_index = int(item_id.split('_')[1]) - 1
            if 0 <= item_index < len(default_items):
                new_item = doc.append("document_checklist", {})
                new_item.document_type = default_items[item_index]
                new_item.received = 1 if kwargs.get('status') == "Received" else 0
                new_item.received_date = getdate(kwargs.get('received_date')) if kwargs.get('received_date') else None
                new_item.remarks = kwargs.get('remarks', "")
                item_updated = True
        
        if not item_updated:
            return {"success": False, "error": {"message": "Checklist item not found", "code": "ITEM_NOT_FOUND"}}
        
        # Save the document
        doc.save()
        
        return {
            "success": True,
            "data": {
                "id": item_id,
                "status": kwargs.get('status'),
                "received_date": kwargs.get('received_date'),
                "remarks": kwargs.get('remarks'),
                "updated": True
            },
            "message": "Checklist item updated successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Update checklist item error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "UPDATE_CHECKLIST_ERROR"}}

def _add_checklist_item(doctype, doc_id, **kwargs):
    """Add new checklist item"""
    try:
        doc = frappe.get_doc(doctype, doc_id)
        
        # Check if document can be modified
        if doc.docstatus != 0:
            return {"success": False, "error": {"message": f"Cannot modify {doc.status} document", "code": "INVALID_STATE"}}
        
        if not kwargs.get('item_name'):
            return {"success": False, "error": {"message": "Item name is required", "code": "MISSING_REQUIRED_FIELDS"}}
        
        # Check if document has document_checklist field
        if not hasattr(doc, 'document_checklist'):
            return {"success": False, "error": {"message": f"{doctype} does not support document checklist", "code": "FEATURE_NOT_AVAILABLE"}}
        
        # Initialize checklist if not exists
        if not doc.document_checklist:
            _initialize_default_checklist(doc, doctype)
        
        # Add new checklist item
        new_item = doc.append("document_checklist", {})
        new_item.document_type = kwargs['item_name']
        new_item.received = 0
        new_item.remarks = kwargs.get('description', "")
        
        # Save the document
        doc.save()
        
        return {
            "success": True,
            "data": {
                "id": new_item.name,
                "item_name": kwargs['item_name'],
                "description": kwargs.get('description', ""),
                "status": "Not Received",
                "received_date": None,
                "remarks": kwargs.get('description', ""),
                "is_required": cint(kwargs.get('is_required', 0)),
                "priority": 99
            },
            "message": "Checklist item added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        frappe.log_error("Mobile API Error", f"Add checklist item error: {str(e)}")
        return {"success": False, "error": {"message": str(e), "code": "ADD_CHECKLIST_ERROR"}}

def _get_default_checklist(doctype):
    """Get default checklist items for document type"""
    if doctype == "Purchase Receipt":
        return [
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
    elif doctype == "Goods Receipt Note":
        return [
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
            }
        ]
    else:
        return []

def _initialize_default_checklist(doc, doctype):
    """Initialize default checklist items for document"""
    default_items = _get_default_checklist(doctype)
    
    for item_name in [item["item_name"] for item in default_items]:
        checklist_item = doc.append("document_checklist", {})
        checklist_item.document_type = item_name
        checklist_item.received = 0
        checklist_item.received_date = None
        checklist_item.remarks = ""


def get_doctype_fields(doctype):
    """Return valid field mappings for a given doctype."""
    validated_doctype = validate_doctype(doctype)
    table_name = safe_table_name(validated_doctype)
    
    # Fetch columns from DB
    columns = frappe.db.sql(f"SHOW COLUMNS FROM {table_name}", as_dict=True)
    existing_columns = [col["Field"] for col in columns]
    
    # Get configured fields
    configured_fields = DOCTYPE_FIELDS.get(validated_doctype, {})
    
    # Build validated field map dynamically
    validated_fields = {}
    for key, fieldname in configured_fields.items():
        validated_fields[key] = fieldname if fieldname in existing_columns else None
    
    # Fallbacks
    if not validated_fields.get("title"):
        validated_fields["title"] = "name"
    if not validated_fields.get("posting_date"):
        validated_fields["posting_date"] = "creation"

    return validated_fields


def get_searchable_fields(doctype):
    """Return searchable fields (common + dynamic) that exist in DB."""
    table_name = safe_table_name(doctype)
    columns = frappe.db.sql(f"SHOW COLUMNS FROM {table_name}", as_dict=True)
    existing_columns = [col["Field"] for col in columns]

    # Common system fields
    common_fields = ["name", "creation", "modified", "docstatus"]

    # Dynamically get fields defined for this doctype (from your config)
    configured_fields = DOCTYPE_FIELDS.get(doctype, {}).values()

    # Combine and deduplicate
    preferred_fields = list(set(common_fields + list(configured_fields)))

    # Return only those that actually exist in DB
    return [field for field in preferred_fields if field in existing_columns]


def build_dynamic_query(doctype, where_clause="1=1", sort_by="creation", sort_order="DESC", limit=20, offset=0):
    """Build SQL dynamically based on doctype configuration."""
    fields = get_doctype_fields(doctype)
    table_name = safe_table_name(doctype)
    child_table = f"`tab{doctype} Item`" if frappe.db.table_exists(f"{doctype} Item") else None

    # Build SELECT fields dynamically (skip None values)
    select_fields = [
        f"doc.name AS id",
        *(f"doc.{v} AS {k}" for k, v in fields.items() if v),
        "doc.docstatus",
        """CASE
            WHEN doc.docstatus = 0 THEN 'Draft'
            WHEN doc.docstatus = 1 AND IFNULL(doc.is_return, 0) = 1 THEN 'Return'
            WHEN doc.docstatus = 1 THEN 'Submitted'
            WHEN doc.docstatus = 2 THEN 'Cancelled'
            ELSE 'Unknown'
        END AS status""",
        "doc.creation",
        "doc.modified"
    ]

    join_clause = f"LEFT JOIN {child_table} child ON child.parent = doc.name" if child_table else ""
    count_field = "COUNT(child.name) AS total_items" if child_table else "0 AS total_items"

    query = f"""
        SELECT SQL_CALC_FOUND_ROWS
            {', '.join(select_fields)},
            {count_field}
        FROM {table_name} doc
        {join_clause}
        WHERE {where_clause}
        GROUP BY doc.name
        ORDER BY doc.{sort_by} {sort_order}
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return query


@frappe.whitelist()
def manage_document_list(doctype, filters=None, sort_by="creation", sort_order="DESC", limit=20, page=1):
    """
    Unified API for document listing with pagination, filters, and dynamic field mapping.
    """
    doctype = validate_doctype(doctype)
    filters = frappe.parse_json(filters) if filters else {}

    offset = (page - 1) * limit

    # Build WHERE clause
    where_conditions = []
    for field, value in filters.items():
        # Support pattern search using dict syntax: {"supplier_name": {"like": "%ABC%"}}
        if isinstance(value, dict) and "like" in value:
            pattern = value["like"]
            where_conditions.append(f"doc.{field} LIKE {frappe.db.escape(pattern)}")
        else:
            # Default to exact match
            where_conditions.append(f"doc.{field} = {frappe.db.escape(value)}")

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    # Build and run query
    query = build_dynamic_query(
        doctype=doctype,
        where_clause=where_clause,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    doc_list = frappe.db.sql(query, {"limit": limit, "offset": offset}, as_dict=True)
    total_count = frappe.db.sql("SELECT FOUND_ROWS() as total", as_dict=True)[0].total
    total_pages = math.ceil(total_count / limit) if total_count else 1

    # Optional metadata for filters
    filters_meta = {"applied": filters, "count": len(filters)}

    return {
        "success": True,
        "data": doc_list,
        "pagination": {
            "page": page,
            "per_page": limit,
            "total": total_count,
            "pages": total_pages
        },
        "filters": filters_meta,
        "searchable_fields": get_searchable_fields(doctype)
    }