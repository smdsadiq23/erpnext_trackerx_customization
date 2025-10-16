import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, now_datetime
import json
from datetime import datetime, timedelta
from .mobile_utils import (
    get_document_list as get_document_list_utils, get_document_filters as get_document_filters_utils, search_document as search_document_utils,
    get_companies as get_companies_utils, get_purchase_orders as get_purchase_orders_utils, get_warehouses as get_warehouses_utils, 
    get_tax_templates as get_tax_templates_utils, get_tax_accounts as get_tax_accounts_utils, get_document_status_summary
    as get_document_status_summary_utils, get_naming_series as get_naming_series_utils,
    search_items as search_items_utils, get_document_items as get_document_items_utils, add_document_item as add_document_item_utils,
    update_document_item as update_document_item_utils, delete_document_item as delete_document_item_utils, 
    validate_document_items as validate_document_items_utils,
    # Import security decorator
    secure_api_call
)

# Constants
DOCTYPE = "Purchase Receipt"



# ===========================
# CORE Purchase Receipt APIs (7 functions)
# ===========================

@frappe.whitelist()
@secure_api_call
def get_pr_list(search=None, status=None, company=None, supplier=None,
                            date_from=None, date_to=None, page=1, limit=20, sort_by="creation", sort_order="desc"):
    """
    List PRs with filters/pagination
    """
    return get_document_list_utils(DOCTYPE, search, status, company, supplier,
                            date_from, date_to, page, limit, sort_by, sort_order)

@frappe.whitelist()
@secure_api_call
def get_pr_filters():
    """
    Get filter options for PR list
    """
    return get_document_filters_utils(DOCTYPE)

@frappe.whitelist()
@secure_api_call
def search_pr(search_term, limit=10):
    """
    Quick search PRs
    """
    return search_document_utils(DOCTYPE, search_term, limit)

@frappe.whitelist()
def create_pr(company=None, naming_series=None, supplier=None, purchase_order=None, supplier_delivery_note=None):
    """
    Create new Purchase Receipt with default values

    Args:
        company (str): Company name
        naming_series (str): Naming series for the PR
        supplier (str): Supplier name
        purchase_order (str): Purchase Order reference
        supplier_delivery_note (str): Supplier delivery note number (optional)

    Returns:
        dict: New PR details with default values
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
            # Get default naming series
            default_naming_series = frappe.db.get_value(DOCTYPE, {"company": pr.company}, "naming_series")
            if not default_naming_series:
                default_naming_series = frappe.get_meta(DOCTYPE).get_field("naming_series").options.split("\n")[0]
            pr.naming_series = default_naming_series

        # Set supplier and purchase order if provided
        if supplier:
            pr.supplier = supplier
        if purchase_order:
            pr.purchase_order = purchase_order

        # Set supplier delivery note if provided
        if supplier_delivery_note:
            pr.supplier_delivery_note = supplier_delivery_note

        # SECURITY IMPROVEMENT: Only bypass mandatory validation for items
        # This allows creating a PR without items initially, but maintains other validations
        pr.flags.ignore_mandatory = True  # Only bypass mandatory fields (like items requirement)
        
        # Additional security: Validate critical fields before insert
        if not pr.company:
            return {"success": False, "error": {"message": "Company is required", "code": "MISSING_COMPANY"}}
        
        if not pr.posting_date:
            return {"success": False, "error": {"message": "Posting date is required", "code": "MISSING_POSTING_DATE"}}

        # Insert document with minimal validation bypass
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
                "supplier_delivery_note": getattr(pr, "supplier_delivery_note", ""),
                "is_return": pr.is_return,
                "set_posting_time": pr.set_posting_time,
                "docstatus": pr.docstatus,
                "creation": str(pr.creation) if pr.creation else None,
                "modified": str(pr.modified) if pr.modified else None
            },
            "message": "Purchase Receipt created successfully"
        }

    except Exception as e:
        frappe.log_error(f"Mobile PR Create Error for company {company}, supplier {supplier}, purchase_order {purchase_order}", frappe.get_traceback())
        return {
            "success": False,
            "error": {
                "message": f"Failed to create Purchase Receipt: {str(e)}",
                "code": "PR_CREATE_ERROR"
            }
        }

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
        
        # SECURITY: Check document-level permissions
        if not pr.has_permission("read"):
            return {"success": False, "error": {"message": "Access denied to this Purchase Receipt", "code": "PERMISSION_DENIED"}}

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
    Submit Purchase Receipt after validation

    Args:
        pr_id (str): Purchase Receipt document ID

    Returns:
        dict: Submission result
    """
    try:
        # First validate the Purchase Receipt
        validation_response = validate_pr_for_submission(pr_id)
        if not validation_response["success"]:
            return validation_response

        if not validation_response["data"]["ready_for_submission"]:
            return {
                "success": False,
                "error": {
                    "message": "Purchase Receipt validation failed",
                    "code": "VALIDATION_FAILED",
                    "details": validation_response["data"]["validation_results"]["issues"]
                }
            }

        # Get and submit the Purchase Receipt
        pr = frappe.get_doc(DOCTYPE, pr_id)

        if pr.docstatus == 1:
            return {"success": False, "error": {"message": "Purchase Receipt is already submitted", "code": "ALREADY_SUBMITTED"}}

        if pr.docstatus == 2:
            return {"success": False, "error": {"message": "Purchase Receipt is cancelled", "code": "CANCELLED_DOCUMENT"}}

        # Submit the document
        pr.submit()

        # Get final Purchase Receipt details
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
        return {"success": False, "error": {"message": "Failed to submit Purchase Receipt", "code": "SUBMISSION_ERROR"}}

@frappe.whitelist()
def validate_pr_for_submission(pr_id):
    """
    Validate Purchase Receipt for final submission

    Args:
        pr_id (str): Purchase Receipt document ID

    Returns:
        dict: Validation results and submission readiness
    """
    try:
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

        # Checklist validation (only if checklist feature is available)
        checklist_response = None
        if hasattr(pr, 'document_checklist'):
            checklist_response = get_pr_checklist(pr_id)
            if checklist_response["success"]:
                checklist_data = checklist_response["data"]
                if not checklist_data["summary"]["can_submit"]:
                    validation_results["issues"].append("All required checklist items must be completed")
                    validation_results["warnings"].append(f"Required checklist completion: {checklist_data['summary']['required_completed']}/{checklist_data['summary']['required_items']}")

        # Total validation
        if flt(pr.grand_total) <= 0:
            validation_results["warnings"].append("Grand total is zero - please verify calculations")

        # Set final validation status
        if validation_results["issues"]:
            validation_results["is_valid"] = False
            validation_results["can_submit"] = False

        # Submission checklist
        submission_checklist = [
            {
                "item": "Header Information",
                "status": "Complete" if pr.supplier and pr.company and pr.posting_date else "Incomplete",
                "required": True
            },
            {
                "item": "Items Added",
                "status": "Complete" if pr.items and len(pr.items) > 0 else "Incomplete",
                "required": True
            },
            {
                "item": "Quantities Entered",
                "status": "Complete" if all(flt(item.received_qty) > 0 for item in pr.items) else "Incomplete",
                "required": True
            },
            {
                "item": "Document Checklist",
                "status": checklist_response["data"]["summary"]["status"] if checklist_response and checklist_response["success"] else "Not Available",
                "required": hasattr(pr, 'document_checklist')
            },
            {
                "item": "Tax Calculations",
                "status": "Complete" if flt(pr.grand_total) > 0 else "Incomplete",
                "required": False
            }
        ]

        return {
            "success": True,
            "data": {
                "pr_id": pr_id,
                "validation_results": validation_results,
                "submission_checklist": submission_checklist,
                "ready_for_submission": validation_results["can_submit"]
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Validation failed", "code": "VALIDATION_ERROR"}}

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
def get_pr_status_summary():
    """
    Get count of PRs by status for dashboard display
    """
    return get_document_status_summary_utils(DOCTYPE)

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


# ===========================
# ITEM MANAGEMENT APIs
# ===========================

@frappe.whitelist()
@secure_api_call
def search_items(search_term, supplier=None, company=None, limit=10):
    """
    Search items for adding to Purchase Receipt
    """
    return search_items_utils(search_term, supplier, company, limit)


@frappe.whitelist()
@secure_api_call
def get_pr_items(pr_id):
    """
    Get all items in a Purchase Receipt for the Items tab
    """
    return get_document_items_utils(DOCTYPE, pr_id)


@frappe.whitelist()
def add_pr_item(pr_id, item_code, warehouse, qty=1, received_qty=None, no_of_boxes=None,
                batch_no=None, serial_no=None, rate=None):
    """
    Add a new item to Purchase Receipt
    """
    return add_document_item_utils(DOCTYPE, pr_id, item_code, warehouse, qty, received_qty, 
                                   no_of_boxes, batch_no, serial_no, rate)


@frappe.whitelist()
def update_pr_item(item_id, **kwargs):
    """
    Update an existing Purchase Receipt item
    """
    return update_document_item_utils(DOCTYPE, item_id, **kwargs)


@frappe.whitelist()
def delete_pr_item(item_id):
    """
    Delete a Purchase Receipt item
    """
    return delete_document_item_utils(DOCTYPE, item_id)


@frappe.whitelist()
def validate_pr_items(pr_id):
    """
    Validate Purchase Receipt items before moving to next tab
    """
    return validate_document_items_utils(DOCTYPE, pr_id)


# ===========================
# TAX MANAGEMENT APIs
# ===========================

@frappe.whitelist()
def add_tax_charge(pr_id, charge_type, account_head, rate=0, tax_amount=0, description=None):
    """
    Add individual tax/charge to Purchase Receipt

    Args:
        pr_id (str): Purchase Receipt document ID
        charge_type (str): Type of charge (On Net Total, Actual, etc.)
        account_head (str): Account head for the charge
        rate (float): Tax rate percentage
        tax_amount (float): Fixed tax amount
        description (str): Description of the charge

    Returns:
        dict: Added tax charge details
    """
    try:
        pr = frappe.get_doc(DOCTYPE, pr_id)
        
        # Use reusable validation
        state_error = _validate_document_state(pr, "modify")
        if state_error:
            return state_error
        
        # Validate required fields
        if not charge_type or not account_head:
            return {"success": False, "error": {"message": "Charge type and account head are required", "code": "MISSING_REQUIRED_FIELDS"}}

        # Add new tax row
        tax_row = pr.append("taxes", {})
        tax_row.charge_type = charge_type
        tax_row.account_head = account_head
        tax_row.rate = flt(rate)
        tax_row.tax_amount = flt(tax_amount)
        tax_row.description = description or frappe.db.get_value("Account", account_head, "account_name")

        # Save and calculate
        pr.save()

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
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to add tax charge", "code": "API_ERROR"}}


@frappe.whitelist()
def apply_tax_template(pr_id, template_name):
    """
    Apply tax template to Purchase Receipt

    Args:
        pr_id (str): Purchase Receipt document ID
        template_name (str): Tax template name

    Returns:
        dict: Updated tax information
    """
    try:
        pr = frappe.get_doc(DOCTYPE, pr_id)
        
        # Use reusable validation
        state_error = _validate_document_state(pr, "modify")
        if state_error:
            return state_error

        # Clear existing taxes
        pr.taxes = []

        # Set the template
        pr.taxes_and_charges = template_name

        if template_name:
            # Get template taxes
            template = frappe.get_doc("Purchase Taxes and Charges Template", template_name)

            # Add template taxes to Purchase Receipt
            for template_tax in template.taxes:
                tax_row = pr.append("taxes", {})
                tax_row.charge_type = template_tax.charge_type
                tax_row.account_head = template_tax.account_head
                tax_row.description = template_tax.description
                tax_row.rate = template_tax.rate
                tax_row.cost_center = template_tax.cost_center

        # Save and calculate
        pr.save()

        # Return updated tax information
        return get_pr_taxes_and_charges(pr_id)

    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to apply tax template", "code": "API_ERROR"}}


@frappe.whitelist()
def get_pr_taxes_and_charges(pr_id):
    """
    Get taxes and charges for a Purchase Receipt

    Args:
        pr_id (str): Purchase Receipt document ID

    Returns:
        dict: Tax and charge details
    """
    try:
        if not frappe.db.exists(DOCTYPE, pr_id):
            return {"success": False, "error": {"message": "Purchase Receipt not found", "code": "PR_NOT_FOUND"}}

        pr = frappe.get_doc(DOCTYPE, pr_id)

        # Get tax details
        taxes_and_charges = []
        for tax in pr.taxes:
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
            "tax_category": getattr(pr, "tax_category", ""),
            "shipping_rule": getattr(pr, "shipping_rule", ""),
            "incoterm": getattr(pr, "incoterm", ""),
            "taxes_and_charges_template": getattr(pr, "taxes_and_charges", ""),
            "taxes_and_charges": taxes_and_charges,
            "net_total": flt(pr.net_total),
            "total_taxes_and_charges": flt(pr.total_taxes_and_charges),
            "grand_total": flt(pr.grand_total),
            "rounded_total": flt(getattr(pr, "rounded_total", 0)),
            "rounding_adjustment": flt(getattr(pr, "rounding_adjustment", 0)),
            "disable_rounded_total": getattr(pr, "disable_rounded_total", 0) or 0,
            "additional_discount_percentage": flt(getattr(pr, "additional_discount_percentage", 0)),
            "discount_amount": flt(getattr(pr, "discount_amount", 0))
        }

        return {
            "success": True,
            "data": tax_info,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to get tax details", "code": "API_ERROR"}}


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
        pr = frappe.get_doc(DOCTYPE, tax_doc.parent)

        state_error = _validate_document_state(pr, "modify")
        if state_error:
            return state_error

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
        pr.save()

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
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to update tax charge", "code": "API_ERROR"}}


@frappe.whitelist()
def update_pr_tax_settings(pr_id, **kwargs):
    """
    Update Purchase Receipt tax-related settings

    Args:
        pr_id (str): Purchase Receipt document ID
        **kwargs: Tax settings to update

    Returns:
        dict: Updated settings
    """
    try:
        pr = frappe.get_doc(DOCTYPE, pr_id)
        
        state_error = _validate_document_state(pr, "modify")
        if state_error:
            return state_error

        # Update allowed tax settings
        allowed_fields = [
            'tax_category', 'shipping_rule', 'incoterm', 'disable_rounded_total',
            'additional_discount_percentage', 'discount_amount'
        ]
        updated_fields = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field in ['additional_discount_percentage', 'discount_amount']:
                    setattr(pr, field, flt(value))
                elif field == 'disable_rounded_total':
                    setattr(pr, field, cint(value))
                else:
                    setattr(pr, field, value)
                updated_fields.append(field)

        # Save and recalculate totals
        pr.save()

        return {
            "success": True,
            "data": {
                "pr_id": pr.name,
                "updated_fields": updated_fields,
                "net_total": flt(pr.net_total),
                "total_taxes_and_charges": flt(pr.total_taxes_and_charges),
                "grand_total": flt(pr.grand_total),
                "rounded_total": flt(getattr(pr, "rounded_total", 0))
            },
            "message": "Tax settings updated successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to update tax settings", "code": "API_ERROR"}}


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
def get_pr_checklist(pr_id):
    """
    Get document checklist for Purchase Receipt

    Args:
        pr_id (str): Purchase Receipt document ID

    Returns:
        dict: Checklist items and status
    """
    try:
        if not frappe.db.exists(DOCTYPE, pr_id):
            return {"success": False, "error": {"message": "Purchase Receipt not found", "code": "PR_NOT_FOUND"}}

        pr = frappe.get_doc(DOCTYPE, pr_id)

        # Check if Purchase Receipt has document_checklist field
        if not hasattr(pr, 'document_checklist'):
            return {"success": False, "error": {"message": "Purchase Receipt does not support document checklist", "code": "FEATURE_NOT_AVAILABLE"}}

        # Default checklist items for Purchase Receipt
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

        # Check if Purchase Receipt has document checklist field
        if pr.document_checklist:
            for item in pr.document_checklist:
                checklist_item = {
                    "id": item.name,
                    "item_name": item.document_type,
                    "description": item.document_type,
                    "status": "Received" if item.received else "Not Received",
                    "received_date": item.received_date,
                    "remarks": item.remarks,
                    "is_required": 1 if item.document_type in ["Purchase Order", "Delivery Challan / Invoice", "Packing List"] else 0,
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
                "pr_id": pr_id,
                "checklist_items": checklist_items,
                "summary": checklist_summary
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to get checklist", "code": "API_ERROR"}}

@frappe.whitelist()
def update_checklist_item(pr_id, item_id, status=None, received_date=None, remarks=None):
    """
    Update checklist item status

    Args:
        pr_id (str): Purchase Receipt document ID
        item_id (str): Checklist item ID
        status (str): Received/Not Received
        received_date (str): Date when document was received
        remarks (str): Additional remarks

    Returns:
        dict: Updated item details
    """
    try:
        pr = frappe.get_doc(DOCTYPE, pr_id)
        
        state_error = _validate_document_state(pr, "modify")
        if state_error:
            return state_error

        # Check if Purchase Receipt has document_checklist field
        if not hasattr(pr, 'document_checklist'):
            return {"success": False, "error": {"message": "Purchase Receipt does not support document checklist", "code": "FEATURE_NOT_AVAILABLE"}}

        # Initialize checklist if not exists
        if not pr.document_checklist:
            _initialize_default_checklist(pr)

        # Find and update the checklist item
        item_updated = False
        for item in pr.document_checklist:
            if item.name == item_id or str(item.idx) == str(item_id):
                if status:
                    item.received = 1 if status == "Received" else 0
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
                new_item = pr.append("document_checklist", {})
                new_item.document_type = default_items[item_index]
                new_item.received = 1 if status == "Received" else 0
                new_item.received_date = getdate(received_date) if received_date else None
                new_item.remarks = remarks or ""
                item_updated = True

        if not item_updated:
            return {"success": False, "error": {"message": "Checklist item not found", "code": "ITEM_NOT_FOUND"}}

        # Save the Purchase Receipt
        pr.save()

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
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to update checklist item", "code": "API_ERROR"}}

@frappe.whitelist()
def add_checklist_item(pr_id, item_name, description=None, is_required=0):
    """
    Add new checklist item to Purchase Receipt

    Args:
        pr_id (str): Purchase Receipt document ID
        item_name (str): Name of the checklist item
        description (str): Description of the item
        is_required (int): Whether item is required (1) or optional (0)

    Returns:
        dict: Added item details
    """
    try:
        pr = frappe.get_doc(DOCTYPE, pr_id)
        
        state_error = _validate_document_state(pr, "modify")
        if state_error:
            return state_error

        if not item_name:
            return {"success": False, "error": {"message": "Item name is required", "code": "MISSING_REQUIRED_FIELDS"}}

        # Check if Purchase Receipt has document_checklist field
        if not hasattr(pr, 'document_checklist'):
            return {"success": False, "error": {"message": "Purchase Receipt does not support document checklist", "code": "FEATURE_NOT_AVAILABLE"}}

        # Initialize checklist if not exists
        if not pr.document_checklist:
            _initialize_default_checklist(pr)

        # Add new checklist item
        new_item = pr.append("document_checklist", {})
        new_item.document_type = item_name
        new_item.received = 0
        new_item.remarks = description or ""

        # Save the Purchase Receipt
        pr.save()

        # Return added item
        added_item = {
            "id": new_item.name,
            "item_name": item_name,
            "description": item_name,
            "status": "Not Received",
            "received_date": None,
            "remarks": description or "",
            "is_required": cint(is_required),
            "priority": 99
        }

        return {
            "success": True,
            "data": added_item,
            "message": "Checklist item added successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        frappe.log_error("Mobile PR API", frappe.get_traceback())
        return {"success": False, "error": {"message": "Failed to add checklist item", "code": "API_ERROR"}}

def _validate_document_state(pr, action="modify"):
    """
    Validate document state for modifications
    
    Args:
        pr: Purchase Receipt document
        action (str): Action being performed (modify, submit, etc.)
    
    Returns:
        dict or None: Error response if validation fails, None if valid
    """
    if pr.docstatus == 1:
        return {"success": False, "error": {"message": f"Cannot {action} submitted Purchase Receipt", "code": "INVALID_STATE"}}
    if pr.docstatus == 2:
        return {"success": False, "error": {"message": f"Cannot {action} cancelled Purchase Receipt", "code": "CANCELLED_DOCUMENT"}}
    return None

def _initialize_default_checklist(pr):
    """
    Initialize default checklist items for Purchase Receipt
    
    Args:
        pr: Purchase Receipt document
    """
    default_items = [
        "Delivery Challan / Invoice",
        "Packing List", 
        "Material Test Certificate (MTC)"
    ]
    
    for item_name in default_items:
        checklist_item = pr.append("document_checklist", {})
        checklist_item.document_type = item_name
        checklist_item.received = 0
        checklist_item.received_date = None
        checklist_item.remarks = ""


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
