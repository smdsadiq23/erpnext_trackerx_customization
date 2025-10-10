import frappe
from frappe import _

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
    except Exception as e:
        frappe.log_error(f"Error in warehouse validation: {str(e)}", "Warehouse Validation Error")

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