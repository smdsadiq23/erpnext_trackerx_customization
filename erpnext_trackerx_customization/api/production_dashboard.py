import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now_datetime
import json
from datetime import datetime
from collections import defaultdict
from .mobile_utils import secure_api_call

# ===========================
# USER COMPANY DETECTION
# ===========================

def get_user_company():
    """
    Get the company associated with current logged-in user
    Priority order:
    1. Employee.company (where Employee.user_id = current_user)
    2. User Permissions on Company doctype
    3. Default company from system settings
    """
    try:
        current_user = frappe.session.user

        # Skip for System Manager and Administrator
        if current_user in ['Administrator'] or 'System Manager' in frappe.get_roles():
            frappe.log_error(f"User {current_user} has System Manager role - no company restriction", "Company Detection")
            return None  # Allow access to all companies

        # Method 1: Get company via Employee record (Primary)
        employee_company = frappe.db.get_value('Employee',
            {'user_id': current_user, 'status': 'Active'},
            'company'
        )

        if employee_company:
            frappe.log_error(f"User {current_user} found via Employee: {employee_company}", "Company Detection")
            return employee_company

        # Method 2: Get company via User Permissions (Fallback)
        user_permissions = frappe.get_all('User Permission',
            filters={
                'user': current_user,
                'allow': 'Company'
            },
            fields=['for_value']
        )

        if user_permissions:
            company = user_permissions[0].for_value
            frappe.log_error(f"User {current_user} found via User Permissions: {company}", "Company Detection")
            return company

        # Method 3: Get default company (Last resort)
        default_company = frappe.db.get_single_value('Global Defaults', 'default_company')
        if default_company:
            frappe.log_error(f"User {current_user} using default company: {default_company}", "Company Detection")
            return default_company

        # No company found
        frappe.log_error(f"No company found for user {current_user}", "Company Detection")
        return None

    except Exception as e:
        frappe.log_error(f"Error detecting company for user {frappe.session.user}: {str(e)}", "Company Detection Error")
        return None

# ===========================
# DYNAMIC OPERATIONS CONSTANTS
# ===========================

# No hardcoded mappings - completely dynamic approach
DEFAULT_OPERATION_ICONS = {
    'knit': '🧶', 'yarn': '🧶', 'stitch': '🧶',
    'wash': '🧼', 'clean': '🧼', 'rinse': '🧼',
    'cut': '✂️', 'trim': '✂️', 'slice': '✂️',
    'pack': '📦', 'box': '📦', 'ship': '📦',
    'check': '✅', 'inspect': '✅', 'quality': '✅', 'qc': '✅',
    'link': '🔗', 'attach': '🔗', 'connect': '🔗', 'join': '🔗',
    'dye': '🎨', 'color': '🎨', 'paint': '🎨',
    'iron': '🔥', 'press': '🔥', 'heat': '🔥',
    'sew': '🪡', 'stitch': '🪡', 'seam': '🪡'
}

# ===========================
# DYNAMIC OPERATION DISCOVERY
# ===========================

def extract_raw_operations_from_process_map(nodes, edges):
    """
    Extract operations exactly as defined in Process Map JSON
    Return them with their natural names and sequence - NO MAPPING
    """
    try:
        operations = []

        if not nodes:
            return []

        # Parse nodes if it's a string
        if isinstance(nodes, str):
            nodes = json.loads(nodes)
        if isinstance(edges, str):
            edges = json.loads(edges)

        # Extract operations from nodes - use exact names
        for node in nodes:
            node_data = node.get('data', {})
            node_type = node.get('type', '') or node_data.get('type', '')

            # Check if this is an operation node
            if 'operation' in node_type.lower() or node_data.get('isOperation'):
                operation_name = (
                    node_data.get('label', '') or
                    node.get('label', '') or
                    node_data.get('name', '') or
                    node.get('id', '')
                ).strip()

                if operation_name:  # Only if operation has a name
                    operations.append({
                        'id': node.get('id'),
                        'name': operation_name,  # Exact name from Process Map
                        'sequence': calculate_sequence_from_edges(node['id'], edges or []),
                        'components': node_data.get('components', []),
                        'node_data': node_data
                    })

        # Sort by sequence to maintain flow order
        operations.sort(key=lambda x: x['sequence'])

        # If no operations found but nodes exist, try to extract any labeled nodes
        if not operations and nodes:
            for idx, node in enumerate(nodes):
                label = (
                    node.get('data', {}).get('label', '') or
                    node.get('label', '') or
                    f"Operation {idx + 1}"
                ).strip()

                if label:
                    operations.append({
                        'id': node.get('id', f'op_{idx}'),
                        'name': label,
                        'sequence': idx,
                        'components': node.get('data', {}).get('components', []),
                        'node_data': node.get('data', {})
                    })

        return operations

    except Exception as e:
        frappe.log_error(f"Error extracting operations from process map: {str(e)}")
        return []

def calculate_sequence_from_edges(node_id, edges):
    """Calculate operation position in the workflow based on incoming edges"""
    try:
        incoming_count = 0
        for edge in edges:
            if edge.get('target') == node_id:
                incoming_count += 1
        return incoming_count
    except:
        return 0

def generate_dynamic_operations_config(operation_names):
    """
    Generate frontend configuration for any set of operations
    No predefined mapping - purely dynamic
    """
    operations_config = []

    for idx, op_name in enumerate(operation_names):
        # Generate color using hash of operation name
        color = generate_color_from_name(op_name)

        # Generate icon based on operation name keywords
        icon = generate_icon_from_name(op_name)

        config = {
            "id": idx + 1,
            "code": op_name,  # Use exact operation name as code
            "name": op_name,  # Display exact operation name
            "icon": icon,
            "color": color,
            "sequence": idx + 1,
            "isVisible": True,
            "columnWidth": calculate_dynamic_column_width(len(operation_names))
        }
        operations_config.append(config)

    return operations_config

def generate_color_from_name(operation_name):
    """Generate consistent color based on operation name hash"""
    hash_value = abs(hash(operation_name.lower())) % 360
    saturation = 65 + (hash_value % 20)  # 65-85%
    lightness = 45 + (hash_value % 15)   # 45-60%
    return f"hsl({hash_value}, {saturation}%, {lightness}%)"

def generate_icon_from_name(operation_name):
    """Generate icon based on operation name keywords"""
    name_lower = operation_name.lower()

    # Find matching icon based on keywords
    for keyword, icon in DEFAULT_OPERATION_ICONS.items():
        if keyword in name_lower:
            return icon

    # Default generic operation icon
    return '⚙️'

def calculate_dynamic_column_width(total_operations):
    """Calculate column width based on number of operations"""
    if total_operations <= 4:
        return 18
    elif total_operations <= 6:
        return 15
    elif total_operations <= 8:
        return 12
    elif total_operations <= 12:
        return 10
    else:
        return 8  # Minimum width for many operations

# ===========================
# ENHANCED WORK ORDER QUERIES
# ===========================

def get_active_work_orders_with_operations(company=None, limit=20):
    """Get active work orders with their associated style group and process map info"""
    try:
        conditions = ["wo.docstatus IN (0, 1)"]  # Include draft and submitted for testing
        values = {"limit": cint(limit) or 20}

        if company:
            conditions.append("wo.company = %(company)s")
            values["company"] = company

        where_clause = " AND ".join(conditions)

        work_orders = frappe.db.sql(f"""
            SELECT
                wo.name,
                wo.creation,
                wo.status
            FROM `tabWork Order` wo
            WHERE {where_clause}
            ORDER BY wo.creation DESC
            LIMIT %(limit)s
        """, values, as_dict=True)

        return work_orders

    except Exception as e:
        frappe.log_error(f"Error getting active work orders: {str(e)}")
        return []

def get_work_order_with_dynamic_operations(wo_name):
    """
    Enhanced version of get_detail_wo with dynamic operation discovery
    """
    try:
        if not wo_name:
            return {}

        # Simplified query focusing on Process Map operations (for testing without Sales Order requirements)
        wo_details = frappe.db.sql("""
            SELECT
                wo.name AS wo_number,
                wo.qty AS wo_quantity,
                wo.production_item,
                wo.planned_start_date,
                wo.expected_delivery_date,
                wo.creation,
                wo.status,

                -- Item & Style Info
                itm.item_name AS product_family,
                itm.custom_colour_code AS color,
                itm.custom_material_composition AS material,
                itm.custom_style_master AS style_number,
                itm.brand AS fty_client,

                -- Style Group & Process Map Info
                sm.style_group,
                pm.name as process_map_name,
                pm.nodes AS process_map_nodes,
                pm.edges AS process_map_edges

            FROM `tabWork Order` wo
                -- Join Item for style information
                INNER JOIN `tabItem` itm ON itm.name = wo.production_item
                    AND itm.custom_select_master = 'Finished Goods'

                -- Join Style Master for style group
                LEFT JOIN `tabStyle Master` sm ON sm.style_number = itm.custom_style_master

                -- Join Process Map for operations
                LEFT JOIN `tabProcess Map` pm ON pm.style_group = sm.style_group
                    AND pm.docstatus IN (0, 1)  # Include draft and submitted for testing

            WHERE wo.name = %s AND wo.docstatus IN (0, 1)  # Include draft and submitted for testing
                AND pm.name IS NOT NULL  # Only include WOs with Process Maps
        """, (wo_name,), as_dict=True)

        if not wo_details:
            return {}

        wo_detail = wo_details[0]

        # Extract operations from process map
        operations = []
        if wo_detail.process_map_nodes:
            operations = extract_raw_operations_from_process_map(
                wo_detail.process_map_nodes,
                wo_detail.process_map_edges
            )

        # Fallback to scan log operations if no process map
        if not operations:
            operations = get_operations_from_scan_logs(wo_name)

        # Get size quantities (fallback for testing without Work Order Line Items)
        size_qty_list = frappe.db.sql("""
            SELECT size, SUM(work_order_allocated_qty) AS qty
            FROM `tabWork Order Line Item`
            WHERE parent = %s
            GROUP BY size
        """, (wo_name,), as_dict=True)

        size_qty_map = {row.size or "": row.qty for row in size_qty_list}

        # Fallback: If no Work Order Line Items, use Work Order quantity or default for testing
        if not size_qty_map:
            if wo_detail.wo_quantity and wo_detail.wo_quantity > 0:
                size_qty_map = {"DEFAULT": wo_detail.wo_quantity}
            else:
                # Default quantity for testing purposes
                size_qty_map = {"DEFAULT": 100}

        sizes = list(size_qty_map.keys())

        # Calculate progress for discovered operations
        progress_data = {}
        if operations:
            progress_data = calculate_progress_for_dynamic_operations(
                wo_name, operations, size_qty_map
            )

        # Transform to dashboard format
        style_name = wo_detail.product_family or "Unknown Style"
        color = wo_detail.color or ""

        # Combine style name with color
        style_with_color = f"{style_name} - {color}" if color else style_name

        # Create description with style and color info
        description_parts = [f"Style: {wo_detail.style_number or 'N/A'}"]
        if color:
            description_parts.append(f"Colour: {color}")
        description = "\n".join(description_parts)

        dashboard_item = {
            "id": wo_detail.wo_number,
            "styleName": style_with_color,
            "description": description,
            "deliveryDate": wo_detail.expected_delivery_date or "",
            "orderQuantity": flt(wo_detail.wo_quantity),  # Add order quantity column
            "totalQuantity": flt(wo_detail.wo_quantity),  # Keep for compatibility
            "operations": operations,
            "progress": progress_data,
            "process_map": wo_detail.process_map_name or "No Process Map"
        }

        return dashboard_item

    except Exception as e:
        frappe.log_error(f"Error getting work order details for {wo_name}: {str(e)}")
        return {}

def get_operations_from_scan_logs(wo_name):
    """Fallback: Get operations from existing scan logs if no process map"""
    try:
        scan_operations = frappe.db.sql("""
            SELECT DISTINCT isl.operation
            FROM `tabTracking Order Bundle Configuration` tbc
                INNER JOIN `tabTracking Order` tor ON tor.name = tbc.parent
                INNER JOIN `tabProduction Item` pi
                    ON pi.tracking_order = tor.name
                    AND pi.bundle_configuration = tbc.name
                INNER JOIN `tabItem Scan Log` isl
                    ON isl.production_item = pi.name
            WHERE tbc.work_order = %s
                AND tbc.parentfield = 'component_bundle_configurations'
                AND tbc.activation_status = 'Completed'
                AND isl.operation IS NOT NULL
                AND isl.operation != ''
            ORDER BY isl.operation
        """, (wo_name,), as_dict=True)

        operations = []
        for idx, row in enumerate(scan_operations):
            operations.append({
                'id': f'fallback_{idx}',
                'name': row.operation,
                'sequence': idx,
                'components': [],
                'node_data': {}
            })

        return operations

    except Exception as e:
        frappe.log_error(f"Error getting fallback operations for {wo_name}: {str(e)}")
        return []

def calculate_progress_for_dynamic_operations(wo_name, operations_list, size_qty_map):
    """
    Calculate progress for any set of operations - no mapping required
    """
    try:
        if not operations_list:
            return {}

        # Get operation names exactly as they are
        operation_names = [op['name'] for op in operations_list]

        # Get scan logs for these specific operations
        scan_logs = frappe.db.sql("""
            SELECT
                isl.operation,
                tbc.size,
                pi.quantity AS pi_qty,
                isl.status
            FROM `tabTracking Order Bundle Configuration` tbc
                INNER JOIN `tabTracking Order` tor ON tor.name = tbc.parent
                INNER JOIN `tabProduction Item` pi
                    ON pi.tracking_order = tor.name
                    AND pi.bundle_configuration = tbc.name
                INNER JOIN `tabTracking Component` tc
                    ON tc.name = pi.component AND tc.is_main = 1
                INNER JOIN `tabItem Scan Log` isl
                    ON isl.production_item = pi.name
                    AND isl.log_status = 'Completed'
                    AND isl.status IN ('Counted','Activated','Pass','QC Reject','SP Reject')
            WHERE tbc.work_order = %(wo_name)s
                AND tbc.parentfield = 'component_bundle_configurations'
                AND tbc.activation_status = 'Completed'
                AND isl.operation IN %(operations)s
        """, {
            'wo_name': wo_name,
            'operations': operation_names  # Use exact operation names
        }, as_dict=True)

        # Process scan logs by operation
        op_size_data = defaultdict(lambda: {"completed": 0, "rejected": 0})

        for log in scan_logs:
            key = (log.operation, log.size or "")
            if log.status in ('Counted', 'Activated', 'Pass'):
                op_size_data[key]["completed"] += log.pi_qty or 0
            elif log.status in ('QC Reject', 'SP Reject'):
                op_size_data[key]["rejected"] += 1

        # Calculate progress using exact operation names as keys
        progress_data = {}
        sizes = list(size_qty_map.keys())

        for operation in operations_list:
            op_name = operation['name']  # Use exact operation name

            total_completed = 0
            total_rejected = 0
            total_qty = sum(size_qty_map.values())

            # Sum across all sizes for this operation
            for size in sizes:
                key = (op_name, size)
                total_completed += op_size_data[key]["completed"]
                total_rejected += op_size_data[key]["rejected"]

            # Calculate metrics
            completion_pct = min((total_completed / total_qty) * 100, 100.0) if total_qty > 0 else 0.0
            pending = max(total_qty - total_completed - total_rejected, 0)

            # Determine status
            if completion_pct >= 100:
                status = 'completed'
            elif completion_pct >= 80:
                status = 'on-track'
            elif completion_pct >= 50:
                status = 'warning'
            else:
                status = 'behind'

            progress_data[op_name] = {  # Key is exact operation name
                "percentage": round(completion_pct, 1),
                "completed": total_completed,
                "rejected": total_rejected,
                "pending": pending,
                "total": total_qty,
                "status": status
            }

        return progress_data

    except Exception as e:
        frappe.log_error(f"Error calculating progress for {wo_name}: {str(e)}")
        return {}

# ===========================
# MAIN API ENDPOINTS
# ===========================

@frappe.whitelist()
@secure_api_call
def get_production_dashboard_data(company=None, limit=20):
    """
    Get dashboard data with completely dynamic operations
    Auto-detects user's company if not specified
    """
    try:
        # Auto-detect user company if not provided
        if company is None:
            company = get_user_company()
            frappe.log_error(f"Auto-detected company: {company} for user: {frappe.session.user}", "Production Dashboard")

        # Log the final company being used
        frappe.log_error(f"Fetching data for company: {company}, user: {frappe.session.user}", "Production Dashboard")

        # Get active work orders
        work_orders = get_active_work_orders_with_operations(company, limit)

        dashboard_data = []
        all_operations_discovered = set()

        for wo in work_orders:
            # Get work order details with dynamic operations
            wo_data = get_work_order_with_dynamic_operations(wo.name)

            if wo_data and wo_data.get('operations'):
                dashboard_data.append(wo_data)
                # Collect all unique operations discovered
                all_operations_discovered.update(
                    [op['name'] for op in wo_data['operations']]
                )

        # Generate dynamic operation configuration for frontend
        operations_config = generate_dynamic_operations_config(
            list(all_operations_discovered)
        )

        return {
            "success": True,
            "data": dashboard_data,
            "operations_config": operations_config,
            "total_operations": len(all_operations_discovered),
            "total_work_orders": len(dashboard_data),
            "company": company,
            "user": frappe.session.user,
            "timestamp": now_datetime().isoformat()
        }

    except Exception as e:
        frappe.log_error(f"Production Dashboard API Error: {str(e)}", frappe.get_traceback())
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "operations_config": []
        }

@frappe.whitelist()
@secure_api_call
def get_work_order_operations(wo_name):
    """
    Get operations for a specific work order
    """
    try:
        wo_data = get_work_order_with_dynamic_operations(wo_name)

        if wo_data:
            return {
                "success": True,
                "data": {
                    "work_order": wo_name,
                    "operations": wo_data.get('operations', []),
                    "progress": wo_data.get('progress', {}),
                    "process_map": wo_data.get('process_map', 'No Process Map')
                }
            }
        else:
            return {
                "success": False,
                "error": f"Work Order {wo_name} not found or no operations configured"
            }

    except Exception as e:
        frappe.log_error(f"Error getting operations for {wo_name}: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
@secure_api_call
def get_all_available_operations():
    """
    Get all unique operations across all work orders
    """
    try:
        all_operations = set()

        # Get operations from all active work orders
        work_orders = get_active_work_orders_with_operations(limit=100)

        for wo in work_orders:
            wo_data = get_work_order_with_dynamic_operations(wo.name)
            if wo_data and wo_data.get('operations'):
                all_operations.update([op['name'] for op in wo_data['operations']])

        operations_config = generate_dynamic_operations_config(list(all_operations))

        return {
            "success": True,
            "data": {
                "operations": list(all_operations),
                "operations_config": operations_config,
                "total": len(all_operations)
            }
        }

    except Exception as e:
        frappe.log_error(f"Error getting all operations: {str(e)}")
        return {"success": False, "error": str(e)}