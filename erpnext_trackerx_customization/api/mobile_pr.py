import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, now_datetime
import json
from datetime import datetime, timedelta
from .mobile_utils import (
    get_document_list, get_document_filters, search_document,
    get_companies, get_purchase_orders, get_warehouses, 
    get_tax_templates, get_tax_accounts, get_document_status_summary
)

# Constants
DOCTYPE = "Purchase Receipt"


# ===========================
# CORE Purchase Receipt APIs (7 functions)
# ===========================

@frappe.whitelist()
def get_pr_list(search=None, status=None, company=None, supplier=None,
                date_from=None, date_to=None, page=1, limit=20, sort_by="creation", sort_order="desc"):
    """
    List PRs with filters/pagination
    """
    return get_document_list(DOCTYPE, search, status, company, supplier,
                            date_from, date_to, page, limit, sort_by, sort_order)

@frappe.whitelist()
def get_pr_filters():
    """
    Get filter options for PR list
    """
    return get_document_filters(DOCTYPE)

@frappe.whitelist()
def search_pr(search_term, limit=10):
    """
    Quick search PRs
    """
    return search_document(DOCTYPE, search_term, limit)

@frappe.whitelist()
def create_pr(company=None, naming_series=None, supplier=None, purchase_order=None):
    """
    Create new Purchase Receipt
    """
    try:
        # Get user defaults
        default_company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

        # Create new Purchase Receipt document
        pr = frappe.new_doc(DOCTYPE)

        # Set default values
        pr.posting_date = getdate()
        pr.posting_time = now_datetime().time()
        pr.set_posting_time = 0
        pr.company = company or default_company
        pr.is_return = 0

        # Set naming series
        if naming_series:
            pr.naming_series = naming_series
        else:
            default_naming_series = frappe.db.get_value(DOCTYPE, {"company": pr.company}, "naming_series")
            if not default_naming_series:
                default_naming_series = frappe.get_meta(DOCTYPE).get_field("naming_series").options.split("\n")[0]
            pr.naming_series = default_naming_series

        # Set supplier and purchase order if provided
        if supplier:
            pr.supplier = supplier
        if purchase_order:
            pr.purchase_order = purchase_order

        # Insert document (save as draft)
        pr.flags.ignore_validate = True
        pr.flags.ignore_mandatory = True
        pr.flags.ignore_links = True

        pr.insert(ignore_permissions=True)

        return {
            "success": True,
            "data": {
                "pr_id": pr.name,
                "series": pr.naming_series,
                "posting_date": str(pr.posting_date),
                "posting_time": str(pr.posting_time) if pr.posting_time else None,
                "company": pr.company,
                "supplier": pr.supplier,
                "purchase_order": pr.purchase_order,
                "is_return": pr.is_return,
                "set_posting_time": pr.set_posting_time,
                "docstatus": pr.docstatus,
                "creation": pr.creation.isoformat() if pr.creation else None,
                "modified": pr.modified.isoformat() if pr.modified else None
            },
            "message": "Purchase Receipt created successfully"
        }

    except Exception as e:
        frappe.log_error("Mobile PR Create Error", frappe.get_traceback())
        return {"success": False, "error": {"message": str(e), "code": "PR_CREATE_ERROR"}}

@frappe.whitelist()
def get_pr(pr_id):
    """
    Get PR details (includes items, taxes, checklist)
    """
    try:
        if not pr_id:
            return {"success": False, "error": {"message": "PR ID is required", "code": "PR_ID_REQUIRED"}}

        # Check if PR exists
        if not frappe.db.exists(DOCTYPE, pr_id):
            return {"success": False, "error": {"message": f"Purchase Receipt {pr_id} not found", "code": "PR_NOT_FOUND"}}

        # Get PR document
        pr = frappe.get_doc(DOCTYPE, pr_id)

        # Format response
        pr_data = {
            "pr_id": pr.name,
            "title": getattr(pr, "title", ""),
            "naming_series": getattr(pr, "naming_series", ""),
            "company": pr.company,
            "posting_date": str(pr.posting_date) if pr.posting_date else None,
            "posting_time": str(pr.posting_time) if pr.posting_time else None,
            "set_posting_time": getattr(pr, "set_posting_time", 0),
            "supplier": pr.supplier,
            "supplier_name": getattr(pr, "supplier_name", ""),
            "supplier_delivery_note": getattr(pr, "supplier_delivery_note", ""),
            "bill_no": getattr(pr, "bill_no", ""),
            "bill_date": str(getattr(pr, "bill_date", "")) if getattr(pr, "bill_date", None) else None,
            "is_return": getattr(pr, "is_return", 0),
            "purchase_order": getattr(pr, "purchase_order", None),
            "currency": getattr(pr, "currency", ""),
            "conversion_rate": flt(getattr(pr, "conversion_rate", 1), 4),
            "docstatus": pr.docstatus,
            "workflow_state": getattr(pr, "workflow_state", ""),
            "status": getattr(pr, "status", ""),
            "total_qty": flt(getattr(pr, "total_qty", 0), 2),
            "total": flt(getattr(pr, "total", 0), 2),
            "net_total": flt(getattr(pr, "net_total", 0), 2),
            "total_taxes_and_charges": flt(getattr(pr, "total_taxes_and_charges", 0), 2),
            "grand_total": flt(getattr(pr, "grand_total", 0), 2),
            "creation": pr.creation.isoformat() if pr.creation else None,
            "modified": pr.modified.isoformat() if pr.modified else None,
            "owner": pr.owner,
            "modified_by": pr.modified_by
        }

        # Get items
        items = []
        for item in pr.items:
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
            items.append(item_data)

        pr_data["items"] = items

        # Get taxes
        taxes = []
        for tax in pr.taxes:
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

        pr_data["taxes"] = taxes

        return {"success": True, "data": pr_data}

    except Exception as e:
        frappe.log_error("Mobile PR Get Error", frappe.get_traceback())
        return {"success": False, "error": {"message": str(e), "code": "PR_GET_ERROR"}}

@frappe.whitelist()
def validate_pr(pr_id):
    """
    Validate PR for submission
    """
    try:
        if not pr_id:
            return {"success": False, "error": {"message": "PR ID is required", "code": "PR_ID_REQUIRED"}}

        pr = frappe.get_doc(DOCTYPE, pr_id)

        validation_results = {
            "is_valid": True,
            "can_submit": True,
            "issues": [],
            "warnings": []
        }

        # Header validation
        if not pr.supplier:
            validation_results["issues"].append("Supplier is required")
        if not pr.company:
            validation_results["issues"].append("Company is required")
        if not pr.posting_date:
            validation_results["issues"].append("Posting date is required")

        # Items validation
        if not pr.items:
            validation_results["issues"].append("At least one item is required")
        else:
            for item in pr.items:
                if not item.item_code:
                    validation_results["issues"].append("All items must have item codes")
                if flt(item.received_qty) <= 0:
                    validation_results["issues"].append("All items must have received quantity greater than 0")

                # Check batch requirements
                if item.item_code:
                    has_batch = frappe.db.get_value("Item", item.item_code, "has_batch_no")
                    if has_batch and not item.batch_no:
                        validation_results["issues"].append(f"Batch number required for item {item.item_code}")

        # Set final validation status
        if validation_results["issues"]:
            validation_results["is_valid"] = False
            validation_results["can_submit"] = False

        return {
            "success": True,
            "data": {
                "pr_id": pr_id,
                "validation_results": validation_results,
                "ready_for_submission": validation_results["can_submit"]
            },
            "message": "Validation completed" if validation_results["is_valid"] else f"Validation failed with {len(validation_results['issues'])} error(s)"
        }

    except Exception as e:
        frappe.log_error("Mobile PR Validation Error", frappe.get_traceback())
        return {"success": False, "error": {"message": str(e), "code": "PR_VALIDATION_ERROR"}}

@frappe.whitelist()
def submit_pr(pr_id):
    """
    Submit PR after validation
    """
    try:
        # First validate the PR
        validation_response = validate_pr(pr_id)
        if not validation_response["success"]:
            return validation_response

        if not validation_response["data"]["ready_for_submission"]:
            return {
                "success": False,
                "error": {
                    "message": "PR validation failed",
                    "code": "VALIDATION_FAILED",
                    "details": validation_response["data"]["validation_results"]["issues"]
                }
            }

        # Get and submit the PR
        pr = frappe.get_doc(DOCTYPE, pr_id)

        if pr.docstatus == 1:
            return {"success": False, "error": {"message": "PR is already submitted", "code": "ALREADY_SUBMITTED"}}

        if pr.docstatus == 2:
            return {"success": False, "error": {"message": "PR is cancelled", "code": "CANCELLED_DOCUMENT"}}

        # Submit the document
        pr.submit()

        # Get final PR details
        submitted_pr = {
            "pr_id": pr.name,
            "status": "Submitted",
            "docstatus": pr.docstatus,
            "submitted_by": frappe.session.user,
            "submission_date": now_datetime(),
            "grand_total": flt(pr.grand_total),
            "currency": pr.currency,
            "supplier": pr.supplier,
            "company": pr.company
        }

        return {
            "success": True,
            "data": submitted_pr,
            "message": "Purchase Receipt submitted successfully",
            "timestamp": datetime.now().isoformat()
        }

    except frappe.ValidationError as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": str(e), "code": "VALIDATION_ERROR"}}
    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to submit PR", "code": "SUBMISSION_ERROR"}}

# ===========================
# HELPER APIs (Reused from mobile_utils)
# ===========================

@frappe.whitelist()
def get_companies():
    """Get companies list for dropdown"""
    return get_companies()

@frappe.whitelist()
def get_purchase_orders(supplier=None, company=None, search=None):
    """Get purchase orders for dropdown"""
    return get_purchase_orders(supplier, company, search)

@frappe.whitelist()
def get_warehouses(company=None):
    """Get list of warehouses for dropdown"""
    return get_warehouses(company)

@frappe.whitelist()
def get_tax_templates():
    """Get available Purchase Taxes and Charges templates"""
    return get_tax_templates()

@frappe.whitelist()
def get_tax_accounts(company=None):
    """Get tax account heads for dropdown"""
    return get_tax_accounts(company)

@frappe.whitelist()
def get_pr_status_summary():
    """
    Get count of PRs by status for dashboard display
    """
    return get_document_status_summary(DOCTYPE)
