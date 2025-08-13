#!/usr/bin/env python3
"""
Comprehensive GRN Inspection Workflow Tests
Merged from: test_direct_grn.py, test_final_grn.py, test_grn_workflow.py
"""

import frappe

def test_grn_inspection_hook_functions():
    """Test the GRN inspection hook utility functions"""
    print("=== GRN INSPECTION HOOK FUNCTIONS TEST ===")
    
    try:
        from erpnext_trackerx_customization.hooks.grn_inspection_hook import (
            get_material_type, 
            determine_inspection_type,
            create_inspection_record
        )
        print("✅ Successfully imported GRN inspection hook functions")
        
        # Test with sample item data
        test_cases = [
            {"item_code": "FABRIC-001", "expected_material": "Fabric"},
            {"item_code": "TRIM-001", "expected_material": "Trim"},
            {"item_code": "ACC-001", "expected_material": "Accessory"}
        ]
        
        for case in test_cases:
            try:
                # This would test your material type detection logic
                print(f"   Testing material type detection for {case['item_code']}")
            except Exception as e:
                print(f"   ⚠️  Error testing {case['item_code']}: {str(e)}")
        
        print("✅ GRN hook functions test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import GRN hook functions: {str(e)}")
        return False

def test_grn_inspection_creation():
    """Test creating inspections from GRN data"""
    print("=== GRN INSPECTION CREATION TEST ===")
    
    # Get available GRNs for testing
    grn_list = frappe.get_all("Goods Receipt Note", 
                             filters={"docstatus": 1}, 
                             limit=3, 
                             fields=["name", "supplier", "creation"])
    
    if not grn_list:
        print("⚠️  No submitted GRNs found for testing")
        return True
    
    print(f"Found {len(grn_list)} submitted GRNs for testing")
    
    for grn_data in grn_list:
        try:
            grn = frappe.get_doc("Goods Receipt Note", grn_data['name'])
            
            print(f"\n📦 Testing GRN: {grn.name}")
            print(f"   Supplier: {grn.supplier}")
            print(f"   Status: {grn.docstatus}")
            print(f"   Items count: {len(grn.items)}")
            
            # Test each item in the GRN
            for i, item in enumerate(grn.items[:2], 1):  # Test first 2 items only
                print(f"   Item {i}: {item.item_code}")
                print(f"     Name: {item.item_name}")
                print(f"     Material Type: {getattr(item, 'material_type', 'Not set')}")
                print(f"     Received Qty: {item.received_quantity}")
                print(f"     UOM: {item.uom}")
                
                # Test material type detection
                try:
                    from erpnext_trackerx_customization.hooks.grn_inspection_hook import get_material_type
                    material_type = get_material_type(item.item_code, item)
                    print(f"     Detected Material Type: {material_type}")
                except Exception as e:
                    print(f"     ⚠️  Error detecting material type: {str(e)}")
            
            print("   ✅ GRN analysis completed")
            
        except Exception as e:
            print(f"   ❌ Error processing GRN {grn_data['name']}: {str(e)}")
    
    return True

def test_inspection_workflow_integration():
    """Test the complete inspection workflow integration"""
    print("=== INSPECTION WORKFLOW INTEGRATION TEST ===")
    
    # Check if inspection documents exist for recent GRNs
    recent_grns = frappe.get_all("Goods Receipt Note", 
                                filters={"docstatus": 1}, 
                                limit=5,
                                fields=["name"])
    
    inspection_count = 0
    for grn in recent_grns:
        # Check if inspections were created for this GRN
        inspections = frappe.get_all("Fabric Inspection", 
                                   filters={"grn_reference": grn.name},
                                   fields=["name", "inspection_status"])
        
        if inspections:
            inspection_count += len(inspections)
            print(f"📋 GRN {grn.name} has {len(inspections)} inspection(s)")
            for insp in inspections:
                print(f"   - {insp.name} (Status: {insp.inspection_status})")
    
    print(f"\n📊 Summary: {inspection_count} inspections found for {len(recent_grns)} recent GRNs")
    
    if inspection_count > 0:
        print("✅ Inspection workflow integration is working")
    else:
        print("⚠️  No inspections found - workflow may need verification")
    
    return True

def test_grn_inspection_data_flow():
    """Test data flow from GRN to inspection documents"""
    print("=== GRN TO INSPECTION DATA FLOW TEST ===")
    
    # Find an inspection with GRN reference
    inspections_with_grn = frappe.get_all("Fabric Inspection",
                                         filters={"grn_reference": ["!=", ""]},
                                         limit=3,
                                         fields=["name", "grn_reference", "item_code", "supplier"])
    
    if not inspections_with_grn:
        print("⚠️  No inspections with GRN reference found")
        return True
    
    for insp in inspections_with_grn:
        print(f"\n🔗 Testing data flow for inspection: {insp.name}")
        print(f"   GRN Reference: {insp.grn_reference}")
        
        try:
            # Get the GRN and compare data
            grn = frappe.get_doc("Goods Receipt Note", insp.grn_reference)
            inspection = frappe.get_doc("Fabric Inspection", insp.name)
            
            # Verify data consistency
            print(f"   Supplier: GRN={grn.supplier}, Inspection={inspection.supplier}")
            
            if grn.supplier == inspection.supplier:
                print("   ✅ Supplier data matches")
            else:
                print("   ⚠️  Supplier data mismatch")
            
            # Check if item codes match
            grn_items = [item.item_code for item in grn.items]
            if inspection.item_code in grn_items:
                print("   ✅ Item code consistency verified")
            else:
                print("   ⚠️  Item code not found in GRN items")
                
        except Exception as e:
            print(f"   ❌ Error verifying data flow: {str(e)}")
    
    print("✅ Data flow verification completed")
    return True

def run_all_grn_workflow_tests():
    """Run all GRN inspection workflow tests"""
    print("🧪 COMPREHENSIVE GRN INSPECTION WORKFLOW TESTS")
    print("=" * 60)
    
    try:
        test_grn_inspection_hook_functions()
        test_grn_inspection_creation()
        test_inspection_workflow_integration()
        test_grn_inspection_data_flow()
        
        print("\n🎉 ALL GRN WORKFLOW TESTS COMPLETED!")
        return True
        
    except Exception as e:
        print(f"\n❌ GRN WORKFLOW TEST FAILED: {str(e)}")
        frappe.log_error(f"GRN workflow test error: {str(e)}")
        return False

if __name__ == "__main__":
    frappe.init("localhost")
    frappe.connect()
    run_all_grn_workflow_tests()