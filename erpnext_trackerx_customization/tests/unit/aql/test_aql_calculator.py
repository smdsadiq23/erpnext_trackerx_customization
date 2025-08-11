# -*- coding: utf-8 -*-
"""
Unit tests for AQL Calculator utility

Tests the core AQL calculation logic including:
- Sample size code determination
- Sample size mapping
- Inspection result logic
- Industry standard compliance
"""

from __future__ import unicode_literals
import unittest
import frappe
from erpnext_trackerx_customization.erpnext_trackerx_customization.utils.aql_calculator import AQLCalculator


class TestAQLCalculator(unittest.TestCase):
    """Test cases for AQL Calculator utility functions"""
    
    def test_sample_size_code_general_levels(self):
        """Test sample size code calculation for general inspection levels"""
        
        test_cases = [
            # (quantity, level, expected_code)
            (50, "1", "C"),
            (50, "2", "D"), 
            (50, "3", "E"),
            (500, "1", "G"),
            (500, "2", "H"),
            (500, "3", "J"),
            (2000, "1", "H"),
            (2000, "2", "J"),
            (2000, "3", "K")
        ]
        
        for quantity, level, expected_code in test_cases:
            with self.subTest(quantity=quantity, level=level):
                actual_code = AQLCalculator.get_sample_size_code(quantity, level)
                self.assertEqual(actual_code, expected_code,
                    f"Quantity {quantity}, Level {level}: Expected {expected_code}, got {actual_code}")
    
    def test_sample_size_code_special_levels(self):
        """Test sample size code calculation for special inspection levels"""
        
        test_cases = [
            # (quantity, level, expected_code)
            (50, "S1", "A"),
            (500, "S1", "C"),
            (2000, "S2", "D"),
            (10000, "S3", "F"),
            (50000, "S4", "H")
        ]
        
        for quantity, level, expected_code in test_cases:
            with self.subTest(quantity=quantity, level=level):
                actual_code = AQLCalculator.get_sample_size_code(quantity, level)
                self.assertEqual(actual_code, expected_code,
                    f"Quantity {quantity}, Level {level}: Expected {expected_code}, got {actual_code}")
    
    def test_sample_size_mapping(self):
        """Test sample size mapping from code letters"""
        
        expected_sizes = {
            'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20,
            'G': 32, 'H': 50, 'J': 80, 'K': 125, 'L': 200,
            'M': 315, 'N': 500, 'P': 800, 'Q': 1250, 'R': 2000
        }
        
        for code, expected_size in expected_sizes.items():
            with self.subTest(code=code):
                actual_size = AQLCalculator.get_sample_size(code)
                self.assertEqual(actual_size, expected_size,
                    f"Code {code}: Expected {expected_size}, got {actual_size}")
    
    def test_inspection_result_determination(self):
        """Test inspection result logic"""
        
        test_cases = [
            # (defects, accept_num, reject_num, expected_result)
            (0, 1, 2, "Accepted"),
            (1, 1, 2, "Accepted"),
            (2, 1, 2, "Rejected"),
            (3, 1, 2, "Rejected"),
            (0, 0, 1, "Accepted"),
            (1, 0, 1, "Rejected"),
            (2, 3, 4, "Accepted"),
            (3, 3, 4, "Accepted"),
            (4, 3, 4, "Rejected"),
            (5, 3, 4, "Rejected")
        ]
        
        for defects, accept_num, reject_num, expected_result in test_cases:
            with self.subTest(defects=defects, accept=accept_num, reject=reject_num):
                actual_result = AQLCalculator.determine_inspection_result(defects, accept_num, reject_num)
                self.assertEqual(actual_result, expected_result,
                    f"Defects {defects}, Accept {accept_num}, Reject {reject_num}: Expected {expected_result}, got {actual_result}")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        
        # Test very small quantities
        code = AQLCalculator.get_sample_size_code(1, "2")
        self.assertEqual(code, "A")
        
        # Test very large quantities
        code = AQLCalculator.get_sample_size_code(1000000, "2")
        self.assertEqual(code, "Q")
        
        # Test invalid code letter
        size = AQLCalculator.get_sample_size("X")
        self.assertEqual(size, 2)  # Should fallback to minimum
        
        # Test boundary acceptance/rejection
        result = AQLCalculator.determine_inspection_result(1, 1, 1)
        self.assertEqual(result, "Accepted")  # Should be accepted when equal to acceptance number


if __name__ == '__main__':
    unittest.main()