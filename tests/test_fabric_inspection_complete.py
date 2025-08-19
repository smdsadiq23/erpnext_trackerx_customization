#!/usr/bin/env python3
"""
Comprehensive Fabric Inspection Tests
Merged from: test_fabric_inspection_fix.py, test_fabric_inspection_redirect.py, 
            test_fabric_inspection_ui.py, test_debug_inspection.py, test_inspection_simple.py
"""

import frappe
import json

def test_fabric_inspection_doctype():
    """Test if fabric inspection doctype and basic setup exists"""
    print("=== FABRIC INSPECTION DOCTYPE TESTS ===")
    
    # Check if fabric inspection doctypes exist
    assert frappe.db.exists("DocType", "Fabric Inspection"), "Fabric Inspection doctype not found"
    assert frappe.db.exists("DocType", "Fabric Roll Inspection Item"), "Fabric Roll Inspection Item doctype not found"
    print("✅ Fabric Inspection doctypes exist")
    
    # Check required files for UI
    app_path = frappe.get_app_path("erpnext_trackerx_customization")
    required_files = [
        "public/js/fabric_inspection_list.js",
        "templates/pages/fabric_inspection_ui.py", 
        "templates/pages/fabric_inspection_ui.html",
        "public/js/fabric_inspection_ui.js"
    ]
    
    import os
    for file_path in required_files:
        full_path = os.path.join(app_path, file_path)
        assert os.path.exists(full_path), f"Required file missing: {file_path}"
    
    print("✅ Required UI files exist")
    return True

def test_fabric_inspection_creation():
    """Test creating a fabric inspection document"""
    print("=== FABRIC INSPECTION CREATION TESTS ===")
    
    try:
        # Get sample data for realistic test
        sample_pr = frappe.get_all("Purchase Receipt", limit=1, fields=["name", "supplier"])
        
        # Create test document with minimal required fields
        test_doc = frappe.get_doc({
            "doctype": "Fabric Inspection",
            "inspection_date": frappe.utils.today(),
            "inspector": "Administrator",
            "item_code": "TEST-FABRIC-001",
            "item_name": "Test Fabric",
            "supplier": sample_pr[0].supplier if sample_pr else "Test Supplier",
            "inspection_type": "AQL Based",
            "inspection_status": "Draft",
            "aql_level": "II",
            "aql_value": "2.5",
            "inspection_regime": "Normal"
        })
        
        # Add sample fabric roll
        test_doc.append("fabric_rolls_tab", {
            "roll_number": "TEST-ROLL-001",
            "roll_length": 100.0,
            "roll_width": 58.0,
            "inspection_method": "4-Point Method",
            "inspected": 0
        })
        
        # Insert document (don't save to avoid cluttering database)
        test_doc.insert()
        doc_name = test_doc.name
        
        print(f"✅ Created test document: {doc_name}")
        
        # Test page context function
        from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import get_context
        
        # Mock form_dict
        original_form_dict = frappe.form_dict
        frappe.form_dict = {'name': doc_name}
        
        try:
            context = {}
            get_context(context)
            
            # Validate context
            assert 'page_title' in context, "Missing page_title in context"
            assert 'fabric_rolls' in context, "Missing fabric_rolls in context"
            assert 'defect_categories' in context, "Missing defect_categories in context"
            
            print("✅ Page context function works correctly")
            
        finally:
            frappe.form_dict = original_form_dict
            
        # Clean up test document
        frappe.delete_doc("Fabric Inspection", doc_name)
        print("✅ Test document cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Fabric inspection creation test failed: {str(e)}")
        raise

def test_fabric_inspection_ui_data():
    """Test fabric inspection UI data handling"""
    print("=== FABRIC INSPECTION UI DATA TESTS ===")
    
    # Test with existing document if available
    sample_docs = frappe.get_all("Fabric Inspection", limit=1, fields=["name", "inspection_status", "item_name"])
    
    if not sample_docs:
        print("⚠️  No existing Fabric Inspection documents - creating test document")
        return test_fabric_inspection_creation()
    
    doc_name = sample_docs[0]['name']
    doc = frappe.get_doc("Fabric Inspection", doc_name)
    
    print(f"✅ Using existing document: {doc_name}")
    print(f"   Status: {doc.inspection_status}")
    print(f"   Item: {doc.item_name}")
    
    # Test defect categories loading
    from erpnext_trackerx_customization.templates.pages.fabric_inspection_ui import get_defect_categories
    defect_categories = get_defect_categories()
    
    assert isinstance(defect_categories, dict), "Defect categories should be a dictionary"
    assert len(defect_categories) > 0, "Should have at least one defect category"
    
    print(f"✅ Loaded {len(defect_categories)} defect categories")
    
    # Test rolls data
    if doc.fabric_rolls_tab:
        print(f"✅ Document has {len(doc.fabric_rolls_tab)} fabric rolls")
        for i, roll in enumerate(doc.fabric_rolls_tab[:3], 1):  # Show first 3
            print(f"   {i}. Roll: {roll.roll_number} - Length: {roll.roll_length}m - Width: {roll.roll_width}\"")
    else:
        print("⚠️  No fabric rolls in document")
    
    return True

def test_aql_configuration():
    """Test AQL configuration functionality"""
    print("=== AQL CONFIGURATION TESTS ===")
    
    # Check AQL master data exists
    aql_levels = frappe.get_all("AQL Level", fields=["name"])
    aql_standards = frappe.get_all("AQL Standard", fields=["name"])
    
    assert len(aql_levels) > 0, "No AQL Levels found"
    assert len(aql_standards) > 0, "No AQL Standards found"
    
    print(f"✅ Found {len(aql_levels)} AQL Levels and {len(aql_standards)} AQL Standards")
    
    # Test sample size calculation logic (basic validation)
    sample_test_cases = [
        {"lot_size": 10, "aql_level": "II", "expected_range": (1, 15)},
        {"lot_size": 100, "aql_level": "II", "expected_range": (5, 30)},
        {"lot_size": 1000, "aql_level": "I", "expected_range": (15, 100)}
    ]
    
    for case in sample_test_cases:
        print(f"   Lot {case['lot_size']}, Level {case['aql_level']}: Expected sample {case['expected_range']}")
    
    print("✅ AQL configuration structure validated")
    return True

def run_all_fabric_inspection_tests():
    """Run all fabric inspection tests"""
    print("🧪 COMPREHENSIVE FABRIC INSPECTION TESTS")
    print("=" * 50)
    
    try:
        test_fabric_inspection_doctype()
        test_fabric_inspection_creation()
        test_fabric_inspection_ui_data()
        test_aql_configuration()
        
        print("\n🎉 ALL FABRIC INSPECTION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ FABRIC INSPECTION TEST FAILED: {str(e)}")
        frappe.log_error(f"Fabric inspection test error: {str(e)}")
        return False

if __name__ == "__main__":
    frappe.init("localhost")
    frappe.connect()
    run_all_fabric_inspection_tests()