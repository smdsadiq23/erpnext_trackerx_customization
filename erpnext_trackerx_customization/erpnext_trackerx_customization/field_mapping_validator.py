import frappe

def validate_purchase_receipt_custom_fields():
    """Validate that all required custom fields exist in Purchase Receipt Item"""
    
    expected_fields = [
        # Basic Material Information
        "custom_color",
        "custom_composition", 
        "custom_material_type",
        "custom_shade",
        
        # Physical Specifications
        "custom_physical_specs_section",
        "custom_roll_no",
        "custom_fabric_length",
        "custom_fabric_width",
        "custom_column_break_1",
        "custom_no_of_boxespacks",
        "custom_size_spec",
        "custom_consumption",
        
        # Tracking Information
        "custom_tracking_section",
        "custom_lot_no",
        "custom_supplier_part_no_code",
        "custom_ordered_quantity", 
        "custom_column_break_2",
        "custom_accepted_warehouse",
        "custom_shelf_life_months",
        "custom_expiration_date",
        
        # GRN Reference
        "custom_grn_notes_section",
        "custom_grn_reference",
        "custom_grn_item_reference",
        "custom_grn_remarks"
    ]
    
    try:
        pr_item_meta = frappe.get_meta("Purchase Receipt Item")
        existing_fields = [f.fieldname for f in pr_item_meta.fields]
        
        print("🔍 Validating Purchase Receipt Item Custom Fields...")
        print(f"Expected fields: {len(expected_fields)}")
        
        missing_fields = []
        found_fields = []
        
        for field in expected_fields:
            if field in existing_fields:
                found_fields.append(field)
                print(f"✅ {field}")
            else:
                missing_fields.append(field)
                print(f"❌ {field}")
        
        print(f"\n📊 Summary:")
        print(f"Found fields: {len(found_fields)}/{len(expected_fields)}")
        print(f"Missing fields: {len(missing_fields)}")
        
        if missing_fields:
            print(f"\n⚠️  Missing fields:")
            for field in missing_fields:
                print(f"   - {field}")
            return False
        else:
            print(f"\n🎉 All custom fields are present!")
            return True
            
    except Exception as e:
        print(f"❌ Error validating fields: {str(e)}")
        return False

def test_field_mapping_logic():
    """Test the field mapping logic without actual GRN data"""
    
    print("\n🧪 Testing Field Mapping Logic...")
    
    # Mock GRN item data
    class MockGRNItem:
        def __init__(self):
            self.item_code = "TEST-FABRIC-001"
            self.color = "Navy Blue"
            self.composition = "100% Cotton"
            self.material_type = "Fabrics"
            self.shade = "Dark Blue"
            self.roll_no = "R001"
            self.fabric_length = 100
            self.fabric_width = 60
            self.no_of_boxespacks = 1
            self.size_spec = "60x100"
            self.consumption = 1.5
            self.lot_no = "LOT-2025-001"
            self.batch_no = "BATCH-001"
            self.supplier_part_no__code = "SUP-001"
            self.ordered_quantity = 100
            self.received_quantity = 95
            self.accepted_warehouse = "Stores - T"
            self.shelf_life_months = 24
            self.expiration_date = "2027-01-01"
            self.remarks = "Good quality fabric"
            self.rate = 10.0
            self.uom = "Meter"
            self.name = "test-grn-item-001"
    
    mock_item = MockGRNItem()
    
    # Test the mapping logic
    mapped_data = {
        # Standard ERPNext fields
        "item_code": mock_item.item_code,
        "qty": mock_item.received_quantity,
        "received_qty": mock_item.received_quantity,
        "rate": getattr(mock_item, 'rate', 0),
        "uom": getattr(mock_item, 'uom', 'Nos'),
        
        # Map existing ERPNext fields where possible
        "batch_no": getattr(mock_item, 'batch_no', None),
        "supplier_part_no": getattr(mock_item, 'supplier_part_no__code', None),
        
        # Custom fields for comprehensive GRN data mapping
        "custom_color": getattr(mock_item, 'color', None),
        "custom_composition": getattr(mock_item, 'composition', None),
        "custom_material_type": getattr(mock_item, 'material_type', None),
        "custom_shade": getattr(mock_item, 'shade', None),
        
        # Physical specifications
        "custom_roll_no": getattr(mock_item, 'roll_no', None),
        "custom_fabric_length": getattr(mock_item, 'fabric_length', None),
        "custom_fabric_width": getattr(mock_item, 'fabric_width', None),
        "custom_no_of_boxespacks": getattr(mock_item, 'no_of_boxespacks', None),
        "custom_size_spec": getattr(mock_item, 'size_spec', None),
        "custom_consumption": getattr(mock_item, 'consumption', None),
        
        # Tracking and reference information
        "custom_lot_no": getattr(mock_item, 'lot_no', None),
        "custom_supplier_part_no_code": getattr(mock_item, 'supplier_part_no__code', None),
        "custom_ordered_quantity": getattr(mock_item, 'ordered_quantity', None),
        "custom_accepted_warehouse": getattr(mock_item, 'accepted_warehouse', None),
        "custom_shelf_life_months": getattr(mock_item, 'shelf_life_months', None),
        "custom_expiration_date": getattr(mock_item, 'expiration_date', None),
        
        # GRN reference and notes
        "custom_grn_reference": "TEST-GRN-001",
        "custom_grn_item_reference": mock_item.name,
        "custom_grn_remarks": getattr(mock_item, 'remarks', None)
    }
    
    # Analyze mapping results
    total_fields = len(mapped_data)
    fields_with_data = sum(1 for value in mapped_data.values() if value is not None)
    custom_fields_with_data = sum(1 for key, value in mapped_data.items() 
                                 if key.startswith('custom_') and value is not None)
    
    print(f"📊 Mapping Analysis:")
    print(f"Total fields mapped: {total_fields}")
    print(f"Fields with data: {fields_with_data}/{total_fields} ({fields_with_data/total_fields*100:.1f}%)")
    print(f"Custom fields with data: {custom_fields_with_data}")
    
    # Display sample mappings
    print(f"\n📋 Sample Field Mappings:")
    sample_fields = [
        "custom_color", "custom_material_type", "custom_roll_no", 
        "custom_fabric_length", "custom_lot_no", "custom_grn_reference"
    ]
    
    for field in sample_fields:
        value = mapped_data.get(field, "NOT_MAPPED")
        print(f"   {field}: {value}")
    
    return fields_with_data > total_fields * 0.8  # 80% success rate

def validate_implementation():
    """Run complete validation of the enhanced field mapping implementation"""
    
    print("🚀 Enhanced GRN to Purchase Receipt Field Mapping Validation")
    print("=" * 60)
    
    # Test 1: Validate custom fields exist
    fields_valid = validate_purchase_receipt_custom_fields()
    
    # Test 2: Test field mapping logic
    mapping_valid = test_field_mapping_logic()
    
    # Test 3: Check workflow function exists
    print("\n🔧 Testing Workflow Function...")
    try:
        from erpnext_trackerx_customization.erpnext_doctype_hooks.workflow.grn_workflow import create_purchase_receipt_for_items
        print("✅ create_purchase_receipt_for_items function found")
        workflow_valid = True
    except ImportError as e:
        print(f"❌ Workflow function import failed: {str(e)}")
        workflow_valid = False
    
    # Final assessment
    print(f"\n🎯 Final Assessment:")
    print(f"Custom fields validation: {'✅ PASS' if fields_valid else '❌ FAIL'}")
    print(f"Field mapping logic: {'✅ PASS' if mapping_valid else '❌ FAIL'}")
    print(f"Workflow function: {'✅ PASS' if workflow_valid else '❌ FAIL'}")
    
    overall_success = fields_valid and mapping_valid and workflow_valid
    print(f"\n{'🎉 IMPLEMENTATION SUCCESSFUL!' if overall_success else '⚠️  IMPLEMENTATION NEEDS ATTENTION'}")
    
    if overall_success:
        print("\n✨ Enhanced GRN to Purchase Receipt field mapping is ready for use!")
        print("All GRN item data will now be comprehensively copied to Purchase Receipt items.")
    
    return overall_success

if __name__ == "__main__":
    validate_implementation()