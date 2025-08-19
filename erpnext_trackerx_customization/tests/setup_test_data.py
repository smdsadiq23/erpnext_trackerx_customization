#!/usr/bin/env python3
"""
Create Dummy Master Data for Testing Complete Trims Inspection Workflow
"""

import frappe
from frappe.utils import today, nowtime


def create_test_suppliers():
    """Create test suppliers"""
    print("\n=== CREATING TEST SUPPLIERS ===")
    
    suppliers = [
        {
            "name": "Quality Trims Supplier Ltd",
            "supplier_type": "Company",
            "country": "India"
        },
        {
            "name": "Fabric World Pvt Ltd", 
            "supplier_type": "Company",
            "country": "India"
        },
        {
            "name": "Office Supplies Co",
            "supplier_type": "Company", 
            "country": "India"
        }
    ]
    
    created_suppliers = []
    for supplier_data in suppliers:
        if not frappe.db.exists("Supplier", supplier_data["name"]):
            supplier = frappe.new_doc("Supplier")
            supplier.supplier_name = supplier_data["name"]
            supplier.supplier_type = supplier_data["supplier_type"]
            supplier.country = supplier_data["country"]
            supplier.save()
            created_suppliers.append(supplier.name)
            print(f"   ✓ Created supplier: {supplier.name}")
        else:
            print(f"   → Supplier already exists: {supplier_data['name']}")
    
    frappe.db.commit()
    return created_suppliers


def create_test_items():
    """Create test items with different inspection requirements"""
    print("\n=== CREATING TEST ITEMS ===")
    
    items = [
        # Items requiring inspection
        {
            "item_code": "BUTTON-METAL-001",
            "item_name": "Metal Button - Silver 15mm",
            "item_group": "Raw Material",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "custom_material_type": "Trims",
            "custom_requires_inspection": 1,
            "inspection_required_before_purchase": 1,
            "custom_preferred_supplier": "Quality Trims Supplier Ltd",
            "custom_select_master": "Trims"
        },
        {
            "item_code": "ZIPPER-YKK-001", 
            "item_name": "YKK Zipper - 12 inch Closed End",
            "item_group": "Raw Material",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "custom_material_type": "Trims",
            "custom_requires_inspection": 1,
            "inspection_required_before_purchase": 1,
            "custom_preferred_supplier": "Quality Trims Supplier Ltd",
            "custom_select_master": "Trims"
        },
        {
            "item_code": "FABRIC-COTTON-001",
            "item_name": "Cotton Fabric - Plain Weave 60 GSM",
            "item_group": "Raw Material", 
            "stock_uom": "Meter",
            "is_stock_item": 1,
            "custom_material_type": "Fabric",
            "custom_requires_inspection": 1,
            "inspection_required_before_purchase": 1,
            "custom_preferred_supplier": "Fabric World Pvt Ltd",
            "custom_select_master": "Fabrics"
        },
        
        # Items NOT requiring inspection
        {
            "item_code": "OFFICE-PAPER-001",
            "item_name": "A4 Paper - 70 GSM",
            "item_group": "Consumable",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "custom_material_type": None,
            "custom_requires_inspection": 0,
            "inspection_required_before_purchase": 0,
            "custom_preferred_supplier": "Office Supplies Co",
            "custom_select_master": None
        },
        {
            "item_code": "OFFICE-PEN-001",
            "item_name": "Ball Point Pen - Blue", 
            "item_group": "Consumable",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "custom_material_type": None,
            "custom_requires_inspection": 0,
            "inspection_required_before_purchase": 0,
            "custom_preferred_supplier": "Office Supplies Co",
            "custom_select_master": None
        }
    ]
    
    created_items = []
    for item_data in items:
        if not frappe.db.exists("Item", item_data["item_code"]):
            item = frappe.new_doc("Item")
            for field, value in item_data.items():
                if value is not None:
                    setattr(item, field, value)
            item.save()
            created_items.append(item.item_code)
            inspection_req = "Yes" if item_data.get("inspection_required_before_purchase") else "No"
            print(f"   ✓ Created item: {item.item_code} (Inspection: {inspection_req})")
        else:
            print(f"   → Item already exists: {item_data['item_code']}")
    
    frappe.db.commit()
    return created_items


def create_test_defect_masters():
    """Create test defect master data"""
    print("\n=== CREATING TEST DEFECT MASTERS ===")
    
    defects = [
        # Physical defects for Trims Inspection
        {"code": "BROKEN", "category": "Physical Defects", "inspection_type": "Trims Inspection", "description": "Broken or cracked component"},
        {"code": "MISSING", "category": "Physical Defects", "inspection_type": "Trims Inspection", "description": "Missing component or part"},
        {"code": "DENT", "category": "Physical Defects", "inspection_type": "Trims Inspection", "description": "Dent or deformation"},
        {"code": "ROUGH_EDGE", "category": "Physical Defects", "inspection_type": "Trims Inspection", "description": "Rough or sharp edge"},
        
        # Visual defects for Trims Inspection
        {"code": "WRONG_COLOR", "category": "Visual Defects", "inspection_type": "Trims Inspection", "description": "Wrong color specification"},
        {"code": "DISCOLORATION", "category": "Visual Defects", "inspection_type": "Trims Inspection", "description": "Color variation or fading"},
        {"code": "STAIN", "category": "Visual Defects", "inspection_type": "Trims Inspection", "description": "Minor staining or marking"},
        {"code": "SMALL_SPOT", "category": "Visual Defects", "inspection_type": "Trims Inspection", "description": "Small spot or blemish"},
        
        # Functional defects for Trims Inspection
        {"code": "CONTAMINATION", "category": "Functional Defects", "inspection_type": "Trims Inspection", "description": "Chemical or physical contamination"},
        {"code": "SCRATCH", "category": "Functional Defects", "inspection_type": "Trims Inspection", "description": "Surface scratch or abrasion"},
        {"code": "MINOR_MARK", "category": "Functional Defects", "inspection_type": "Trims Inspection", "description": "Minor cosmetic marking"}
    ]
    
    created_defects = []
    for defect in defects:
        if not frappe.db.exists("Defect Master", defect["code"]):
            defect_doc = frappe.new_doc("Defect Master")
            defect_doc.defect_code = defect["code"]
            defect_doc.defect_name = defect["description"]  # Use description as name
            defect_doc.defect_category = defect["category"]
            defect_doc.description = defect["description"]
            defect_doc.inspection_type = defect["inspection_type"]
            defect_doc.save()
            created_defects.append(defect["code"])
            print(f"   ✓ Created defect: {defect['code']} ({defect['category']})")
        else:
            print(f"   → Defect already exists: {defect['code']}")
    
    frappe.db.commit()
    return created_defects


def create_aql_levels():
    """Create AQL levels if they don't exist"""
    print("\n=== CREATING AQL LEVELS ===")
    
    aql_levels = [
        {"level_code": "1", "level_name": "General Inspection Level I", "description": "Light inspection level"},
        {"level_code": "2", "level_name": "General Inspection Level II", "description": "Standard inspection level"},
        {"level_code": "3", "level_name": "General Inspection Level III", "description": "Tight inspection level"}
    ]
    
    created_levels = []
    for level in aql_levels:
        if not frappe.db.exists("AQL Level", level["level_code"]):
            aql_level = frappe.new_doc("AQL Level")
            aql_level.level_code = level["level_code"]
            aql_level.level_name = level["level_name"]
            aql_level.description = level["description"]
            aql_level.save()
            created_levels.append(level["level_code"])
            print(f"   ✓ Created AQL Level: {level['level_code']}")
        else:
            print(f"   → AQL Level already exists: {level['level_code']}")
    
    frappe.db.commit()
    return created_levels


def verify_master_data():
    """Verify all master data is created correctly"""
    print("\n=== VERIFYING MASTER DATA ===")
    
    # Check suppliers
    suppliers = frappe.db.count("Supplier", filters={"supplier_name": ["like", "%Test%"]})
    print(f"   ✓ Test suppliers created: {suppliers}")
    
    # Check items
    inspection_items = frappe.db.count("Item", filters={"inspection_required_before_purchase": 1})
    non_inspection_items = frappe.db.count("Item", filters={"inspection_required_before_purchase": 0})
    print(f"   ✓ Items requiring inspection: {inspection_items}")
    print(f"   ✓ Items not requiring inspection: {non_inspection_items}")
    
    # Check defects
    critical_defects = frappe.db.count("Defect Master", filters={"defect_category": "Critical"})
    major_defects = frappe.db.count("Defect Master", filters={"defect_category": "Major"})
    minor_defects = frappe.db.count("Defect Master", filters={"defect_category": "Minor"})
    print(f"   ✓ Critical defects: {critical_defects}")
    print(f"   ✓ Major defects: {major_defects}")
    print(f"   ✓ Minor defects: {minor_defects}")
    
    # Check AQL levels
    aql_levels = frappe.db.count("AQL Level")
    print(f"   ✓ AQL levels: {aql_levels}")
    
    return {
        "suppliers": suppliers,
        "inspection_items": inspection_items,
        "non_inspection_items": non_inspection_items,
        "defects": {"critical": critical_defects, "major": major_defects, "minor": minor_defects},
        "aql_levels": aql_levels
    }


def create_all_dummy_data():
    """Create all dummy master data"""
    print("=" * 80)
    print("CREATING DUMMY MASTER DATA FOR TESTING")
    print("=" * 80)
    
    try:
        # Create suppliers
        suppliers = create_test_suppliers()
        
        # Create items
        items = create_test_items()
        
        # Create defect masters
        defects = create_test_defect_masters()
        
        # Create AQL levels
        aql_levels = create_aql_levels()
        
        # Verify all data
        verification = verify_master_data()
        
        print("\n" + "=" * 80)
        print("🎉 ALL DUMMY MASTER DATA CREATED SUCCESSFULLY!")
        print(f"   ✅ Suppliers: {len(suppliers)} created")
        print(f"   ✅ Items: {len(items)} created")
        print(f"   ✅ Defects: {len(defects)} created")
        print(f"   ✅ AQL Levels: {len(aql_levels)} created")
        print("\n📋 MASTER DATA SUMMARY:")
        print(f"   • Total suppliers: {verification['suppliers']}")
        print(f"   • Items requiring inspection: {verification['inspection_items']}")
        print(f"   • Items not requiring inspection: {verification['non_inspection_items']}")
        print(f"   • Defect categories: Critical({verification['defects']['critical']}) Major({verification['defects']['major']}) Minor({verification['defects']['minor']})")
        print(f"   • AQL levels: {verification['aql_levels']}")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ DUMMY DATA CREATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Setup Frappe environment
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    # Create dummy data
    success = create_all_dummy_data()
    
    # Exit with appropriate code
    exit(0 if success else 1)