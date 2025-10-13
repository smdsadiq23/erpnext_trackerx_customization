import frappe
from frappe import _
from frappe.utils import flt, today, add_days

# Import barcode/QR code generation utilities
try:
    from labelx.utils.generators import generate_barcode_base64, generate_qrcode_base64
    BARCODE_UTILS_AVAILABLE = True
except ImportError:
    BARCODE_UTILS_AVAILABLE = False
    frappe.log_error("labelx.utils.generators not available for warehouse barcode generation", "Warehouse Barcode Import Error")

def before_save(doc, method):
    """Generate and store barcode & QR code for warehouse before saving"""
    if BARCODE_UTILS_AVAILABLE and doc.name:
        generate_warehouse_barcodes(doc)

def generate_warehouse_barcodes(warehouse):
    """Generate barcode and QR code for the warehouse"""
    try:
        # Only generate if not already set
        if not getattr(warehouse, 'warehouse_barcode_image', None) or not getattr(warehouse, 'warehouse_qr_code_image', None):
            # Use warehouse name as the barcode/QR code data
            warehouse_code = warehouse.name  # e.g., "Main Store - CX"

            # Generate Base64 images
            barcode_b64 = generate_barcode_base64(warehouse_code)
            qrcode_b64 = generate_qrcode_base64(warehouse_code)

            # Store in fields (only if fields exist)
            if hasattr(warehouse, 'warehouse_barcode_image'):
                warehouse.warehouse_barcode_image = barcode_b64
            if hasattr(warehouse, 'warehouse_qr_code_image'):
                warehouse.warehouse_qr_code_image = qrcode_b64
            if hasattr(warehouse, 'warehouse_barcode'):
                warehouse.warehouse_barcode = warehouse_code
            if hasattr(warehouse, 'warehouse_qr_code_display'):
                # Create HTML to display QR code
                warehouse.warehouse_qr_code_display = f'<img src="{qrcode_b64}" style="max-width: 150px; max-height: 150px;" alt="Warehouse QR Code"/>'

            frappe.logger().info(f"Generated barcode and QR code for warehouse: {warehouse.name}")

    except Exception as e:
        frappe.log_error(f"Error generating warehouse barcode/QR code: {str(e)}", "Warehouse Barcode Generation Error")

def validate(doc, method):
    """Additional validation for warehouse with barcode fields"""
    try:
        # Log when warehouse barcode fields are accessed for debugging
        if hasattr(doc, 'warehouse_barcode') and doc.warehouse_barcode:
            frappe.logger().info(f"Warehouse {doc.name} has barcode: {doc.warehouse_barcode}")

        # Update parent warehouse capacity from child warehouse
        if hasattr(doc, 'capacity') and doc.capacity and doc.parent_warehouse:
            update_parent_warehouse_capacity_from_child_with_current_doc(doc.parent_warehouse, doc.name, doc.capacity)
        else:
            pass
    except Exception as e:
        frappe.log_error(f"Error in warehouse validation: {str(e)}", "Warehouse Validation Error")

def after_insert(doc, method):
    """Hook triggered when a new warehouse is created"""
    try:
        # Generate barcodes for new warehouse
        if BARCODE_UTILS_AVAILABLE and doc.name:
            generate_warehouse_barcodes(doc)

        # Auto-create putaway rules if warehouse has capacity
        if hasattr(doc, 'capacity') and doc.capacity and not doc.is_group:
            create_putaway_rules_for_warehouse(doc)

    except Exception as e:
        frappe.log_error(f"Error in warehouse after_insert hook: {str(e)}")

def on_update(doc, method):
    """Actions to perform after warehouse is updated"""
    try:
        # Regenerate barcode if warehouse name changed
        if BARCODE_UTILS_AVAILABLE and doc.name:
            # Check if we need to regenerate (name might have changed)
            current_barcode = getattr(doc, 'warehouse_barcode', None)
            if current_barcode and current_barcode != doc.name:
                # Name changed, regenerate barcode
                generate_warehouse_barcodes(doc)
                frappe.logger().info(f"Regenerated barcode for renamed warehouse: {doc.name}")

        # Sync capacity changes with existing putaway rules
        if doc.has_value_changed('capacity') and hasattr(doc, 'capacity') and doc.capacity:
            sync_capacity_with_putaway_rules(doc)

    except Exception as e:
        frappe.log_error(f"Error in warehouse on_update: {str(e)}", "Warehouse Update Error")

@frappe.whitelist()
def regenerate_warehouse_barcode(warehouse_name):
    """
    Manually regenerate barcode for a specific warehouse

    Args:
        warehouse_name: Name of the warehouse

    Returns:
        dict: Result of barcode regeneration
    """
    try:
        warehouse = frappe.get_doc("Warehouse", warehouse_name)

        if not BARCODE_UTILS_AVAILABLE:
            frappe.throw(_("Barcode generation utilities not available"))

        # Force regeneration by clearing existing values
        if hasattr(warehouse, 'warehouse_barcode_image'):
            warehouse.warehouse_barcode_image = None
        if hasattr(warehouse, 'warehouse_qr_code_image'):
            warehouse.warehouse_qr_code_image = None

        # Generate new barcodes
        generate_warehouse_barcodes(warehouse)

        # Save the warehouse
        warehouse.save()

        return {
            "success": True,
            "message": _("Warehouse barcode regenerated successfully"),
            "warehouse_name": warehouse.name,
            "barcode_data": getattr(warehouse, 'warehouse_barcode', None)
        }

    except Exception as e:
        frappe.log_error(f"Error regenerating warehouse barcode: {str(e)}")
        frappe.throw(_("Failed to regenerate warehouse barcode: {0}").format(str(e)))

@frappe.whitelist()
def get_warehouse_barcode_data(warehouse_name):
    """
    Get barcode/QR code data for a warehouse

    Args:
        warehouse_name: Name of the warehouse

    Returns:
        dict: Warehouse barcode data
    """
    try:
        warehouse = frappe.get_doc("Warehouse", warehouse_name)

        return {
            "success": True,
            "warehouse_name": warehouse.name,
            "warehouse_barcode": getattr(warehouse, 'warehouse_barcode', None),
            "warehouse_barcode_image": getattr(warehouse, 'warehouse_barcode_image', None),
            "warehouse_qr_code_image": getattr(warehouse, 'warehouse_qr_code_image', None),
            "has_barcode_fields": all([
                hasattr(warehouse, 'warehouse_barcode'),
                hasattr(warehouse, 'warehouse_barcode_image'),
                hasattr(warehouse, 'warehouse_qr_code_image')
            ])
        }

    except Exception as e:
        frappe.log_error(f"Error getting warehouse barcode data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# ===========================
# CAPACITY MANAGEMENT FUNCTIONS
# ===========================

def create_putaway_rules_for_warehouse(warehouse_doc):
    """Auto-create putaway rules for new warehouses with capacity"""
    try:
        # Get active stock items for the company
        items = frappe.get_all("Item",
                             filters={
                                 "disabled": 0,
                                 "is_stock_item": 1
                             },
                             fields=["name"],
                             limit=10)  # Limit to prevent too many rules

        if items:
            from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.warehouse_capacity_manager.warehouse_capacity_manager import auto_create_putaway_rules_from_warehouse

            # Create putaway rules for selected items
            result = auto_create_putaway_rules_from_warehouse(warehouse_doc.name, items)

            if result.get("success"):
                frappe.msgprint(_("Auto-created {0} putaway rules for warehouse {1}").format(
                    result.get("created_rules", 0), warehouse_doc.name
                ), alert=True)

    except Exception as e:
        frappe.log_error(f"Error creating putaway rules for warehouse: {str(e)}")

def sync_capacity_with_putaway_rules(warehouse_doc):
    """Sync capacity changes with existing putaway rules"""
    try:
        # Update all putaway rules for this warehouse
        putaway_rules = frappe.get_all("Putaway Rule",
                                     filters={"warehouse": warehouse_doc.name},
                                     fields=["name"])

        updated_rules = 0
        for rule in putaway_rules:
            rule_doc = frappe.get_doc("Putaway Rule", rule.name)
            rule_doc.capacity = warehouse_doc.capacity
            rule_doc.uom = getattr(warehouse_doc, 'capacity_unit', 'Meter')
            rule_doc.save(ignore_permissions=True)
            updated_rules += 1

        if updated_rules > 0:
            frappe.msgprint(_("Updated capacity in {0} putaway rules for warehouse {1}").format(
                updated_rules, warehouse_doc.name
            ), alert=True)

    except Exception as e:
        frappe.log_error(f"Error syncing capacity with putaway rules: {str(e)}")

# ===========================
# SCHEDULED TASKS
# ===========================

def daily_capacity_sync():
    """Daily scheduled job to sync warehouse capacity with putaway rules"""
    try:
        from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.warehouse_capacity_manager.warehouse_capacity_manager import sync_warehouse_capacity_with_putaway_rules

        result = sync_warehouse_capacity_with_putaway_rules()

        if result.get("success") and result.get("total_rules_updated", 0) > 0:
            # Send email notification to administrators
            send_capacity_sync_notification(result)

    except Exception as e:
        frappe.log_error(f"Error in daily_capacity_sync: {str(e)}")

def weekly_capacity_report():
    """Weekly scheduled job to generate capacity utilization report"""
    try:
        from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.warehouse_capacity_manager.warehouse_capacity_manager import get_warehouse_capacity_summary

        result = get_warehouse_capacity_summary()

        if result.get("success"):
            generate_weekly_capacity_report(result.get("capacity_summary", []))

    except Exception as e:
        frappe.log_error(f"Error in weekly_capacity_report: {str(e)}")

def send_capacity_sync_notification(sync_result):
    """Send email notification about capacity sync results"""
    try:
        # Get system managers
        recipients = frappe.get_all("Has Role",
                                  filters={"role": "System Manager"},
                                  fields=["parent"])

        if not recipients:
            return

        recipient_emails = [r.parent for r in recipients]

        subject = "Daily Warehouse Capacity Sync Report"
        message = f"""
        <h3>Warehouse Capacity Sync Completed</h3>
        <p><strong>Date:</strong> {today()}</p>
        <p><strong>Synchronized Warehouses:</strong> {sync_result.get('synced_warehouses', 0)}</p>
        <p><strong>Updated Putaway Rules:</strong> {sync_result.get('total_rules_updated', 0)}</p>
        <p><strong>Status:</strong> Success</p>
        """

        frappe.sendmail(
            recipients=recipient_emails,
            subject=subject,
            message=message
        )

    except Exception as e:
        frappe.log_error(f"Error sending capacity sync notification: {str(e)}")

def generate_weekly_capacity_report(capacity_data):
    """Generate and send weekly capacity utilization report"""
    try:
        if not capacity_data:
            return

        # Calculate summary statistics
        total_warehouses = len(capacity_data)
        high_utilization_warehouses = [w for w in capacity_data if w.get('utilization_percent', 0) > 80]
        low_utilization_warehouses = [w for w in capacity_data if w.get('utilization_percent', 0) < 20]

        # Get recipients
        recipients = frappe.get_all("Has Role",
                                  filters={"role": "Stock Manager"},
                                  fields=["parent"])

        if not recipients:
            return

        recipient_emails = [r.parent for r in recipients]

        subject = "Weekly Warehouse Capacity Utilization Report"

        # Build HTML message
        message = f"""
        <h2>Weekly Warehouse Capacity Report</h2>
        <p><strong>Report Date:</strong> {today()}</p>

        <h3>Summary</h3>
        <ul>
            <li>Total Warehouses: {total_warehouses}</li>
            <li>High Utilization (&gt;80%): {len(high_utilization_warehouses)}</li>
            <li>Low Utilization (&lt;20%): {len(low_utilization_warehouses)}</li>
        </ul>
        """

        # High utilization warnings
        if high_utilization_warehouses:
            message += """
            <h3 style="color: #d9534f;">⚠️ High Utilization Warehouses</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f5f5f5;">
                    <th>Warehouse</th>
                    <th>Utilization %</th>
                    <th>Current Stock</th>
                    <th>Capacity</th>
                    <th>Available Space</th>
                </tr>
            """
            for wh in high_utilization_warehouses:
                message += f"""
                <tr>
                    <td>{wh.get('warehouse', '')}</td>
                    <td>{wh.get('utilization_percent', 0):.1f}%</td>
                    <td>{wh.get('current_stock', 0)}</td>
                    <td>{wh.get('capacity', 0)}</td>
                    <td>{wh.get('available_space', 0)}</td>
                </tr>
                """
            message += "</table>"

        message += "<p><em>This is an automated report generated by the Warehouse Capacity Management System.</em></p>"

        frappe.sendmail(
            recipients=recipient_emails,
            subject=subject,
            message=message
        )

        # Also create a log
        frappe.log_error(f"Weekly capacity report sent to {len(recipient_emails)} recipients",
                        "Weekly Capacity Report")

    except Exception as e:
        frappe.log_error(f"Error generating weekly capacity report: {str(e)}")

# ===========================
# PARENT-CHILD WAREHOUSE CAPACITY MANAGEMENT
# ===========================

def update_parent_warehouse_capacity_from_child(parent_warehouse_name):
    """Update parent warehouse capacity from child warehouse"""
    try:

        if not parent_warehouse_name:
            return

        parent_warehouse = frappe.get_doc("Warehouse", parent_warehouse_name)

        # Get all child warehouses with capacity field
        child_warehouses = frappe.get_all(
            "Warehouse",
            filters={"parent_warehouse": parent_warehouse_name},
            fields=["name", "capacity", "capacity_unit"]
        )


        if not child_warehouses:
            return

        total_capacity = 0
        capacity_unit = None

        for child_warehouse in child_warehouses:
            if child_warehouse.capacity:
                total_capacity += child_warehouse.capacity
                # Use the first non-null capacity unit
                if not capacity_unit and child_warehouse.capacity_unit:
                    capacity_unit = child_warehouse.capacity_unit


        # Update parent warehouse capacity
        if hasattr(parent_warehouse, 'capacity'):
            old_capacity = getattr(parent_warehouse, 'capacity', 0)
            parent_warehouse.capacity = total_capacity
            if capacity_unit and hasattr(parent_warehouse, 'capacity_unit'):
                parent_warehouse.capacity_unit = capacity_unit
            parent_warehouse.save()
        else:
            pass
    except Exception as e:
        frappe.msgprint(f"ERROR: Failed to update parent warehouse capacity: {str(e)}")
        frappe.log_error(f"Error updating parent warehouse capacity: {str(e)}", "Parent Warehouse Capacity Update Error")

def update_parent_warehouse_capacity_from_child_with_current_doc(parent_warehouse_name, current_child_name, current_child_capacity):
    """Update parent warehouse capacity using the current document's capacity value"""
    try:

        if not parent_warehouse_name:
            return

        parent_warehouse = frappe.get_doc("Warehouse", parent_warehouse_name)
        # Get all child warehouses with capacity field
        child_warehouses = frappe.get_all(
            "Warehouse",
            filters={"parent_warehouse": parent_warehouse_name},
            fields=["name", "capacity", "capacity_unit"]
        )


        if not child_warehouses:

            return

        total_capacity = 0
        capacity_unit = None

        for child_warehouse in child_warehouses:

            if child_warehouse.name == current_child_name:
                # Use the current document's capacity for the warehouse being updated
                if current_child_capacity:
                    total_capacity += current_child_capacity
                    if not capacity_unit and child_warehouse.capacity_unit:
                        capacity_unit = child_warehouse.capacity_unit
            else:
                # Use database capacity for other warehouses
                if child_warehouse.capacity:
                    total_capacity += child_warehouse.capacity
                    if not capacity_unit and child_warehouse.capacity_unit:
                        capacity_unit = child_warehouse.capacity_unit


        # Update parent warehouse capacity
        if hasattr(parent_warehouse, 'capacity'):
            old_capacity = getattr(parent_warehouse, 'capacity', 0)
            parent_warehouse.capacity = total_capacity
            if capacity_unit and hasattr(parent_warehouse, 'capacity_unit'):
                parent_warehouse.capacity_unit = capacity_unit
            parent_warehouse.save()
        else:
            pass
    except Exception as e:
        frappe.msgprint(f"ERROR: Failed to update parent warehouse capacity: {str(e)}")
        frappe.log_error(f"Error updating parent warehouse capacity: {str(e)}", "Parent Warehouse Capacity Update Error")