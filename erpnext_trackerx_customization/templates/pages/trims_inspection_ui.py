import frappe
import json
from frappe import _


def get_context(context):
    """Get context for trims inspection UI page"""
    try:
        # Get inspection name from URL
        inspection_name = frappe.form_dict.get('inspection') or frappe.form_dict.get('name')
        if not inspection_name:
            frappe.throw(_("Inspection parameter missing"))
        
        # Get the inspection document
        if not frappe.db.exists("Trims Inspection", inspection_name):
            frappe.throw(_("Trims Inspection {0} not found").format(inspection_name))
        
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("read"):
            frappe.throw(_("You do not have permission to view this inspection"))
        
        # Get inspection items (simulated from GRN or manual entry)
        inspection_items = get_inspection_items(inspection_doc)
        
        # Get defect categories for trims
        defect_categories = get_trims_defect_categories()
        
        # Get existing defects data
        defects_data = {}
        if inspection_doc.get('defects_data'):
            try:
                defects_data = json.loads(inspection_doc.defects_data)
            except:
                defects_data = {}
        
        # Get current user roles
        user_roles = frappe.get_roles(frappe.session.user)
        is_quality_inspector = "Quality Inspector" in user_roles
        is_quality_manager = "Quality Manager" in user_roles
        is_system_user = "Administrator" in user_roles or "System Manager" in user_roles
        
        # Import read-only check function
        from erpnext_trackerx_customization.api.trims_inspection import is_inspection_readonly_for_user
        
        # Check write permissions (has permission, not submitted, and not read-only for user)
        can_write = (inspection_doc.has_permission("write") and 
                    inspection_doc.get('inspection_status') != 'Submitted' and
                    not is_inspection_readonly_for_user(inspection_doc))
        
        # Set context
        context.update({
            'page_title': f'Trims Inspection: {inspection_name}',
            'inspection_name': inspection_name,
            'inspection_doc': inspection_doc,
            'inspection_items': inspection_items,
            'defect_categories': defect_categories,
            'defects_data': defects_data,
            'can_write': can_write,
            'is_readonly': is_inspection_readonly_for_user(inspection_doc),
            'is_quality_inspector': is_quality_inspector,
            'is_quality_manager': is_quality_manager,
            'is_system_user': is_system_user,
            'show_manager_actions': is_quality_manager and inspection_doc.get('inspection_status') in ['Rejected', 'In Progress', 'Hold']
        })
        
    except Exception as e:
        frappe.log_error(f"Error in trims inspection UI context: {str(e)}")
        frappe.throw(_("Error loading inspection: {0}").format(str(e)))


def get_inspection_items(inspection_doc):
    """Get items for inspection (simulated data for now)"""
    items = []
    
    # For now, create sample items based on total pieces
    total_pieces = inspection_doc.get('total_pieces', 100)
    pieces_per_item = max(1, total_pieces // 10)  # Divide into max 10 items
    
    for i in range(1, min(11, total_pieces + 1)):
        items.append({
            'item_number': f"ITEM-{i:03d}",
            'description': f"Sample item {i}",
            'pieces': pieces_per_item if i < 10 else (total_pieces - (pieces_per_item * 9)),
            'status': 'Pending'
        })
    
    return items


def get_trims_defect_categories():
    """Get defect categories for trims inspection"""
    return {
        'Critical Defects': [
            {'name': 'Broken', 'code': 'BROKEN'},
            {'name': 'Missing', 'code': 'MISSING'},
            {'name': 'Wrong Color', 'code': 'WRONG_COLOR'},
            {'name': 'Wrong Size', 'code': 'WRONG_SIZE'},
            {'name': 'Contamination', 'code': 'CONTAMINATION'}
        ],
        'Major Defects': [
            {'name': 'Scratch', 'code': 'SCRATCH'},
            {'name': 'Dent', 'code': 'DENT'},
            {'name': 'Discoloration', 'code': 'DISCOLORATION'},
            {'name': 'Rough Edge', 'code': 'ROUGH_EDGE'},
            {'name': 'Assembly Error', 'code': 'ASSEMBLY_ERROR'}
        ],
        'Minor Defects': [
            {'name': 'Surface Mark', 'code': 'SURFACE_MARK'},
            {'name': 'Slight Variation', 'code': 'SLIGHT_VARIATION'},
            {'name': 'Minor Scratch', 'code': 'MINOR_SCRATCH'},
            {'name': 'Polish Issue', 'code': 'POLISH_ISSUE'},
            {'name': 'Packaging Issue', 'code': 'PACKAGING_ISSUE'}
        ]
    }


@frappe.whitelist()
def trims_manager_pass_inspection(inspection_name, manager_comment=""):
    """Quality Manager action to pass a trims inspection"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Update inspection status to Accepted
        inspection_doc.inspection_status = "Accepted"
        if hasattr(inspection_doc, 'quality_grade'):
            inspection_doc.quality_grade = "A"
        
        # Add manager comment
        if manager_comment:
            existing_remarks = inspection_doc.get('manager_remarks') or ''
            timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            new_remark = f"[{timestamp}] Quality Manager: {manager_comment}"
            
            if existing_remarks:
                inspection_doc.manager_remarks = f"{existing_remarks}\n{new_remark}"
            else:
                inspection_doc.manager_remarks = new_remark
        
        # Save the document
        inspection_doc.save()
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Trims Inspection marked as Accepted",
            "new_status": "Accepted"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in trims_manager_pass_inspection: {str(e)}")
        frappe.throw(_("Error updating inspection: {0}").format(str(e)))

@frappe.whitelist()
def trims_manager_fail_inspection(inspection_name, manager_comment=""):
    """Quality Manager action to fail a trims inspection"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Update inspection status to Rejected
        inspection_doc.inspection_status = "Rejected"
        if hasattr(inspection_doc, 'quality_grade'):
            inspection_doc.quality_grade = "C"
        
        # Add manager comment
        if manager_comment:
            existing_remarks = inspection_doc.get('manager_remarks') or ''
            timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            new_remark = f"[{timestamp}] Quality Manager: {manager_comment}"
            
            if existing_remarks:
                inspection_doc.manager_remarks = f"{existing_remarks}\n{new_remark}"
            else:
                inspection_doc.manager_remarks = new_remark
        
        # Save the document
        inspection_doc.save()
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Trims Inspection marked as Rejected",
            "new_status": "Rejected"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in trims_manager_fail_inspection: {str(e)}")
        frappe.throw(_("Error updating inspection: {0}").format(str(e)))

@frappe.whitelist()
def trims_manager_conditional_pass(inspection_name, manager_comment=""):
    """Quality Manager action to conditionally pass a failed trims inspection"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Check if inspection can be conditionally accepted
        current_status = inspection_doc.get('inspection_status', '')
        if current_status not in ['Rejected', 'In Progress', 'Hold']:
            frappe.throw(_("Conditional pass can only be applied to rejected, in progress, or hold inspections"))
        
        # Update inspection status to Conditional Accept
        inspection_doc.inspection_status = "Conditional Accept"
        if hasattr(inspection_doc, 'quality_grade'):
            inspection_doc.quality_grade = "B"
        
        # Add mandatory comment for conditional pass
        if not manager_comment:
            frappe.throw(_("Manager comment is required for conditional pass"))
        
        existing_remarks = inspection_doc.get('manager_remarks') or ''
        timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        new_remark = f"[{timestamp}] Quality Manager - CONDITIONAL PASS: {manager_comment}"
        
        if existing_remarks:
            inspection_doc.manager_remarks = f"{existing_remarks}\n{new_remark}"
        else:
            inspection_doc.manager_remarks = new_remark
        
        # Save the document
        inspection_doc.save()
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Trims Inspection marked as Conditional Accept",
            "new_status": "Conditional Accept"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in trims_manager_conditional_pass: {str(e)}")
        frappe.throw(_("Error updating inspection: {0}").format(str(e)))

@frappe.whitelist()
def trims_manager_conditional_pass_with_purchase_receipt(inspection_name, manager_comment=""):
    """Quality Manager action to conditionally pass rejected trims inspection and create purchase receipt"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Verify inspection is in Rejected status
        if inspection_doc.inspection_status != "Rejected":
            frappe.throw(_("This action can only be performed on Rejected inspections"))
        
        # Verify comment is provided
        if not manager_comment or not manager_comment.strip():
            frappe.throw(_("Manager comment is required for conditional pass"))
        
        # Update inspection status to Conditional Accept
        inspection_doc.inspection_status = "Conditional Accept"
        inspection_doc.quality_grade = "B"
        
        # Add manager comment
        existing_remarks = inspection_doc.get('manager_remarks') or ''
        timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        new_remark = f"[{timestamp}] Quality Manager - CONDITIONAL ACCEPT WITH PURCHASE RECEIPT: {manager_comment}"
        
        if existing_remarks:
            inspection_doc.manager_remarks = f"{existing_remarks}\n{new_remark}"
        else:
            inspection_doc.manager_remarks = new_remark
        
        # Save the inspection
        inspection_doc.save()
        
        # Create Purchase Receipt
        purchase_receipt_result = create_trims_purchase_receipt_from_inspection(inspection_doc)
        
        frappe.db.commit()
        
        response = {
            "status": "success",
            "message": f"Trims inspection conditionally accepted. Purchase Receipt {purchase_receipt_result['name']} created.",
            "purchase_receipt_name": purchase_receipt_result['name'],
            "purchase_receipt_url": f"/app/purchase-receipt/{purchase_receipt_result['name']}",
            "new_status": "Conditional Accept"
        }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in trims_manager_conditional_pass_with_purchase_receipt: {str(e)}")
        frappe.throw(_("Error creating conditional pass and purchase receipt: {0}").format(str(e)))

@frappe.whitelist()
def manager_submit_trims_for_purchase_receipt(inspection_name, manager_remarks=""):
    """Quality Manager action to submit accepted trims inspection and create purchase receipt"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Verify inspection is in Accepted status
        if inspection_doc.inspection_status != "Accepted":
            frappe.throw(_("Only Accepted inspections can be submitted for purchase receipt creation"))
        
        # Add manager remarks if provided
        if manager_remarks:
            existing_remarks = inspection_doc.get('manager_remarks') or ''
            timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            new_remark = f"[{timestamp}] Quality Manager - SUBMIT FOR PURCHASE RECEIPT: {manager_remarks}"
            
            if existing_remarks:
                inspection_doc.manager_remarks = f"{existing_remarks}\n{new_remark}"
            else:
                inspection_doc.manager_remarks = new_remark
        
        # Update inspection status to Submitted
        inspection_doc.inspection_status = "Submitted"
        
        # Add submitted tracking fields
        inspection_doc.submitted_by = frappe.session.user
        inspection_doc.submitted_date = frappe.utils.now_datetime()
        
        # Add submission details to remarks
        existing_remarks = inspection_doc.get('remarks') or ''
        timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        submission_note = f"[{timestamp}] PURCHASE RECEIPT CREATED - Quality Manager: {frappe.session.user}"
        
        if existing_remarks:
            inspection_doc.remarks = f"{existing_remarks}\n\n{submission_note}"
        else:
            inspection_doc.remarks = submission_note
        
        # Save the inspection
        inspection_doc.save()
        
        # Create Purchase Receipt
        purchase_receipt_result = create_trims_purchase_receipt_from_inspection(inspection_doc)
        
        frappe.db.commit()
        
        response = {
            "status": "success",
            "message": f"Trims inspection submitted successfully. Purchase Receipt {purchase_receipt_result['name']} created.",
            "purchase_receipt_name": purchase_receipt_result['name'],
            "purchase_receipt_url": f"/app/purchase-receipt/{purchase_receipt_result['name']}",
            "new_status": "Submitted"
        }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in manager_submit_trims_for_purchase_receipt: {str(e)}")
        frappe.throw(_("Error creating purchase receipt: {0}").format(str(e)))

def create_trims_purchase_receipt_from_inspection(inspection_doc):
    """Create a Purchase Receipt based on the trims inspection"""
    try:
        # Get the linked GRN
        if not inspection_doc.grn_reference:
            frappe.throw(_("No GRN reference found in inspection"))
        
        grn_doc = frappe.get_doc("Goods Receipt Note", inspection_doc.grn_reference)
        
        # Create new Purchase Receipt
        purchase_receipt = frappe.new_doc("Purchase Receipt")
        
        # Set basic details from GRN
        purchase_receipt.supplier = grn_doc.supplier
        purchase_receipt.supplier_name = grn_doc.get('supplier_name', grn_doc.supplier)
        purchase_receipt.company = grn_doc.get('company')
        purchase_receipt.set_warehouse = grn_doc.get('set_warehouse')
        purchase_receipt.posting_date = frappe.utils.getdate()
        purchase_receipt.posting_time = frappe.utils.nowtime()
        purchase_receipt.set_posting_time = 1
        
        # Add reference fields
        purchase_receipt.trims_inspection_reference = inspection_doc.name
        purchase_receipt.grn_reference = inspection_doc.grn_reference
        purchase_receipt.linked_grn = inspection_doc.grn_reference
        
        # Calculate accepted quantity based on inspection results
        total_accepted_qty = 0
        accepted_percentage = 100  # Default to 100% if no specific rejection data
        
        # Check if there are specific defect counts that indicate rejections
        if hasattr(inspection_doc, 'total_critical_defects') and hasattr(inspection_doc, 'total_pieces'):
            if inspection_doc.total_critical_defects > 0:
                # Calculate rejection percentage based on critical defects
                rejection_rate = min(inspection_doc.total_critical_defects / inspection_doc.total_pieces * 100, 100)
                accepted_percentage = max(100 - rejection_rate, 0)
        
        # Find corresponding item in GRN
        grn_item = None
        for grn_item_row in grn_doc.get('items', []):
            if grn_item_row.item_code == inspection_doc.item_code:
                grn_item = grn_item_row
                break
        
        if grn_item:
            try:
                # Calculate accepted quantity and rate
                accepted_qty = getattr(grn_item, 'received_quantity', 1) * (accepted_percentage / 100)
                total_accepted_qty = accepted_qty
                rate = getattr(grn_item, 'rate', 0) or 0
                if rate == 0 and hasattr(grn_item, 'amount') and hasattr(grn_item, 'received_quantity'):
                    rate = grn_item.amount / max(grn_item.received_quantity, 1)
                
                # Get item name from Item master
                item_name = grn_item.item_code
                try:
                    item_doc = frappe.get_doc("Item", grn_item.item_code)
                    item_name = item_doc.item_name or grn_item.item_code
                except:
                    pass
                
                # Ensure all required fields have valid values
                uom = grn_item.uom or 'Pcs'
                if not uom:
                    uom = 'Pcs'
                
                # Create Purchase Receipt item with minimal fields to avoid validation issues
                purchase_receipt.append('items', {
                    'item_code': grn_item.item_code,
                    'item_name': item_name or grn_item.item_code,
                    'description': item_name or grn_item.item_code,
                    'received_qty': accepted_qty,
                    'qty': accepted_qty,
                    'uom': uom,
                    'stock_uom': uom,
                    'conversion_factor': 1,
                    'rate': rate or 0,
                    'base_rate': rate or 0,
                    'amount': accepted_qty * (rate or 0),
                    'base_amount': accepted_qty * (rate or 0),
                    'warehouse': grn_doc.get('set_warehouse'),
                    'remarks': f"Quality Grade: {getattr(inspection_doc, 'quality_grade', 'N/A')}, Acceptance Rate: {accepted_percentage:.1f}% | Quality Inspection: {inspection_doc.name}"
                })
                
            except Exception as item_error:
                frappe.log_error(f"Error processing trims item: {str(item_error)}")
                pass
        
        # Add inspection summary in remarks
        purchase_receipt.remarks = f"""Purchase Receipt created from Trims Inspection: {inspection_doc.name}
GRN Reference: {inspection_doc.grn_reference}
Total Accepted Quantity: {total_accepted_qty}
Acceptance Rate: {accepted_percentage:.1f}%
Quality Manager: {frappe.session.user}
Inspection Result: {inspection_doc.inspection_result}
Overall Quality Grade: {inspection_doc.quality_grade}

Critical Defects: {getattr(inspection_doc, 'total_critical_defects', 0)}
Major Defects: {getattr(inspection_doc, 'total_major_defects', 0)}
Minor Defects: {getattr(inspection_doc, 'total_minor_defects', 0)}

Manager Remarks:
{inspection_doc.get('manager_remarks', 'No additional remarks')}"""
        
        # Save the Purchase Receipt
        purchase_receipt.save()
        
        return {
            'name': purchase_receipt.name,
            'doctype': 'Purchase Receipt'
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating trims purchase receipt: {str(e)}")
        frappe.throw(_("Error creating purchase receipt: {0}").format(str(e)))