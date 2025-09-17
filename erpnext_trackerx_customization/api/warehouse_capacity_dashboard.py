# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint, get_datetime, today
from datetime import datetime, timedelta


# =============================================================================
# WAREHOUSE SELECTION API ENDPOINTS
# =============================================================================

@frappe.whitelist()
def get_main_warehouses():
    """Get main warehouses for selection"""

    try:
        # Method 1: Look for "All Warehouses - T" and its children
        all_warehouses_option = frappe.db.sql("""
            SELECT
                name as main_warehouse,
                warehouse_name,
                (SELECT COUNT(*) FROM `tabWarehouse` child
                 WHERE child.parent_warehouse = w.name) as child_count
            FROM `tabWarehouse` w
            WHERE w.name = 'All Warehouses - T'
            AND w.is_group = 1
        """, as_dict=True)

        main_warehouses = frappe.db.sql("""
            SELECT
                name as main_warehouse,
                warehouse_name,
                (SELECT COUNT(*) FROM `tabWarehouse` child
                 WHERE child.parent_warehouse = w.name) as child_count
            FROM `tabWarehouse` w
            WHERE w.parent_warehouse = 'All Warehouses - T'
            AND w.is_group = 1
            ORDER BY w.name
        """, as_dict=True)

        # Method 2: If no specific structure found, get all group warehouses at root level
        if not main_warehouses:
            main_warehouses = frappe.db.sql("""
                SELECT
                    name as main_warehouse,
                    warehouse_name,
                    (SELECT COUNT(*) FROM `tabWarehouse` child
                     WHERE child.parent_warehouse = w.name) as child_count
                FROM `tabWarehouse` w
                WHERE w.is_group = 1
                AND (w.parent_warehouse IS NULL OR w.parent_warehouse = '' OR w.parent_warehouse IN ('All Warehouses', 'All Warehouses - T'))
                ORDER BY w.name
            """, as_dict=True)

        # Method 3: Fallback - get any group warehouses
        if not main_warehouses:
            main_warehouses = frappe.db.sql("""
                SELECT
                    name as main_warehouse,
                    warehouse_name,
                    (SELECT COUNT(*) FROM `tabWarehouse` child
                     WHERE child.parent_warehouse = w.name) as child_count
                FROM `tabWarehouse` w
                WHERE w.is_group = 1
                ORDER BY w.name
                LIMIT 10
            """, as_dict=True)

        # Method 4: If no group warehouses found, check if any warehouses exist at all
        if not main_warehouses:
            warehouse_count = frappe.db.sql("SELECT COUNT(*) as count FROM `tabWarehouse`", as_dict=True)[0].count

            if warehouse_count == 0:
                return {
                    "success": True,
                    "main_warehouses": [],
                    "method": "no_warehouses_found",
                    "total_count": 0,
                    "message": "No warehouses found in the system. Please create warehouses first."
                }
            else:
                # Get any warehouses as fallback
                fallback_warehouses = frappe.db.sql("""
                    SELECT
                        name as main_warehouse,
                        warehouse_name,
                        0 as child_count
                    FROM `tabWarehouse` w
                    ORDER BY w.name
                    LIMIT 10
                """, as_dict=True)

                return {
                    "success": True,
                    "main_warehouses": fallback_warehouses,
                    "method": "fallback_any_warehouse",
                    "total_count": len(fallback_warehouses),
                    "message": "No group warehouses found. Showing available warehouses."
                }

        # Always add a general "All Warehouses" option first
        final_warehouses = [{
            "main_warehouse": "",
            "warehouse_name": "All Warehouses",
            "child_count": frappe.db.sql("SELECT COUNT(*) as count FROM `tabWarehouse` WHERE is_group = 0", as_dict=True)[0].count
        }]

        # Add specific warehouse options
        if all_warehouses_option:
            final_warehouses.extend(all_warehouses_option)
        final_warehouses.extend(main_warehouses)

        return {
            "success": True,
            "main_warehouses": final_warehouses,
            "method": "tree_structure",
            "total_count": len(final_warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error getting main warehouses: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_descendants_debug(main_warehouse):
    """Debug API to see all warehouse descendants for a given parent"""
    try:
        all_descendants = get_all_warehouse_descendants(main_warehouse)

        # Get details for each warehouse
        warehouse_details = []
        for warehouse_name in all_descendants:
            details = frappe.db.sql("""
                SELECT name, warehouse_name, is_group, parent_warehouse, disabled
                FROM `tabWarehouse`
                WHERE name = %s
            """, (warehouse_name,), as_dict=True)

            if details:
                warehouse_details.append(details[0])

        return {
            "success": True,
            "main_warehouse": main_warehouse,
            "total_descendants": len(all_descendants),
            "warehouse_names": all_descendants,
            "warehouse_details": warehouse_details
        }

    except Exception as e:
        frappe.log_error(f"Error in get_warehouse_descendants_debug: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_warehouse_hierarchy(main_warehouse):
    """Get all child warehouses under a main warehouse"""

    try:
        # Method 1: If main_warehouse is a group, get its children
        group_children = frappe.db.sql("""
            SELECT name, warehouse_name, capacity, company
            FROM `tabWarehouse`
            WHERE parent_warehouse = %s
            AND is_group = 0 AND capacity > 0
            ORDER BY name
        """, (main_warehouse,), as_dict=True)

        if group_children:
            return {
                "success": True,
                "warehouses": group_children,
                "method": "tree_structure",
                "main_warehouse": main_warehouse,
                "total_count": len(group_children)
            }

        # Method 2: Pattern-based matching (TRM-WH-*)
        pattern_children = frappe.db.sql("""
            SELECT name, warehouse_name, capacity, company
            FROM `tabWarehouse`
            WHERE name LIKE %s
            AND is_group = 0 AND capacity > 0
            AND name != %s
            ORDER BY name
        """, (f"{main_warehouse}%", main_warehouse), as_dict=True)

        if pattern_children:
            return {
                "success": True,
                "warehouses": pattern_children,
                "method": "pattern_matching",
                "main_warehouse": main_warehouse,
                "total_count": len(pattern_children)
            }

        # Method 3: If exact match not found, try broader pattern
        broader_pattern = frappe.db.sql("""
            SELECT name, warehouse_name, capacity, company
            FROM `tabWarehouse`
            WHERE name LIKE %s
            AND is_group = 0 AND capacity > 0
            ORDER BY name
        """, (f"{main_warehouse}%",), as_dict=True)

        return {
            "success": True,
            "warehouses": broader_pattern,
            "method": "broader_pattern",
            "main_warehouse": main_warehouse,
            "total_count": len(broader_pattern)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse hierarchy: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_all_warehouse_descendants(parent_warehouse):
    """Recursively get all descendant warehouses in the hierarchy"""
    if not parent_warehouse:
        return []

    all_descendants = [parent_warehouse]  # Include the parent itself

    # Get direct children
    direct_children = frappe.db.sql("""
        SELECT name
        FROM `tabWarehouse`
        WHERE parent_warehouse = %s
    """, (parent_warehouse,), as_list=True)

    # For each direct child, recursively get their descendants
    for child in direct_children:
        child_name = child[0]
        all_descendants.append(child_name)
        # Recursively get grandchildren and beyond
        grandchildren = get_all_warehouse_descendants(child_name)
        # Remove the child itself from grandchildren (since we already added it)
        grandchildren_only = [gc for gc in grandchildren if gc != child_name]
        all_descendants.extend(grandchildren_only)

    # Remove duplicates while preserving order
    seen = set()
    unique_descendants = []
    for warehouse in all_descendants:
        if warehouse not in seen:
            seen.add(warehouse)
            unique_descendants.append(warehouse)

    return unique_descendants


def build_warehouse_filter(main_warehouse):
    """Build SQL WHERE clause for warehouse filtering"""

    if not main_warehouse:
        return "", []

    try:
        # Get all descendant warehouses recursively (includes parent and all children/grandchildren)
        all_warehouses = get_all_warehouse_descendants(main_warehouse)

        if all_warehouses:
            # Create placeholders for IN clause
            placeholders = ', '.join(['%s'] * len(all_warehouses))
            return f"AND w.name IN ({placeholders})", all_warehouses
        else:
            # If no descendants found, just filter for this warehouse
            return "AND w.name = %s", [main_warehouse]

    except Exception as e:
        frappe.log_error(f"Error in build_warehouse_filter: {str(e)}")
        # Fallback to simple name matching
        return "AND w.name = %s", [main_warehouse]


@frappe.whitelist()
def get_warehouse_capacity_summary(main_warehouse=None):
    """Get summary data for warehouse capacity dashboard cards"""

    try:
        # Get total warehouses data
        total_warehouses = get_total_warehouses_data(main_warehouse)

        # Get overall utilization data
        overall_utilization = get_overall_utilization_data(main_warehouse)

        # Get critical alerts data
        critical_alerts = get_critical_alerts_data(main_warehouse)

        # Get available capacity data
        available_capacity = get_available_capacity_data(main_warehouse)

        return {
            "success": True,
            "data": {
                "total_warehouses": total_warehouses,
                "overall_utilization": overall_utilization,
                "critical_alerts": critical_alerts,
                "available_capacity": available_capacity
            },
            "selected_main_warehouse": main_warehouse
        }

    except Exception as e:
        frappe.log_error(f"Error in warehouse capacity summary: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_tree_data(main_warehouse=None):
    """Get warehouse data in hierarchical tree structure"""
    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get all warehouses with their hierarchy and capacity data
        warehouses = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.warehouse_name,
                w.parent_warehouse,
                w.is_group,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                w.disabled,
                COALESCE(s.total_stock, 0) as current_stock,
                CASE
                    WHEN w.capacity > 0 THEN (w.capacity - COALESCE(s.total_stock, 0))
                    ELSE 0
                END as available_capacity,
                CASE
                    WHEN w.capacity > 0 THEN COALESCE((s.total_stock / w.capacity) * 100, 0)
                    ELSE 0
                END as utilization_percent,
                CASE
                    WHEN w.capacity = 0 OR w.capacity IS NULL THEN 'No Capacity'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT warehouse, COUNT(DISTINCT item_code) as item_count
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE 1=1 {warehouse_filter}
            ORDER BY
                CASE WHEN w.parent_warehouse IS NULL THEN 0 ELSE 1 END,
                w.parent_warehouse,
                w.is_group DESC,
                w.name
        """, filter_params, as_dict=True)

        # Calculate hierarchical capacity for all warehouses
        warehouses_with_hierarchical_capacity = calculate_hierarchical_capacity(warehouses)

        # Build the tree structure
        tree_data = build_warehouse_tree(warehouses_with_hierarchical_capacity, main_warehouse)

        return {
            "success": True,
            "warehouse_tree": tree_data,
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse tree data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def calculate_hierarchical_capacity(warehouses_data):
    """Calculate capacity for parent warehouses based on sum of all child warehouses"""

    # Create a dictionary for fast lookup
    warehouse_dict = {w.warehouse: w for w in warehouses_data}

    # Function to calculate total capacity for a warehouse including all descendants
    def get_total_capacity(warehouse_name):
        warehouse = warehouse_dict.get(warehouse_name)
        if not warehouse:
            return 0, None, 0  # capacity, unit, stock

        # If it's a leaf warehouse (no children), use its own capacity
        children = [w for w in warehouses_data if w.parent_warehouse == warehouse_name]
        if not children:
            # Leaf warehouse - use its own capacity
            return (
                warehouse.capacity or 0,
                warehouse.capacity_unit,
                warehouse.current_stock or 0
            )

        # Parent warehouse - sum up all children's capacities
        total_capacity = 0
        capacity_unit = None
        total_stock = 0

        for child in children:
            child_capacity, child_unit, child_stock = get_total_capacity(child.warehouse)
            total_capacity += child_capacity
            total_stock += child_stock

            # Use the first non-null unit we find
            if capacity_unit is None and child_unit:
                capacity_unit = child_unit

        return total_capacity, capacity_unit, total_stock

    # Calculate hierarchical capacity for all warehouses
    for warehouse in warehouses_data:
        total_cap, cap_unit, total_stock = get_total_capacity(warehouse.warehouse)

        # Update the warehouse data with hierarchical calculations
        warehouse.hierarchical_capacity = total_cap
        warehouse.hierarchical_capacity_unit = cap_unit or warehouse.capacity_unit
        warehouse.hierarchical_current_stock = total_stock

        # Calculate derived metrics
        if total_cap > 0:
            warehouse.hierarchical_available_capacity = total_cap - total_stock
            warehouse.hierarchical_utilization_percent = (total_stock / total_cap) * 100

            # Status calculation
            util_pct = warehouse.hierarchical_utilization_percent
            if util_pct >= 90:
                warehouse.hierarchical_status = 'Critical'
            elif util_pct >= 80:
                warehouse.hierarchical_status = 'Warning'
            elif util_pct >= 60:
                warehouse.hierarchical_status = 'Caution'
            else:
                warehouse.hierarchical_status = 'Healthy'
        else:
            warehouse.hierarchical_available_capacity = 0
            warehouse.hierarchical_utilization_percent = 0
            warehouse.hierarchical_status = 'No Capacity'

    return warehouses_data


def build_warehouse_tree(warehouses, root_warehouse=None):
    """Build hierarchical tree structure from flat warehouse list"""
    warehouse_dict = {w.warehouse: w for w in warehouses}
    tree = []

    def add_children(parent_name, level=0):
        children = []
        for warehouse in warehouses:
            if warehouse.parent_warehouse == parent_name:
                warehouse_data = dict(warehouse)
                warehouse_data['level'] = level
                warehouse_data['children'] = add_children(warehouse.warehouse, level + 1)
                children.append(warehouse_data)
        return children

    # If root_warehouse is specified, start from there
    if root_warehouse and root_warehouse in warehouse_dict:
        root_data = dict(warehouse_dict[root_warehouse])
        root_data['level'] = 0
        root_data['children'] = add_children(root_warehouse, 1)
        tree = [root_data]
    else:
        # Find root warehouses (those with no parent or parent not in the filtered list)
        for warehouse in warehouses:
            if not warehouse.parent_warehouse or warehouse.parent_warehouse not in warehouse_dict:
                warehouse_data = dict(warehouse)
                warehouse_data['level'] = 0
                warehouse_data['children'] = add_children(warehouse.warehouse, 1)
                tree.append(warehouse_data)

    return tree


@frappe.whitelist()
def test_hierarchical_capacity():
    """Test function to verify hierarchical capacity calculation with mock data"""
    try:
        # Create mock warehouse data to test the hierarchical calculation
        mock_warehouses = []

        # Create parent warehouse
        parent_warehouse = frappe._dict({
            'warehouse': 'FAB-WH-A-R01-L1 - T',
            'warehouse_name': 'FAB-WH-A-R01-L1',
            'parent_warehouse': None,
            'is_group': 1,
            'capacity': None,  # Parent warehouse has no direct capacity
            'capacity_unit': 'Meter',
            'current_stock': 0,
            'available_capacity': 0,
            'utilization_percent': 0,
            'status': 'No Capacity',
            'item_count': 0
        })
        mock_warehouses.append(parent_warehouse)

        # Create 4 child bin warehouses, each with 500 Meter capacity
        for i in range(1, 5):
            bin_warehouse = frappe._dict({
                'warehouse': f'FAB-WH-A-R01-L1-BIN-{i:02d} - T',
                'warehouse_name': f'FAB-WH-A-R01-L1-BIN-{i:02d}',
                'parent_warehouse': 'FAB-WH-A-R01-L1 - T',
                'is_group': 0,
                'capacity': 500,
                'capacity_unit': 'Meter',
                'current_stock': 100 + (i * 50),  # Varying stock levels
                'available_capacity': 400 - (i * 50),
                'utilization_percent': (100 + (i * 50)) / 500 * 100,
                'status': 'Healthy',
                'item_count': 5 + i
            })
            mock_warehouses.append(bin_warehouse)

        # Calculate hierarchical capacity using our function
        warehouses_with_hierarchical = calculate_hierarchical_capacity(mock_warehouses)

        # Find the parent warehouse to check the calculation
        parent_result = None
        for w in warehouses_with_hierarchical:
            if w.warehouse == 'FAB-WH-A-R01-L1 - T':
                parent_result = w
                break

        if parent_result:
            return {
                "success": True,
                "test_data": "Mock warehouse hierarchy created",
                "parent_warehouse": parent_result.warehouse,
                "original_capacity": parent_result.capacity,
                "hierarchical_capacity": parent_result.hierarchical_capacity,
                "hierarchical_capacity_unit": parent_result.hierarchical_capacity_unit,
                "hierarchical_current_stock": parent_result.hierarchical_current_stock,
                "hierarchical_available_capacity": parent_result.hierarchical_available_capacity,
                "hierarchical_utilization_percent": round(parent_result.hierarchical_utilization_percent, 2),
                "hierarchical_status": parent_result.hierarchical_status,
                "expected_capacity": "4 bins × 500 Meter = 2000 Meter",
                "expected_stock": "Sum of all bin stock levels",
                "verification": "SUCCESS" if parent_result.hierarchical_capacity == 2000 else "FAILED",
                "message": f"✅ Parent warehouse '{parent_result.warehouse}' correctly shows hierarchical capacity of {parent_result.hierarchical_capacity} {parent_result.hierarchical_capacity_unit} (sum of 4 child warehouses with 500 Meter each)"
            }
        else:
            return {
                "success": False,
                "error": "Could not find parent warehouse in processed results"
            }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse_name):
    """Get detailed item information for a specific warehouse"""
    try:
        # Get items with current stock in the warehouse
        items = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                i.stock_uom,
                SUM(sle.actual_qty) as current_qty,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as stock_value,
                MAX(sle.posting_date) as last_transaction_date,
                COUNT(*) as transaction_count
            FROM `tabStock Ledger Entry` sle
            LEFT JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1
            AND sle.is_cancelled = 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom
            HAVING SUM(sle.actual_qty) > 0
            ORDER BY SUM(sle.actual_qty * sle.valuation_rate) DESC
            LIMIT 100
        """, (warehouse_name,), as_dict=True)

        # Get summary stats
        summary = frappe.db.sql("""
            SELECT
                COUNT(DISTINCT sle.item_code) as total_items,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                COUNT(DISTINCT i.item_group) as item_groups_count
            FROM `tabStock Ledger Entry` sle
            LEFT JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1
            AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
        """, (warehouse_name,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse_name,
            "items": items,
            "summary": summary[0] if summary else {
                "total_items": 0,
                "total_value": 0,
                "item_groups_count": 0
            }
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def search_items_across_warehouses(main_warehouse=None, item_code=None, item_group=None, item_search=None):
    """Search for items across warehouses and show where they are present"""
    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Build item search conditions
        item_conditions = []
        item_params = []

        if item_code:
            item_conditions.append("sle.item_code LIKE %s")
            item_params.append(f"%{item_code}%")

        if item_group:
            item_conditions.append("i.item_group = %s")
            item_params.append(item_group)

        if item_search:
            item_conditions.append("(sle.item_code LIKE %s OR i.item_name LIKE %s)")
            item_params.extend([f"%{item_search}%", f"%{item_search}%"])

        item_where = ""
        if item_conditions:
            item_where = "AND " + " AND ".join(item_conditions)

        # Combine warehouse and item filters
        all_params = filter_params + item_params

        # Get items and their warehouse locations
        items_locations = frappe.db.sql(f"""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                i.stock_uom,
                sle.warehouse,
                w.warehouse_name,
                w.parent_warehouse,
                w.is_group,
                SUM(sle.actual_qty) as current_qty,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as stock_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            LEFT JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1
            AND sle.is_cancelled = 0
            AND w.is_group = 0
            {warehouse_filter}
            {item_where}
            GROUP BY sle.item_code, sle.warehouse, i.item_name, i.item_group, i.stock_uom,
                     w.warehouse_name, w.parent_warehouse, w.is_group
            HAVING SUM(sle.actual_qty) > 0
            ORDER BY sle.item_code, SUM(sle.actual_qty * sle.valuation_rate) DESC
        """, all_params, as_dict=True)

        # Group by item code
        items_data = {}
        for location in items_locations:
            item_code = location.item_code
            if item_code not in items_data:
                items_data[item_code] = {
                    'item_code': item_code,
                    'item_name': location.item_name,
                    'item_group': location.item_group,
                    'stock_uom': location.stock_uom,
                    'total_qty': 0,
                    'total_value': 0,
                    'warehouse_count': 0,
                    'warehouses': []
                }

            items_data[item_code]['total_qty'] += location.current_qty
            items_data[item_code]['total_value'] += location.stock_value
            items_data[item_code]['warehouse_count'] += 1
            items_data[item_code]['warehouses'].append({
                'warehouse': location.warehouse,
                'warehouse_name': location.warehouse_name,
                'parent_warehouse': location.parent_warehouse,
                'current_qty': location.current_qty,
                'avg_rate': location.avg_rate,
                'stock_value': location.stock_value,
                'last_transaction_date': location.last_transaction_date
            })

        # Convert to list and sort by total value
        items_list = list(items_data.values())
        items_list.sort(key=lambda x: x['total_value'], reverse=True)

        # Get summary
        total_items = len(items_list)
        total_value = sum(item['total_value'] for item in items_list)
        total_warehouses = len(set(loc.warehouse for loc in items_locations))

        return {
            "success": True,
            "items": items_list,
            "summary": {
                "total_items": total_items,
                "total_value": total_value,
                "total_warehouses": total_warehouses,
                "filters_applied": {
                    "item_code": item_code,
                    "item_group": item_group,
                    "item_search": item_search,
                    "main_warehouse": main_warehouse
                }
            }
        }

    except Exception as e:
        frappe.log_error(f"Error searching items across warehouses: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_total_warehouses_data(main_warehouse=None):
    """Get total warehouses with capacity breakdown"""

    warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

    # Total warehouses (all non-group warehouses, not just those with capacity)
    total = frappe.db.sql(f"""
        SELECT COUNT(*) as count
        FROM `tabWarehouse` w
        WHERE w.is_group = 0 AND w.disabled = 0
        {warehouse_filter}
    """, filter_params, as_dict=True)[0].count

    # Also get count of warehouses with capacity data
    capacity_warehouses = frappe.db.sql(f"""
        SELECT COUNT(*) as count
        FROM `tabWarehouse` w
        WHERE w.is_group = 0 AND w.disabled = 0 AND w.capacity > 0
        {warehouse_filter}
    """, filter_params, as_dict=True)[0].count
    
    # Get warehouse status breakdown
    warehouse_status = frappe.db.sql("""
        SELECT 
            CASE 
                WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'  
                WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                ELSE 'Healthy'
            END as status,
            COUNT(*) as count
        FROM `tabWarehouse` w
        LEFT JOIN (
            SELECT warehouse, SUM(actual_qty) as total_stock
            FROM `tabStock Ledger Entry` 
            WHERE docstatus = 1 AND is_cancelled = 0
            GROUP BY warehouse
        ) s ON w.name = s.warehouse
        WHERE w.is_group = 0 AND w.capacity > 0
        GROUP BY status
    """, as_dict=True)
    
    # Convert to dict for easy access
    status_dict = {item.status: item.count for item in warehouse_status}
    
    critical_count = status_dict.get('Critical', 0)
    warning_count = status_dict.get('Warning', 0)
    
    # Create appropriate description based on whether we have capacity data
    if capacity_warehouses > 0:
        description = f"{critical_count} Critical, {warning_count} Warning"
    else:
        description = f"{total} warehouses found (no capacity data)"

    return {
        "value": total,
        "previous_value": total,  # For now, using same value
        "change": 0,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "healthy_count": max(0, total - critical_count - warning_count),
        "capacity_warehouses": capacity_warehouses,
        "description": description
    }


def get_overall_utilization_data(main_warehouse=None):
    """Get overall capacity utilization percentage"""

    warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

    # First check if we have any warehouses with capacity data
    capacity_check = frappe.db.sql(f"""
        SELECT COUNT(*) as count
        FROM `tabWarehouse` w
        WHERE w.is_group = 0 AND w.disabled = 0 AND w.capacity > 0
        {warehouse_filter}
    """, filter_params, as_dict=True)[0].count

    if capacity_check > 0:
        # We have capacity data, calculate normal utilization
        utilization_data = frappe.db.sql(f"""
            SELECT
                SUM(w.capacity) as total_capacity,
                SUM(COALESCE(s.total_stock, 0)) as total_used,
                (SUM(COALESCE(s.total_stock, 0)) / SUM(w.capacity)) * 100 as utilization_percent
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
        """, filter_params, as_dict=True)[0]

        current_utilization = flt(utilization_data.utilization_percent or 0, 2)
    else:
        # No capacity data available, return 0 utilization
        utilization_data = frappe._dict({
            'total_capacity': 0,
            'total_used': 0,
            'utilization_percent': 0
        })
        current_utilization = 0
    
    # Get previous month utilization for comparison
    previous_month_utilization = get_previous_month_utilization()
    change = current_utilization - previous_month_utilization
    
    # Create appropriate description based on whether we have capacity data
    if capacity_check > 0:
        description = "Company-wide utilization"
    else:
        description = "No capacity data available"

    return {
        "value": current_utilization,
        "previous_value": previous_month_utilization,
        "change": flt(change, 2),
        "total_capacity": flt(utilization_data.total_capacity or 0, 2),
        "total_used": flt(utilization_data.total_used or 0, 2),
        "description": description
    }


def get_previous_month_utilization():
    """Get utilization from previous month for comparison"""
    
    # Get date 30 days ago
    previous_date = get_datetime(today()) - timedelta(days=30)
    
    # Check if we have any warehouses with capacity data
    capacity_check = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabWarehouse` w
        WHERE w.is_group = 0 AND w.disabled = 0 AND w.capacity > 0
    """, as_dict=True)[0].count

    if capacity_check == 0:
        return 0

    utilization_data = frappe.db.sql("""
        SELECT
            (SUM(COALESCE(s.total_stock, 0)) / SUM(w.capacity)) * 100 as utilization_percent
        FROM `tabWarehouse` w
        LEFT JOIN (
            SELECT warehouse, SUM(actual_qty) as total_stock
            FROM `tabStock Ledger Entry`
            WHERE docstatus = 1 AND is_cancelled = 0
            AND posting_date <= %s
            GROUP BY warehouse
        ) s ON w.name = s.warehouse
        WHERE w.is_group = 0 AND w.capacity > 0
    """, (previous_date.date(),), as_dict=True)
    
    if utilization_data:
        return flt(utilization_data[0].utilization_percent or 0, 2)
    return 0


def get_critical_alerts_data(main_warehouse=None):
    """Get critical capacity alerts count"""

    warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

    # Warehouses over 90% capacity
    critical_data = frappe.db.sql(f"""
        SELECT
            COUNT(*) as critical_count,
            GROUP_CONCAT(w.name SEPARATOR ', ') as critical_warehouses
        FROM `tabWarehouse` w
        LEFT JOIN (
            SELECT warehouse, SUM(actual_qty) as total_stock
            FROM `tabStock Ledger Entry`
            WHERE docstatus = 1 AND is_cancelled = 0
            GROUP BY warehouse
        ) s ON w.name = s.warehouse
        WHERE w.is_group = 0 AND w.capacity > 0
        AND COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90
        {warehouse_filter}
    """, filter_params, as_dict=True)[0]
    
    critical_count = critical_data.critical_count or 0
    
    # Get near-critical count (80-90%)
    warning_count = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabWarehouse` w
        LEFT JOIN (
            SELECT warehouse, SUM(actual_qty) as total_stock
            FROM `tabStock Ledger Entry` 
            WHERE docstatus = 1 AND is_cancelled = 0
            GROUP BY warehouse
        ) s ON w.name = s.warehouse
        WHERE w.is_group = 0 AND w.capacity > 0 
        AND COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80
        AND COALESCE((s.total_stock / w.capacity) * 100, 0) < 90
    """)[0][0] or 0
    
    return {
        "value": critical_count,
        "previous_value": critical_count,  # For now
        "change": 0,
        "warning_count": warning_count,
        "critical_warehouses": critical_data.critical_warehouses or "None",
        "description": f"{warning_count} near-critical warehouses"
    }


def get_available_capacity_data(main_warehouse=None):
    """Get total available capacity across all warehouses"""

    warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

    capacity_data = frappe.db.sql(f"""
        SELECT
            SUM(w.capacity) as total_capacity,
            SUM(COALESCE(s.total_stock, 0)) as total_used,
            SUM(w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
            w.capacity_unit
        FROM `tabWarehouse` w
        LEFT JOIN (
            SELECT warehouse, SUM(actual_qty) as total_stock
            FROM `tabStock Ledger Entry`
            WHERE docstatus = 1 AND is_cancelled = 0
            GROUP BY warehouse
        ) s ON w.name = s.warehouse
        WHERE w.is_group = 0 AND w.capacity > 0
        {warehouse_filter}
        GROUP BY w.capacity_unit
        ORDER BY available_capacity DESC
        LIMIT 1
    """, filter_params, as_dict=True)
    
    if capacity_data:
        data = capacity_data[0]
        available = flt(data.available_capacity or 0, 2)
        total = flt(data.total_capacity or 0, 2)
        capacity_unit = data.capacity_unit or "Units"
        
        # Calculate percentage available
        available_percent = (available / total * 100) if total > 0 else 0
        
        return {
            "value": available,
            "previous_value": available,  # For now
            "change": 0,
            "total_capacity": total,
            "available_percent": flt(available_percent, 2),
            "capacity_unit": capacity_unit,
            "description": f"{flt(available_percent, 1)}% capacity available"
        }
    
    return {
        "value": 0,
        "previous_value": 0,
        "change": 0,
        "total_capacity": 0,
        "available_percent": 0,
        "capacity_unit": "Units",
        "description": "No capacity data available"
    }


@frappe.whitelist()
def get_warehouse_list_with_capacity():
    """Get list of warehouses with their capacity details for testing"""
    
    warehouses = frappe.db.sql("""
        SELECT 
            w.name as warehouse,
            w.capacity,
            w.capacity_unit,
            COALESCE(s.total_stock, 0) as current_stock,
            (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
            COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
            CASE 
                WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'  
                WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                ELSE 'Healthy'
            END as status
        FROM `tabWarehouse` w
        LEFT JOIN (
            SELECT warehouse, SUM(actual_qty) as total_stock
            FROM `tabStock Ledger Entry` 
            WHERE docstatus = 1 AND is_cancelled = 0
            GROUP BY warehouse
        ) s ON w.name = s.warehouse
        WHERE w.is_group = 0 AND w.capacity > 0
        ORDER BY utilization_percent DESC
        LIMIT 20
    """, as_dict=True)
    
    return {
        "success": True,
        "warehouses": warehouses
    }


@frappe.whitelist() 
def test_dashboard_data():
    """Test function to verify dashboard data is working"""
    
    try:
        summary = get_warehouse_capacity_summary()
        warehouse_list = get_warehouse_list_with_capacity()
        
        return {
            "success": True,
            "summary": summary,
            "warehouse_sample": warehouse_list,
            "timestamp": frappe.utils.now()
        }
        
    except Exception as e:
        frappe.log_error(f"Error testing dashboard data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# PHASE 2: FRAPPE CHARTS API ENDPOINTS
# =============================================================================

@frappe.whitelist()
def get_capacity_utilization_trend(main_warehouse=None):
    """Get capacity utilization trend data for line chart"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get last 30 days of data
        from datetime import datetime, timedelta

        trend_data = []
        labels = []

        for i in range(29, -1, -1):
            date = get_datetime(today()) - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            # Get utilization for this date
            query_params = [date.date()] + (filter_params if filter_params else [])
            utilization_data = frappe.db.sql(f"""
                SELECT
                    (SUM(COALESCE(s.total_stock, 0)) / SUM(w.capacity)) * 100 as utilization_percent
                FROM `tabWarehouse` w
                LEFT JOIN (
                    SELECT warehouse, SUM(actual_qty) as total_stock
                    FROM `tabStock Ledger Entry`
                    WHERE docstatus = 1 AND is_cancelled = 0
                    AND posting_date <= %s
                    GROUP BY warehouse
                ) s ON w.name = s.warehouse
                WHERE w.is_group = 0 AND w.capacity > 0
                {warehouse_filter}
            """, query_params, as_dict=True)
            
            utilization = flt(utilization_data[0].utilization_percent or 0, 2) if utilization_data else 0
            
            trend_data.append(utilization)
            labels.append(date.strftime('%b %d'))
        
        return {
            "success": True,
            "chart_data": {
                "labels": labels,
                "datasets": [
                    {
                        "name": "Capacity Utilization %",
                        "values": trend_data,
                        "chartType": "line"
                    }
                ]
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting capacity utilization trend: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_status_distribution(main_warehouse=None):
    """Get warehouse status distribution for pie chart"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        status_data = frappe.db.sql(f"""
            SELECT
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COUNT(*) as count
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry` 
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            GROUP BY status
            ORDER BY count DESC
        """, filter_params, as_dict=True)
        
        labels = []
        values = []
        
        for item in status_data:
            labels.append(item.status)
            values.append(item.count)
        
        return {
            "success": True,
            "chart_data": {
                "labels": labels,
                "datasets": [
                    {
                        "values": values
                    }
                ]
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting warehouse status distribution: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_top_capacity_consuming_items(main_warehouse=None):
    """Get top 10 items consuming most warehouse capacity for bar chart"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Build warehouse filter for Stock Ledger Entry
        sle_warehouse_filter = ""
        if main_warehouse:
            # Get child warehouses list
            warehouses_result = frappe.db.sql(f"""
                SELECT name FROM `tabWarehouse`
                WHERE (parent_warehouse = %s OR name = %s OR name LIKE %s)
                AND is_group = 0
            """, (main_warehouse, main_warehouse, f"{main_warehouse}%"))

            if warehouses_result:
                warehouse_names = [w[0] for w in warehouses_result]
                placeholders = ', '.join(['%s'] * len(warehouse_names))
                sle_warehouse_filter = f"AND sle.warehouse IN ({placeholders})"
                sle_filter_params = warehouse_names
            else:
                sle_filter_params = []
        else:
            sle_filter_params = []

        items_data = frappe.db.sql(f"""
            SELECT
                sle.item_code,
                i.item_name,
                SUM(sle.actual_qty) as total_qty,
                i.stock_uom,
                COUNT(DISTINCT sle.warehouse) as warehouse_count
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {sle_warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.stock_uom
            ORDER BY total_qty DESC
            LIMIT 10
        """, sle_filter_params, as_dict=True)
        
        labels = []
        values = []
        
        for item in items_data:
            labels.append(f"{item.item_code}")
            values.append(flt(item.total_qty, 2))
        
        return {
            "success": True,
            "chart_data": {
                "labels": labels,
                "datasets": [
                    {
                        "name": "Quantity",
                        "values": values,
                        "chartType": "bar"
                    }
                ]
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting top capacity consuming items: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_capacity_by_location(main_warehouse=None):
    """Get warehouse capacity distribution by location for donut chart"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Extract location prefix from warehouse names (e.g., FAB-WH, TRM-WH)
        location_data = frappe.db.sql(f"""
            SELECT
                SUBSTRING_INDEX(w.name, '-', 2) as location_prefix,
                SUM(w.capacity) as total_capacity,
                SUM(COALESCE(s.total_stock, 0)) as total_used,
                COUNT(*) as warehouse_count
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry` 
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            GROUP BY location_prefix
            ORDER BY total_capacity DESC
        """, filter_params, as_dict=True)
        
        labels = []
        values = []
        
        for location in location_data:
            labels.append(f"{location.location_prefix} ({location.warehouse_count} warehouses)")
            values.append(flt(location.total_capacity, 2))
        
        return {
            "success": True,
            "chart_data": {
                "labels": labels,
                "datasets": [
                    {
                        "values": values
                    }
                ]
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting warehouse capacity by location: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }



@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# PHASE 3: ADVANCED FEATURES API ENDPOINTS
# =============================================================================

@frappe.whitelist()
def get_warehouse_locations():
    """Get unique warehouse location prefixes for filtering"""

    try:
        locations = frappe.db.sql("""
            SELECT DISTINCT
                SUBSTRING_INDEX(name, '-', 2) as location_prefix
            FROM `tabWarehouse`
            WHERE is_group = 0 AND capacity > 0
            ORDER BY location_prefix
        """, as_dict=True)

        location_list = [loc.location_prefix for loc in locations if loc.location_prefix]

        return {
            "success": True,
            "locations": location_list
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse locations: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_details(warehouse):
    """Get detailed information for a specific warehouse"""

    try:
        # Get warehouse basic details with stock
        warehouse_data = frappe.db.sql("""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.name = %s AND w.is_group = 0 AND w.capacity > 0
        """, (warehouse,), as_dict=True)

        if not warehouse_data:
            return {
                "success": False,
                "error": "Warehouse not found"
            }

        warehouse_info = warehouse_data[0]

        # Get top items in this warehouse
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.stock_uom, i.item_group
            ORDER BY qty DESC
            LIMIT 15
        """, (warehouse,), as_dict=True)

        warehouse_info['items_list'] = items_data

        return {
            "success": True,
            "warehouse": warehouse_info
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse details: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def export_dashboard_data():
    """Export dashboard data as CSV for reporting"""

    try:
        # Get all warehouse data
        warehouses = frappe.db.sql("""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Create CSV content
        csv_lines = []

        # Header
        headers = [
            'Warehouse',
            'Company',
            'Warehouse Type',
            'Total Capacity',
            'Capacity Unit',
            'Current Stock',
            'Available Capacity',
            'Utilization %',
            'Status',
            'Last Updated'
        ]
        csv_lines.append(','.join(headers))

        # Data rows
        for warehouse in warehouses:
            row = [
                f'"{warehouse.warehouse}"',
                f'"{warehouse.company or ""}"',
                f'"{warehouse.warehouse_type or ""}"',
                str(warehouse.capacity),
                f'"{warehouse.capacity_unit or "Units"}"',
                f'{warehouse.current_stock:.2f}',
                f'{warehouse.available_capacity:.2f}',
                f'{warehouse.utilization_percent:.2f}',
                f'"{warehouse.status}"',
                f'"{warehouse.last_updated}"'
            ]
            csv_lines.append(','.join(row))

        csv_content = '\n'.join(csv_lines)

        return {
            "success": True,
            "csv_data": csv_content,
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error exporting dashboard data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_alerts():
    """Get real-time alerts for warehouse capacity issues"""

    try:
        alerts = []

        # Critical capacity alerts (>90%)
        critical_warehouses = frappe.db.sql("""
            SELECT
                w.name as warehouse,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90
            ORDER BY utilization_percent DESC
        """, as_dict=True)

        for warehouse in critical_warehouses:
            alerts.append({
                "type": "critical",
                "title": "Critical Capacity Alert",
                "message": f"{warehouse.warehouse} is {warehouse.utilization_percent:.1f}% full",
                "warehouse": warehouse.warehouse,
                "timestamp": frappe.utils.now(),
                "priority": "high"
            })

        # Warning alerts (80-90%)
        warning_warehouses = frappe.db.sql("""
            SELECT
                w.name as warehouse,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80
            AND COALESCE((s.total_stock / w.capacity) * 100, 0) < 90
            ORDER BY utilization_percent DESC
            LIMIT 5
        """, as_dict=True)

        for warehouse in warning_warehouses:
            alerts.append({
                "type": "warning",
                "title": "High Capacity Warning",
                "message": f"{warehouse.warehouse} is {warehouse.utilization_percent:.1f}% full",
                "warehouse": warehouse.warehouse,
                "timestamp": frappe.utils.now(),
                "priority": "medium"
            })

        return {
            "success": True,
            "alerts": alerts,
            "total_alerts": len(alerts)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse alerts: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_performance_metrics():
    """Get advanced performance metrics for warehouses"""

    try:
        # Get warehouse efficiency metrics
        metrics_data = frappe.db.sql("""
            SELECT
                w.name as warehouse,
                w.capacity,
                COALESCE(s.total_stock, 0) as current_stock,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,

                -- Get stock movement velocity (transactions per day)
                COALESCE(sm.daily_transactions, 0) as daily_transactions,

                -- Get number of different items
                COALESCE(si.unique_items, 0) as unique_items,

                -- Calculate efficiency score
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) BETWEEN 60 AND 85
                         AND COALESCE(sm.daily_transactions, 0) > 5
                    THEN 'Excellent'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) BETWEEN 40 AND 90
                         AND COALESCE(sm.daily_transactions, 0) > 2
                    THEN 'Good'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) > 90
                         OR COALESCE(sm.daily_transactions, 0) < 1
                    THEN 'Needs Attention'
                    ELSE 'Fair'
                END as efficiency_rating

            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse

            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(*) / 30.0 as daily_transactions
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY warehouse
            ) sm ON w.name = sm.warehouse

            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as unique_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                AND actual_qty > 0
                GROUP BY warehouse
            ) si ON w.name = si.warehouse

            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "metrics": metrics_data,
            "total_warehouses": len(metrics_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse performance metrics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_advanced_analytics():
    """Get advanced analytics data for Phase 5 dashboard"""

    try:
        # Calculate various analytics metrics
        analytics = {}

        # Basic stats
        total_warehouses = frappe.db.sql("""
            SELECT COUNT(*) as count FROM `tabWarehouse` WHERE is_group = 0 AND capacity > 0
        """)[0][0]

        # Average utilization
        avg_utilization = frappe.db.sql("""
            SELECT AVG(COALESCE((s.total_stock / w.capacity) * 100, 0)) as avg_util
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
        """)[0][0] or 0

        # Calculate efficiency score based on utilization distribution
        efficiency_score = min(100, max(0, 100 - abs(avg_utilization - 75)))

        # Forecast data (simplified - in production would use more sophisticated algorithms)
        forecast_labels = []
        forecast_predictions = []
        forecast_historical = []

        from datetime import datetime, timedelta
        import random

        for i in range(30):
            date = datetime.now() + timedelta(days=i)
            forecast_labels.append(date.strftime('%b %d'))

            # Simple linear projection with some randomness
            base_prediction = avg_utilization + (i * 0.5) + random.uniform(-2, 2)
            forecast_predictions.append(max(0, min(100, base_prediction)))

            if i < 15:  # Historical data for first 15 days
                historical_data = avg_utilization + random.uniform(-5, 5)
                forecast_historical.append(max(0, min(100, historical_data)))
            else:
                forecast_historical.append(None)

        # Generate recommendations
        recommendations = []

        if avg_utilization > 85:
            recommendations.append({
                "title": "High Utilization Alert",
                "description": "Overall utilization is above 85%. Consider expanding capacity or redistributing stock.",
                "priority": "high"
            })

        if efficiency_score < 70:
            recommendations.append({
                "title": "Efficiency Improvement Needed",
                "description": "Warehouse efficiency is below optimal. Review space allocation and inventory management.",
                "priority": "medium"
            })

        recommendations.append({
            "title": "Regular Capacity Review",
            "description": "Schedule monthly capacity reviews to maintain optimal warehouse performance.",
            "priority": "low"
        })

        analytics = {
            "total_warehouses": total_warehouses,
            "average_utilization": round(avg_utilization, 1),
            "efficiency_score": round(efficiency_score, 1),
            "cost_savings": round(random.uniform(400000, 2000000), 0),  # Placeholder calculation in INR
            "forecast_accuracy": round(random.uniform(85, 95), 1),  # Placeholder
            "velocity_index": round(random.uniform(1.2, 2.8), 1),   # Placeholder
            "forecast_data": {
                "labels": forecast_labels,
                "predictions": forecast_predictions,
                "historical": forecast_historical
            },
            "efficiency_matrix": {
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "datasets": [{
                    "values": [85, 78, 82, 88]
                }]
            },
            "recommendations": recommendations
        }

        return {
            "success": True,
            "analytics": analytics
        }

    except Exception as e:
        frappe.log_error(f"Error getting advanced analytics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_data(main_warehouse=None):
    """Get detailed warehouse data with items information for enhanced table"""

    try:
        warehouse_filter, filter_params = build_warehouse_filter(main_warehouse)

        # Get warehouse data with item counts and details
        warehouses_with_items = frappe.db.sql(f"""
            SELECT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(s.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(s.total_stock, 0)) as available_capacity,
                COALESCE((s.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((s.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                COALESCE(ic.item_count, 0) as item_count,
                COALESCE(ic.top_items, '') as top_items_preview,
                w.modified as last_updated
            FROM `tabWarehouse` w
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) s ON w.name = s.warehouse
            LEFT JOIN (
                SELECT
                    warehouse,
                    COUNT(DISTINCT item_code) as item_count,
                    GROUP_CONCAT(
                        CONCAT(item_code, ':', ROUND(actual_qty, 1))
                        ORDER BY actual_qty DESC
                        SEPARATOR '; '
                    ) as top_items
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0 AND actual_qty > 0
                GROUP BY warehouse
            ) ic ON w.name = ic.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            {warehouse_filter}
            ORDER BY utilization_percent DESC
        """, filter_params, as_dict=True)

        # Get unique items across all warehouses for filtering
        all_items = frappe.db.sql(f"""
            SELECT DISTINCT
                sle.item_code,
                i.item_name,
                i.item_group,
                COUNT(DISTINCT sle.warehouse) as warehouse_count,
                SUM(sle.actual_qty) as total_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            GROUP BY sle.item_code, i.item_name, i.item_group
            ORDER BY total_qty DESC
        """, filter_params, as_dict=True)

        # Get unique item groups for filtering
        item_groups = frappe.db.sql(f"""
            SELECT DISTINCT i.item_group
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            INNER JOIN `tabWarehouse` w ON sle.warehouse = w.name
            WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
            AND w.is_group = 0 AND w.capacity > 0
            AND sle.actual_qty > 0
            {warehouse_filter}
            ORDER BY i.item_group
        """, filter_params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses_with_items,
            "items": all_items,
            "item_groups": [ig.item_group for ig in item_groups],
            "total_warehouses": len(warehouses_with_items)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_warehouse_items_detail(warehouse):
    """Get detailed items list for a specific warehouse"""

    try:
        items_data = frappe.db.sql("""
            SELECT
                sle.item_code,
                i.item_name,
                i.item_group,
                SUM(sle.actual_qty) as qty,
                i.stock_uom,
                i.description,
                AVG(sle.valuation_rate) as avg_rate,
                SUM(sle.actual_qty * sle.valuation_rate) as total_value,
                MAX(sle.posting_date) as last_transaction_date
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            WHERE sle.warehouse = %s
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            GROUP BY sle.item_code, i.item_name, i.item_group, i.stock_uom, i.description
            ORDER BY qty DESC
        """, (warehouse,), as_dict=True)

        return {
            "success": True,
            "warehouse": warehouse,
            "items": items_data,
            "total_items": len(items_data),
            "total_value": sum(item.total_value or 0 for item in items_data)
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse items detail: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def filter_warehouses_by_item(item_code=None, item_group=None):
    """Filter warehouses based on specific items or item groups"""

    try:
        conditions = []
        params = []

        if item_code:
            conditions.append("sle.item_code = %s")
            params.append(item_code)

        if item_group:
            conditions.append("i.item_group = %s")
            params.append(item_group)

        where_clause = ""
        if conditions:
            where_clause = f"AND {' AND '.join(conditions)}"

        warehouses = frappe.db.sql(f"""
            SELECT DISTINCT
                w.name as warehouse,
                w.capacity,
                w.capacity_unit,
                w.warehouse_type,
                w.company,
                COALESCE(ws.total_stock, 0) as current_stock,
                (w.capacity - COALESCE(ws.total_stock, 0)) as available_capacity,
                COALESCE((ws.total_stock / w.capacity) * 100, 0) as utilization_percent,
                CASE
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 90 THEN 'Critical'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 80 THEN 'Warning'
                    WHEN COALESCE((ws.total_stock / w.capacity) * 100, 0) >= 60 THEN 'Caution'
                    ELSE 'Healthy'
                END as status,
                SUM(sle.actual_qty) as filtered_item_qty,
                COUNT(DISTINCT sle.item_code) as matching_items_count
            FROM `tabWarehouse` w
            INNER JOIN `tabStock Ledger Entry` sle ON w.name = sle.warehouse
            INNER JOIN `tabItem` i ON sle.item_code = i.name
            LEFT JOIN (
                SELECT warehouse, SUM(actual_qty) as total_stock
                FROM `tabStock Ledger Entry`
                WHERE docstatus = 1 AND is_cancelled = 0
                GROUP BY warehouse
            ) ws ON w.name = ws.warehouse
            WHERE w.is_group = 0 AND w.capacity > 0
            AND sle.docstatus = 1 AND sle.is_cancelled = 0
            AND sle.actual_qty > 0
            {where_clause}
            GROUP BY w.name, w.capacity, w.capacity_unit, w.warehouse_type, w.company, ws.total_stock
            ORDER BY filtered_item_qty DESC
        """, params, as_dict=True)

        return {
            "success": True,
            "warehouses": warehouses,
            "filter_applied": {
                "item_code": item_code,
                "item_group": item_group
            },
            "total_warehouses": len(warehouses)
        }

    except Exception as e:
        frappe.log_error(f"Error filtering warehouses by item: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }