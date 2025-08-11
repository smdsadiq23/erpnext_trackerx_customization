# -*- coding: utf-8 -*-
"""
Integration tests for AQL Workflow

Tests the complete AQL workflow from Item configuration to Material Inspection.
"""

from __future__ import unicode_literals
import unittest
import frappe
from erpnext_trackerx_customization.erpnext_trackerx_customization.utils.aql_calculator import AQLCalculator


class TestAQLWorkflow(unittest.TestCase):
    """Integration tests for complete AQL workflow"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for the class"""
        frappe.set_user("Administrator")
        
        # Create test AQL Level
        if not frappe.db.exists("AQL Level", "2"):
            aql_level = frappe.get_doc({
                "doctype": "AQL Level",
                "level_code": "2",
                "level_type": "General",
                "description": "Test General Level II",
                "is_active": 1
            })
            aql_level.insert(ignore_permissions=True)
        
        # Create test AQL Standard
        if not frappe.db.exists("AQL Standard", "2.5"):
            aql_standard = frappe.get_doc({
                "doctype": "AQL Standard",
                "aql_value": "2.5",
                "description": "Test 2.5% AQL",
                "is_active": 1
            })
            aql_standard.insert(ignore_permissions=True)
        
        # Create test AQL Table entry
        table_name = "H-2.5-Normal"
        if not frappe.db.exists("AQL Table", table_name):
            aql_table = frappe.get_doc({
                "doctype": "AQL Table",
                "sample_code_letter": "H",
                "sample_size": 50,
                "aql_value": "2.5",
                "inspection_regime": "Normal",
                "acceptance_number": 3,
                "rejection_number": 4,
                "is_active": 1
            })
            aql_table.insert(ignore_permissions=True)
        
        frappe.db.commit()
    
    @classmethod 
    def tearDownClass(cls):
        """Clean up test data"""
        # Clean up test records
        test_items = frappe.get_all("Item", filters={"item_code": ["like", "TEST_AQL_%"]}, pluck="name")
        for item in test_items:
            frappe.delete_doc("Item", item, ignore_permissions=True)
        
        frappe.db.commit()
    
    def test_item_aql_configuration(self):
        """Test Item AQL configuration fields"""
        
        # Create test item with AQL configuration
        item_code = "TEST_AQL_ITEM_001"
        
        if frappe.db.exists("Item", item_code):
            frappe.delete_doc("Item", item_code, ignore_permissions=True)
        
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Test AQL Item",
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "custom_aql_inspection_level": "2",
            "custom_inspection_regime": "Normal",
            "custom_accepted_quality_level": "2.5"
        })
        item.insert(ignore_permissions=True)
        
        # Verify configuration
        saved_item = frappe.get_doc("Item", item_code)
        self.assertEqual(saved_item.custom_aql_inspection_level, "2")
        self.assertEqual(saved_item.custom_inspection_regime, "Normal")
        self.assertEqual(saved_item.custom_accepted_quality_level, "2.5")
    
    def test_aql_criteria_calculation(self):
        """Test full AQL criteria calculation for configured item"""
        
        item_code = "TEST_AQL_ITEM_002"
        
        if frappe.db.exists("Item", item_code):
            frappe.delete_doc("Item", item_code, ignore_permissions=True)
        
        # Create item with AQL configuration
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Test AQL Item 2",
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "custom_aql_inspection_level": "2",
            "custom_inspection_regime": "Normal",
            "custom_accepted_quality_level": "2.5"
        })
        item.insert(ignore_permissions=True)
        
        # Test AQL criteria calculation
        quantity = 500
        aql_data = AQLCalculator.calculate_aql_criteria(item_code, quantity)
        
        # Verify expected values
        self.assertEqual(aql_data["sample_code_letter"], "H")
        self.assertEqual(aql_data["sample_size"], 50)
        self.assertEqual(aql_data["acceptance_number"], 3)
        self.assertEqual(aql_data["rejection_number"], 4)
        self.assertEqual(aql_data["inspection_level"], "2")
        self.assertEqual(aql_data["aql_value"], "2.5")
        self.assertEqual(aql_data["inspection_regime"], "Normal")
    
    def test_material_inspection_item_integration(self):
        """Test Material Inspection Item with AQL calculation"""
        
        item_code = "TEST_AQL_ITEM_003"
        
        if frappe.db.exists("Item", item_code):
            frappe.delete_doc("Item", item_code, ignore_permissions=True)
        
        # Create item with AQL configuration
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Test AQL Item 3",
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "custom_aql_inspection_level": "2",
            "custom_inspection_regime": "Normal",
            "custom_accepted_quality_level": "2.5"
        })
        item.insert(ignore_permissions=True)
        
        # Create Material Inspection Item
        mir_item = frappe.get_doc({
            "doctype": "Material Inspection Item",
            "item_code": item_code,
            "received_quantity": 500,
            "material_type": "Raw Material",
            "defects_found": 2,
            "accepted_qty": 0,
            "rejected_qty": 0
        })
        
        # Trigger validation (this calculates AQL values)
        mir_item.validate()
        
        # Verify AQL calculations
        self.assertEqual(mir_item.sample_size, 50)
        self.assertEqual(mir_item.acceptance_number, 3)
        self.assertEqual(mir_item.rejection_number, 4)
        self.assertEqual(mir_item.inspection_result, "Accepted")
        self.assertEqual(mir_item.accepted_qty, 500)
        self.assertEqual(mir_item.rejected_qty, 0)
    
    def test_rejection_scenario(self):
        """Test Material Inspection Item rejection scenario"""
        
        item_code = "TEST_AQL_ITEM_004"
        
        if frappe.db.exists("Item", item_code):
            frappe.delete_doc("Item", item_code, ignore_permissions=True)
        
        # Create item with AQL configuration
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Test AQL Item 4",
            "item_group": "All Item Groups",
            "stock_uom": "Nos",
            "custom_aql_inspection_level": "2",
            "custom_inspection_regime": "Normal",
            "custom_accepted_quality_level": "2.5"
        })
        item.insert(ignore_permissions=True)
        
        # Create Material Inspection Item with high defects
        mir_item = frappe.get_doc({
            "doctype": "Material Inspection Item",
            "item_code": item_code,
            "received_quantity": 500,
            "material_type": "Raw Material",
            "defects_found": 5,  # Above rejection threshold of 4
            "accepted_qty": 0,
            "rejected_qty": 0
        })
        
        # Trigger validation
        mir_item.validate()
        
        # Verify rejection
        self.assertEqual(mir_item.inspection_result, "Rejected")
        self.assertEqual(mir_item.accepted_qty, 0)
        self.assertEqual(mir_item.rejected_qty, 500)


if __name__ == '__main__':
    unittest.main()