"""
API methods for Trims Inspection functionality
"""

import frappe
import json
from frappe import _


@frappe.whitelist()
def save_progress(inspection_name, defects_data=None, items_data=None, checklist_data=None, **kwargs):
    """Save trims inspection progress without determining final results"""
    try:
        inspection = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Initialize data with safe defaults
        if defects_data is None:
            defects_data = {}
        if items_data is None:
            items_data = {}
        if checklist_data is None:
            checklist_data = []
            
        # Parse JSON strings if needed
        if isinstance(defects_data, str):
            try:
                defects_data = json.loads(defects_data) if defects_data else {}
            except json.JSONDecodeError:
                defects_data = {}
                
        if isinstance(items_data, str):
            try:
                items_data = json.loads(items_data) if items_data else {}
            except json.JSONDecodeError:
                items_data = {}
                
        if isinstance(checklist_data, str):
            try:
                checklist_data = json.loads(checklist_data) if checklist_data else []
            except json.JSONDecodeError:
                checklist_data = []
        
        # Update defects data
        if defects_data:
            inspection.defects_data = json.dumps(defects_data)
        
        # Skip complex calculations for now
        # Focus on core requirement: save defects and update status
        
        # Update status to In Progress (key requirement)
        # Change status to In Progress if it's currently Draft or Hold
        if inspection.inspection_status in ["Draft", "Hold"]:
            inspection.inspection_status = "In Progress"
        
        # Save without determining final results
        inspection.save()
        frappe.db.commit()
        
        return {
            'success': True,
            'message': f'Trims inspection progress saved successfully. Status: {inspection.inspection_status}',
            'status': inspection.inspection_status,
            'inspection_status': inspection.inspection_status  # Ensure status is included
        }
        
    except Exception as e:
        frappe.throw(_("Error saving inspection progress: {0}").format(str(e)))

@frappe.whitelist()
def save_inspection_data(inspection_name, defects_data, items_data, checklist_data=None):
    """
    Save trims inspection data including defects, items, and checklist results
    
    Args:
        inspection_name (str): Name of the trims inspection document
        defects_data (dict): Defect data for each item
        items_data (dict): Item metadata
        checklist_data (list): Checklist results data
    
    Returns:
        dict: Success message and updated data
    """
    try:
        # Get the inspection document
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Parse JSON strings if needed
        if isinstance(defects_data, str):
            defects_data = json.loads(defects_data)
        if isinstance(items_data, str):
            items_data = json.loads(items_data)
        if isinstance(checklist_data, str):
            checklist_data = json.loads(checklist_data)
        
        # Update defects data (stored as JSON) - clean it before saving
        if defects_data:
            cleaned_defects_data = clean_defects_data(defects_data)
            inspection_doc.set('defects_data', json.dumps(cleaned_defects_data))
        
        # Update items data if provided
        if items_data:
            inspection_doc.set('items_data', json.dumps(items_data))
        
        # Update checklist data
        if checklist_data:
            # Clear existing checklist items
            inspection_doc.set('trims_checklist_items', [])
            
            # Add new checklist items
            for index, checklist_item in enumerate(checklist_data):
                if checklist_item.get('results'):
                    results = checklist_item['results']
                    inspection_doc.append('trims_checklist_items', {
                        'test_parameter': checklist_item.get('test_parameter', ''),
                        'standard_requirement': checklist_item.get('standard_requirement', ''),
                        'actual_result': results.get('actual_result', ''),
                        'status': results.get('status', ''),
                        'remarks': results.get('remarks', ''),
                        'test_method': checklist_item.get('test_method', ''),
                        'test_category': checklist_item.get('test_category', ''),
                        'is_mandatory': checklist_item.get('is_mandatory', 0)
                    })
        
        # Calculate and update defect totals using cleaned data
        total_critical = 0
        total_major = 0 
        total_minor = 0
        
        if defects_data:
            cleaned_defects_data = clean_defects_data(defects_data)
            for item_number, item_defects in cleaned_defects_data.items():
                for defect_key, count in item_defects.items():
                    if count and int(count) > 0:
                        # Extract defect code from key
                        parts = defect_key.split('_')
                        defect_code = parts[-1] if parts else defect_key
                        
                        # Determine defect severity
                        severity = get_defect_severity(defect_code)
                        defect_count = int(count)
                        
                        if severity == 'Critical':
                            total_critical += defect_count
                        elif severity == 'Major':
                            total_major += defect_count
                        else:
                            total_minor += defect_count
        
        # Update defect totals
        inspection_doc.total_critical_defects = total_critical
        inspection_doc.total_major_defects = total_major
        inspection_doc.total_minor_defects = total_minor
        
        # Determine inspection result based on defect counts and checklist
        inspection_result = determine_inspection_result(
            total_critical, total_major, total_minor, checklist_data
        )
        inspection_doc.inspection_result = inspection_result
        
        # Update quality grade
        quality_grade = get_quality_grade(total_critical, total_major, total_minor)
        inspection_doc.quality_grade = quality_grade
        
        # Save the document
        inspection_doc.save()
        frappe.db.commit()
        
        return {
            'message': 'Trims inspection saved successfully',
            'inspection_result': inspection_result,
            'quality_grade': quality_grade,
            'defect_totals': {
                'critical': total_critical,
                'major': total_major,
                'minor': total_minor
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error saving trims inspection data: {str(e)}")
        frappe.throw(_("Error saving inspection data: {0}").format(str(e)))


def get_defect_severity(defect_code):
    """
    Determine defect severity based on defect code
    
    Args:
        defect_code (str): The defect code
        
    Returns:
        str: 'Critical', 'Major', or 'Minor'
    """
    defect_code_upper = defect_code.upper()
    
    # Critical defects that cause immediate rejection
    critical_defects = ['BROKEN', 'MISSING', 'WRONG_COLOR', 'WRONG_SIZE', 'CONTAMINATION', 'HOLE', 'CUT']
    
    # Major defects that significantly impact quality  
    major_defects = ['SCRATCH', 'DENT', 'DISCOLORATION', 'ROUGH_EDGE', 'ASSEMBLY_ERROR', 'STAIN', 'MARK']
    
    if any(critical in defect_code_upper for critical in critical_defects):
        return 'Critical'
    elif any(major in defect_code_upper for major in major_defects):
        return 'Major'
    else:
        return 'Minor'


def determine_inspection_result(critical_count, major_count, minor_count, checklist_data):
    """
    Determine overall inspection result based on defect counts and checklist results
    
    Args:
        critical_count (int): Number of critical defects
        major_count (int): Number of major defects  
        minor_count (int): Number of minor defects
        checklist_data (list): Checklist results
        
    Returns:
        str: 'Accepted', 'Rejected', or 'Conditional Accept'
    """
    # Check for failed mandatory checklist items
    mandatory_failures = 0
    if checklist_data:
        for item in checklist_data:
            if (item.get('is_mandatory') and 
                item.get('results', {}).get('status') == 'Fail'):
                mandatory_failures += 1
    
    # Immediate rejection criteria
    if critical_count > 0 or mandatory_failures > 0:
        return 'Rejected'
    
    # Conditional acceptance criteria
    if major_count > 5 or minor_count > 10:
        return 'Conditional Accept'
    
    # Otherwise accepted
    return 'Accepted'


def get_quality_grade(critical_count, major_count, minor_count):
    """
    Determine quality grade based on defect counts
    
    Args:
        critical_count (int): Number of critical defects
        major_count (int): Number of major defects
        minor_count (int): Number of minor defects
        
    Returns:
        str: Quality grade
    """
    if critical_count > 0:
        return 'F - Rejected'
    elif major_count > 5 or minor_count > 10:
        return 'C - Conditional'
    elif major_count > 2 or minor_count > 5:
        return 'B - Good'
    else:
        return 'A - Excellent'


@frappe.whitelist()
def get_inspection_data(inspection_name):
    """
    Get trims inspection data for UI
    
    Args:
        inspection_name (str): Name of the trims inspection document
        
    Returns:
        dict: Inspection data including defects, items, and checklist
    """
    try:
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("read"):
            frappe.throw(_("You do not have permission to view this inspection"))
        
        # Get defects data and clean it
        defects_data = {}
        if inspection_doc.get('defects_data'):
            try:
                raw_defects_data = json.loads(inspection_doc.defects_data)
                defects_data = clean_defects_data(raw_defects_data)
            except:
                defects_data = {}
        
        # Get items data  
        items_data = {}
        if inspection_doc.get('items_data'):
            items_data = json.loads(inspection_doc.items_data)
        
        # Get checklist data
        checklist_items = []
        for item in inspection_doc.get('trims_checklist_items', []):
            checklist_items.append({
                'test_parameter': item.test_parameter,
                'standard_requirement': item.standard_requirement,
                'actual_result': item.actual_result,
                'status': item.status,
                'remarks': item.remarks,
                'test_method': item.test_method,
                'test_category': item.test_category,
                'is_mandatory': item.is_mandatory
            })
        
        return {
            'name': inspection_doc.name,
            'material_type': inspection_doc.material_type,
            'total_pieces': inspection_doc.total_pieces,
            'defects': defects_data,
            'items': items_data,
            'checklist_items': checklist_items,
            'canWrite': inspection_doc.has_permission("write"),
            'inspection_status': inspection_doc.inspection_status,
            'inspection_result': inspection_doc.inspection_result,
            'quality_grade': inspection_doc.quality_grade
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting trims inspection data: {str(e)}")
        frappe.throw(_("Error loading inspection data: {0}").format(str(e)))


@frappe.whitelist()
def create_inspection_from_grn(grn_name, item_code, material_type="Trims"):
    """
    Create a new trims inspection from GRN data
    
    Args:
        grn_name (str): Name of the GRN document
        item_code (str): Item code to create inspection for
        material_type (str): Material type
        
    Returns:
        dict: Created inspection document name and details
    """
    try:
        # Get GRN document
        grn_doc = frappe.get_doc("Goods Receipt Note", grn_name)
        
        # Find the item in GRN
        grn_item = None
        for item in grn_doc.items:
            if item.item_code == item_code:
                grn_item = item
                break
        
        if not grn_item:
            frappe.throw(_("Item {0} not found in GRN {1}").format(item_code, grn_name))
        
        # Create trims inspection document
        inspection_doc = frappe.new_doc("Trims Inspection")
        inspection_doc.update({
            'grn_reference': grn_name,
            'supplier': grn_doc.supplier,
            'item_code': item_code,
            'item_name': grn_item.item_name,
            'material_type': material_type,
            'total_quantity': grn_item.qty,
            'unit_of_measure': grn_item.uom,
            'total_pieces': int(grn_item.qty),  # Assuming 1:1 ratio for pieces
            'inspection_status': 'Draft',
            'inspection_result': 'Pending',
            'inspector': frappe.session.user
        })
        
        # Save the document
        inspection_doc.save()
        frappe.db.commit()
        
        return {
            'message': 'Trims inspection created successfully',
            'inspection_name': inspection_doc.name,
            'inspection_url': f'/app/trims-inspection/{inspection_doc.name}'
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating trims inspection: {str(e)}")
        frappe.throw(_("Error creating trims inspection: {0}").format(str(e)))


def clean_defects_data(defects_data):
    """Clean defects data to remove malformed values and ensure proper formatting"""
    if not defects_data or not isinstance(defects_data, dict):
        return {}
    
    cleaned_data = {}
    
    for item_number, item_defects in defects_data.items():
        if not isinstance(item_defects, dict):
            continue
            
        cleaned_item_defects = {}
        
        for defect_key, count_value in item_defects.items():
            # Skip empty or null values
            if not count_value or count_value in [0, "0", "", None]:
                continue
            
            # Clean the count value
            cleaned_count = clean_count_value(count_value)
            
            # Only store valid positive numbers
            if cleaned_count > 0:
                cleaned_item_defects[defect_key] = int(cleaned_count)
        
        # Only store items that have defects
        if cleaned_item_defects:
            cleaned_data[item_number] = cleaned_item_defects
    
    return cleaned_data


def clean_count_value(count_value):
    """Clean a single count value, removing malformed data and returning a valid integer"""
    if isinstance(count_value, (int, float)):
        return int(count_value) if count_value > 0 else 0
    
    if isinstance(count_value, str):
        import re
        
        # First, try to extract a proper number from the start of the string
        number_match = re.match(r'^\d+', count_value)
        if number_match:
            try:
                result = int(number_match.group(0))
                return result if result > 0 else 0
            except (ValueError, TypeError):
                pass
        
        # Last resort: remove all non-numeric chars and try to parse
        cleaned = re.sub(r'[^0-9]', '', count_value)
        if cleaned:
            try:
                result = int(cleaned)
                return result if result > 0 else 0
            except (ValueError, TypeError):
                pass
    
    return 0


@frappe.whitelist()
def hold_inspection(inspection_name, hold_reason):
    """Put trims inspection on hold with reason"""
    try:
        inspection = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Update status and hold details
        inspection.inspection_status = "Hold"
        inspection.hold_reason = hold_reason
        inspection.hold_timestamp = frappe.utils.now()
        inspection.hold_by = frappe.session.user
        
        # Save with validation but ensure status remains Hold
        inspection.save()
        
        # Double-check that status is still Hold after validation
        if inspection.inspection_status != "Hold":
            inspection.inspection_status = "Hold"
            inspection.save()
        
        frappe.db.commit()
        
        return {
            'success': True,
            'message': 'Trims inspection placed on hold successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error holding trims inspection: {str(e)}")
        frappe.throw(_("Error holding inspection: {0}").format(str(e)))


@frappe.whitelist()
def submit_inspection(inspection_name):
    """Submit trims inspection for completion"""
    try:
        inspection = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Validate inspection completeness
        validation_result = validate_trims_inspection_completeness(inspection)
        if not validation_result['valid']:
            frappe.throw(_("Cannot submit inspection: {0}").format(validation_result['reason']))
        
        # First set to Submitted status
        inspection.inspection_status = "Submitted"
        
        # Then auto-determine final inspection result based on defects and checklist
        auto_result = determine_inspection_result(
            inspection.total_critical_defects or 0,
            inspection.total_major_defects or 0,
            inspection.total_minor_defects or 0,
            get_trims_checklist_data_for_determination(inspection)
        )
        inspection.inspection_result = auto_result
        
        # Update status to final result
        inspection.inspection_status = auto_result
        
        inspection.save()
        frappe.db.commit()
        
        return {
            'success': True,
            'message': 'Trims inspection submitted successfully',
            'inspection_status': auto_result
        }
        
    except Exception as e:
        frappe.log_error(f"Error submitting trims inspection: {str(e)}")
        frappe.throw(_("Error submitting inspection: {0}").format(str(e)))


@frappe.whitelist()
def update_status(inspection_name, status):
    """Update trims inspection status"""
    try:
        inspection = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Validate status transition
        if not is_valid_trims_status_transition(inspection.inspection_status, status):
            frappe.throw(_("Invalid status transition from {0} to {1}").format(inspection.inspection_status, status))
        
        inspection.inspection_status = status
        inspection.save()
        frappe.db.commit()
        
        return {
            'success': True,
            'message': f'Status updated to {status}'
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating trims inspection status: {str(e)}")
        frappe.throw(_("Error updating status: {0}").format(str(e)))


def validate_trims_inspection_completeness(inspection):
    """Validate if trims inspection is ready for submission"""
    # Check mandatory checklist items
    mandatory_incomplete = []
    for item in inspection.get('trims_checklist_items', []):
        if item.is_mandatory and not item.status:
            mandatory_incomplete.append(item.test_parameter)
    
    if mandatory_incomplete:
        return {
            'valid': False,
            'reason': f'Mandatory tests not completed: {", ".join(mandatory_incomplete)}'
        }
    
    # Check if any data has been entered
    has_defects = bool(inspection.get('defects_data'))
    has_checklist = bool(inspection.get('trims_checklist_items'))
    
    if not has_defects and not has_checklist:
        return {
            'valid': False,
            'reason': 'No inspection data has been recorded'
        }
    
    return {'valid': True}


def get_trims_checklist_data_for_determination(inspection):
    """Get checklist data in format needed for result determination"""
    checklist_data = []
    for item in inspection.get('trims_checklist_items', []):
        checklist_data.append({
            'is_mandatory': item.is_mandatory,
            'results': {
                'status': item.status
            }
        })
    return checklist_data


def is_valid_trims_status_transition(current_status, new_status):
    """Check if status transition is valid for trims inspection"""
    valid_transitions = {
        'Draft': ['In Progress', 'Hold'],
        'In Progress': ['Hold', 'Submitted'],
        'Hold': ['In Progress', 'Submitted'],
        'Submitted': ['Accepted', 'Rejected', 'Conditional Accept'],
        'Accepted': [],      # Terminal status
        'Rejected': [],      # Terminal status  
        'Conditional Accept': []  # Terminal status
    }
    
    return new_status in valid_transitions.get(current_status, [])