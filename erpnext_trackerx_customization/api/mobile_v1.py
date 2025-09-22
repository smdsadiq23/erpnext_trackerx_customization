import frappe
from frappe import _
from frappe.utils import flt, cint
import json


@frappe.whitelist()
def create_sample_test_data():
    """Create sample data for testing mobile APIs"""
    try:
        print("Creating sample data for mobile API testing...")

        # Step 1: Create Master Checklist items
        master_items = [
            {
                "material_type": "Fabrics",
                "test_parameter": "GSM Check",
                "standard_requirement": "150-160",
                "test_method": "ASTM D3776",
                "test_category": "Physical",
                "is_mandatory": 1,
                "display_order": 1,
                "unit_of_measurement": "gsm",
                "tolerance": "±5",
                "description": "Fabric weight per square meter",
                "is_active": 1
            },
            {
                "material_type": "Fabrics",
                "test_parameter": "Fabric Width",
                "standard_requirement": "58-60 inches",
                "test_method": "Manual Measurement",
                "test_category": "Dimensional",
                "is_mandatory": 1,
                "display_order": 2,
                "unit_of_measurement": "inches",
                "tolerance": "±1",
                "description": "Fabric width measurement",
                "is_active": 1
            },
            {
                "material_type": "Fabrics",
                "test_parameter": "Color Fastness",
                "standard_requirement": "Grade 4-5",
                "test_method": "AATCC 61",
                "test_category": "Color",
                "is_mandatory": 1,
                "display_order": 3,
                "unit_of_measurement": "Grade",
                "tolerance": "±0.5",
                "description": "Color fastness to laundering",
                "is_active": 1
            }
        ]

        created_master = 0
        existing_master = frappe.db.count('Master Checklist', {'material_type': 'Fabrics'})

        if existing_master == 0:
            for item in master_items:
                try:
                    doc = frappe.get_doc({
                        "doctype": "Master Checklist",
                        **item
                    })
                    doc.insert()
                    created_master += 1
                except Exception as e:
                    print(f"Error creating Master Checklist: {str(e)}")

        # Step 2: Create Fabric Inspections
        sample_inspections = [
            {
                "material_type": "Fabrics",
                "inspection_status": "Draft",
                "lot_number": "LOT-2024-001",
                "supplier": "ABC Textiles",
                "fabric_type": "Cotton Twill",
                "color": "Navy Blue"
            },
            {
                "material_type": "Fabrics",
                "inspection_status": "In Progress",
                "lot_number": "LOT-2024-002",
                "supplier": "XYZ Fabrics",
                "fabric_type": "Polyester Blend",
                "color": "Black"
            },
            {
                "material_type": "Fabrics",
                "inspection_status": "Completed",
                "lot_number": "LOT-2024-003",
                "supplier": "DEF Textiles",
                "fabric_type": "Denim",
                "color": "Indigo"
            },
            {
                "material_type": "Fabrics",
                "inspection_status": "On Hold",
                "lot_number": "LOT-2024-004",
                "supplier": "GHI Fabrics",
                "fabric_type": "Silk Blend",
                "color": "White"
            }
        ]

        created_inspections = 0
        existing_inspections = frappe.db.count('Fabric Inspection')

        if existing_inspections == 0:
            for inspection in sample_inspections:
                try:
                    doc = frappe.get_doc({
                        "doctype": "Fabric Inspection",
                        **inspection,
                        "inspection_date": frappe.utils.today(),
                        "inspection_type": "AQL Based",
                        "aql_level": "II",
                        "aql_value": "2.5",
                        "inspection_regime": "Normal"
                    })
                    doc.insert()
                    created_inspections += 1
                except Exception as e:
                    print(f"Error creating Fabric Inspection: {str(e)}")

        frappe.db.commit()

        return {
            "success": True,
            "message": "Sample data created successfully",
            "data": {
                "master_checklist_created": created_master,
                "existing_master": existing_master,
                "inspections_created": created_inspections,
                "existing_inspections": existing_inspections,
                "total_master": frappe.db.count('Master Checklist', {'is_active': 1}),
                "total_inspections": frappe.db.count('Fabric Inspection')
            }
        }

    except Exception as e:
        frappe.log_error(f"Error creating sample data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# ===========================
# HOME PAGE APIs
# ===========================

@frappe.whitelist()
def get_status_summary():
    """Get count of inspections by status for dashboard display"""
    try:
        # Get count of inspections by status
        status_counts = frappe.db.sql("""
            SELECT inspection_status, COUNT(*) as count
            FROM `tabFabric Inspection`
            WHERE docstatus != 2
            GROUP BY inspection_status
        """, as_dict=True)

        # Format result with status as key
        result = {}
        total = 0
        for item in status_counts:
            status = item['inspection_status'] or 'Draft'
            count = item['count']
            result[status] = count
            total += count

        result['total'] = total

        return {
            "success": True,
            "data": result,
            "timestamp": frappe.utils.now()
        }

    except Exception as e:
        frappe.log_error(f"Error getting status summary: {str(e)}")
        frappe.throw(_("Error loading status summary: {0}").format(str(e)))

@frappe.whitelist()
def get_inspection_list(status=None, search=None, page=1, limit=20, sort_by="creation", sort_order="desc"):
    """Get paginated list of inspections with filtering and search"""
    try:
        page = cint(page) or 1
        limit = cint(limit) or 20
        start = (page - 1) * limit

        # Build filters
        filters = [['docstatus', '!=', 2]]

        # Status filter
        if status and status != "All":
            filters.append(['inspection_status', '=', status])

        # Search filter - search across multiple fields
        if search:
            search_term = f'%{search}%'
            # For now, search only in main fields to avoid complex OR conditions
            filters.append(['name', 'like', search_term])

        # Get inspections
        inspections = frappe.get_list(
            'Fabric Inspection',
            filters=filters,
            fields=[
                'name', 'inspection_status', 'purchase_order_reference',
                'grn_reference', 'supplier', 'inspector', 'inspection_date',
                'total_rolls', 'item_code', 'item_name', 'creation'
            ],
            limit=limit,
            start=start,
            order_by=f"{sort_by} {sort_order}"
        )

        # Get total count for pagination
        total_count = frappe.db.count('Fabric Inspection', filters)

        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "success": True,
            "data": {
                "inspections": inspections,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
        }

    except Exception as e:
        frappe.log_error(f"Error getting inspection list: {str(e)}")
        frappe.throw(_("Error loading inspection list: {0}").format(str(e)))

# ===========================
# INSPECTION DETAILS APIs
# ===========================

@frappe.whitelist()
def get_inspection_details(inspection_id):
    """Get complete inspection details for mobile app"""
    try:
        # Get inspection document
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("read"):
            frappe.throw(_("You do not have permission to view this inspection"))

        # Build response data
        response_data = {
            "header": {
                "name": inspection.name,
                "inspection_date": inspection.inspection_date,
                "inspector": inspection.inspector,
                "inspection_status": inspection.inspection_status,
                "inspection_type": inspection.inspection_type or "Four-Point Inspection"
            },
            "summary": {
                "total_penalty_points": flt(inspection.total_defect_points or 0),
                "total_inspected_meters": calculate_total_inspected_meters(inspection),
                "average_diameter": 0.0,  # Calculate if needed
                "points_per_100_sqm": calculate_average_points_per_100_sqm(inspection)
            },
            "overall_status": {
                "inspection_status": determine_overall_inspection_status(inspection),
                "final_decision": inspection.inspection_result or "Pending"
            },
            "aql_configuration": {
                "inspection_type": inspection.inspection_type or "AQL Based",
                "aql_level": inspection.aql_level or "",
                "aql_value": inspection.aql_value or "",
                "inspection_regime": inspection.inspection_regime or "Normal",
                "sample_rolls_text": generate_sample_rolls_text(inspection)
            },
            "general_details": {
                "supplier": inspection.supplier or "",
                "item_name": inspection.item_name or "",
                "item_code": inspection.item_code or "",
                "grn_reference": inspection.grn_reference or "",
                "purchase_order": inspection.purchase_order_reference or "",
                "total_quantity": flt(inspection.total_quantity or 0),
                "total_rolls": cint(inspection.total_rolls or 0)
            },
            "roll_details": build_roll_details(inspection),
            "physical_testing": build_physical_testing(inspection),
            "summary_counts": calculate_summary_counts(inspection)
        }

        return {
            "success": True,
            "data": response_data
        }

    except Exception as e:
        frappe.log_error(f"Error getting inspection details: {str(e)}")
        frappe.throw(_("Error loading inspection details: {0}").format(str(e)))

@frappe.whitelist()
def update_aql_configuration(inspection_id, inspection_type=None, aql_level=None, aql_value=None, inspection_regime=None):
    """Update AQL configuration for an inspection"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Update AQL fields
        if inspection_type is not None:
            inspection.inspection_type = inspection_type
        if aql_level is not None:
            inspection.aql_level = aql_level
        if aql_value is not None:
            inspection.aql_value = aql_value
        if inspection_regime is not None:
            inspection.inspection_regime = inspection_regime

        # Update status to In Progress if currently Draft
        if inspection.inspection_status == "Draft":
            inspection.inspection_status = "In Progress"

        inspection.save()

        return {
            "success": True,
            "message": "AQL configuration updated successfully",
            "data": {
                "inspection_status": inspection.inspection_status
            }
        }

    except Exception as e:
        frappe.log_error(f"Error updating AQL configuration: {str(e)}")
        frappe.throw(_("Error updating AQL configuration: {0}").format(str(e)))

@frappe.whitelist()
def update_physical_testing(inspection_id, test_results):
    """Update physical testing results for an inspection"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Parse test_results if it's a string
        if isinstance(test_results, str):
            test_results = json.loads(test_results)

        # Update test results
        updated_count = 0
        for test_result in test_results:
            test_parameter = test_result.get('test_parameter')
            if not test_parameter:
                continue

            # Find the corresponding checklist item
            for item in inspection.fabric_checklist_items:
                if item.test_parameter == test_parameter:
                    item.status = test_result.get('status', '')
                    item.actual_result = test_result.get('actual_result', '')
                    item.remarks = test_result.get('remarks', '')
                    updated_count += 1
                    break

        # Update status to In Progress if currently Draft
        if inspection.inspection_status == "Draft":
            inspection.inspection_status = "In Progress"

        inspection.save()

        return {
            "success": True,
            "message": "Physical testing results updated successfully",
            "data": {
                "updated_count": updated_count,
                "inspection_status": inspection.inspection_status
            }
        }

    except Exception as e:
        frappe.log_error(f"Error updating physical testing: {str(e)}")
        frappe.throw(_("Error updating physical testing: {0}").format(str(e)))

@frappe.whitelist()
def hold_inspection(inspection_id, hold_reason):
    """Put an inspection on hold"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Update hold details
        inspection.inspection_status = "Hold"
        inspection.hold_reason = hold_reason
        inspection.hold_timestamp = frappe.utils.now()
        inspection.hold_by = frappe.session.user

        inspection.save()

        return {
            "success": True,
            "message": "Inspection placed on hold successfully",
            "data": {
                "inspection_status": "Hold",
                "hold_timestamp": inspection.hold_timestamp,
                "hold_by": inspection.hold_by
            }
        }

    except Exception as e:
        frappe.log_error(f"Error holding inspection: {str(e)}")
        frappe.throw(_("Error holding inspection: {0}").format(str(e)))

@frappe.whitelist()
def save_inspection_progress(inspection_id, section=None, data=None, auto_save=False):
    """Save inspection progress without final determination"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Parse data if it's a string
        if isinstance(data, str):
            data = json.loads(data)

        # Handle different sections
        if section == "physical_testing" and data:
            test_results = data.get('test_results', [])
            if test_results:
                # Update test results
                for test_result in test_results:
                    test_parameter = test_result.get('test_parameter')
                    if test_parameter:
                        for item in inspection.fabric_checklist_items:
                            if item.test_parameter == test_parameter:
                                if 'status' in test_result:
                                    item.status = test_result['status']
                                if 'actual_result' in test_result:
                                    item.actual_result = test_result['actual_result']
                                if 'remarks' in test_result:
                                    item.remarks = test_result['remarks']
                                break

        # Update status to In Progress if currently Draft or Hold
        if inspection.inspection_status in ["Draft", "Hold"]:
            inspection.inspection_status = "In Progress"

        inspection.save()

        return {
            "success": True,
            "message": "Progress saved successfully",
            "data": {
                "inspection_status": inspection.inspection_status,
                "last_updated": frappe.utils.now()
            }
        }

    except Exception as e:
        frappe.log_error(f"Error saving inspection progress: {str(e)}")
        frappe.throw(_("Error saving progress: {0}").format(str(e)))

# ===========================
# MASTER DATA APIs
# ===========================

@frappe.whitelist()
def get_aql_levels():
    """Get active AQL levels for mobile dropdown"""
    try:
        levels = frappe.get_all(
            'AQL Level',
            filters={'is_active': 1},
            fields=['level_code as value', 'description', 'level_type'],
            order_by='level_code'
        )

        # Format for mobile dropdown
        formatted_levels = []
        for level in levels:
            formatted_levels.append({
                'value': level['value'],
                'label': f"{level['value']} - {level['description'] or 'General Inspection Level'}",
                'description': level['description'],
                'level_type': level['level_type']
            })

        return {'success': True, 'data': formatted_levels}

    except Exception as e:
        frappe.log_error(f"Error getting AQL levels: {str(e)}")
        frappe.throw(_("Error loading AQL levels: {0}").format(str(e)))

@frappe.whitelist()
def get_aql_values():
    """Get active AQL values for mobile dropdown"""
    try:
        values = frappe.get_all(
            'AQL Standard',
            filters={'is_active': 1},
            fields=['aql_value as value', 'description'],
            order_by='CAST(aql_value AS DECIMAL(10,3))'
        )

        # Format for mobile dropdown
        formatted_values = []
        for val in values:
            formatted_values.append({
                'value': val['value'],
                'label': f"{val['value']}% - {val['description'] or 'Quality Level'}",
                'description': val['description']
            })

        return {'success': True, 'data': formatted_values}

    except Exception as e:
        frappe.log_error(f"Error getting AQL values: {str(e)}")
        frappe.throw(_("Error loading AQL values: {0}").format(str(e)))

@frappe.whitelist()
def get_inspection_types():
    """Get inspection types from Fabric Inspection doctype options"""
    try:
        # Get from doctype field options
        doctype_meta = frappe.get_meta('Fabric Inspection')
        inspection_type_field = doctype_meta.get_field('inspection_type')

        if inspection_type_field and inspection_type_field.options:
            types = inspection_type_field.options.split('\n')
            formatted_types = []

            descriptions = {
                'AQL Based': 'Statistical sampling based on Acceptance Quality Level standards',
                '100% Inspection': 'Complete inspection of all units/rolls',
                'Custom Sampling': 'Custom sampling method defined by quality requirements'
            }

            for type_val in types:
                if type_val.strip():
                    formatted_types.append({
                        'value': type_val.strip(),
                        'label': type_val.strip(),
                        'description': descriptions.get(type_val.strip(), '')
                    })

            return {'success': True, 'data': formatted_types}

        return {'success': False, 'error': 'No inspection types found'}

    except Exception as e:
        frappe.log_error(f"Error getting inspection types: {str(e)}")
        frappe.throw(_("Error loading inspection types: {0}").format(str(e)))

@frappe.whitelist()
def get_inspection_regimes():
    """Get inspection regimes from Fabric Inspection doctype options"""
    try:
        # Get from doctype field options
        doctype_meta = frappe.get_meta('Fabric Inspection')
        regime_field = doctype_meta.get_field('inspection_regime')

        if regime_field and regime_field.options:
            regimes = regime_field.options.split('\n')
            formatted_regimes = []

            descriptions = {
                'Normal': 'Standard inspection regime for routine quality control',
                'Tightened': 'Stricter inspection when quality issues have been detected',
                'Reduced': 'Relaxed inspection for proven suppliers with good quality history'
            }

            for regime_val in regimes:
                if regime_val.strip():
                    formatted_regimes.append({
                        'value': regime_val.strip(),
                        'label': regime_val.strip(),
                        'description': descriptions.get(regime_val.strip(), '')
                    })

            return {'success': True, 'data': formatted_regimes}

        return {'success': False, 'error': 'No inspection regimes found'}

    except Exception as e:
        frappe.log_error(f"Error getting inspection regimes: {str(e)}")
        frappe.throw(_("Error loading inspection regimes: {0}").format(str(e)))

@frappe.whitelist()
def get_inspection_config():
    """Get all inspection configuration master data in one call"""
    try:
        return {
            'success': True,
            'data': {
                'aql_levels': get_aql_levels()['data'],
                'aql_values': get_aql_values()['data'],
                'inspection_types': get_inspection_types()['data'],
                'inspection_regimes': get_inspection_regimes()['data']
            },
            'cache_ttl': 3600  # Cache for 1 hour
        }

    except Exception as e:
        frappe.log_error(f"Error getting inspection config: {str(e)}")
        frappe.throw(_("Error loading inspection config: {0}").format(str(e)))

# ===========================
# HELPER FUNCTIONS
# ===========================

def calculate_total_inspected_meters(inspection):
    """Calculate total inspected meters"""
    total = 0
    for roll in inspection.fabric_rolls_tab or []:
        if roll.inspected:
            total += flt(roll.roll_length or 0)
    return total

def calculate_average_points_per_100_sqm(inspection):
    """Calculate average points per 100 square meters"""
    total_points = 0
    total_area = 0

    for roll in inspection.fabric_rolls_tab or []:
        if roll.inspected:
            points = flt(roll.points_per_100_sqm or 0)
            area = flt(roll.roll_length or 0) * flt(roll.roll_width or 60) * 0.0254 / 100  # Convert to 100 sqm units
            total_points += points * area
            total_area += area

    return (total_points / total_area) if total_area > 0 else 0

def determine_overall_inspection_status(inspection):
    """Determine overall inspection status for display"""
    if not inspection.fabric_rolls_tab:
        return "Pending"

    total_rolls = len(inspection.fabric_rolls_tab)
    inspected_rolls = sum(1 for roll in inspection.fabric_rolls_tab if roll.inspected)

    if inspected_rolls == 0:
        return "Pending"
    elif inspected_rolls == total_rolls:
        # All rolls inspected - check results
        accepted_rolls = sum(1 for roll in inspection.fabric_rolls_tab
                           if roll.inspected and roll.roll_result in ['First Quality', 'Accepted'])

        if accepted_rolls == total_rolls:
            return "Passed"
        else:
            return "Failed"
    else:
        return "In Progress"

def generate_sample_rolls_text(inspection):
    """Generate sample rolls description text"""
    if inspection.inspection_type == "100% Inspection":
        return f"{inspection.total_rolls or 0} rolls (100% inspection)"
    elif inspection.inspection_type == "AQL Based":
        sample_rolls = inspection.required_sample_rolls or 0
        total_rolls = inspection.total_rolls or 0
        return f"{sample_rolls} rolls ({total_rolls} units, AQL sampling)"
    else:
        return f"{inspection.total_rolls or 0} rolls (custom sampling)"

def build_roll_details(inspection):
    """Build roll details array for API response"""
    rolls = []
    for roll in inspection.fabric_rolls_tab or []:
        rolls.append({
            "roll_number": roll.roll_number,
            "length": flt(roll.roll_length or 0),
            "width": flt(roll.roll_width or 0),
            "gsm": flt(roll.gsm or 0),
            "status": "Inspected" if roll.inspected else "Pending"
        })
    return rolls

def build_physical_testing(inspection):
    """Build physical testing array for API response"""
    tests = []
    for item in inspection.fabric_checklist_items or []:
        tests.append({
            "test_parameter": item.test_parameter,
            "category": item.test_category or "Physical Testing",
            "standard_requirement": item.standard_requirement,
            "test_method": item.test_method or "",
            "unit_of_measurement": item.unit_of_measurement or "",
            "tolerance": item.tolerance or "",
            "is_mandatory": bool(item.is_mandatory),
            "display_order": cint(item.display_order or 999),
            "status": item.status or "",
            "actual_result": item.actual_result or "",
            "remarks": item.remarks or ""
        })

    # Sort by display_order
    tests.sort(key=lambda x: x['display_order'])
    return tests

def calculate_summary_counts(inspection):
    """Calculate summary counts for checklist"""
    total_tests = len(inspection.fabric_checklist_items or [])
    passed = sum(1 for item in inspection.fabric_checklist_items if item.status == 'Pass')
    failed = sum(1 for item in inspection.fabric_checklist_items if item.status == 'Fail')
    na = sum(1 for item in inspection.fabric_checklist_items if item.status == 'N/A')
    pending = total_tests - passed - failed - na

    return {
        "passed": passed,
        "failed": failed,
        "na": na,
        "pending": pending
    }

# ===========================
# ROLL DETAILS APIs
# ===========================

@frappe.whitelist()
def get_roll_details(inspection_id, roll_id=None):
    """Get roll details for fabric inspection including all roll information fields"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("read"):
            frappe.throw(_("You do not have permission to view this inspection"))

        # Get specific roll or all rolls
        if roll_id:
            # Find specific roll
            roll_data = None
            available_rolls = []

            for roll in inspection.fabric_rolls_tab or []:
                available_rolls.append({
                    'name': roll.name,
                    'roll_number': getattr(roll, 'roll_number', 'N/A')
                })

                # Try matching by both name and roll_number
                if roll.name == roll_id or getattr(roll, 'roll_number', '') == roll_id:
                    roll_data = build_detailed_roll_info(roll)
                    break

            if not roll_data:
                error_msg = f"Roll not found. Looking for: '{roll_id}'. Available rolls: {available_rolls}"
                frappe.log_error(error_msg)
                frappe.throw(_(f"Roll not found. Roll ID '{roll_id}' does not exist in inspection '{inspection_id}'. Available rolls: {len(available_rolls)}"))

            return {
                "success": True,
                "data": roll_data
            }
        else:
            # Get all rolls with summary info
            rolls = []
            for roll in inspection.fabric_rolls_tab or []:
                rolls.append(build_roll_summary(roll))

            return {
                "success": True,
                "data": {
                    "inspection_id": inspection_id,
                    "total_rolls": len(rolls),
                    "rolls": rolls
                }
            }

    except Exception as e:
        frappe.log_error(f"Error getting roll details: {str(e)}")
        frappe.throw(_("Error loading roll details: {0}").format(str(e)))

@frappe.whitelist()
def save_roll_details(inspection_id, roll_id, roll_data):
    """Save roll details including roll information and defects"""
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Parse data if it's a string
        if isinstance(roll_data, str):
            roll_data = json.loads(roll_data)

        # Find the roll
        roll_item = None
        available_rolls = []

        for roll in inspection.fabric_rolls_tab or []:
            available_rolls.append({
                'name': roll.name,
                'roll_number': getattr(roll, 'roll_number', 'N/A')
            })

            # Try matching by both name and roll_number
            if roll.name == roll_id or getattr(roll, 'roll_number', '') == roll_id:
                roll_item = roll
                break

        if not roll_item:
            error_msg = f"Roll not found for saving. Looking for: '{roll_id}'. Available rolls: {available_rolls}"
            frappe.log_error(error_msg)
            frappe.throw(_(f"Roll not found. Roll ID '{roll_id}' does not exist in inspection '{inspection_id}'. Available rolls: {len(available_rolls)}"))

        # Update roll information fields
        if 'diameter_inches' in roll_data:
            roll_item.diameter_inches = flt(roll_data['diameter_inches'])
        if 'inspected_gsm' in roll_data:
            roll_item.inspected_gsm = flt(roll_data['inspected_gsm'])
        if 'actual_gsm' in roll_data:
            roll_item.actual_gsm = flt(roll_data['actual_gsm'])
        if 'inspected_length_m' in roll_data:
            roll_item.inspected_length_m = flt(roll_data['inspected_length_m'])
        if 'actual_length_m' in roll_data:
            roll_item.actual_length_m = flt(roll_data['actual_length_m'])
        if 'inspected_width_m' in roll_data:
            roll_item.inspected_width_m = flt(roll_data['inspected_width_m'])
        if 'actual_width_m' in roll_data:
            roll_item.actual_width_m = flt(roll_data['actual_width_m'])
        if 'inspected_shade' in roll_data:
            roll_item.inspected_shade = roll_data['inspected_shade']
        if 'actual_shade' in roll_data:
            roll_item.actual_shade = roll_data['actual_shade']

        # Handle defects - Create Link targets and use ORM
        if 'defects' in roll_data and roll_data['defects']:
            # Clear existing defects for this roll
            for existing_defect in roll_item.defects:
                existing_defect.delete()

            # Prepare JSON defects data (for calculation system)
            if inspection.defects_data:
                try:
                    defects_data = json.loads(inspection.defects_data) if isinstance(inspection.defects_data, str) else inspection.defects_data
                except:
                    defects_data = {}
            else:
                defects_data = {}

            roll_number = getattr(roll_item, 'roll_number', roll_item.name)
            defects_data[roll_number] = {}

            # Process each defect and save directly to database
            for defect_data in roll_data['defects']:
                # Ensure Defect Master exists
                defect_name = defect_data.get('defect', '')
                defect_code = defect_name.upper().replace(' ', '_')
                if defect_name and not frappe.db.exists("Defect Master", defect_code):
                    # Create Defect Master if it doesn't exist
                    defect_master = frappe.new_doc("Defect Master")
                    defect_master.defect_code = defect_code
                    defect_master.defect_name = defect_name
                    defect_master.defect_type = defect_data.get('defect_type', 'Major')
                    defect_master.inspection_type = "Fabric Inspection"
                    defect_master.material_type = "Fabrics"
                    defect_master.is_active = 1
                    # Add required point criteria for fabric inspection
                    defect_master.point_1_criteria = "≤ 1\""
                    defect_master.point_2_criteria = "1\" to 3\""
                    defect_master.point_3_criteria = "3\" to 6\""
                    defect_master.point_4_criteria = "> 6\""
                    defect_master.insert(ignore_permissions=True)

                # Ensure Defect Category exists
                category_name = defect_data.get('category', '')
                category_code = category_name.upper().replace(' ', '_')
                if category_name and not frappe.db.exists("Defect Category", category_code):
                    # Create Defect Category if it doesn't exist
                    defect_category = frappe.new_doc("Defect Category")
                    defect_category.category_code = category_code
                    defect_category.category_name = category_name
                    defect_category.material_type = "Fabrics"
                    defect_category.is_active = 1
                    defect_category.insert(ignore_permissions=True)

                # Get defect_type
                defect_type = defect_data.get('defect_type', 'Major')
                if not defect_type and defect_name:
                    try:
                        defect_doc = frappe.get_doc("Defect Master", defect_code)
                        defect_type = defect_doc.defect_type
                    except:
                        defect_type = 'Major'

                # Calculate points
                size = flt(defect_data.get('size', 0))
                if defect_type == "Critical":
                    points = 4.0
                elif defect_type == "Major":
                    points = 3.0 if size > 1 else 2.0
                elif defect_type == "Minor":
                    points = 2.0 if size > 3 else 1.0
                else:
                    points = 1.0

                # Create defect using Frappe ORM (now that link targets exist)
                defect_doc = frappe.new_doc("Fabric Roll Inspection Defect")
                defect_doc.parent = roll_item.name
                defect_doc.parenttype = "Fabric Roll Inspection Item"
                defect_doc.parentfield = "defects"
                defect_doc.defect = defect_code
                defect_doc.category = category_code
                defect_doc.defect_type = defect_type
                defect_doc.size = size
                defect_doc.points_auto = points
                defect_doc.insert(ignore_permissions=True)

                # Debug logging
                frappe.logger().info(f"Created defect: {defect_doc.name} for parent: {roll_item.name}, defect: {defect_code}, category: {category_code}, type: {defect_type}, size: {size}")

                # Also add to roll_item's defects in memory for immediate access
                defect_dict = {
                    'defect': defect_code,
                    'category': category_code,
                    'defect_type': defect_type,
                    'size': size,
                    'points_auto': points
                }
                if not hasattr(roll_item, '_temp_defects'):
                    roll_item._temp_defects = []
                roll_item._temp_defects.append(defect_dict)

                # Add to JSON format for calculation system
                defect_key = f"{category_name}_{defect_name}"
                defects_data[roll_number][defect_key] = size

            # Save JSON defects data
            inspection.defects_data = json.dumps(defects_data)

        # Mark as inspected if not already
        if not roll_item.inspected:
            roll_item.inspected = 1

        # Save the inspection and commit database changes
        try:
            # Save inspection (defects already saved via ORM)
            inspection._preserve_mobile_defects = True
            inspection.save()
            frappe.db.commit()  # Commit all changes including ORM inserts

            # Reload the inspection to get fresh defects data
            inspection.reload()
            # Find the roll item again after reload
            for roll in inspection.fabric_rolls_tab or []:
                if roll.name == roll_item.name or getattr(roll, 'roll_number', '') == roll_id:
                    roll_item = roll
                    break

        except Exception as save_error:
            frappe.logger().error(f"Save error: {save_error}")
            frappe.db.rollback()  # Rollback on error
            raise

        return {
            "success": True,
            "message": "Roll details saved successfully",
            "data": build_detailed_roll_info(roll_item)
        }

    except Exception as e:
        error_msg = f"Error saving roll details: {str(e)}"
        frappe.log_error(error_msg)
        frappe.throw(_(error_msg))

@frappe.whitelist()
def get_defect_categories(material_type="Fabrics"):
    """Get defect categories filtered by material type"""
    try:
        categories = frappe.get_all(
            'Defect Category',
            filters={
                'material_type': material_type,
                'is_active': 1
            },
            fields=['category_code as value', 'category_name as label', 'description'],
            order_by='sort_order, category_name'
        )

        return {
            "success": True,
            "data": categories
        }

    except Exception as e:
        frappe.log_error(f"Error getting defect categories: {str(e)}")
        frappe.throw(_("Error loading defect categories: {0}").format(str(e)))

@frappe.whitelist()
def get_defects_by_category(category_code=None, material_type="Fabrics"):
    """Get defects filtered by category and material type"""
    try:
        filters = {'material_type': material_type, 'is_active': 1}
        if category_code:
            filters['defect_category'] = category_code

        defects = frappe.get_all(
            'Defect Master',
            filters=filters,
            fields=['name as value', 'defect_name as label', 'defect_category as category', 'defect_description as description', 'defect_type'],
            order_by='defect_category, defect_name'
        )

        return {
            "success": True,
            "data": defects
        }

    except Exception as e:
        frappe.log_error(f"Error getting defects: {str(e)}")
        frappe.throw(_("Error loading defects: {0}").format(str(e)))

@frappe.whitelist()
def get_roll_defect_dropdown_data(material_type="Fabrics"):
    """Get all defect dropdown data in one call for roll details screen"""
    try:
        return {
            'success': True,
            'data': {
                'categories': get_defect_categories(material_type)['data'],
                'defects': get_defects_by_category(material_type=material_type)['data']
            },
            'cache_ttl': 3600  # Cache for 1 hour
        }

    except Exception as e:
        frappe.log_error(f"Error getting roll defect dropdown data: {str(e)}")
        frappe.throw(_("Error loading defect dropdown data: {0}").format(str(e)))

# ===========================
# ROLL HELPER FUNCTIONS
# ===========================

def build_detailed_roll_info(roll):
    """Build detailed roll information for API response"""
    return {
        "roll_id": roll.name,
        "roll_number": roll.roll_number,
        "compact_roll_no": roll.compact_roll_no or "",
        "shade_code": roll.shade_code or "",
        "lot_number": roll.lot_number or "",

        # Basic measurements
        "roll_length": flt(roll.roll_length or 0),
        "roll_width": flt(roll.roll_width or 0),
        "gsm": flt(roll.gsm or 0),

        # Roll information fields
        "diameter_inches": flt(roll.diameter_inches or 0),
        "inspected_gsm": flt(roll.inspected_gsm or 0),
        "actual_gsm": flt(roll.actual_gsm or 0),
        "inspected_length_m": flt(roll.inspected_length_m or 0),
        "actual_length_m": flt(roll.actual_length_m or 0),
        "inspected_width_m": flt(roll.inspected_width_m or 0),
        "actual_width_m": flt(roll.actual_width_m or 0),
        "inspected_shade": roll.inspected_shade or "",
        "actual_shade": roll.actual_shade or "",

        # Calculated fields
        "total_size_inches": flt(roll.total_size_inches or 0),
        "total_points_auto": flt(roll.total_points_auto or 0),
        "points_per_100_sqm": flt(roll.points_per_100_sqm or 0),

        # Status and results
        "inspected": bool(roll.inspected),
        "roll_result": roll.roll_result or "Pending",
        "roll_grade": roll.roll_grade or "",

        # Defects
        "defects": build_roll_defects(roll),

        # Remarks
        "roll_remarks": roll.roll_remarks or ""
    }

def build_roll_summary(roll):
    """Build roll summary for listing"""
    return {
        "roll_id": roll.name,
        "roll_number": roll.roll_number,
        "length": flt(roll.roll_length or 0),
        "width": flt(roll.roll_width or 0),
        "gsm": flt(roll.gsm or 0),
        "total_points": flt(roll.total_points_auto or 0),
        "points_per_100_sqm": flt(roll.points_per_100_sqm or 0),
        "status": "Inspected" if roll.inspected else "Pending",
        "result": roll.roll_result or "Pending"
    }

def build_roll_defects(roll):
    """Build defects array for roll"""
    defects = []

    # First check if we have temporary defects (from current save operation)
    if hasattr(roll, '_temp_defects') and roll._temp_defects:
        frappe.logger().info(f"Using temporary defects: {len(roll._temp_defects)} defects found")
        for defect_dict in roll._temp_defects:
            defects.append({
                "defect": defect_dict.get("defect", ""),
                "category": defect_dict.get("category", ""),
                "defect_type": defect_dict.get("defect_type", ""),
                "size": flt(defect_dict.get("size", 0)),
                "points_auto": flt(defect_dict.get("points_auto", 0))
            })
    else:
        # Use regular child table defects
        frappe.logger().info(f"Using child table defects: {len(roll.defects or [])} defects found")
        for defect_row in roll.defects or []:
            defects.append({
                "defect": defect_row.defect or "",
                "category": defect_row.category or "",
                "defect_type": getattr(defect_row, 'defect_type', '') or "",
                "size": flt(defect_row.size or 0),
                "points_auto": flt(defect_row.points_auto or 0)
            })

    frappe.logger().info(f"Returning {len(defects)} defects from build_roll_defects")
    return defects