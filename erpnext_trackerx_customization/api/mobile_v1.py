import frappe
from frappe import _
from frappe.utils import flt, cint
import json

# ===========================
# UTILITY FUNCTIONS
# ===========================

def format_total_rolls_display(total_quantity, unit_of_measure, total_rolls):
    """
    Format total rolls display as: "500kg (1 Roll)" or "1500.5 Meter (3 Rolls)"

    Args:
        total_quantity (float): The received quantity
        unit_of_measure (str): The unit of measurement
        total_rolls (int): Number of rolls

    Returns:
        str: Formatted display string
    """
    try:
        # Convert values to proper types
        quantity = flt(total_quantity or 0)
        rolls = cint(total_rolls or 0)
        unit = str(unit_of_measure or "").strip()

        # If no quantity or rolls, return just roll count
        if not quantity or not rolls:
            rolls_text = "Roll" if rolls == 1 else "Rolls"
            return f"{rolls} {rolls_text}"

        # Format quantity - remove trailing zeros
        if quantity == int(quantity):
            quantity_str = str(int(quantity))
        else:
            quantity_str = f"{quantity:g}"  # Removes trailing zeros

        # Standardize unit abbreviations for mobile display
        unit_mapping = {
            "Kilogram": "kg", "Kg": "kg", "KG": "kg", "kg": "kg",
            "Meter": "m", "Metre": "m", "M": "m", "m": "m",
            "Piece": "pcs", "Pieces": "pcs", "PCS": "pcs", "pcs": "pcs",
            "Yard": "yd", "YD": "yd", "yd": "yd",
            "Inch": "in", "IN": "in", "in": "in"
        }

        standardized_unit = unit_mapping.get(unit, unit.lower() if unit else "")

        # Handle singular/plural for rolls
        rolls_text = "Roll" if rolls == 1 else "Rolls"

        # Create final formatted string
        return f"{quantity_str}{standardized_unit} ({rolls} {rolls_text})"

    except Exception as e:
        # Fallback to basic roll count if formatting fails
        frappe.log_error(f"Error formatting total rolls display: {str(e)}")
        rolls_text = "Roll" if cint(total_rolls) == 1 else "Rolls"
        return f"{cint(total_rolls or 0)} {rolls_text}"

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

        # Build response as array of key-value objects for consistent mobile format
        result = {}
        total = 0
        for item in status_counts:
            status = item['inspection_status'] or 'Draft'
            count = item['count']
            result[status] = count
            total += count

        # Convert to array format
        response_data = []

        # Add status counts
        for status, count in result.items():
            response_data.append({
                "key": status,
                "value": count
            })

        # Add total
        response_data.append({
            "key": "Total",
            "value": total
        })

        return {
            "success": True,
            "data": response_data,
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

        # Search filter - search across multiple fields using SQL
        if search:
            search_term = f'%{search}%'

            # Build base WHERE conditions for filters
            where_conditions = ["docstatus != 2"]
            values = []

            # Add status filter if provided
            if status and status != "All":
                where_conditions.append("inspection_status = %s")
                values.append(status)

            # Add search conditions for multiple fields
            search_conditions = [
                "name LIKE %s",
                "purchase_order_reference LIKE %s",
                "grn_reference LIKE %s",
                "supplier LIKE %s",
                "item_code LIKE %s",
                "item_name LIKE %s"
            ]

            # Combine search conditions with OR
            search_where = f"({' OR '.join(search_conditions)})"
            where_conditions.append(search_where)

            # Add search term for each search field
            for _ in search_conditions:
                values.append(search_term)

            # Build complete WHERE clause
            where_clause = " AND ".join(where_conditions)

            # Get inspections using SQL query
            inspections = frappe.db.sql(f"""
                SELECT
                    name, inspection_status, purchase_order_reference,
                    grn_reference, supplier, inspector, inspection_date,
                    total_rolls, total_quantity, unit_of_measure,
                    item_code, item_name, creation
                FROM `tabFabric Inspection`
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT {start}, {limit}
            """, values, as_dict=True)

            # Get total count for pagination with search
            total_count = frappe.db.sql(f"""
                SELECT COUNT(*)
                FROM `tabFabric Inspection`
                WHERE {where_clause}
            """, values)[0][0]

        else:
            # No search - use regular get_list for better performance
            inspections = frappe.get_list(
                'Fabric Inspection',
                filters=filters,
                fields=[
                    'name', 'inspection_status', 'purchase_order_reference',
                    'grn_reference', 'supplier', 'inspector', 'inspection_date',
                    'total_rolls', 'total_quantity', 'unit_of_measure',
                    'item_code', 'item_name', 'creation'
                ],
                limit=limit,
                start=start,
                order_by=f"{sort_by} {sort_order}"
            )

            # Get total count for pagination
            total_count = frappe.db.count('Fabric Inspection', filters)

        # Format total_rolls display for all inspections
        for inspection in inspections:
            inspection['total_rolls'] = format_total_rolls_display(
                inspection.get('total_quantity'),
                inspection.get('unit_of_measure'),
                inspection.get('total_rolls')
            )

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

def get_item_fabric_details(item_code):
    """Fetch fabric-specific details from Item master"""
    if not item_code:
        return {}

    try:
        item_doc = frappe.get_doc("Item", item_code)

        # Handle construction type link field
        construction_type_name = ""
        if hasattr(item_doc, 'custom_construction_type_link') and item_doc.custom_construction_type_link:
            try:
                construction_doc = frappe.get_doc("Construction Type", item_doc.custom_construction_type_link)
                construction_type_name = getattr(construction_doc, 'construction_type', item_doc.custom_construction_type_link)
            except Exception:
                construction_type_name = item_doc.custom_construction_type_link

        return {
            "gsm": getattr(item_doc, 'custom_gsm', '') or '',
            "dia": flt(getattr(item_doc, 'custom_dia', 0)) or 0.0,
            "width": getattr(item_doc, 'custom_width', '') or '',
            "material_composition": getattr(item_doc, 'custom_material_composition', '') or '',
            "construction_type": construction_type_name
        }
    except Exception as e:
        frappe.log_error(f"Error fetching fabric details for item {item_code}: {str(e)}")
        return {
            "gsm": '',
            "dia": 0.0,
            "width": '',
            "material_composition": '',
            "construction_type": ''
        }

def get_business_unit_details(grn_reference):
    """Fetch business unit details from GRN and related doctypes"""
    if not grn_reference:
        return {}

    try:
        # Get GRN document
        grn_doc = frappe.get_doc("Goods Receipt Note", grn_reference)

        # Initialize response
        bu_details = {
            "business_unit_code": "",
            "business_unit_name": "",
            "strategic_business_unit_code": "",
            "strategic_business_unit_name": "",
            "factory_business_unit_code": "",
            "factory_business_unit_name": ""
        }

        # Get Company (Business Unit) details
        if grn_doc.company:
            try:
                company_doc = frappe.get_doc("Company", grn_doc.company)
                bu_details.update({
                    "business_unit_code": getattr(company_doc, 'abbr', '') or grn_doc.company,
                    "business_unit_name": getattr(company_doc, 'company_name', '') or grn_doc.company
                })
            except Exception:
                bu_details.update({
                    "business_unit_code": grn_doc.company,
                    "business_unit_name": grn_doc.company
                })

        # Get Strategic Business Unit details
        if grn_doc.strategic_business_unit:
            try:
                sbu_doc = frappe.get_doc("Strategic Business Unit", grn_doc.strategic_business_unit)
                bu_details.update({
                    "strategic_business_unit_code": getattr(sbu_doc, 'sbu_code', '') or '',
                    "strategic_business_unit_name": getattr(sbu_doc, 'sbu_name', '') or grn_doc.strategic_business_unit
                })
            except Exception:
                bu_details.update({
                    "strategic_business_unit_code": "",
                    "strategic_business_unit_name": grn_doc.strategic_business_unit
                })

        # Get Factory Business Unit details
        if grn_doc.factory_business_unit:
            try:
                fbu_doc = frappe.get_doc("Factory Business Unit", grn_doc.factory_business_unit)
                bu_details.update({
                    "factory_business_unit_code": getattr(fbu_doc, 'factory_code', '') or '',
                    "factory_business_unit_name": getattr(fbu_doc, 'factory_name', '') or grn_doc.factory_business_unit
                })
            except Exception:
                bu_details.update({
                    "factory_business_unit_code": "",
                    "factory_business_unit_name": grn_doc.factory_business_unit
                })

        return bu_details

    except Exception as e:
        frappe.log_error(f"Error fetching business unit details for GRN {grn_reference}: {str(e)}")
        return {
            "business_unit_code": "",
            "business_unit_name": "",
            "strategic_business_unit_code": "",
            "strategic_business_unit_name": "",
            "factory_business_unit_code": "",
            "factory_business_unit_name": ""
        }

@frappe.whitelist()
def get_inspection_details(inspection_id=None):
    """Get complete inspection details for mobile app"""
    try:
        # Validate required parameters
        if not inspection_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Inspection ID is required",
                    "details": "Please provide a valid inspection ID"
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }
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

        # Get fabric details from item master
        fabric_details = get_item_fabric_details(inspection.item_code)

        # Get business unit details from GRN
        business_unit_details = get_business_unit_details(inspection.grn_reference)

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
                "final_decision": inspection.inspection_result or "Pending",
                **({"hold_reason": inspection.hold_reason, "hold_remarks": inspection.remarks} if inspection.inspection_status == "Hold" else {})
            },
            "aql_configuration": {
                "inspection_type": inspection.inspection_type or "AQL Based",
                "aql_level": inspection.aql_level or "",
                "aql_value": inspection.aql_value or "",
                "inspection_regime": inspection.inspection_regime or "Normal",
                "sampling_percentage": flt(getattr(inspection, 'sampling_percentage', 0)),
                "sample_rolls_text": generate_sample_rolls_text(inspection),
                "no_of_rolls_to_be_inspected": str(inspection.required_sample_rolls or 0),
                "sample_size_to_be_inspected": calculate_sample_size_based_on_uom(inspection)
            },
            "general_details": {
                "supplier": inspection.supplier or "",
                "item_name": inspection.item_name or "",
                "item_code": inspection.item_code or "",
                "grn_reference": inspection.grn_reference or "",
                "purchase_order": inspection.purchase_order_reference or "",
                "total_quantity": flt(inspection.total_quantity or 0),
                "total_rolls": format_total_rolls_display(
                    inspection.total_quantity,
                    getattr(inspection, 'unit_of_measure', None),
                    inspection.total_rolls
                ),
                # New business unit fields from GRN
                "business_unit_code": business_unit_details.get("business_unit_code", ""),
                "business_unit_name": business_unit_details.get("business_unit_name", ""),
                "strategic_business_unit_code": business_unit_details.get("strategic_business_unit_code", ""),
                "strategic_business_unit_name": business_unit_details.get("strategic_business_unit_name", ""),
                "factory_business_unit_code": business_unit_details.get("factory_business_unit_code", ""),
                "factory_business_unit_name": business_unit_details.get("factory_business_unit_name", ""),
                # New fabric-specific fields from Item master
                "gsm": fabric_details.get("gsm", ""),
                "dia": fabric_details.get("dia", 0.0),
                "width": fabric_details.get("width", ""),
                "material_composition": fabric_details.get("material_composition", ""),
                "construction_type": fabric_details.get("construction_type", "")
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
        # Log technical details
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Get inspection details failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Get Inspection Details Error")
        except Exception:
            pass

        # Determine user-friendly error message
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection was not found"
            error_code = "INSPECTION_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to view this inspection"
            error_code = "PERMISSION_DENIED"
        else:
            user_message = "An error occurred while loading inspection details"
            error_code = "DATA_FETCH_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your request and try again"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

@frappe.whitelist()
def update_aql_configuration(inspection_id=None, inspection_type=None, aql_level=None, aql_value=None, inspection_regime=None, sampling_percentage=None):
    """Update AQL configuration for an inspection"""
    try:
        # Validate required parameters
        if not inspection_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Inspection ID is required",
                    "details": "Please provide a valid inspection ID"
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }
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
        if sampling_percentage is not None:
            inspection.sampling_percentage = flt(sampling_percentage)

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
        # Log technical details
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"AQL configuration update failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="AQL Configuration Update Error")
        except Exception:
            pass

        # Determine user-friendly error message
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection was not found"
            error_code = "INSPECTION_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to modify this inspection"
            error_code = "PERMISSION_DENIED"
        else:
            user_message = "An error occurred while updating AQL configuration"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your request and try again"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

@frappe.whitelist()
def update_physical_testing(inspection_id=None, test_results=None):
    """Update physical testing results for an inspection"""
    try:
        # Validate required parameters
        validation_errors = []

        if not inspection_id:
            validation_errors.append({
                "field": "inspection_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Inspection ID is required"
            })

        if not test_results:
            validation_errors.append({
                "field": "test_results",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Test results data is required"
            })

        if validation_errors:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Required parameters are missing",
                    "details": "Please provide all required parameters for physical testing update",
                    "validation_errors": validation_errors
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }
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
        # Log technical details
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Physical testing update failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Physical Testing Update Error")
        except Exception:
            pass

        # Determine user-friendly error message
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection was not found"
            error_code = "INSPECTION_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to modify this inspection"
            error_code = "PERMISSION_DENIED"
        elif "json" in str(e).lower() or "invalid" in str(e).lower():
            user_message = "The test results data format is invalid"
            error_code = "INVALID_DATA_FORMAT"
        else:
            user_message = "An error occurred while updating physical testing results"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your data and try again"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

@frappe.whitelist()
def hold_inspection(inspection_id=None, hold_reason=None):
    """Put an inspection on hold"""
    try:
        # Validate required parameters
        validation_errors = []

        if not inspection_id:
            validation_errors.append({
                "field": "inspection_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Inspection ID is required"
            })

        if not hold_reason or not str(hold_reason).strip():
            validation_errors.append({
                "field": "hold_reason",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Hold reason is required"
            })

        if validation_errors:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Required parameters are missing",
                    "details": "Please provide all required parameters for holding inspection",
                    "validation_errors": validation_errors
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }
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
        # Log technical details
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Hold inspection failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Hold Inspection Error")
        except Exception:
            pass

        # Determine user-friendly error message
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection was not found"
            error_code = "INSPECTION_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to modify this inspection"
            error_code = "PERMISSION_DENIED"
        else:
            user_message = "An error occurred while placing inspection on hold"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your request and try again"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

@frappe.whitelist()
def resume_inspection(inspection_id=None):
    """Resume an inspection from hold status"""
    try:
        # Validate required parameters
        if not inspection_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Inspection ID is required",
                    "details": "Please provide a valid inspection ID"
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Validate current status
        if inspection.inspection_status != "Hold":
            return {
                "success": False,
                "message": "Cannot resume: Inspection is not on hold",
                "data": {
                    "inspection_id": inspection_id,
                    "current_status": inspection.inspection_status,
                    "error": "Only inspections with 'Hold' status can be resumed"
                }
            }

        # Store previous hold information for response
        previous_hold_info = {
            "hold_reason": inspection.hold_reason,
            "hold_by": inspection.hold_by,
            "hold_timestamp": inspection.hold_timestamp
        }

        # Change status to In Progress
        inspection.inspection_status = "In Progress"

        # Add resume tracking to remarks (internal tracking)
        timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        resume_note = f"[{timestamp}] Inspection resumed by {frappe.session.user}"

        existing_remarks = inspection.remarks or ''
        if existing_remarks:
            inspection.remarks = f"{existing_remarks}\n{resume_note}"
        else:
            inspection.remarks = resume_note

        # Save the inspection
        inspection.save()

        return {
            "success": True,
            "message": "Inspection resumed successfully",
            "data": {
                "inspection_id": inspection.name,
                "inspection_status": inspection.inspection_status,
                "resumed_by": frappe.session.user,
                "resumed_timestamp": frappe.utils.now(),
                "previous_hold_info": previous_hold_info
            }
        }

    except Exception as e:
        # Log technical details
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Resume inspection failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Resume Inspection Error")
        except Exception:
            pass

        # Determine user-friendly error message
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection was not found"
            error_code = "INSPECTION_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to modify this inspection"
            error_code = "PERMISSION_DENIED"
        else:
            user_message = "An error occurred while resuming the inspection"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your request and try again"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

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
            # Use actual_length_m which is set by mobile API, fallback to roll_length
            length = flt(roll.actual_length_m or roll.roll_length or 0)
            total += length
    return total

def calculate_average_points_per_100_sqm(inspection):
    """Calculate average points per 100 square meters"""
    total_points = 0
    total_area = 0

    for roll in inspection.fabric_rolls_tab or []:
        if roll.inspected:
            points = flt(roll.points_per_100_sqm or 0)
            # Use actual_length_m which is set by mobile API, fallback to roll_length
            length = flt(roll.actual_length_m or roll.roll_length or 0)
            width = flt(roll.actual_width_m or roll.roll_width or 1.5)  # Default 1.5m width
            area = length * width / 100  # Convert to 100 sqm units
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
    elif inspection.inspection_type == "Custom Sampling":
        sample_rolls = inspection.required_sample_rolls or 0
        total_rolls = inspection.total_rolls or 0
        sampling_percent = flt(getattr(inspection, 'sampling_percentage', 0))
        return f"{sample_rolls} rolls ({total_rolls} units, {sampling_percent}% sampling)"
    else:
        return f"{inspection.total_rolls or 0} rolls (custom sampling)"

def build_roll_details(inspection):
    """Build roll details array for API response"""
    rolls = []
    for roll in inspection.fabric_rolls_tab or []:
        rolls.append({
            "roll_id": roll.name,
            "roll_number": roll.roll_number,
            "length": flt(roll.roll_length or 0),
            "width": flt(roll.roll_width or 0),
            "gsm": flt(roll.gsm or 0),
            "status": "Inspected" if roll.inspected else "Pending",
            "result": roll.roll_result or "Pending",
            "autopicked": bool(getattr(roll, 'autopicked', 0))
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

def calculate_sample_size_based_on_uom(inspection):
    """
    Calculate sample_size_to_be_inspected based on AQL logic and UOM
    Returns: "19kg" or "25 Meter" based on UOM
    """
    try:
        if inspection.inspection_type == "AQL Based":
            # Use required_sample_meters from AQL calculation
            sample_amount = flt(getattr(inspection, 'required_sample_meters', 0))

            # If no AQL sample meters calculated, fallback to autopicked quantity
            if not sample_amount:
                sample_amount = calculate_autopicked_quantity(inspection)

            unit_of_measure = getattr(inspection, 'unit_of_measure', None)

            if unit_of_measure in ["Kilogram", "Kg", "kg", "KG"]:
                return f"{sample_amount:.0f}kg"
            elif unit_of_measure in ["Meter", "Metre", "m", "M"]:
                return f"{sample_amount:.0f} Meter"
            else:
                return f"{sample_amount:.2f} {unit_of_measure or ''}".strip()

        elif inspection.inspection_type == "100% Inspection":
            total_quantity = flt(inspection.total_quantity or 0)
            unit_display = standardize_uom_display(getattr(inspection, 'unit_of_measure', None))
            return f"{total_quantity:.0f}{unit_display}"

        else:
            # Custom sampling - calculate from autopicked rolls
            autopicked_quantity = calculate_autopicked_quantity(inspection)
            unit_display = standardize_uom_display(getattr(inspection, 'unit_of_measure', None))
            return f"{autopicked_quantity:.0f}{unit_display}"

    except Exception as e:
        # Fallback to basic display
        frappe.log_error(f"Error calculating sample size: {str(e)}")
        return "0 units"

def standardize_uom_display(unit_of_measure):
    """
    Standardize UOM display for mobile
    """
    if not unit_of_measure:
        return ""

    mapping = {
        "Kilogram": "kg", "Kg": "kg", "KG": "kg", "kg": "kg",
        "Meter": " Meter", "Metre": " Meter", "M": " Meter", "m": " Meter",
        "Piece": " pcs", "Pieces": " pcs", "PCS": " pcs", "pcs": " pcs"
    }
    return mapping.get(unit_of_measure, f" {unit_of_measure}")

def calculate_autopicked_quantity(inspection):
    """
    Calculate total quantity from autopicked rolls
    """
    total = 0
    for roll in inspection.fabric_rolls_tab or []:
        if getattr(roll, 'autopicked', 0):
            total += flt(getattr(roll, 'roll_length', 0))
    return total

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
def save_roll_details(inspection_id=None, roll_id=None, roll_data=None):
    """
    Save roll details including roll information and defects
    Uses in-memory child table appending to avoid data loss from parent.save() overwrites
    """
    try:
        # Validate required parameters with industry-standard error responses
        validation_errors = []

        if not inspection_id:
            validation_errors.append({
                "field": "inspection_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Inspection ID is required"
            })

        if not roll_id:
            validation_errors.append({
                "field": "roll_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Roll ID is required"
            })

        if not roll_data:
            validation_errors.append({
                "field": "roll_data",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Roll data is required"
            })

        if validation_errors:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Required parameters are missing",
                    "details": "Please provide all required parameters for saving roll details",
                    "validation_errors": validation_errors
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }

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
            "inspected_shade", "actual_shade", "roll_length", "roll_width", "gsm", "roll_remarks"
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

            # Ensure master data exists
            get_or_create_defect_master(defect_name, defect_type)
            get_or_create_defect_category(category_name)

            # Build defect dict for child table
            defect_dict = {
                "defect": defect_name,
                "category": category_name,
                "defect_type": defect_type,
                "size": size
                # points_auto will be calculated automatically in fabric_roll_inspection_defect.py
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
            # points_auto will be calculated automatically in validate() method
            defect_doc.insert(ignore_permissions=True)

        # Mark inspected and save parent without triggering child updates
        if not roll_item.inspected:
            roll_item.inspected = 1

        # Trigger calculations after defects are inserted
        roll_item.calculate_total_points()
        roll_item.calculate_total_size()
        roll_item.calculate_points_per_100_sqm()

        # Save the calculated values and roll_remarks to the database
        frappe.db.set_value("Fabric Roll Inspection Item", roll_item.name, {
            "total_points_auto": roll_item.total_points_auto,
            "total_defect_points": roll_item.total_defect_points,
            "total_size_inches": roll_item.total_size_inches,
            "points_per_100_sqm": roll_item.points_per_100_sqm,
            "roll_remarks": roll_item.roll_remarks
        })

        # Update parent document fields only
        inspection._preserve_mobile_defects = True
        inspection.save(ignore_permissions=True)

        # Calculate roll grades without overwriting defects
        inspection.calculate_roll_grades_only()

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
        # Log technical details for internal debugging
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Save roll details failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Save Roll Details Error")
        except Exception:
            # If logging fails, continue without logging
            pass

        # Determine user-friendly error message based on exception type
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection or roll was not found"
            error_code = "RESOURCE_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to modify this inspection"
            error_code = "PERMISSION_DENIED"
        elif "invalid" in str(e).lower() or "json" in str(e).lower():
            user_message = "The provided roll data format is invalid"
            error_code = "INVALID_DATA_FORMAT"
        else:
            user_message = "An error occurred while saving roll details"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your data and try again, or contact support if the issue persists"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "roll_id": roll_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

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
        try:
            frappe.log_error(f"Get defect categories failed: {str(e)[:100]}", title="Get Defect Categories Error")
        except Exception:
            pass

        return {
            "success": False,
            "error": {
                "code": "DATA_FETCH_ERROR",
                "message": "Unable to load defect categories",
                "details": "Please try again or contact support if the issue persists"
            },
            "timestamp": frappe.utils.now(),
            "data": None
        }

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
# AUTHENTICATION APIs
# ===========================

@frappe.whitelist(allow_guest=True)
def mobile_login(usr, pwd):
    """Enhanced login API that includes user roles and permissions"""
    try:
        # Attempt login using Frappe's standard authentication
        frappe.local.login_manager.authenticate(user=usr, pwd=pwd)
        frappe.local.login_manager.post_login()

        # Get user document
        user_doc = frappe.get_doc("User", frappe.session.user)

        # Get user roles
        user_roles = frappe.get_roles(frappe.session.user)

        # Get user permissions relevant to fabric inspection
        permissions = {
            "can_create_inspection": "Quality Inspector" in user_roles or "Administrator" in user_roles,
            "can_submit_inspection": "Quality Inspector" in user_roles or "Administrator" in user_roles,
            "can_override_rejection": "Quality Manager" in user_roles or "Administrator" in user_roles,
            "can_approve_hold": "Quality Manager" in user_roles or "Administrator" in user_roles,
            "is_administrator": "Administrator" in user_roles
        }

        # Get user profile information
        user_profile = {
            "full_name": user_doc.full_name or user_doc.name,
            "email": user_doc.email,
            "user_image": user_doc.user_image,
            "mobile_no": user_doc.mobile_no,
            "enabled": user_doc.enabled
        }

        # Build response
        response = {
            "success": True,
            "message": "Login successful",
            "data": {
                "user": {
                    "name": frappe.session.user,
                    "profile": user_profile,
                    "roles": user_roles,
                    "permissions": permissions
                },
                "session": {
                    "sid": frappe.session.sid,
                    "session_expiry": frappe.utils.add_days(frappe.utils.now(), 7).isoformat(),
                    "csrf_token": frappe.sessions.get_csrf_token() if hasattr(frappe.sessions, 'get_csrf_token') else None
                },
                "app_config": {
                    "base_url": frappe.utils.get_url(),
                    "api_version": "mobile_v1",
                    "server_time": frappe.utils.now()
                }
            }
        }

        return response

    except frappe.exceptions.AuthenticationError:
        return {
            "success": False,
            "message": "Invalid username or password",
            "error_type": "authentication_failed"
        }
    except Exception as e:
        frappe.log_error(f"Mobile login error: {str(e)}", title="Mobile Login Error")
        return {
            "success": False,
            "message": "Login failed due to server error",
            "error_type": "server_error",
            "error_details": str(e) if frappe.conf.get("developer_mode") else None
        }

@frappe.whitelist()
def get_user_info():
    """Get current user information including roles and permissions"""
    try:
        # Get user document
        user_doc = frappe.get_doc("User", frappe.session.user)

        # Get user roles
        user_roles = frappe.get_roles(frappe.session.user)

        # Get user permissions relevant to fabric inspection
        permissions = {
            "can_create_inspection": "Quality Inspector" in user_roles or "Administrator" in user_roles,
            "can_submit_inspection": "Quality Inspector" in user_roles or "Administrator" in user_roles,
            "can_override_rejection": "Quality Manager" in user_roles or "Administrator" in user_roles,
            "can_approve_hold": "Quality Manager" in user_roles or "Administrator" in user_roles,
            "is_administrator": "Administrator" in user_roles
        }

        # Get user profile information
        user_profile = {
            "full_name": user_doc.full_name or user_doc.name,
            "email": user_doc.email,
            "user_image": user_doc.user_image,
            "mobile_no": user_doc.mobile_no,
            "enabled": user_doc.enabled
        }

        return {
            "success": True,
            "data": {
                "user": {
                    "name": frappe.session.user,
                    "profile": user_profile,
                    "roles": user_roles,
                    "permissions": permissions
                },
                "session": {
                    "sid": frappe.session.sid,
                    "server_time": frappe.utils.now()
                }
            }
        }

    except Exception as e:
        frappe.log_error(f"Get user info error: {str(e)}", title="User Info Error")
        return {
            "success": False,
            "message": "Failed to get user information",
            "error_details": str(e)
        }

@frappe.whitelist()
def refresh_user_session():
    """Refresh user session and get updated information"""
    try:
        # Validate current session
        if frappe.session.user == "Guest":
            return {
                "success": False,
                "message": "No active session found",
                "error_type": "session_expired"
            }

        # Get fresh user information
        return get_user_info()

    except Exception as e:
        frappe.log_error(f"Session refresh error: {str(e)}", title="Session Refresh Error")
        return {
            "success": False,
            "message": "Failed to refresh session",
            "error_details": str(e)
        }

# ===========================
# QUALITY INSPECTOR & MANAGER SUBMIT APIs
# ===========================

@frappe.whitelist()
def quality_inspector_submit(inspection_id=None, final_remarks=None):
    """Quality Inspector Submit API - handles both Accepted and Rejected inspections"""
    try:
        # Validate required parameters with industry-standard error responses
        validation_errors = []

        if not inspection_id:
            validation_errors.append({
                "field": "inspection_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Inspection ID is required"
            })

        if validation_errors:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Required parameters are missing",
                    "details": "Please provide all required parameters for Quality Inspector submission",
                    "validation_errors": validation_errors
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }
        # Get inspection document
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to submit this inspection"))

        # Check if already submitted
        if inspection.docstatus == 1:
            return {
                "success": False,
                "message": "Inspection is already submitted",
                "data": {
                    "inspection_status": inspection.inspection_status,
                    "docstatus": inspection.docstatus
                }
            }

        # Perform pre-submission validation
        validation_result = inspection.validate_inspection_completion_inline()

        if not validation_result.get('valid', False):
            errors = validation_result.get('errors', [])
            return {
                "success": False,
                "message": "Inspection validation failed",
                "errors": errors,
                "data": {
                    "inspection_status": inspection.inspection_status,
                    "validation_errors": errors
                }
            }

        # Add final remarks if provided
        if final_remarks:
            existing_remarks = inspection.remarks or ''
            timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            new_remark = f"[{timestamp}] Quality Inspector Final Remarks: {final_remarks}"

            if existing_remarks:
                inspection.remarks = f"{existing_remarks}\n{new_remark}"
            else:
                inspection.remarks = new_remark

        # Check inspection result and handle accordingly
        inspection_result = inspection.inspection_result

        if inspection_result == 'Accepted':
            # Case 1: Accepted - Submit and create Purchase Receipt
            inspection.inspection_status = 'Accepted'
            inspection.submitted_by = frappe.session.user
            inspection.submitted_date = frappe.utils.now()

            # Save and submit the document
            inspection.save()
            inspection.submit()

            # Create Purchase Receipt
            try:
                purchase_receipt_result = create_purchase_receipt_from_inspection_mobile(inspection)

                return {
                    "success": True,
                    "message": "Inspection submitted successfully and Purchase Receipt created",
                    "data": {
                        "inspection_id": inspection.name,
                        "inspection_status": inspection.inspection_status,
                        "docstatus": inspection.docstatus,
                        "inspection_result": inspection.inspection_result,
                        "purchase_receipt_created": True,
                        "purchase_receipt_name": purchase_receipt_result['name'],
                        "purchase_receipt_url": f"/app/purchase-receipt/{purchase_receipt_result['name']}"
                    }
                }
            except Exception as pr_error:
                frappe.log_error(f"Error creating Purchase Receipt: {str(pr_error)}")
                return {
                    "success": True,
                    "message": "Inspection submitted successfully but Purchase Receipt creation failed",
                    "data": {
                        "inspection_id": inspection.name,
                        "inspection_status": inspection.inspection_status,
                        "docstatus": inspection.docstatus,
                        "inspection_result": inspection.inspection_result,
                        "purchase_receipt_created": False,
                        "error": str(pr_error)
                    }
                }

        elif inspection_result == 'Rejected':
            # Case 2: Rejected - Change status to Rejected (no submission)
            inspection.inspection_status = 'Rejected'
            # Add rejection info to remarks instead of non-existent fields
            timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            rejection_note = f"[{timestamp}] Inspection rejected by Quality Inspector: {frappe.session.user}"

            existing_remarks = inspection.remarks or ''
            if existing_remarks:
                inspection.remarks = f"{existing_remarks}\n{rejection_note}"
            else:
                inspection.remarks = rejection_note

            # Save without submitting
            inspection.save()

            return {
                "success": True,
                "message": "Inspection marked as rejected",
                "data": {
                    "inspection_id": inspection.name,
                    "inspection_status": inspection.inspection_status,
                    "docstatus": inspection.docstatus,
                    "inspection_result": inspection.inspection_result,
                    "purchase_receipt_created": False,
                    "requires_manager_review": True
                }
            }

        else:
            # Case 3: Other statuses - not ready for submission
            return {
                "success": False,
                "message": f"Cannot submit inspection with result: {inspection_result}",
                "data": {
                    "inspection_id": inspection.name,
                    "inspection_status": inspection.inspection_status,
                    "inspection_result": inspection_result,
                    "error": "Inspection result must be 'Accepted' or 'Rejected' for Quality Inspector submission"
                }
            }

    except Exception as e:
        # Log technical details for internal debugging
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Quality Inspector submit failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Quality Inspector Submit Error")
        except Exception:
            # If logging fails, continue without logging
            pass

        # Determine user-friendly error message based on exception type
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection was not found"
            error_code = "INSPECTION_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to perform this action"
            error_code = "PERMISSION_DENIED"
        elif "already" in str(e).lower():
            user_message = "This inspection has already been processed"
            error_code = "ALREADY_PROCESSED"
        else:
            user_message = "An error occurred while processing your request"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your request and try again, or contact support if the issue persists"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

@frappe.whitelist()
def quality_manager_submit(inspection_id=None, manager_reason=None):
    """Quality Manager Submit API - handles Rejected inspections with conditional acceptance"""
    try:
        # Validate required parameters with industry-standard error responses
        validation_errors = []

        if not inspection_id:
            validation_errors.append({
                "field": "inspection_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Inspection ID is required"
            })

        if not manager_reason or not str(manager_reason).strip():
            validation_errors.append({
                "field": "manager_reason",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Manager reason is required for quality decisions"
            })

        if validation_errors:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Required parameters are missing",
                    "details": "Please provide all required parameters for Quality Manager submission",
                    "validation_errors": validation_errors
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }

        # Get inspection document
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to submit this inspection"))

        # Verify user has Quality Manager role
        user_roles = frappe.get_roles(frappe.session.user)
        if "Quality Manager" not in user_roles and "Administrator" not in user_roles:
            return {
                "success": False,
                "message": "Only Quality Managers can perform this action",
                "data": {"inspection_id": inspection_id}
            }

        # Check if inspection is in the correct state for manager override
        if inspection.inspection_result != 'Rejected' or inspection.inspection_status != 'Rejected':
            return {
                "success": False,
                "message": "Quality Manager can only submit inspections that are in 'Rejected' status",
                "data": {
                    "inspection_id": inspection_id,
                    "current_result": inspection.inspection_result,
                    "current_status": inspection.inspection_status,
                    "error": "Inspection must be rejected by Quality Inspector first"
                }
            }

        # Check if already submitted
        if inspection.docstatus == 1:
            return {
                "success": False,
                "message": "Inspection is already submitted",
                "data": {
                    "inspection_status": inspection.inspection_status,
                    "docstatus": inspection.docstatus
                }
            }

        # Add manager override reason
        timestamp = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        manager_override_note = f"[{timestamp}] Quality Manager Override by {frappe.session.user}: {manager_reason}"

        existing_remarks = inspection.manager_remarks or ''
        if existing_remarks:
            inspection.manager_remarks = f"{existing_remarks}\n{manager_override_note}"
        else:
            inspection.manager_remarks = manager_override_note

        # Change inspection result to Conditional Accept
        inspection.inspection_result = 'Conditional Accept'
        inspection.inspection_status = 'Conditional Accept'

        # Set manager approval fields
        inspection.approval_timestamp = frappe.utils.now()
        inspection.submitted_by = frappe.session.user
        inspection.submitted_date = frappe.utils.now()

        # Save and submit the document
        inspection.save()
        inspection.submit()

        # Create Purchase Receipt
        try:
            purchase_receipt_result = create_purchase_receipt_from_inspection_mobile(inspection)

            return {
                "success": True,
                "message": "Inspection conditionally accepted by Quality Manager and Purchase Receipt created",
                "data": {
                    "inspection_id": inspection.name,
                    "inspection_status": inspection.inspection_status,
                    "docstatus": inspection.docstatus,
                    "inspection_result": inspection.inspection_result,
                    "manager_reason": manager_reason,
                    "purchase_receipt_created": True,
                    "purchase_receipt_name": purchase_receipt_result['name'],
                    "purchase_receipt_url": f"/app/purchase-receipt/{purchase_receipt_result['name']}"
                }
            }
        except Exception as pr_error:
            frappe.log_error(f"Error creating Purchase Receipt for manager submission: {str(pr_error)}")
            return {
                "success": True,
                "message": "Inspection conditionally accepted but Purchase Receipt creation failed",
                "data": {
                    "inspection_id": inspection.name,
                    "inspection_status": inspection.inspection_status,
                    "docstatus": inspection.docstatus,
                    "inspection_result": inspection.inspection_result,
                    "manager_reason": manager_reason,
                    "purchase_receipt_created": False,
                    "error": str(pr_error)
                }
            }

    except Exception as e:
        # Log technical details for internal debugging
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Quality Manager submit failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Quality Manager Submit Error")
        except Exception:
            # If logging fails, continue without logging
            pass

        # Determine user-friendly error message based on exception type
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection was not found"
            error_code = "INSPECTION_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to perform this action"
            error_code = "PERMISSION_DENIED"
        elif "already" in str(e).lower():
            user_message = "This inspection has already been processed"
            error_code = "ALREADY_PROCESSED"
        else:
            user_message = "An error occurred while processing your request"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your request and try again, or contact support if the issue persists"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

def create_purchase_receipt_from_inspection_mobile(inspection_doc):
    """Create Purchase Receipt from fabric inspection for mobile API"""
    # Use our own self-contained implementation
    return create_purchase_receipt_mobile(inspection_doc)

def create_purchase_receipt_mobile(inspection_doc):
    """Create Purchase Receipt from fabric inspection - self-contained implementation"""
    try:
        # Get the linked GRN
        if not inspection_doc.grn_reference:
            frappe.throw(_("No GRN reference found in inspection"))

        grn_doc = frappe.get_doc("Goods Receipt Note", inspection_doc.grn_reference)

        # Create new Purchase Receipt
        purchase_receipt = frappe.new_doc("Purchase Receipt")

        # Set basic details from GRN and inspection
        purchase_receipt.supplier = grn_doc.supplier
        purchase_receipt.supplier_name = getattr(grn_doc, 'supplier_name', grn_doc.supplier)
        purchase_receipt.company = getattr(grn_doc, 'company', frappe.defaults.get_user_default("Company"))
        purchase_receipt.set_warehouse = getattr(grn_doc, 'set_warehouse', None)
        purchase_receipt.posting_date = frappe.utils.getdate()
        purchase_receipt.posting_time = frappe.utils.nowtime()
        purchase_receipt.set_posting_time = 1

        # Add currency and price list from GRN if available
        if hasattr(grn_doc, 'currency'):
            purchase_receipt.currency = grn_doc.currency
        if hasattr(grn_doc, 'buying_price_list'):
            purchase_receipt.buying_price_list = grn_doc.buying_price_list

        # Add reference fields using correct custom field names
        purchase_receipt.linked_inspection = inspection_doc.name
        purchase_receipt.linked_grn = inspection_doc.grn_reference

        # Add inspection summary in remarks
        inspection_summary = f"Created from Fabric Inspection: {inspection_doc.name} | " \
                           f"Result: {inspection_doc.inspection_result} | " \
                           f"Grade: {inspection_doc.quality_grade or 'N/A'} | " \
                           f"Inspector: {inspection_doc.inspector or 'N/A'}"
        purchase_receipt.remarks = inspection_summary

        # Generate unique purchase receipt number for mandatory field
        timestamp = frappe.utils.now_datetime().strftime("%Y%m%d%H%M%S")
        generated_pr_no = f"PR-INSP-{inspection_doc.name}-{timestamp}"
        purchase_receipt.custom_purchase_receipt_no = generated_pr_no

        # Process fabric rolls and create PR items
        fabric_rolls = inspection_doc.get('fabric_rolls_tab', [])
        total_accepted_qty = 0
        total_accepted_amount = 0
        pr_items_created = 0

        # Get accepted/conditional rolls for processing
        accepted_results = ['First Quality', 'Accepted', 'Conditional Accept']

        for roll in fabric_rolls:
            roll_result = getattr(roll, 'roll_result', '')
            roll_number = getattr(roll, 'roll_number', 'N/A')

            if roll_result in accepted_results:
                # Find corresponding item in GRN
                grn_item = None
                for grn_item_row in grn_doc.get('items', []):
                    if grn_item_row.item_code == inspection_doc.item_code:
                        grn_item = grn_item_row
                        break

                if grn_item:
                    # Get item details from Item master since GRN item has limited fields
                    item_doc = frappe.get_doc("Item", grn_item.item_code)

                    # Calculate quantities - use roll length as quantity
                    received_qty = flt(getattr(roll, 'roll_length', 1)) or 1
                    # For now use a default rate since GRN item doesn't have rate
                    rate = 0  # Will be filled manually in PR
                    amount = received_qty * rate

                    # Create detailed inspection remarks for this roll
                    roll_remarks = f"Roll {roll_number}: Grade {getattr(roll, 'roll_grade', 'N/A')}, " \
                                 f"Defect Points: {flt(getattr(roll, 'total_defect_points', 0))}, " \
                                 f"Points/100sqm: {flt(getattr(roll, 'points_per_100_sqm', 0)):.2f}, " \
                                 f"Result: {roll_result}"

                    # Append item to Purchase Receipt
                    pr_item = purchase_receipt.append('items', {
                        'item_code': grn_item.item_code,
                        'item_name': item_doc.item_name,
                        'description': item_doc.description or item_doc.item_name,
                        'qty': received_qty,
                        'uom': item_doc.stock_uom,
                        'rate': rate,
                        'amount': amount,
                        'warehouse': getattr(grn_item, 'selected_warehouse', purchase_receipt.set_warehouse),
                        'project': None,  # GRN doesn't have project field
                        'cost_center': None  # GRN doesn't have cost_center field
                    })

                    # Add custom fields if they exist in the Purchase Receipt Item doctype
                    if hasattr(pr_item, 'inspection_remarks'):
                        pr_item.inspection_remarks = roll_remarks
                    if hasattr(pr_item, 'roll_number'):
                        pr_item.roll_number = roll_number
                    if hasattr(pr_item, 'fabric_grade'):
                        pr_item.fabric_grade = getattr(roll, 'roll_grade', '')
                    if hasattr(pr_item, 'inspection_result'):
                        pr_item.inspection_result = roll_result

                    total_accepted_qty += received_qty
                    total_accepted_amount += amount
                    pr_items_created += 1

                    frappe.logger().info(f"Added roll {roll_number} to Purchase Receipt: qty={received_qty}, amount={amount}")

        # If no specific rolls were accepted, create a consolidated item
        if pr_items_created == 0:
            # Get the first matching GRN item as template
            grn_item = None
            for grn_item_row in grn_doc.get('items', []):
                if grn_item_row.item_code == inspection_doc.item_code:
                    grn_item = grn_item_row
                    break

            if grn_item:
                # Get item details from Item master
                item_doc = frappe.get_doc("Item", grn_item.item_code)

                # Use total quantity from inspection or default to 1
                total_qty = flt(inspection_doc.total_quantity) or 1
                rate = 0  # Default rate - will be filled manually
                amount = total_qty * rate

                consolidated_remarks = f"Consolidated item from Inspection {inspection_doc.name}: " \
                                     f"Result {inspection_doc.inspection_result}, " \
                                     f"Total Rolls: {len(fabric_rolls)}"

                pr_item = purchase_receipt.append('items', {
                    'item_code': inspection_doc.item_code,
                    'item_name': item_doc.item_name,
                    'description': f"Fabric from inspection {inspection_doc.name}",
                    'qty': total_qty,
                    'uom': item_doc.stock_uom,
                    'rate': rate,
                    'amount': amount,
                    'warehouse': purchase_receipt.set_warehouse,
                    'project': None,  # GRN doesn't have project field
                    'cost_center': None  # GRN doesn't have cost_center field
                })

                # Add custom fields
                if hasattr(pr_item, 'inspection_remarks'):
                    pr_item.inspection_remarks = consolidated_remarks
                if hasattr(pr_item, 'inspection_result'):
                    pr_item.inspection_result = inspection_doc.inspection_result

                total_accepted_qty = total_qty
                total_accepted_amount = amount
                pr_items_created = 1

        # Validate that we have at least one item
        if not purchase_receipt.items:
            frappe.throw(_("No items could be created for Purchase Receipt. Please check the inspection data."))

        # Save Purchase Receipt in draft status
        purchase_receipt.save()

        # Log success
        frappe.logger().info(f"Successfully created Purchase Receipt {purchase_receipt.name} from inspection {inspection_doc.name}: "
                           f"{pr_items_created} items, total qty: {total_accepted_qty}")

        return {
            'name': purchase_receipt.name,
            'status': 'Draft',
            'total_qty': total_accepted_qty,
            'total_amount': total_accepted_amount,
            'items_count': pr_items_created,
            'docstatus': purchase_receipt.docstatus
        }

    except Exception as e:
        # Create shorter error message for logging to avoid length issues
        short_error = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        error_msg = f"PR creation failed for {inspection_doc.name}: {short_error}"

        try:
            frappe.log_error(error_msg, title="Purchase Receipt Creation Error")
        except Exception:
            # If logging fails, continue without logging
            pass

        # Raise a shorter exception message
        raise Exception(f"Error creating Purchase Receipt: {str(e)}")

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
        "autopicked": bool(getattr(roll, 'autopicked', 0)),

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
        "result": roll.roll_result or "Pending",
        "autopicked": bool(getattr(roll, 'autopicked', 0))
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

# ===========================
# AUTOPICK ROLL MANAGEMENT APIs
# ===========================

@frappe.whitelist()
def toggle_roll_autopick(inspection_id=None, roll_id=None, autopicked=None):
    """
    Toggle or set autopicked flag for a specific roll
    Allows manual override of AQL-based auto-selection
    """
    try:
        # Validate required parameters
        validation_errors = []

        if not inspection_id:
            validation_errors.append({
                "field": "inspection_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Inspection ID is required"
            })

        if not roll_id:
            validation_errors.append({
                "field": "roll_id",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Roll ID is required"
            })

        if autopicked is None:
            validation_errors.append({
                "field": "autopicked",
                "code": "MISSING_REQUIRED_PARAMETER",
                "message": "Autopicked flag value is required"
            })

        if validation_errors:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Required parameters are missing",
                    "details": "Please provide all required parameters",
                    "validation_errors": validation_errors
                },
                "timestamp": frappe.utils.now(),
                "data": None
            }

        # Get inspection document
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check permissions
        if not inspection.has_permission("write"):
            frappe.throw(_("You do not have permission to modify this inspection"))

        # Find the roll
        roll_item = None
        for roll in inspection.fabric_rolls_tab or []:
            if roll.name == roll_id or getattr(roll, 'roll_number', '') == roll_id:
                roll_item = roll
                break

        if not roll_item:
            return {
                "success": False,
                "error": {
                    "code": "ROLL_NOT_FOUND",
                    "message": f"Roll with ID '{roll_id}' not found in inspection",
                    "details": f"Available rolls: {len(inspection.fabric_rolls_tab or [])}"
                },
                "timestamp": frappe.utils.now()
            }

        # Update autopicked flag
        previous_value = getattr(roll_item, 'autopicked', 0)
        roll_item.autopicked = 1 if autopicked else 0

        # Save the inspection
        inspection.save()

        return {
            "success": True,
            "message": f"Roll autopick flag updated successfully",
            "data": {
                "inspection_id": inspection_id,
                "roll_id": roll_item.name,
                "roll_number": roll_item.roll_number,
                "previous_autopicked": bool(previous_value),
                "current_autopicked": bool(roll_item.autopicked),
                "action": "enabled" if roll_item.autopicked else "disabled"
            }
        }

    except Exception as e:
        # Log technical details
        short_error = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        error_msg = f"Toggle roll autopick failed: {short_error}"

        try:
            frappe.log_error(error_msg, title="Toggle Roll Autopick Error")
        except Exception:
            pass

        # Determine user-friendly error message
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            user_message = "The specified inspection or roll was not found"
            error_code = "RESOURCE_NOT_FOUND"
        elif "permission" in str(e).lower():
            user_message = "You do not have permission to modify this inspection"
            error_code = "PERMISSION_DENIED"
        else:
            user_message = "An error occurred while updating roll autopick flag"
            error_code = "INTERNAL_ERROR"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": user_message,
                "details": "Please check your request and try again"
            },
            "timestamp": frappe.utils.now(),
            "data": {
                "inspection_id": inspection_id,
                "roll_id": roll_id,
                "request_id": frappe.generate_hash(length=8)
            }
        }

@frappe.whitelist()
def refresh_auto_pick(inspection_id=None):
    """
    Refresh/re-run auto-picking for an inspection
    Useful when inspection configuration changes
    """
    try:
        if not inspection_id:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Inspection ID is required",
                    "details": "Please provide a valid inspection ID"
                },
                "timestamp": frappe.utils.now()
            }

        # Import and use the roll picker API
        from erpnext_trackerx_customization.erpnext_trackerx_customization.utils.aql.roll_picker import auto_pick_rolls_for_inspection
        result = auto_pick_rolls_for_inspection(inspection_id)

        return result

    except Exception as e:
        frappe.log_error(f"Error refreshing auto-pick: {str(e)}")
        return {
            "success": False,
            "message": f"Error refreshing auto-pick: {str(e)}"
        }

@frappe.whitelist()
def force_autopick_update(inspection_id=None):
    """
    Force update autopicked flags for an existing inspection
    This is a workaround for inspections created before autopick feature
    """
    try:
        if not inspection_id:
            return {
                "success": False,
                "message": "Inspection ID is required"
            }

        # Get inspection
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        # Check if it's AQL based and has sample rolls configured
        if inspection.inspection_type != 'AQL Based' or not inspection.required_sample_rolls:
            return {
                "success": False,
                "message": f"Inspection {inspection_id} is not AQL Based or missing sample roll configuration"
            }

        # Import and use the roll picker
        from erpnext_trackerx_customization.erpnext_trackerx_customization.utils.aql.roll_picker import IntelligentRollPicker

        picker = IntelligentRollPicker(inspection)
        selected_rolls = picker.auto_pick_rolls()

        # Update all rolls
        updated_count = 0
        for roll in inspection.fabric_rolls_tab:
            if roll.name in selected_rolls:
                roll.autopicked = 1
                updated_count += 1
            else:
                roll.autopicked = 0

        # Save the inspection
        inspection.save()

        return {
            "success": True,
            "message": f"Force updated autopick flags for {inspection_id}",
            "data": {
                "inspection_id": inspection_id,
                "total_rolls": len(inspection.fabric_rolls_tab),
                "autopicked_rolls": updated_count,
                "selected_roll_ids": selected_rolls
            }
        }

    except Exception as e:
        frappe.log_error(f"Error force updating autopick: {str(e)}")
        return {
            "success": False,
            "message": f"Error force updating autopick: {str(e)}"
        }