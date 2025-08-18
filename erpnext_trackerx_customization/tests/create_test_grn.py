#!/usr/bin/env python3
"""
Create Test GRN with Mixed Inspection and Non-Inspection Items
"""

import frappe
from frappe.utils import today, nowtime


def create_purchase_order_first(supplier, items):
    """Create a Purchase Order first"""
    print(f"   Creating Purchase Order for supplier: {supplier}")
    
    po = frappe.new_doc("Purchase Order")
    po.supplier = supplier
    po.transaction_date = today()
    po.schedule_date = today()
    
    for idx, item in enumerate(items, 1):
        po.append("items", {
            "item_code": item["item_code"],
            "item_name": item["item_name"],
            "qty": item["qty"],
            "uom": "Nos",
            "rate": item["rate"],
            "amount": item["qty"] * item["rate"],
            "schedule_date": today()
        })
    
    po.save()
    po.submit()
    print(f"   ✓ Purchase Order created: {po.name}")
    return po.name


def create_mixed_test_grn():
    """Create a test GRN with both inspection and non-inspection items"""
    print("\n=== CREATING TEST GRN WITH MIXED ITEMS ===")
    
    # Get the latest items created
    inspection_items = frappe.db.sql("""
        SELECT item_code, item_name, custom_preferred_supplier
        FROM `tabItem` 
        WHERE inspection_required_before_purchase = 1 
        AND (item_code LIKE '%TRM-%' OR item_code LIKE '%FAB-%')
        ORDER BY creation DESC 
        LIMIT 2
    """, as_dict=True)
    
    non_inspection_items = frappe.db.sql("""
        SELECT item_code, item_name, custom_preferred_supplier
        FROM `tabItem` 
        WHERE inspection_required_before_purchase = 0 
        AND item_code LIKE '%FG-%'
        ORDER BY creation DESC 
        LIMIT 2
    """, as_dict=True)
    
    print(f"   Found {len(inspection_items)} inspection items")
    print(f"   Found {len(non_inspection_items)} non-inspection items")
    
    if not inspection_items or not non_inspection_items:
        print("   ❌ No suitable items found for GRN creation")
        return None
    
    # Use the first inspection item's supplier
    supplier = inspection_items[0].get('custom_preferred_supplier') or "Quality Trims Supplier Ltd"
    
    # Prepare all items for PO
    all_items = []
    
    # Add inspection items
    for idx, item in enumerate(inspection_items, 1):
        qty = 100 + (idx * 50)
        rate = 5.00 + idx
        all_items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": qty,
            "rate": rate,
            "requires_inspection": 1
        })
    
    # Add non-inspection items  
    for idx, item in enumerate(non_inspection_items, 1):
        qty = 20 + (idx * 10)
        rate = 2.00 + idx
        all_items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": qty,
            "rate": rate,
            "requires_inspection": 0
        })
    
    # Create Purchase Order first
    po_name = create_purchase_order_first(supplier, all_items)
    
    # Create GRN
    grn = frappe.new_doc("Goods Receipt Note")
    grn.supplier = supplier
    grn.posting_date = today()
    grn.posting_time = nowtime()
    grn.set_posting_time = 1
    grn.purchase_order = po_name
    
    print(f"   Creating GRN for supplier: {supplier}")
    
    # Add all items to GRN
    for idx, item in enumerate(all_items, 1):
        grn_item = {
            "item_code": item["item_code"],
            "item_name": item["item_name"],
            "qty": item["qty"],
            "received_quantity": item["qty"],
            "uom": "Nos",
            "rate": item["rate"],
            "amount": item["qty"] * item["rate"],
            "custom_requires_inspection": item["requires_inspection"],
            "roll_no": f"ROLL-{idx:03d}"  # Set roll_no before appending
        }
        
        grn.append("items", grn_item)
        
        inspection_text = "Inspection" if item["requires_inspection"] else "Non-Inspection"
        print(f"   → Added {inspection_text} item: {item['item_code']} (Qty: {item['qty']})")
    
    # Save GRN
    grn.save()
    print(f"   ✓ GRN created: {grn.name}")
    
    # Display GRN summary
    inspection_items_count = sum(1 for item in all_items if item["requires_inspection"])
    non_inspection_items_count = sum(1 for item in all_items if not item["requires_inspection"])
    total_amount = sum(item["qty"] * item["rate"] for item in all_items)
    
    print(f"   📋 GRN Summary:")
    print(f"      • GRN Number: {grn.name}")
    print(f"      • Purchase Order: {po_name}")
    print(f"      • Supplier: {grn.supplier}")
    print(f"      • Total Items: {len(all_items)}")
    print(f"      • Inspection Items: {inspection_items_count}")
    print(f"      • Non-Inspection Items: {non_inspection_items_count}")
    print(f"      • Total Amount: {total_amount:.2f}")
    
    frappe.db.commit()
    return grn.name


def submit_test_grn_and_check_workflow(grn_name):
    """Submit the test GRN and check if workflow triggers correctly"""
    print(f"\n=== SUBMITTING TEST GRN: {grn_name} ===")
    
    try:
        grn = frappe.get_doc("Goods Receipt Note", grn_name)
        
        print("   Submitting GRN...")
        grn.submit()
        
        print(f"   ✓ GRN {grn_name} submitted successfully")
        
        # Check for created inspections
        print("   Checking for created inspections...")
        
        # Check Trims Inspections
        trims_inspections = frappe.db.get_list(
            "Trims Inspection",
            filters={"grn_reference": grn_name},
            fields=["name", "item_code", "material_type", "inspection_status"]
        )
        
        # Check Fabric Inspections
        fabric_inspections = frappe.db.get_list(
            "Fabric Inspection", 
            filters={"grn_reference": grn_name},
            fields=["name", "item_code", "material_type", "inspection_status"]
        )
        
        # Check Purchase Receipts - search by supplier and recent creation
        purchase_receipts = frappe.db.get_list(
            "Purchase Receipt",
            filters={
                "supplier": grn.supplier,
                "creation": [">=", frappe.utils.add_days(frappe.utils.today(), -1)]
            },
            fields=["name", "supplier", "docstatus"],
            limit=10
        )
        
        print(f"   📋 Workflow Results:")
        print(f"      • Trims Inspections created: {len(trims_inspections)}")
        for inspection in trims_inspections:
            print(f"        - {inspection.name} ({inspection.item_code}) - {inspection.inspection_status}")
        
        print(f"      • Fabric Inspections created: {len(fabric_inspections)}")
        for inspection in fabric_inspections:
            print(f"        - {inspection.name} ({inspection.item_code}) - {inspection.inspection_status}")
        
        print(f"      • Purchase Receipts created: {len(purchase_receipts)}")
        for pr in purchase_receipts:
            status = "Draft" if pr.docstatus == 0 else "Submitted" if pr.docstatus == 1 else "Cancelled"
            print(f"        - {pr.name} ({pr.supplier}) - {status}")
        
        return {
            "grn_name": grn_name,
            "trims_inspections": trims_inspections,
            "fabric_inspections": fabric_inspections,
            "purchase_receipts": purchase_receipts
        }
        
    except Exception as e:
        print(f"   ❌ Error submitting GRN: {str(e)}")
        raise e


def run_grn_workflow_test():
    """Run complete GRN workflow test"""
    print("=" * 80)
    print("RUNNING GRN WORKFLOW TEST WITH REAL DATA")
    print("=" * 80)
    
    try:
        # Step 1: Create test GRN
        grn_name = create_mixed_test_grn()
        if not grn_name:
            return False
        
        # Step 2: Submit GRN and check workflow
        workflow_results = submit_test_grn_and_check_workflow(grn_name)
        
        print("\n" + "=" * 80)
        print("🎉 GRN WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        print(f"   ✅ GRN created and submitted: {grn_name}")
        print(f"   ✅ Inspections created: {len(workflow_results['trims_inspections']) + len(workflow_results['fabric_inspections'])}")
        print(f"   ✅ Purchase Receipts created: {len(workflow_results['purchase_receipts'])}")
        print("\n🔄 NEXT STEPS:")
        print("   • Test inspection workflows with created inspections")
        print("   • Verify status transitions")
        print("   • Test defects entry and calculations")
        print("=" * 80)
        
        return workflow_results
        
    except Exception as e:
        print(f"\n❌ GRN WORKFLOW TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Setup Frappe environment
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    # Run GRN workflow test
    success = run_grn_workflow_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)