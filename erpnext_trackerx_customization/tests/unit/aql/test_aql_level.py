# -*- coding: utf-8 -*-
"""
Unit tests for AQL Level DocType

Tests validation logic and data integrity for AQL Level master data.
"""

from __future__ import unicode_literals
import unittest
import frappe
from frappe.test_runner import make_test_records


class TestAQLLevel(unittest.TestCase):
    """Test cases for AQL Level DocType"""
    
    def setUp(self):
        """Set up test data"""
        frappe.set_user("Administrator")
    
    def tearDown(self):
        """Clean up test data"""
        # Delete test records
        frappe.db.delete("AQL Level", {"level_code": ["in", ["TEST_1", "TEST_INVALID"]]})
        frappe.db.commit()
    
    def test_aql_level_creation(self):
        """Test creating valid AQL Level records"""
        
        # Test General level creation
        level = frappe.get_doc({
            "doctype": "AQL Level",
            "level_code": "TEST_1",
            "level_type": "General",
            "description": "Test General Level",
            "is_active": 1
        })
        level.insert(ignore_permissions=True)
        
        self.assertEqual(level.level_code, "TEST_1")
        self.assertEqual(level.level_type, "General")
        self.assertTrue(level.is_active)
    
    def test_general_level_validation(self):
        """Test validation for General inspection levels"""
        
        valid_general_codes = ["1", "2", "3"]
        
        for code in valid_general_codes:
            level = frappe.get_doc({
                "doctype": "AQL Level",
                "level_code": code,
                "level_type": "General",
                "description": f"Test General Level {code}",
                "is_active": 1
            })
            
            # Should not raise an exception
            try:
                level.validate()
            except Exception as e:
                self.fail(f"Valid general level code {code} raised exception: {e}")
    
    def test_special_level_validation(self):
        """Test validation for Special inspection levels"""
        
        valid_special_codes = ["S1", "S2", "S3", "S4"]
        
        for code in valid_special_codes:
            level = frappe.get_doc({
                "doctype": "AQL Level",
                "level_code": code,
                "level_type": "Special",
                "description": f"Test Special Level {code}",
                "is_active": 1
            })
            
            # Should not raise an exception
            try:
                level.validate()
            except Exception as e:
                self.fail(f"Valid special level code {code} raised exception: {e}")
    
    def test_invalid_level_validation(self):
        """Test validation rejects invalid level codes"""
        
        # Test invalid general level
        with self.assertRaises(Exception):
            level = frappe.get_doc({
                "doctype": "AQL Level",
                "level_code": "4",
                "level_type": "General",
                "description": "Invalid General Level",
                "is_active": 1
            })
            level.validate()
        
        # Test invalid special level
        with self.assertRaises(Exception):
            level = frappe.get_doc({
                "doctype": "AQL Level",
                "level_code": "S5",
                "level_type": "Special", 
                "description": "Invalid Special Level",
                "is_active": 1
            })
            level.validate()
    
    def test_unique_level_code(self):
        """Test that level codes must be unique"""
        
        # Create first level
        level1 = frappe.get_doc({
            "doctype": "AQL Level",
            "level_code": "TEST_1",
            "level_type": "General",
            "description": "First test level",
            "is_active": 1
        })
        level1.insert(ignore_permissions=True)
        
        # Try to create duplicate
        level2 = frappe.get_doc({
            "doctype": "AQL Level",
            "level_code": "TEST_1",
            "level_type": "Special",
            "description": "Duplicate test level",
            "is_active": 1
        })
        
        with self.assertRaises(Exception):
            level2.insert(ignore_permissions=True)


if __name__ == '__main__':
    unittest.main()