import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """
    Create Purchase Receipt Item custom fields for enhanced GRN data mapping.
    This function is called during migration via hooks.py after_migrate.
    """
    
    try:
        frappe.logger().info("Creating Purchase Receipt and Purchase Receipt Item custom fields for GRN data mapping...")

        # Define custom fields for Purchase Receipt and Purchase Receipt Item
        custom_fields = {
            "Purchase Receipt": [
                # Inspection and Quality Control Section
                {
                    "fieldname": "linked_inspection",
                    "label": "Linked Inspection",
                    "fieldtype": "Link",
                    "options": "Fabric Inspection",
                    "insert_after": "linked_grn",
                    "read_only": 1,
                    "description": "Reference to associated Fabric Inspection document"
                }
            ],
            "Purchase Receipt Item": [
                # Basic Material Information
                {
                    "fieldname": "custom_color",
                    "label": "Color",
                    "fieldtype": "Data",
                    "insert_after": "description",
                    "description": "Color from GRN"
                },
                {
                    "fieldname": "custom_composition",
                    "label": "Composition", 
                    "fieldtype": "Data",
                    "insert_after": "custom_color",
                    "description": "Fabric composition from GRN"
                },
                {
                    "fieldname": "custom_material_type",
                    "label": "Material Type",
                    "fieldtype": "Data",
                    "insert_after": "custom_composition",
                    "description": "Material type from GRN"
                },
                {
                    "fieldname": "custom_shade",
                    "label": "Shade",
                    "fieldtype": "Data", 
                    "insert_after": "custom_material_type",
                    "description": "Shade information from GRN"
                },
                
                # Physical Specifications Section
                {
                    "fieldname": "custom_physical_specs_section",
                    "label": "Physical Specifications",
                    "fieldtype": "Section Break",
                    "insert_after": "custom_shade",
                    "collapsible": 1
                },
                {
                    "fieldname": "custom_roll_no",
                    "label": "Roll Number",
                    "fieldtype": "Data",
                    "insert_after": "custom_physical_specs_section",
                    "description": "Roll number from GRN"
                },
                {
                    "fieldname": "custom_fabric_length",
                    "label": "Fabric Length",
                    "fieldtype": "Int",
                    "insert_after": "custom_roll_no",
                    "description": "Fabric length from GRN"
                },
                {
                    "fieldname": "custom_fabric_width", 
                    "label": "Fabric Width",
                    "fieldtype": "Int",
                    "insert_after": "custom_fabric_length",
                    "description": "Fabric width from GRN"
                },
                {
                    "fieldname": "custom_column_break_1",
                    "fieldtype": "Column Break",
                    "insert_after": "custom_fabric_width"
                },
                {
                    "fieldname": "custom_no_of_boxespacks",
                    "label": "Number of Boxes/Packs",
                    "fieldtype": "Float",
                    "insert_after": "custom_column_break_1",
                    "precision": "2",
                    "description": "Number of boxes/packs from GRN"
                },
                {
                    "fieldname": "custom_size_spec",
                    "label": "Size Specification", 
                    "fieldtype": "Data",
                    "insert_after": "custom_no_of_boxespacks",
                    "description": "Size specifications from GRN"
                },
                {
                    "fieldname": "custom_consumption",
                    "label": "Consumption",
                    "fieldtype": "Float",
                    "insert_after": "custom_size_spec",
                    "precision": "3",
                    "description": "Consumption data from GRN"
                },
                
                # Tracking Information Section
                {
                    "fieldname": "custom_tracking_section",
                    "label": "Tracking & Reference Information", 
                    "fieldtype": "Section Break",
                    "insert_after": "custom_consumption",
                    "collapsible": 1
                },
                {
                    "fieldname": "custom_lot_no",
                    "label": "Lot Number",
                    "fieldtype": "Data",
                    "insert_after": "custom_tracking_section",
                    "description": "Lot number from GRN"
                },
                {
                    "fieldname": "custom_supplier_part_no_code",
                    "label": "Supplier Part Number/Code",
                    "fieldtype": "Data", 
                    "insert_after": "custom_lot_no",
                    "description": "Supplier part number/code from GRN"
                },
                {
                    "fieldname": "custom_ordered_quantity",
                    "label": "Originally Ordered Quantity",
                    "fieldtype": "Int",
                    "insert_after": "custom_supplier_part_no_code",
                    "description": "Originally ordered quantity from GRN"
                },
                {
                    "fieldname": "custom_column_break_2",
                    "fieldtype": "Column Break",
                    "insert_after": "custom_ordered_quantity"
                },
                {
                    "fieldname": "custom_accepted_warehouse",
                    "label": "Accepted Warehouse",
                    "fieldtype": "Link",
                    "options": "Warehouse",
                    "insert_after": "custom_column_break_2",
                    "description": "Accepted warehouse from GRN"
                },
                {
                    "fieldname": "custom_shelf_life_months",
                    "label": "Shelf Life (Months)",
                    "fieldtype": "Int",
                    "insert_after": "custom_accepted_warehouse",
                    "description": "Shelf life in months from GRN"
                },
                {
                    "fieldname": "custom_expiration_date",
                    "label": "Expiration Date",
                    "fieldtype": "Date",
                    "insert_after": "custom_shelf_life_months",
                    "description": "Expiration date from GRN"
                },
                
                # GRN Reference Section
                {
                    "fieldname": "custom_grn_notes_section",
                    "label": "GRN Reference & Notes",
                    "fieldtype": "Section Break", 
                    "insert_after": "custom_expiration_date",
                    "collapsible": 1
                },
                {
                    "fieldname": "custom_grn_reference",
                    "label": "GRN Reference",
                    "fieldtype": "Link",
                    "options": "Goods Receipt Note",
                    "insert_after": "custom_grn_notes_section",
                    "read_only": 1,
                    "description": "Reference to source GRN"
                },
                {
                    "fieldname": "custom_grn_item_reference",
                    "label": "GRN Item Reference",
                    "fieldtype": "Data",
                    "insert_after": "custom_grn_reference",
                    "read_only": 1,
                    "description": "Reference to source GRN item"
                },
                {
                    "fieldname": "custom_grn_batch_no",
                    "label": "GRN Batch Number",
                    "fieldtype": "Data",
                    "insert_after": "custom_grn_item_reference",
                    "read_only": 1,
                    "description": "Batch number from source GRN (data field, not validated)"
                },
                {
                    "fieldname": "custom_grn_remarks",
                    "label": "GRN Remarks",
                    "fieldtype": "Text",
                    "insert_after": "custom_grn_item_reference",
                    "description": "Remarks from GRN"
                }
            ]
        }
        
        # Create the custom fields
        create_custom_fields(custom_fields, ignore_validate=True)

        pr_field_count = len(custom_fields["Purchase Receipt"])
        pri_field_count = len(custom_fields["Purchase Receipt Item"])
        total_field_count = pr_field_count + pri_field_count

        frappe.logger().info(f"Successfully created {pr_field_count} Purchase Receipt fields and {pri_field_count} Purchase Receipt Item fields")

        # Show success message
        print(f"✅ Purchase Receipt: Created {pr_field_count} custom fields")
        print(f"✅ Purchase Receipt Item: Created {pri_field_count} custom fields for enhanced GRN data mapping")
        print(f"📊 Total: {total_field_count} custom fields created")
        
        return True
        
    except Exception as e:
        error_msg = f"Error creating Purchase Receipt Item custom fields: {str(e)}"
        frappe.logger().error(error_msg)
        frappe.log_error(error_msg, "Purchase Receipt Custom Fields Creation")
        print(f"❌ Error: {error_msg}")
        return False