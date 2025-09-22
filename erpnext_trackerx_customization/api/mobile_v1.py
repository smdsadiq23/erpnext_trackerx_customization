import frappe
from frappe import _
from frappe.utils import flt, cint
import json



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

        # Force reload child tables to ensure defects are loaded for all rolls
        for roll in inspection.fabric_rolls_tab or []:
            if hasattr(roll, 'defects'):
                # Force reload defects for each roll
                roll_doc = frappe.get_doc("Fabric Roll Inspection Item", roll.name)
                roll.defects = roll_doc.defects

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

        # Force load child table data from database
        for roll in inspection.fabric_rolls_tab or []:
            if hasattr(roll, 'defects'):
                # Get fresh defect data from database
                defects_data = frappe.get_all(
                    "Fabric Roll Inspection Defect",
                    filters={"parent": roll.name},
                    fields=["name", "defect", "category", "defect_type", "size", "points_auto"]
                )
                # Convert to proper objects
                roll.defects = [frappe._dict(d) for d in defects_data]

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
    """
    Save roll details including roll information and defects
    Uses in-memory child table appending to avoid data loss from parent.save() overwrites
    """
    try:
        # Parse form data
        if not inspection_id or not roll_id:
            frappe.throw(_("inspection_id and roll_id are required"), frappe.ValidationError)

        # Normalize roll_data to dict
        if isinstance(roll_data, str):
            try:
                roll_data = json.loads(roll_data)
            except Exception:
                frappe.throw(_("Invalid roll_data JSON"), frappe.ValidationError)

        # Load inspection doc
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Find the roll item in the parent's child table
        roll_item = None
        for roll in inspection.fabric_rolls_tab or []:
            if roll.name == roll_id or getattr(roll, 'roll_number', '') == roll_id:
                roll_item = roll
                break

        if not roll_item:
            frappe.throw(_("Roll not found: {0}").format(roll_id), frappe.ValidationError)

        # Update scalar fields on the roll_item (only if present in payload)
        scalar_fields = [
            "diameter_inches", "compact_roll_no", "inspected_gsm", "actual_gsm",
            "inspected_length_m", "actual_length_m", "inspected_width_m", "actual_width_m",
            "inspected_shade", "actual_shade", "roll_length", "roll_width", "gsm"
        ]
        for field in scalar_fields:
            if field in roll_data:
                setattr(roll_item, field, roll_data.get(field))

        # Robust deterministic defect handling with proper CRUD semantics
        defects_payload = roll_data.get("defects") or []

        # Helper functions for deterministic master data handling
        def get_or_create_defect_master(defect_name, defect_type="Major"):
            """Get existing defect master or create deterministically"""
            if not defect_name:
                return None

            # Normalize defect name for consistent lookup
            normalized_name = defect_name.strip()

            # Case-insensitive lookup by defect_name
            existing = frappe.db.get_value(
                "Defect Master",
                {"defect_name": normalized_name},
                "name"
            )
            if existing:
                return existing

            # Create with deterministic slug as defect_code
            import re
            defect_code = re.sub(r'[^a-zA-Z0-9]', '_', normalized_name.upper())
            defect_code = re.sub(r'_+', '_', defect_code).strip('_')

            # Ensure uniqueness with minimal counter if needed
            base_code = defect_code
            counter = 1
            while frappe.db.exists("Defect Master", defect_code):
                defect_code = f"{base_code}_{counter}"
                counter += 1

            dm = frappe.new_doc("Defect Master")
            dm.defect_code = defect_code
            dm.defect_name = normalized_name
            dm.defect_type = defect_type
            dm.inspection_type = "Fabric Inspection"
            dm.point_1_criteria = "≤ 3\""
            dm.point_2_criteria = "3\" to 6\""
            dm.point_3_criteria = "6\" to 9\""
            dm.point_4_criteria = "> 9\""
            dm.insert(ignore_permissions=True)
            return dm.name

        def get_or_create_defect_category(category_name):
            """Get existing defect category or create deterministically"""
            if not category_name:
                return None

            # Normalize category name
            normalized_name = category_name.strip()

            # Lookup by category_name + material_type
            existing = frappe.db.get_value(
                "Defect Category",
                {
                    "category_name": normalized_name,
                    "material_type": "Fabrics"
                },
                "name"
            )
            if existing:
                return existing

            # Create with deterministic slug
            import re
            category_code = re.sub(r'[^a-zA-Z0-9]', '_', normalized_name.upper())
            category_code = re.sub(r'_+', '_', category_code).strip('_')

            base_code = category_code
            counter = 1
            while frappe.db.exists("Defect Category", category_code):
                category_code = f"{base_code}_{counter}"
                counter += 1

            dc = frappe.new_doc("Defect Category")
            dc.category_code = category_code
            dc.category_name = normalized_name
            dc.material_type = "Fabrics"
            dc.insert(ignore_permissions=True)
            return dc.name

        # Build new defects list with proper create/update/delete semantics
        new_defects_list = []

        for d in defects_payload:
            # Normalize incoming data
            defect_name = (d.get("defect") or "").strip()
            category_name = (d.get("category") or "").strip()
            defect_type = (d.get("defect_type") or "Major").strip()
            size = round(flt(d.get("size", 0.0)), 2)  # Round to 2 decimal places for consistency
            points_auto = flt(d.get("points_auto", 0.0))

            # Ensure master data exists
            get_or_create_defect_master(defect_name, defect_type)
            get_or_create_defect_category(category_name)

            # Build defect dict for child table
            defect_dict = {
                "defect": defect_name,
                "category": category_name,
                "defect_type": defect_type,
                "size": size,
                "points_auto": points_auto
            }

            # If client provides existing child row name, include it for update
            if d.get("name"):
                defect_dict["name"] = d["name"]

            new_defects_list.append(defect_dict)

        # Alternative approach: Direct child record management
        # 1. Delete existing defects from database
        frappe.db.delete("Fabric Roll Inspection Defect", {"parent": roll_item.name})

        # 2. Create new defect records directly
        for defect_dict in new_defects_list:
            defect_doc = frappe.new_doc("Fabric Roll Inspection Defect")
            defect_doc.parent = roll_item.name
            defect_doc.parenttype = "Fabric Roll Inspection Item"
            defect_doc.parentfield = "defects"
            defect_doc.defect = defect_dict["defect"]
            defect_doc.category = defect_dict["category"]
            defect_doc.defect_type = defect_dict["defect_type"]
            defect_doc.size = defect_dict["size"]
            defect_doc.points_auto = defect_dict["points_auto"]
            defect_doc.insert(ignore_permissions=True)

        # Mark inspected and save parent without triggering child updates
        if not roll_item.inspected:
            roll_item.inspected = 1

        # Update parent document fields only
        inspection._preserve_mobile_defects = True
        inspection.save(ignore_permissions=True)
        frappe.db.commit()

        # Reload defects from database for response
        fresh_defects = frappe.get_all(
            "Fabric Roll Inspection Defect",
            filters={"parent": roll_item.name},
            fields=["name", "defect", "category", "defect_type", "size", "points_auto"]
        )
        # Set fresh defects on roll item for response building
        roll_item.defects = [frappe._dict(d) for d in fresh_defects]

        # Build response from the updated roll item
        reloaded_roll = roll_item

        return {
            "success": True,
            "message": "Roll details saved successfully",
            "data": build_detailed_roll_info(reloaded_roll)
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
    for defect_row in roll.defects or []:
        defects.append({
            "defect": defect_row.defect or "",
            "category": defect_row.category or "",
            "defect_type": getattr(defect_row, 'defect_type', '') or "",
            "size": flt(defect_row.size or 0),
            "points_auto": flt(defect_row.points_auto or 0)
        })
    return defects