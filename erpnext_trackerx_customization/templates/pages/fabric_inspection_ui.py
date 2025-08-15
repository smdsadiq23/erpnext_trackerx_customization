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
        
        # Prepare context data
        context.update({
            'inspection_doc': inspection_data,
            'inspection_name': inspection_name,
            'defect_categories': defect_categories,
            'defects_data': defects_data,
            'fabric_rolls': fabric_rolls,
            'can_write': inspection_doc.has_permission("write"),
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