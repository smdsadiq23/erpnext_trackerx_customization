#!/usr/bin/env python3

import frappe
from erpnext_trackerx_customization.erpnext_doctype_hooks.workflow.grn_workflow import create_inspections_on_grn_submit

def test_grn_submission():
    """Test GRN submission and workflow"""
    
    frappe.init(site="trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    grn_name = "GRN-PRE-2025-00018"
    
    try:
        # Get the GRN document
        grn = frappe.get_doc("Goods Receipt Note", grn_name)
        
        print(f"GRN Status before submission: {grn.docstatus}")
        print(f"GRN has {len(grn.items)} items")
        
        # Check each item's inspection requirement
        for item in grn.items:
            item_doc = frappe.get_doc("Item", item.item_code)
            inspection_required = getattr(item_doc, 'inspection_required_before_purchase', 0)
            print(f"Item: {item.item_code}, Material Type: {item.material_type}, Inspection Required: {inspection_required}")
        
        # Submit the GRN if not already submitted
        if grn.docstatus == 0:
            print("Submitting GRN...")
            grn.submit()
            print("GRN submitted successfully!")
        else:
            print("GRN already submitted")
            
        # Manually trigger the workflow to test
        print("Testing workflow...")
        create_inspections_on_grn_submit(grn, "on_submit")
        
        # Check for created Purchase Receipts
        purchase_receipts = frappe.db.sql("""
            SELECT name, supplier, posting_date, docstatus 
            FROM `tabPurchase Receipt` 
            WHERE creation >= CURDATE() 
            ORDER BY creation DESC
        """, as_dict=True)
        
        print(f"\nPurchase Receipts created today: {len(purchase_receipts)}")
        for pr in purchase_receipts:
            print(f"  - {pr.name} | {pr.supplier} | Status: {pr.docstatus}")
            
        # Check for created inspections
        fabric_inspections = frappe.db.sql("""
            SELECT name, grn_reference, material_type, inspection_status
            FROM `tabFabric Inspection`
            WHERE creation >= CURDATE()
            ORDER BY creation DESC
        """, as_dict=True)
        
        trims_inspections = frappe.db.sql("""
            SELECT name, grn_reference, material_type, inspection_status
            FROM `tabTrims Inspection`
            WHERE creation >= CURDATE()
            ORDER BY creation DESC
        """, as_dict=True)
        
        print(f"\nFabric Inspections created today: {len(fabric_inspections)}")
        for fi in fabric_inspections:
            print(f"  - {fi.name} | GRN: {fi.grn_reference} | Material: {fi.material_type}")
            
        print(f"\nTrims Inspections created today: {len(trims_inspections)}")
        for ti in trims_inspections:
            print(f"  - {ti.name} | GRN: {ti.grn_reference} | Material: {ti.material_type}")
            
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        frappe.log_error(f"GRN submission test error: {str(e)}", "GRN Test")
        return False
    
    finally:
        frappe.db.commit()

if __name__ == "__main__":
    test_grn_submission()