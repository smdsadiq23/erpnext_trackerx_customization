import frappe
from frappe import _
from frappe.utils import flt, cint
import json

@frappe.whitelist()
def get_grn_rolls(grn_reference):
    """Get fabric rolls from GRN reference"""
    try:
        if not grn_reference:
            return []
        
        # Check if GRN exists
        if not frappe.db.exists("Goods Receipt Note", grn_reference):
            frappe.throw(_("GRN {0} not found").format(grn_reference))
        
        # Get GRN document
        grn = frappe.get_doc("Goods Receipt Note", grn_reference)
        
        rolls = []
        for item in grn.items:
            # Extract roll information from GRN items
            roll_data = {
                'roll_number': item.get('roll_number') or f"ROLL-{len(rolls)+1:03d}",
                'shade_code': item.get('shade_code') or '',
                'lot_number': item.get('lot_number') or '',
                'length': flt(item.get('qty') or 0),  # Use qty as length
                'width': flt(item.get('width') or 60),  # Default width
                'item_code': item.item_code,
                'item_name': item.item_name
            }
            rolls.append(roll_data)
        
        return rolls
        
    except Exception as e:
        frappe.log_error(f"Error getting GRN rolls: {str(e)}")
        frappe.throw(_("Error fetching rolls from GRN: {0}").format(str(e)))

@frappe.whitelist()
def calculate_aql_sample_size(lot_size, aql_level, aql_value, inspection_regime='Normal'):
    """Calculate AQL sample size"""
    try:
        lot_size = cint(lot_size)
        
        # Simple AQL calculation based on standard tables
        aql_map = {
            'I': {
                '0.4': 8, '0.65': 13, '1.0': 20, '1.5': 32, '2.5': 50, '4.0': 80
            },
            'II': {
                '0.4': 13, '0.65': 20, '1.0': 32, '1.5': 50, '2.5': 80, '4.0': 125
            },
            'III': {
                '0.4': 20, '0.65': 32, '1.0': 50, '1.5': 80, '2.5': 125, '4.0': 200
            }
        }
        
        # Get sample size from AQL table
        level_data = aql_map.get(aql_level, aql_map['II'])
        sample_size = level_data.get(str(aql_value), level_data.get('2.5', 80))
        
        # Adjust for lot size
        if lot_size < sample_size:
            sample_rolls = lot_size
            sample_size_percent = 100
        else:
            sample_rolls = min(sample_size, lot_size)
            sample_size_percent = (sample_rolls / lot_size) * 100
        
        # Estimate sample meters
        avg_roll_length = 50  # Default
        sample_meters = sample_rolls * avg_roll_length
        
        return {
            'sample_size': round(sample_size_percent, 2),
            'sample_rolls': sample_rolls,
            'sample_meters': sample_meters
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating AQL sample size: {str(e)}")
        return {'sample_size': 25, 'sample_rolls': 1, 'sample_meters': 50}

@frappe.whitelist()
def generate_inspection_report(inspection_doc):
    """Generate inspection report"""
    try:
        # Simple report generation
        inspection = frappe.get_doc("Fabric Inspection", inspection_doc)
        
        # For now, just return a success message
        frappe.msgprint(_("Report generation feature will be implemented"))
        
        return {
            'success': True,
            'message': 'Report generation initiated',
            'report_url': f'/app/fabric-inspection/{inspection_doc}'
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating inspection report: {str(e)}")
        frappe.throw(_("Error generating report: {0}").format(str(e)))

@frappe.whitelist()
def save_progress(inspection_name, defects_data=None, rolls_data=None, checklist_data=None, **kwargs):
    """Save fabric inspection progress without determining final results"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Remove debug logging to avoid character length errors
        
        # Initialize data with safe defaults
        if defects_data is None:
            defects_data = {}
        if rolls_data is None:
            rolls_data = {}
        if checklist_data is None:
            checklist_data = []
            
        # Parse JSON strings if needed
        if isinstance(defects_data, str):
            try:
                defects_data = json.loads(defects_data) if defects_data else {}
            except json.JSONDecodeError:
                defects_data = {}
                
        if isinstance(rolls_data, str):
            try:
                rolls_data = json.loads(rolls_data) if rolls_data else {}
            except json.JSONDecodeError:
                rolls_data = {}
                
        if isinstance(checklist_data, str):
            try:
                checklist_data = json.loads(checklist_data) if checklist_data else []
            except json.JSONDecodeError:
                checklist_data = []
        
        # Update defects data - simple save without complex cleaning
        if defects_data and isinstance(defects_data, dict):
            # Simple save - just ensure it's a valid dict
            inspection.defects_data = json.dumps(defects_data)
        
        # Update rolls data if provided
        if rolls_data and isinstance(rolls_data, dict):
            # Clear existing rolls
            inspection.set('fabric_rolls_tab', [])
            
            # Process rolls data - handle both dict format with proper error handling
            for roll_key, roll_data in rolls_data.items():
                if isinstance(roll_data, dict):
                    try:
                        inspection.append('fabric_rolls_tab', {
                            'roll_number': roll_data.get('roll_number', roll_key),
                            'roll_length': flt(roll_data.get('roll_length', roll_data.get('length', 0))),
                            'roll_width': flt(roll_data.get('roll_width', roll_data.get('width', 0))),
                            'shade_code': roll_data.get('shade_code', ''),
                            'lot_number': roll_data.get('lot_number', ''),
                            'gsm': flt(roll_data.get('gsm', 0)),
                            'compact_roll_no': roll_data.get('compact_roll_no', ''),
                            'sample_length': flt(roll_data.get('sample_length', 0)),
                            'inspection_method': roll_data.get('inspection_method', '4-Point Method'),
                            'inspection_percentage': flt(roll_data.get('inspection_percentage', 100)),
                            'inspected': cint(roll_data.get('inspected', 0)),
                            'total_defect_points': flt(roll_data.get('total_defect_points', 0)),
                            'points_per_100_sqm': flt(roll_data.get('points_per_100_sqm', 0)),
                            'defect_density': flt(roll_data.get('defect_density', 0)),
                            'roll_grade': roll_data.get('roll_grade', ''),
                            'roll_result': roll_data.get('roll_result', 'Pending'),
                            'accept_reject_reason': roll_data.get('accept_reject_reason', ''),
                            'roll_remarks': roll_data.get('roll_remarks', '')
                        })
                    except Exception as roll_error:
                        # Log individual roll error but continue processing
                        frappe.log_error(f"Error processing roll {roll_key}: {str(roll_error)}")
                        continue
        
        # Update checklist data if provided
        if checklist_data and isinstance(checklist_data, list):
            # Clear existing checklist items
            inspection.set('fabric_checklist_items', [])
            
            # Add new checklist items with proper error handling
            for checklist_item in checklist_data:
                if isinstance(checklist_item, dict) and checklist_item.get('results'):
                    try:
                        results = checklist_item['results']
                        inspection.append('fabric_checklist_items', {
                            'test_parameter': checklist_item.get('test_parameter', ''),
                            'standard_requirement': checklist_item.get('standard_requirement', ''),
                            'actual_result': results.get('actual_result', ''),
                            'status': results.get('status', ''),
                            'remarks': results.get('remarks', ''),
                            'test_method': checklist_item.get('test_method', ''),
                            'test_category': checklist_item.get('test_category', ''),
                            'is_mandatory': cint(checklist_item.get('is_mandatory', 0))
                        })
                    except Exception as checklist_error:
                        # Log individual checklist error but continue processing
                        frappe.log_error(f"Error processing checklist item: {str(checklist_error)}")
                        continue
        
        # Update status to In Progress (key requirement)
        # Change status to In Progress if it's currently Draft or Hold
        if inspection.inspection_status in ["Draft", "Hold"]:
            inspection.inspection_status = "In Progress"
        
        # Save without determining final results
        inspection.save()
        frappe.db.commit()
        
        return {
            'success': True, 
            'message': f'Inspection progress saved successfully. Status: {inspection.inspection_status}',
            'status': inspection.inspection_status,
            'inspection_status': inspection.inspection_status  # Ensure status is included
        }
        
    except Exception as e:
        frappe.throw(_("Error saving inspection progress: {0}").format(str(e)))

@frappe.whitelist()
def save_inspection_data(inspection_name, defects_data, rolls_data=None, checklist_data=None):
    """Save fabric inspection data including defects, rolls, and checklist results"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Parse JSON strings if needed
        if isinstance(defects_data, str):
            defects_data = json.loads(defects_data)
        if isinstance(rolls_data, str):
            rolls_data = json.loads(rolls_data)
        if isinstance(checklist_data, str):
            checklist_data = json.loads(checklist_data)
        
        # Update defects data - clean it before saving
        if defects_data:
            cleaned_defects_data = clean_defects_data(defects_data)
            inspection.defects_data = json.dumps(cleaned_defects_data)
        
        # Update rolls data
        if rolls_data:
            inspection.rolls_data = json.dumps(rolls_data)
            
            # Also update the fabric_rolls_tab child table with roll metadata
            for roll_number, roll_data in rolls_data.items():
                # Find the corresponding fabric roll record
                fabric_roll = None
                for roll_item in inspection.fabric_rolls_tab:
                    if roll_item.roll_number == roll_number:
                        fabric_roll = roll_item
                        break
                
                if fabric_roll:
                    # Update the fabric roll record with metadata
                    if 'compact_roll_no' in roll_data:
                        fabric_roll.compact_roll_no = roll_data['compact_roll_no']
                    if 'gsm' in roll_data:
                        fabric_roll.gsm = flt(roll_data['gsm'])
                    if 'roll_width' in roll_data:
                        fabric_roll.roll_width = flt(roll_data['roll_width'])
                    if 'roll_length' in roll_data:
                        fabric_roll.roll_length = flt(roll_data['roll_length'])
                    if 'lot_number' in roll_data:
                        fabric_roll.lot_number = roll_data['lot_number']
                    if 'shade_code' in roll_data:
                        fabric_roll.shade_code = roll_data['shade_code']
        
        # Update checklist data
        if checklist_data:
            # Clear existing checklist items
            inspection.set('fabric_checklist_items', [])
            
            # Add new checklist items
            for index, checklist_item in enumerate(checklist_data):
                if checklist_item.get('results'):
                    results = checklist_item['results']
                    inspection.append('fabric_checklist_items', {
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
        total_defect_points = 0
        
        if defects_data:
            cleaned_defects_data = clean_defects_data(defects_data)
            for roll_number, roll_defects in cleaned_defects_data.items():
                for defect_key, size_inches in roll_defects.items():
                    if size_inches and float(size_inches) > 0:
                        # Extract defect code from key
                        parts = defect_key.split('_')
                        defect_code = parts[-1] if parts else defect_key
                        
                        # Calculate points based on size (industry standard four-point system)
                        points = calculate_defect_points_from_size(defect_code, float(size_inches))
                        total_defect_points += points
        
        # Update total defect points
        inspection.total_defect_points = total_defect_points
        
        # Determine inspection result based on defect points and checklist
        inspection_result = determine_fabric_inspection_result(total_defect_points, checklist_data)
        inspection.inspection_result = inspection_result
        
        # Update quality grade
        quality_grade = get_fabric_quality_grade(total_defect_points)
        inspection.quality_grade = quality_grade
        
        # Save the document
        inspection.save()
        frappe.db.commit()
        
        return {
            'success': True, 
            'message': 'Fabric inspection saved successfully',
            'inspection_result': inspection_result,
            'quality_grade': quality_grade,
            'total_defect_points': total_defect_points
        }
        
    except Exception as e:
        frappe.log_error(f"Error saving fabric inspection data: {str(e)}")
        frappe.throw(_("Error saving inspection data: {0}").format(str(e)))


def calculate_defect_points_from_size(defect_code, size_inches):
    """Calculate defect points based on size in inches (industry standard four-point system)"""
    if size_inches <= 0:
        return 0
    
    defect_type = defect_code.lower()
    
    # Critical defects (holes, cuts, tears) - stricter thresholds
    if any(critical in defect_type for critical in ['hole', 'cut', 'tear']):
        if size_inches <= 1:
            return 1
        elif size_inches <= 3:
            return 2
        elif size_inches <= 6:
            return 3
        else:
            return 4
    
    # Stains and marks - moderate thresholds
    elif any(stain in defect_type for stain in ['stain', 'spot', 'mark']):
        if size_inches <= 2:
            return 1
        elif size_inches <= 4:
            return 2
        elif size_inches <= 8:
            return 3
        else:
            return 4
    
    # Yarn defects - lenient thresholds as they're often longer
    elif any(yarn in defect_type for yarn in ['yarn', 'thread']):
        if size_inches <= 3:
            return 1
        elif size_inches <= 6:
            return 2
        elif size_inches <= 12:
            return 3
        else:
            return 4
    
    # Default defect thresholds
    else:
        if size_inches <= 2:
            return 1
        elif size_inches <= 4:
            return 2
        elif size_inches <= 8:
            return 3
        else:
            return 4


def determine_fabric_inspection_result(total_defect_points, checklist_data):
    """Determine overall fabric inspection result based on defect points and checklist results"""
    # Check for failed mandatory checklist items
    mandatory_failures = 0
    if checklist_data:
        for item in checklist_data:
            if (item.get('is_mandatory') and 
                item.get('results', {}).get('status') == 'Fail'):
                mandatory_failures += 1
    
    # Immediate rejection criteria
    if mandatory_failures > 0:
        return 'Rejected'
    
    # Points per 100 square meters thresholds
    if total_defect_points <= 25:
        return 'Accepted'
    elif total_defect_points <= 50:
        return 'Conditional Accept'
    else:
        return 'Rejected'


def get_fabric_quality_grade(total_defect_points):
    """Determine quality grade based on defect points"""
    if total_defect_points <= 10:
        return 'A - Excellent'
    elif total_defect_points <= 25:
        return 'B - Good'
    elif total_defect_points <= 50:
        return 'C - Conditional'
    else:
        return 'F - Rejected'


def clean_defects_data(defects_data):
    """Clean defects data to remove malformed values and ensure proper formatting"""
    if not defects_data or not isinstance(defects_data, dict):
        return {}
    
    cleaned_data = {}
    
    for roll_number, roll_defects in defects_data.items():
        if not isinstance(roll_defects, dict):
            continue
            
        cleaned_roll_defects = {}
        
        for defect_key, size_value in roll_defects.items():
            # Skip empty or null values
            if not size_value or size_value in [0, "0", "", None]:
                continue
            
            # Clean the size value
            cleaned_size = clean_size_value(size_value)
            
            # Only store valid positive numbers
            if cleaned_size > 0:
                cleaned_roll_defects[defect_key] = cleaned_size
        
        # Only store rolls that have defects
        if cleaned_roll_defects:
            cleaned_data[roll_number] = cleaned_roll_defects
    
    return cleaned_data


def clean_size_value(size_value):
    """Clean a single size value, removing malformed data and returning a valid float"""
    if isinstance(size_value, (int, float)):
        return float(size_value) if size_value > 0 else 0.0
    
    if isinstance(size_value, str):
        import re
        
        # First, try to extract a proper decimal number from the start of the string
        # This handles cases like "6.5abc" -> "6.5"
        decimal_match = re.match(r'^\d*\.?\d+', size_value)
        if decimal_match:
            clean_number = decimal_match.group(0)
            try:
                result = float(clean_number)
                # If the original string contains letters/special chars after numbers, 
                # and it's not a simple case like "6.5", be more conservative
                if re.search(r'[a-zA-Z]', size_value) and len(size_value) > len(clean_number):
                    # For malformed cases like "6No0", prefer the first digit only
                    first_digit_match = re.match(r'^\d+', size_value)
                    if first_digit_match and len(first_digit_match.group(0)) < len(clean_number):
                        return float(first_digit_match.group(0))
                return result
            except (ValueError, TypeError):
                pass
        
        # If no proper decimal found, try to extract just the first number
        number_match = re.match(r'^\d+', size_value)
        if number_match:
            try:
                return float(number_match.group(0))
            except (ValueError, TypeError):
                pass
        
        # Last resort: remove all non-numeric chars and try to parse
        cleaned = re.sub(r'[^0-9.]', '', size_value)
        if cleaned:
            try:
                return float(cleaned)
            except (ValueError, TypeError):
                pass
    
    return 0.0


@frappe.whitelist()
def get_inspection_data(inspection_name):
    """Get fabric inspection data for UI including checklist results"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("read"):
            frappe.throw(_("You do not have permission to view this inspection"))
        
        # Get defects data and clean it
        defects_data = {}
        if inspection.get('defects_data'):
            try:
                raw_defects_data = json.loads(inspection.defects_data)
                defects_data = clean_defects_data(raw_defects_data)
            except:
                defects_data = {}
        
        # Get checklist data
        checklist_items = []
        for item in inspection.get('fabric_checklist_items', []):
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
        
        # Get rolls data
        rolls_data = []
        for roll in inspection.get('fabric_rolls_tab', []):
            rolls_data.append({
                'roll_number': roll.roll_number,
                'roll_length': roll.roll_length,
                'roll_width': roll.roll_width,
                'shade_code': roll.shade_code,
                'lot_number': roll.lot_number,
                'gsm': roll.gsm,
                'compact_roll_no': roll.compact_roll_no,
                'sample_length': roll.sample_length,
                'inspection_method': roll.inspection_method,
                'inspection_percentage': roll.inspection_percentage,
                'inspected': roll.inspected,
                'total_defect_points': roll.total_defect_points,
                'points_per_100_sqm': roll.points_per_100_sqm,
                'defect_density': roll.defect_density,
                'roll_grade': roll.roll_grade,
                'roll_result': roll.roll_result,
                'accept_reject_reason': roll.accept_reject_reason,
                'roll_remarks': roll.roll_remarks
            })
        
        return {
            'success': True,
            'name': inspection.name,
            'defects': defects_data,
            'checklist_items': checklist_items,
            'rolls': rolls_data,
            'canWrite': inspection.has_permission("write")
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting fabric inspection data: {str(e)}")
        frappe.throw(_("Error loading inspection data: {0}").format(str(e)))


@frappe.whitelist()
def hold_inspection(inspection_name, hold_reason):
    """Put inspection on hold with reason"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_name)
        
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
            'message': 'Inspection placed on hold successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error holding fabric inspection: {str(e)}")
        frappe.throw(_("Error holding inspection: {0}").format(str(e)))


@frappe.whitelist()
def submit_inspection(inspection_name):
    """Submit inspection for completion"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Validate inspection completeness
        validation_result = validate_inspection_completeness(inspection)
        if not validation_result['valid']:
            frappe.throw(_("Cannot submit inspection: {0}").format(validation_result['reason']))
        
        # Auto-determine final inspection status based on defects and checklist
        auto_result = determine_fabric_inspection_result(
            inspection.total_defect_points or 0,
            get_checklist_data_for_determination(inspection)
        )
        inspection.inspection_status = auto_result
        
        inspection.save()
        frappe.db.commit()
        
        return {
            'success': True,
            'message': 'Inspection submitted successfully',
            'inspection_status': auto_result
        }
        
    except Exception as e:
        frappe.log_error(f"Error submitting fabric inspection: {str(e)}")
        frappe.throw(_("Error submitting inspection: {0}").format(str(e)))


@frappe.whitelist()
def update_status(inspection_name, status):
    """Update inspection status"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_name)
        
        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))
        
        # Validate status transition
        if not is_valid_status_transition(inspection.inspection_status, status):
            frappe.throw(_("Invalid status transition from {0} to {1}").format(inspection.inspection_status, status))
        
        inspection.inspection_status = status
        inspection.save()
        frappe.db.commit()
        
        return {
            'success': True,
            'message': f'Status updated to {status}'
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating inspection status: {str(e)}")
        frappe.throw(_("Error updating status: {0}").format(str(e)))


def validate_inspection_completeness(inspection):
    """Validate if inspection is ready for submission"""
    # Check mandatory checklist items
    mandatory_incomplete = []
    for item in inspection.get('fabric_checklist_items', []):
        if item.is_mandatory and not item.status:
            mandatory_incomplete.append(item.test_parameter)
    
    if mandatory_incomplete:
        return {
            'valid': False,
            'reason': f'Mandatory tests not completed: {", ".join(mandatory_incomplete)}'
        }
    
    # Check if any data has been entered
    has_defects = bool(inspection.get('defects_data'))
    has_checklist = bool(inspection.get('fabric_checklist_items'))
    
    if not has_defects and not has_checklist:
        return {
            'valid': False,
            'reason': 'No inspection data has been recorded'
        }
    
    return {'valid': True}


def get_checklist_data_for_determination(inspection):
    """Get checklist data in format needed for result determination"""
    checklist_data = []
    for item in inspection.get('fabric_checklist_items', []):
        checklist_data.append({
            'is_mandatory': item.is_mandatory,
            'results': {
                'status': item.status
            }
        })
    return checklist_data


def is_valid_status_transition(current_status, new_status):
    """Check if status transition is valid"""
    valid_transitions = {
        'Draft': ['In Progress', 'Hold'],
        'In Progress': ['Hold', 'Completed'],
        'Hold': ['In Progress', 'Completed'],
        'Completed': []  # No transitions from completed
    }
    
    return new_status in valid_transitions.get(current_status, [])