import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """
    Comprehensive warehouse fields setup for storage capacity, business unit integration, and barcode/QR code functionality.
    This function consolidates warehouse customizations and removes deprecated fields.
    """

    try:
        frappe.logger().info("Setting up warehouse fields (business unit integration + capacity + barcode/QR code)...")

        # Step 1: Remove deprecated fields from old warehouse_customization
        deprecated_fields = [
            "bin_location", "zone_type", "rack_number", "level_number", "bin_number",
            "temperature_min", "temperature_max", "humidity_min", "humidity_max",
            "supports_shade_segregation"
        ]

        removed_count = 0
        for field_name in deprecated_fields:
            try:
                custom_field_name = f"Warehouse-{field_name}"
                if frappe.db.exists("Custom Field", custom_field_name):
                    frappe.delete_doc("Custom Field", custom_field_name)
                    removed_count += 1
                    frappe.logger().info(f"Removed deprecated field: {field_name}")
            except Exception as e:
                frappe.logger().warning(f"Could not remove field {field_name}: {str(e)}")

        print(f"🧹 Removed {removed_count} deprecated warehouse fields")

        # Step 2: Define consolidated custom fields for Warehouse doctype
        custom_fields = {
            "Warehouse": [
                # Business Unit Integration Section
                {
                    "fieldname": "business_unit",
                    "label": "Business Unit",
                    "fieldtype": "Link",
                    "options": "Company",
                    "insert_after": "company",
                    "description": "Business Unit for this warehouse",
                    "in_filter": 1,
                    "in_standard_filter": 1
                },
                {
                    "fieldname": "strategic_business_unit",
                    "label": "Strategic Business Unit",
                    "fieldtype": "Link",
                    "options": "Strategic Business Unit",
                    "insert_after": "business_unit",
                    "description": "Strategic Business Unit for this warehouse",
                    "in_filter": 1,
                    "in_standard_filter": 1
                },
                {
                    "fieldname": "factory",
                    "label": "Factory",
                    "fieldtype": "Link",
                    "options": "Factory Business Unit",
                    "insert_after": "strategic_business_unit",
                    "description": "Factory Business Unit for this warehouse",
                    "in_filter": 1,
                    "in_standard_filter": 1
                },

                # Storage & Capacity Section
                {
                    "fieldname": "warehouse_storage_section",
                    "label": "Storage & Capacity",
                    "fieldtype": "Section Break",
                    "insert_after": "factory",
                    "collapsible": 1,
                    "description": "Warehouse storage capacity and unit of measurement"
                },
                {
                    "fieldname": "capacity",
                    "label": "Storage Capacity",
                    "fieldtype": "Float",
                    "insert_after": "warehouse_storage_section",
                    "precision": "2",
                    "description": "Maximum storage capacity for this warehouse"
                },
                {
                    "fieldname": "capacity_unit",
                    "label": "Capacity Unit",
                    "fieldtype": "Link",
                    "options": "UOM",
                    "insert_after": "capacity",
                    "description": "Unit of measurement for storage capacity"
                },

                # Barcode & QR Code Section
                {
                    "fieldname": "warehouse_barcode_section",
                    "label": "Warehouse Barcode & QR Code",
                    "fieldtype": "Section Break",
                    "insert_after": "capacity_unit",
                    "collapsible": 1,
                    "description": "Auto-generated barcode and QR code for warehouse identification"
                },
                {
                    "fieldname": "warehouse_barcode",
                    "label": "Warehouse Barcode",
                    "fieldtype": "Barcode",
                    "insert_after": "warehouse_barcode_section",
                    "read_only": 1,
                    "width": "200",
                    "description": "Auto-generated barcode for this warehouse"
                },
                {
                    "fieldname": "warehouse_column_break",
                    "fieldtype": "Column Break",
                    "insert_after": "warehouse_barcode"
                },
                {
                    "fieldname": "warehouse_qr_code_display",
                    "label": "Warehouse QR Code",
                    "fieldtype": "HTML",
                    "insert_after": "warehouse_column_break",
                    "read_only": 1,
                    "description": "Auto-generated QR code for this warehouse"
                },
                {
                    "fieldname": "warehouse_barcode_image",
                    "label": "Warehouse Barcode Image",
                    "fieldtype": "Long Text",
                    "insert_after": "warehouse_qr_code_display",
                    "hidden": 1,
                    "print_hide": 1,
                    "description": "Base64 encoded warehouse barcode image"
                },
                {
                    "fieldname": "warehouse_qr_code_image",
                    "label": "Warehouse QR Code Image",
                    "fieldtype": "Long Text",
                    "insert_after": "warehouse_barcode_image",
                    "hidden": 1,
                    "print_hide": 1,
                    "description": "Base64 encoded warehouse QR code image"
                }
            ]
        }

        # Step 3: Create/update the consolidated custom fields
        create_custom_fields(custom_fields, ignore_validate=True)

        business_unit_field_count = 3  # business_unit, strategic_business_unit, factory
        capacity_field_count = 3       # storage_section, capacity, capacity_unit
        barcode_field_count = 6        # section, barcode, column_break, qr_display, barcode_image, qr_image
        total_field_count = business_unit_field_count + capacity_field_count + barcode_field_count

        frappe.logger().info(f"Successfully created {total_field_count} warehouse fields")

        # Success messages
        print(f"✅ Business Unit Integration: Created {business_unit_field_count} business unit fields")
        print(f"✅ Warehouse Storage: Created {capacity_field_count} capacity/storage fields")
        print(f"✅ Warehouse Barcode: Created {barcode_field_count} barcode/QR code fields")
        print(f"📊 Total: {total_field_count} warehouse fields configured")
        print(f"🔗 Business Unit: Links to Company, Strategic Business Unit, Factory Business Unit")
        print(f"🔗 Capacity Unit: Links to UOM doctype for better integration")

        return True

    except Exception as e:
        error_msg = f"Error setting up warehouse fields: {str(e)}"
        frappe.logger().error(error_msg)
        frappe.log_error(error_msg, "Warehouse Fields Setup")
        print(f"❌ Error: {error_msg}")
        return False

def cleanup_old_warehouse_fields():
    """
    Utility function to clean up old warehouse customizations if needed.
    Can be called manually if migration issues occur.
    """
    try:
        # Remove any remaining old custom fields
        old_field_patterns = [
            "Warehouse-bin_location", "Warehouse-zone_type", "Warehouse-rack_number",
            "Warehouse-level_number", "Warehouse-bin_number", "Warehouse-temperature_min",
            "Warehouse-temperature_max", "Warehouse-humidity_min", "Warehouse-humidity_max",
            "Warehouse-supports_shade_segregation"
        ]

        removed = 0
        for field_name in old_field_patterns:
            if frappe.db.exists("Custom Field", field_name):
                frappe.delete_doc("Custom Field", field_name)
                removed += 1

        print(f"🧹 Cleanup completed: {removed} old fields removed")
        return True

    except Exception as e:
        print(f"❌ Cleanup error: {str(e)}")
        return False

def create_warehouse_business_unit_fields():
    """
    Alternative function to create business unit fields manually via console.
    Usage: bench --site trackerx.local console
    >>> from erpnext_trackerx_customization.setup.warehouse_fields import create_warehouse_business_unit_fields
    >>> create_warehouse_business_unit_fields()
    """
    try:
        business_unit_fields = {
            "Warehouse": [
                {
                    "fieldname": "business_unit",
                    "label": "Business Unit",
                    "fieldtype": "Link",
                    "options": "Company",
                    "insert_after": "company",
                    "description": "Business Unit for this warehouse",
                    "in_filter": 1,
                    "in_standard_filter": 1,
                    "reqd": 0
                },
                {
                    "fieldname": "strategic_business_unit",
                    "label": "Strategic Business Unit",
                    "fieldtype": "Link",
                    "options": "Strategic Business Unit",
                    "insert_after": "business_unit",
                    "description": "Strategic Business Unit for this warehouse",
                    "in_filter": 1,
                    "in_standard_filter": 1,
                    "reqd": 0
                },
                {
                    "fieldname": "factory",
                    "label": "Factory",
                    "fieldtype": "Link",
                    "options": "Factory Business Unit",
                    "insert_after": "strategic_business_unit",
                    "description": "Factory Business Unit for this warehouse",
                    "in_filter": 1,
                    "in_standard_filter": 1,
                    "reqd": 0
                }
            ]
        }

        create_custom_fields(business_unit_fields, ignore_validate=True)

        print("✅ Warehouse business unit fields created successfully!")
        print("📋 Fields added:")
        for field in business_unit_fields["Warehouse"]:
            print(f"   - {field['label']} ({field['fieldname']})")

        return True
    except Exception as e:
        print(f"❌ Error creating business unit fields: {str(e)}")
        return False