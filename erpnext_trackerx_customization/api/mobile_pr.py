import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, now_datetime
import json
from datetime import datetime, timedelta
from .mobile_utils import (
    get_companies as get_companies_utils, get_purchase_orders as get_purchase_orders_utils, get_warehouses as get_warehouses_utils, 
    get_tax_templates as get_tax_templates_utils, get_tax_accounts as get_tax_accounts_utils, get_naming_series as get_naming_series_utils,
    secure_api_call
)

# Constants
DOCTYPE = "Purchase Receipt"



# ===========================
# HELPER APIs (Reused from mobile_utils)
# ===========================

@frappe.whitelist()
@secure_api_call
def get_companies():
    """Get companies list for dropdown"""
    return get_companies_utils()

@frappe.whitelist()
@secure_api_call
def get_purchase_orders(supplier=None, company=None, search=None):
    """Get purchase orders for dropdown"""
    return get_purchase_orders_utils(supplier, company, search)

@frappe.whitelist()
@secure_api_call
def get_warehouses(company=None):
    """Get list of warehouses for dropdown"""
    return get_warehouses_utils(company)

@frappe.whitelist()
@secure_api_call
def get_tax_templates():
    """Get available Purchase Taxes and Charges templates"""
    return get_tax_templates_utils()

@frappe.whitelist()
@secure_api_call
def get_tax_accounts(company=None):
    """Get tax account heads for dropdown"""
    return get_tax_accounts_utils(company)

@frappe.whitelist()
@secure_api_call
def get_naming_series():
    """
    Get available naming series for Purchase Receipt
    """
    return get_naming_series_utils(DOCTYPE)

@frappe.whitelist()
def update_pr_header(pr_id, **kwargs):
    """
    Update PR header information

    Args:
        pr_id (str): PR document name
        **kwargs: Fields to update

    Returns:
        dict: Update result
    """
    try:
        if not pr_id:
            return {
                "success": False,
                "error": {
                    "message": "PR ID is required",
                    "code": "PR_ID_REQUIRED"
                }
            }

        # Get PR document
        pr = frappe.get_doc(DOCTYPE, pr_id)

        # Check if PR can be modified
        if pr.docstatus != 0:
            return {
                "success": False,
                "error": {
                    "message": f"Cannot modify {pr.status} Purchase Receipt",
                    "code": "PR_NOT_DRAFT"
                }
            }

        # Track changes
        changes = {}

        # Update allowed fields
        updatable_fields = [
            'posting_date', 'posting_time', 'set_posting_time', 'company',
            'supplier_delivery_note', 'bill_no', 'bill_date', 'is_return',
            'purchase_order', 'supplier', 'title', 'remarks', 'currency',
            'conversion_rate', 'buying_price_list', 'price_list_currency',
            'plc_conversion_rate', 'ignore_pricing_rule'
        ]

        for field, value in kwargs.items():
            if field in updatable_fields and hasattr(pr, field):
                old_value = getattr(pr, field)

                # Handle date fields
                if field in ['posting_date', 'bill_date'] and value:
                    value = getdate(value)

                # Handle time fields
                if field == 'posting_time' and value:
                    from frappe.utils import get_time
                    value = get_time(value)

                # Handle boolean fields
                if field in ['set_posting_time', 'is_return', 'ignore_pricing_rule']:
                    value = cint(value)

                # Handle float fields
                if field in ['conversion_rate', 'plc_conversion_rate']:
                    value = flt(value)

                if old_value != value:
                    setattr(pr, field, value)
                    changes[field] = {"old": old_value, "new": value}

        # If purchase order is updated, update supplier automatically
        if 'purchase_order' in changes and changes['purchase_order']['new']:
            po_name = changes['purchase_order']['new']
            po_supplier = frappe.db.get_value("Purchase Order", po_name, "supplier")
            if po_supplier and po_supplier != pr.supplier:
                pr.supplier = po_supplier
                changes['supplier'] = {"old": pr.supplier, "new": po_supplier}

        # Save document if changes were made
        if changes:
            pr.save(ignore_permissions=True)

        return {
            "success": True,
            "data": {
                "pr_id": pr.name,
                "changes_made": len(changes),
                "changes": changes,
                "modified": pr.modified.isoformat() if pr.modified else None
            },
            "message": f"Purchase Receipt updated successfully. {len(changes)} field(s) changed."
        }

    except Exception as e:
        frappe.log_error("Mobile PR Update Error", frappe.get_traceback())
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "PR_UPDATE_ERROR"
            }
        }



@frappe.whitelist()
def calculate_pr_totals(pr_id):
    """
    Calculate and return Purchase Receipt totals

    Args:
        pr_id (str): Purchase Receipt document ID

    Returns:
        dict: Calculated totals
    """
    try:
        pr = frappe.get_doc(DOCTYPE, pr_id)

        # Force recalculation
        pr.save()

        totals = {
            "net_total": flt(pr.net_total),
            "total_taxes_and_charges": flt(pr.total_taxes_and_charges),
            "grand_total": flt(pr.grand_total),
            "rounded_total": flt(getattr(pr, "rounded_total", 0)),
            "rounding_adjustment": flt(getattr(pr, "rounding_adjustment", 0)),
            "discount_amount": flt(getattr(pr, "discount_amount", 0)),
            "additional_discount_percentage": flt(getattr(pr, "additional_discount_percentage", 0)),
            "currency": pr.currency,

            # Breakdown for display
            "totals_breakdown": {
                "items_total": flt(pr.net_total),
                "taxes_total": flt(pr.total_taxes_and_charges),
                "discount": flt(getattr(pr, "discount_amount", 0)),
                "final_total": flt(getattr(pr, "rounded_total", 0)) if not getattr(pr, "disable_rounded_total", 0) else flt(pr.grand_total)
            }
        }

        return {
            "success": True,
            "data": totals,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to calculate totals", "code": "API_ERROR"}}


@frappe.whitelist()
@secure_api_call
def validate_pr_header(pr_id):
    """
    Validate PR header before moving to next tab

    Args:
        pr_id (str): PR document name

    Returns:
        dict: Validation result
    """
    try:
        if not pr_id:
            return {
                "success": False,
                "error": {
                    "message": "PR ID is required",
                    "code": "PR_ID_REQUIRED"
                }
            }

        # Get PR document
        pr = frappe.get_doc("Purchase Receipt", pr_id)

        # Validation rules
        errors = []
        warnings = []

        # Required field validations
        if not pr.company:
            errors.append("Company is required")

        if not pr.posting_date:
            errors.append("Posting date is required")

        if not pr.supplier:
            errors.append("Supplier is required")

        # Business logic validations
        if pr.posting_date and getdate(pr.posting_date) > getdate():
            warnings.append("Posting date is in the future")

        if pr.is_return and not pr.return_against:
            warnings.append("Return against document is recommended for return entries")

        # Purchase order validations
        if pr.items:
            po_list = list(set([item.purchase_order for item in pr.items if item.purchase_order]))
            if len(po_list) > 1:
                warnings.append("Multiple purchase orders found in items")

        # Supplier delivery note validation
        if pr.supplier_delivery_note and not pr.purchase_order:
            warnings.append("Purchase order is recommended when supplier delivery note is provided")

        # Currency validation
        if pr.currency != pr.company_currency:
            warnings.append("Currency differs from company currency")

        return {
            "success": True,
            "data": {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "can_proceed": len(errors) == 0,
                "pr_id": pr.name,
                "status": pr.status,
                "docstatus": pr.docstatus
            },
            "message": "Validation completed" if len(errors) == 0 else f"Validation failed with {len(errors)} error(s)"
        }

    except Exception as e:
        frappe.log_error(f"Error validating PR {pr_id}: {str(e)}", "Mobile PR Validation Error")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "code": "PR_VALIDATION_ERROR"
            }
        }