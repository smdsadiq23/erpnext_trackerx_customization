import frappe
from frappe import _
import json

def get_context(context):
    """
    Context function for the fabric inspection UI page
    """
    
    # Get the inspection document name from URL parameters
    inspection_name = frappe.form_dict.get('inspection') or frappe.form_dict.get('name')
    
    if not inspection_name:
        frappe.throw(_("Inspection document name is required"))
    
    try:
        # Get the fabric inspection document
        inspection_doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("read"):
            frappe.throw(_("You don't have permission to view this document"))
        
        # Get defect categories from Defect Master
        defect_categories = get_defect_categories()
        
        # Convert fabric rolls to serializable format with AQL-based filtering
        fabric_rolls = []
        try:
            # Get AQL configuration for roll filtering
            inspection_type = getattr(inspection_doc, 'inspection_type', 'AQL Based')
            required_sample_rolls = getattr(inspection_doc, 'required_sample_rolls', 0)
            total_rolls = getattr(inspection_doc, 'total_rolls', 0)
            
            # Get all available rolls
            all_rolls = inspection_doc.fabric_rolls_tab or []
            
            # Filter rolls based on AQL requirements
            rolls_to_inspect = get_aql_filtered_rolls(all_rolls, inspection_type, required_sample_rolls, total_rolls)
            
            for roll in rolls_to_inspect:
                roll_data = {}
                
                # Safely extract all available fields
                available_fields = [
                    'roll_number', 'roll_length', 'roll_width', 'shade_code', 'lot_number',
                    'sample_length', 'inspection_method', 'inspection_percentage', 'inspected',
                    'total_defect_points', 'points_per_100_sqm', 'defect_density',
                    'roll_grade', 'roll_result', 'accept_reject_reason', 'roll_remarks'
                ]
                
                for field in available_fields:
                    if hasattr(roll, field):
                        value = getattr(roll, field)
                        # Convert to appropriate type for JSON serialization
                        if value is None:
                            value = '' if field in ['roll_number', 'shade_code', 'lot_number', 'inspection_method', 'roll_grade', 'roll_result', 'accept_reject_reason', 'roll_remarks'] else 0
                        roll_data[field] = value
                    else:
                        # Set default values for missing fields
                        default_values = {
                            'roll_number': '',
                            'roll_length': 0,
                            'roll_width': 0,
                            'shade_code': '',
                            'lot_number': '',
                            'sample_length': 0,
                            'inspection_method': '4-Point Method',
                            'inspection_percentage': 100,
                            'inspected': 0,
                            'total_defect_points': 0,
                            'points_per_100_sqm': 0,
                            'defect_density': 0,
                            'roll_grade': '',
                            'roll_result': 'Pending',
                            'accept_reject_reason': '',
                            'roll_remarks': ''
                        }
                        roll_data[field] = default_values.get(field, '')
                
                # Add GSM field if it doesn't exist (might be needed for display)
                roll_data['gsm'] = getattr(roll, 'gsm', 0)
                # Add compact_roll_no if needed
                roll_data['compact_roll_no'] = getattr(roll, 'compact_roll_no', '')
                
                fabric_rolls.append(roll_data)
                
        except Exception as roll_error:
            frappe.log_error(f"Error processing fabric rolls: {str(roll_error)}")
            # Continue with empty rolls list if there's an error

        # Convert inspection doc to serializable format
        inspection_data = {}
        try:
            inspection_fields = [
                'name', 'inspection_date', 'inspector', 'supplier', 'item_name', 'item_code',
                'grn_reference', 'total_quantity', 'total_rolls', 'inspection_status',
                'inspection_result', 'total_defect_points', 'quality_grade',
                'inspection_type', 'aql_level', 'aql_value', 'required_sample_size',
                'required_sample_rolls', 'inspection_regime'
            ]
            
            for field in inspection_fields:
                if hasattr(inspection_doc, field):
                    value = getattr(inspection_doc, field)
                    if field == 'inspection_date' and value:
                        value = str(value)
                    elif value is None:
                        value = '' if field in ['name', 'inspector', 'supplier', 'item_name', 'item_code', 'grn_reference', 'inspection_status', 'inspection_result', 'quality_grade', 'inspection_type', 'aql_level', 'aql_value', 'inspection_regime'] else 0
                    inspection_data[field] = value
                else:
                    # Set default values
                    default_values = {
                        'name': inspection_name,
                        'inspection_date': '',
                        'inspector': '',
                        'supplier': '',
                        'item_name': '',
                        'item_code': '',
                        'grn_reference': '',
                        'total_quantity': 0,
                        'total_rolls': 0,
                        'inspection_status': 'Draft',
                        'inspection_result': 'Pending',
                        'total_defect_points': 0,
                        'quality_grade': '',
                        'inspection_type': 'AQL Based',
                        'aql_level': 'II',
                        'aql_value': '2.5',
                        'required_sample_size': 0,
                        'required_sample_rolls': 0,
                        'inspection_regime': 'Normal'
                    }
                    inspection_data[field] = default_values.get(field, '')
                    
        except Exception as doc_error:
            frappe.log_error(f"Error processing inspection document: {str(doc_error)}")
            # Use minimal data
            inspection_data = {
                'name': inspection_name,
                'inspection_date': '',
                'inspector': '',
                'supplier': '',
                'item_name': '',
                'item_code': '',
                'grn_reference': '',
                'total_quantity': 0,
                'total_rolls': 0,
                'inspection_status': 'Draft',
                'inspection_result': 'Pending',
                'total_defect_points': 0,
                'quality_grade': '',
                'inspection_type': 'AQL Based',
                'aql_level': 'II',
                'aql_value': '2.5',
                'required_sample_size': 0,
                'required_sample_rolls': 0,
                'inspection_regime': 'Normal'
            }
        
        # Get defects data safely
        defects_data = {}
        try:
            defects_data = get_defects_data(inspection_doc)
        except Exception as defects_error:
            frappe.log_error(f"Error getting defects data: {str(defects_error)}")
        
        # Get current user roles
        user_roles = frappe.get_roles(frappe.session.user)
        is_quality_inspector = "Quality Inspector" in user_roles
        is_quality_manager = "Quality Manager" in user_roles
        is_system_user = "Administrator" in user_roles or "System Manager" in user_roles
        
        # Check if inspection can be written to (not submitted and has write permission)
        can_write = inspection_doc.has_permission("write") and inspection_doc.get('inspection_status') != 'Submitted'
        
        # Prepare context data
        context.update({
            'inspection_doc': inspection_data,
            'inspection_name': inspection_name,
            'defect_categories': defect_categories,
            'defects_data': defects_data,
            'fabric_rolls': fabric_rolls,
            'can_write': can_write,
            'is_quality_inspector': is_quality_inspector,
            'is_quality_manager': is_quality_manager,
            'is_system_user': is_system_user,
            'show_manager_actions': is_quality_manager and inspection_doc.get('inspection_status') in ['Rejected', 'In Progress', 'Hold'],
            'page_title': f'Four-Point Inspection - {inspection_name}',
            'show_sidebar': False,
            'show_header': True
        })
        
        return context
        
    except frappe.DoesNotExistError:
        frappe.throw(_("Inspection document '{0}' not found").format(inspection_name))
    except Exception as e:
        frappe.log_error(f"Error in fabric inspection UI: {str(e)}")
        frappe.throw(_("Error loading inspection data: {0}").format(str(e)))

def get_defect_categories():
    """
    Get defect categories from Defect Master
    """
    try:
        defects = frappe.get_all("Defect Master", 
                                filters={
                                    "inspection_type": "Fabric Inspection",
                                    "is_active": 1
                                },
                                fields=[
                                    "defect_code", 
                                    "defect_name", 
                                    "defect_category",
                                    "point_1_criteria",
                                    "point_2_criteria", 
                                    "point_3_criteria",
                                    "point_4_criteria"
                                ])
        
        # Group defects by category
        categories = {}
        for defect in defects:
            category = defect.defect_category or "Other"
            if category not in categories:
                categories[category] = []
            
            # Determine points based on defect master point system
            points = get_defect_points_from_master(defect)
                
            categories[category].append({
                'code': defect.defect_code,
                'name': defect.defect_name,
                'points': points
            })
        
        # If no defects found, return default categories
        if not categories:
            categories = get_default_defect_categories()
            
        return categories
        
    except Exception as e:
        frappe.log_error(f"Error getting defect categories: {str(e)}")
        return get_default_defect_categories()

def get_default_defect_categories():
    """
    Default defect categories for four-point system
    """
    return {
        'Holes & Yarn Defects': [
            {'code': 'HOLE', 'name': 'Holes', 'points': 4},
            {'code': 'PROC_HOLE', 'name': 'Processing Holes', 'points': 4},
            {'code': 'THIN_YARN', 'name': 'Thin Yarn', 'points': 2},
            {'code': 'THICK_YARN', 'name': 'Thick Yarn', 'points': 2}
        ],
        'Stains & Marks': [
            {'code': 'BLACK_DOT', 'name': 'Black Dot Oil Stain', 'points': 3},
            {'code': 'GREASE', 'name': 'Grease Mark', 'points': 3},
            {'code': 'RUST', 'name': 'Rust Stain', 'points': 3}
        ]
    }

def get_defect_points_from_master(defect):
    """
    Calculate defect points based on defect master criteria and size
    This implements the industry-standard point calculation system
    """
    try:
        # Get the point system configuration from defect master
        point_1_criteria = defect.get('point_1_criteria', '')
        point_2_criteria = defect.get('point_2_criteria', '')
        point_3_criteria = defect.get('point_3_criteria', '')
        point_4_criteria = defect.get('point_4_criteria', '')
        
        # Industry standard point calculation based on defect size thresholds
        # This should be configured in the defect master with size ranges
        
        # For now, implement a standard four-point system based on defect type
        defect_type = defect.get('defect_name', '').lower()
        
        # Critical defects (4 points) - holes and major structural issues
        if any(keyword in defect_type for keyword in ['hole', 'cut', 'tear', 'break']):
            return 4
        
        # Major defects (3 points) - stains and visible marks
        elif any(keyword in defect_type for keyword in ['stain', 'spot', 'mark', 'discolor']):
            return 3
        
        # Minor defects (2 points) - yarn irregularities
        elif any(keyword in defect_type for keyword in ['yarn', 'thread', 'texture']):
            return 2
        
        # Minimal defects (1 point) - slight variations
        elif any(keyword in defect_type for keyword in ['shade', 'slight', 'minor']):
            return 1
        
        # Use criteria-based calculation if configured
        if point_4_criteria:
            return 4
        elif point_3_criteria:
            return 3
        elif point_2_criteria:
            return 2
        elif point_1_criteria:
            return 1
        
        # Default to 2 points for unknown defects
        return 2
        
    except Exception as e:
        frappe.log_error(f"Error calculating defect points: {str(e)}")
        return 2

def get_aql_filtered_rolls(all_rolls, inspection_type, required_sample_rolls, total_rolls):
    """
    Filter rolls based on AQL configuration and sampling requirements
    """
    try:
        # For 100% inspection, return all rolls
        if inspection_type == '100% Inspection':
            return all_rolls
        
        # For AQL-based inspection, select sample rolls
        if inspection_type == 'AQL Based' and required_sample_rolls > 0:
            # If required sample rolls is specified, take that number
            sample_count = min(int(required_sample_rolls), len(all_rolls))
            
            # Implement systematic sampling for representative selection
            if sample_count >= len(all_rolls):
                return all_rolls
            
            # Calculate sampling interval
            interval = len(all_rolls) // sample_count if sample_count > 0 else 1
            selected_rolls = []
            
            # Select rolls at regular intervals for representative sampling
            for i in range(0, len(all_rolls), interval):
                if len(selected_rolls) < sample_count:
                    selected_rolls.append(all_rolls[i])
            
            # If we still need more rolls, add from the end
            while len(selected_rolls) < sample_count and len(selected_rolls) < len(all_rolls):
                for roll in reversed(all_rolls):
                    if roll not in selected_rolls:
                        selected_rolls.append(roll)
                        if len(selected_rolls) >= sample_count:
                            break
            
            return selected_rolls
        
        # Default: return all rolls if no specific requirement
        return all_rolls
        
    except Exception as e:
        frappe.log_error(f"Error filtering rolls based on AQL: {str(e)}")
        # Return all rolls if filtering fails
        return all_rolls

def get_defects_data(inspection_doc):
    """
    Get defects data from the inspection document
    """
    try:
        if inspection_doc.defects_data:
            if isinstance(inspection_doc.defects_data, str):
                return json.loads(inspection_doc.defects_data)
            return inspection_doc.defects_data
        return {}
    except Exception:
        return {}


@frappe.whitelist()
def fabric_manager_pass_inspection(inspection_name, manager_comment=""):
    """Quality Manager action to pass an inspection"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Update inspection status to Accepted
        inspection_doc.inspection_status = "Accepted"
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
            "message": "Inspection marked as Accepted",
            "new_status": "Accepted"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in fabric_manager_pass_inspection: {str(e)}")
        frappe.throw(_("Error updating inspection: {0}").format(str(e)))

@frappe.whitelist()
def fabric_manager_fail_inspection(inspection_name, manager_comment=""):
    """Quality Manager action to fail an inspection"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Update inspection status to Rejected
        inspection_doc.inspection_status = "Rejected"
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
            "message": "Inspection marked as Rejected",
            "new_status": "Rejected"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in fabric_manager_fail_inspection: {str(e)}")
        frappe.throw(_("Error updating inspection: {0}").format(str(e)))

@frappe.whitelist()
def fabric_manager_conditional_pass(inspection_name, manager_comment=""):
    """Quality Manager action to conditionally pass a failed inspection"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You don't have permission to modify this document"))
        
        # Check if inspection was previously rejected or can be conditionally accepted
        current_status = inspection_doc.get('inspection_status', '')
        if current_status not in ['Rejected', 'In Progress', 'Hold']:
            frappe.throw(_("Conditional pass can only be applied to rejected, in progress, or hold inspections"))
        
        # Update inspection status to Conditional Accept
        inspection_doc.inspection_status = "Conditional Accept"
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
            "message": "Inspection marked as Conditional Accept",
            "new_status": "Conditional Accept"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in fabric_manager_conditional_pass: {str(e)}")
        frappe.throw(_("Error updating inspection: {0}").format(str(e)))

@frappe.whitelist()
def fabric_manager_conditional_pass_with_purchase_receipt(inspection_name, manager_comment=""):
    """Quality Manager action to conditionally pass rejected inspection and create purchase receipt"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
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
        purchase_receipt_result = create_purchase_receipt_from_inspection(inspection_doc)
        
        frappe.db.commit()
        
        response = {
            "status": "success",
            "message": f"Inspection conditionally accepted. Purchase Receipt {purchase_receipt_result['name']} created.",
            "purchase_receipt_name": purchase_receipt_result['name'],
            "purchase_receipt_url": f"/app/purchase-receipt/{purchase_receipt_result['name']}",
            "new_status": "Conditional Accept"
        }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in fabric_manager_conditional_pass_with_purchase_receipt: {str(e)}")
        frappe.throw(_("Error creating conditional pass and purchase receipt: {0}").format(str(e)))

@frappe.whitelist()
def manager_submit_for_purchase_receipt(inspection_name, manager_remarks=""):
    """Quality Manager action to submit accepted inspection and create purchase receipt"""
    try:
        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            frappe.throw(_("Only Quality Managers can perform this action"))
        
        # Get inspection document
        inspection_doc = frappe.get_doc("Fabric Inspection", inspection_name)
        
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
        purchase_receipt_result = create_purchase_receipt_from_inspection(inspection_doc)
        
        frappe.db.commit()
        
        response = {
            "status": "success",
            "message": f"Inspection submitted successfully. Purchase Receipt {purchase_receipt_result['name']} created.",
            "purchase_receipt_name": purchase_receipt_result['name'],
            "purchase_receipt_url": f"/app/purchase-receipt/{purchase_receipt_result['name']}",
            "new_status": "Submitted"
        }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in manager_submit_for_purchase_receipt: {str(e)}")
        frappe.throw(_("Error creating purchase receipt: {0}").format(str(e)))

def create_purchase_receipt_from_inspection(inspection_doc):
    """Create a Purchase Receipt based on the fabric inspection using enhanced field mapping"""
    try:
        # Import enhanced field mapping utility
        from erpnext_trackerx_customization.erpnext_trackerx_customization.utils.purchase_receipt_field_mapper import (
            create_enhanced_purchase_receipt_item, log_field_mapping_summary
        )
        
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
        purchase_receipt.fabric_inspection_reference = inspection_doc.name
        purchase_receipt.grn_reference = inspection_doc.grn_reference
        purchase_receipt.linked_grn = inspection_doc.grn_reference
        
        # Add items from inspection with enhanced field mapping
        total_accepted_qty = 0
        pr_items_created = []
        
        # Debug: Log fabric rolls data
        fabric_rolls = inspection_doc.get('fabric_rolls_tab', [])
        frappe.logger().info(f"Fabric Inspection {inspection_doc.name}: Found {len(fabric_rolls)} fabric rolls")
        
        for roll in fabric_rolls:
            roll_result = roll.get('roll_result')
            roll_number = getattr(roll, 'roll_number', 'N/A')
            frappe.logger().info(f"Roll {roll_number}: result = '{roll_result}'")
            
            if roll_result in ['First Quality', 'Accepted', 'Conditional Accept']:
                # Find corresponding item in GRN
                grn_item = None
                for grn_item_row in grn_doc.get('items', []):
                    if grn_item_row.item_code == inspection_doc.item_code:
                        grn_item = grn_item_row
                        break
                
                if grn_item:
                    try:
                        # Calculate quantities for inspection overrides
                        received_qty = roll.roll_length or 1
                        
                        # Create enhanced inspection remarks
                        inspection_remarks = f"Fabric Inspection: {inspection_doc.name} | Quality Grade: {getattr(roll, 'roll_grade', 'N/A')} | Defect Points: {getattr(roll, 'total_defect_points', 0)} | Roll No: {getattr(roll, 'roll_number', 'N/A')} | Roll Result: {getattr(roll, 'roll_result', 'N/A')}"
                        
                        # Use enhanced field mapping with inspection-specific overrides
                        pr_item_data = create_enhanced_purchase_receipt_item(
                            grn_item, 
                            grn_doc,
                            qty=received_qty,  # Override with inspection-approved quantity
                            remarks=inspection_remarks  # Override with inspection details
                        )
                        
                        # Add to Purchase Receipt
                        purchase_receipt.append('items', pr_item_data)
                        pr_items_created.append(pr_item_data)
                        total_accepted_qty += received_qty
                        
                        frappe.logger().info(f"Added roll {roll_number} to Purchase Receipt with qty {received_qty}")
                        
                    except Exception as item_error:
                        frappe.log_error(f"Error processing roll {getattr(roll, 'roll_number', 'unknown')}: {str(item_error)}")
                        continue
        
        # If no accepted rolls found, add the item anyway with conditional acceptance
        if not pr_items_created:
            frappe.logger().warning(f"No accepted rolls found for inspection {inspection_doc.name}, adding item with conditional acceptance")
            
            # Find GRN item
            grn_item = None
            for grn_item_row in grn_doc.get('items', []):
                if grn_item_row.item_code == inspection_doc.item_code:
                    grn_item = grn_item_row
                    break
            
            if grn_item:
                # Use a minimal quantity for conditional acceptance
                conditional_qty = 1
                total_accepted_qty = conditional_qty
                
                inspection_remarks = f"Fabric Inspection: {inspection_doc.name} | Conditional Acceptance - No specific roll acceptance data | Quality Manager Decision: {inspection_doc.get('manager_remarks', 'N/A')}"
                
                pr_item_data = create_enhanced_purchase_receipt_item(
                    grn_item, 
                    grn_doc,
                    qty=conditional_qty,
                    remarks=inspection_remarks
                )
                
                purchase_receipt.append('items', pr_item_data)
                pr_items_created.append(pr_item_data)
                
                frappe.logger().info(f"Added conditional acceptance item with qty {conditional_qty}")
        
        # Ensure we have at least one item before proceeding
        if not pr_items_created:
            frappe.throw(_("No items could be added to Purchase Receipt. Please check the inspection data and try again."))
        
        # Log field mapping summary for monitoring
        log_field_mapping_summary(pr_items_created, "Fabric Inspection")
        
        # Add inspection summary in remarks
        purchase_receipt.remarks = f"""Purchase Receipt created from Quality Inspection: {inspection_doc.name}
GRN Reference: {inspection_doc.grn_reference}
Total Accepted Quantity: {total_accepted_qty}
Quality Manager: {frappe.session.user}
Inspection Result: {inspection_doc.inspection_result}
Overall Quality Grade: {inspection_doc.quality_grade}

Manager Remarks:
{inspection_doc.get('manager_remarks', 'No additional remarks')}"""
        
        # Initialize financial totals to prevent None errors
        purchase_receipt.total_qty = sum(item.get('qty', 0) for item in pr_items_created)
        purchase_receipt.total = sum(item.get('amount', 0) for item in pr_items_created)
        purchase_receipt.net_total = purchase_receipt.total
        purchase_receipt.grand_total = purchase_receipt.total
        purchase_receipt.base_total = purchase_receipt.total
        purchase_receipt.base_net_total = purchase_receipt.total  
        purchase_receipt.base_grand_total = purchase_receipt.total
        purchase_receipt.base_rounded_total = purchase_receipt.total
        purchase_receipt.rounded_total = purchase_receipt.total
        
        # Calculate totals before saving to prevent validation errors
        purchase_receipt.run_method("calculate_taxes_and_totals")
        
        # Save the Purchase Receipt
        purchase_receipt.save()
        
        return {
            'name': purchase_receipt.name,
            'doctype': 'Purchase Receipt'
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating purchase receipt: {str(e)}")
        frappe.throw(_("Error creating purchase receipt: {0}").format(str(e)))