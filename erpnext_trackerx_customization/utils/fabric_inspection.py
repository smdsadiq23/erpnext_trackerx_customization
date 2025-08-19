# -*- coding: utf-8 -*-
"""
Fabric Inspection Utilities

Provides utility functions for fabric inspection workflows including 
point calculation and quality assessment.
"""

import frappe
from typing import List, Dict, Any

class FabricInspectionCalculator:
    """Utility class for fabric inspection calculations"""
    
    @staticmethod
    def calculate_defect_points(defect_code: str, defect_size: str) -> int:
        """
        Calculate points for a specific defect based on its size
        
        Args:
            defect_code: Code of the defect (e.g., 'YD001', 'WD005')
            defect_size: Measurement of the defect (e.g., '2.5', '1/4', '4.2 inches')
            
        Returns:
            int: Point value (1-4) based on defect criteria
            
        Example:
            points = FabricInspectionCalculator.calculate_defect_points('YD001', '4.5')
            # Returns: 2 (for Thick Yarn 4.5" = 2 points as it's in 3" to 6" range)
        """
        try:
            defect_doc = frappe.get_doc("Defect Master", defect_code)
            return defect_doc.get_point_value(defect_size)
        except:
            return 1  # Default to 1 point if defect not found
    
    @staticmethod
    def calculate_total_points(defects: List[Dict]) -> Dict[str, Any]:
        """
        Calculate total points for multiple defects in a fabric inspection
        
        Args:
            defects: List of defect dictionaries with 'code' and 'size' keys
            Example: [
                {'code': 'YD001', 'size': '4.5'},
                {'code': 'WD002', 'size': '2.1'},
                {'code': 'DD003', 'size': '8.0'}
            ]
            
        Returns:
            dict: Calculation results with total points, defect breakdown, and quality grade
            
        Example:
            defects = [
                {'code': 'YD001', 'size': '4.5'},  # Thick Yarn 4.5" = 2 points
                {'code': 'YD001', 'size': '8.0'},  # Thick Yarn 8.0" = 3 points
                {'code': 'WD002', 'size': '2.0'}   # Missing End 2.0" = 1 point
            ]
            result = FabricInspectionCalculator.calculate_total_points(defects)
            # Returns: {'total_points': 6, 'defect_count': 3, 'details': [...], 'quality_grade': 'B'}
        """
        total_points = 0
        defect_details = []
        defect_categories = {}
        
        for defect in defects:
            defect_code = defect.get('code', '')
            defect_size = defect.get('size', '1.0')
            
            # Calculate points for this defect
            points = FabricInspectionCalculator.calculate_defect_points(defect_code, defect_size)
            total_points += points
            
            # Get defect details
            try:
                defect_doc = frappe.get_doc("Defect Master", defect_code)
                defect_name = defect_doc.defect_name
                defect_category = defect_doc.defect_category
                
                # Track defects by category
                if defect_category not in defect_categories:
                    defect_categories[defect_category] = {'count': 0, 'points': 0}
                defect_categories[defect_category]['count'] += 1
                defect_categories[defect_category]['points'] += points
                
            except:
                defect_name = f"Unknown ({defect_code})"
                defect_category = "Unknown"
            
            defect_details.append({
                'code': defect_code,
                'name': defect_name,
                'category': defect_category,
                'size': defect_size,
                'points': points
            })
        
        # Calculate quality grade based on total points
        quality_grade = FabricInspectionCalculator.get_quality_grade(total_points, len(defects))
        
        return {
            'total_points': total_points,
            'defect_count': len(defects),
            'defect_details': defect_details,
            'defect_categories': defect_categories,
            'quality_grade': quality_grade,
            'points_per_defect': round(total_points / len(defects), 2) if len(defects) > 0 else 0
        }
    
    @staticmethod
    def get_quality_grade(total_points: int, defect_count: int) -> str:
        """
        Determine quality grade based on total points and defect count
        
        Args:
            total_points: Total defect points
            defect_count: Number of defects found
            
        Returns:
            str: Quality grade (A, B, C, D, F)
        """
        if defect_count == 0:
            return 'A+'
        
        avg_points_per_defect = total_points / defect_count
        
        # Grade based on average severity and total points
        if total_points <= 5 and avg_points_per_defect <= 1.5:
            return 'A'
        elif total_points <= 10 and avg_points_per_defect <= 2.0:
            return 'B'
        elif total_points <= 20 and avg_points_per_defect <= 2.5:
            return 'C'
        elif total_points <= 35:
            return 'D'
        else:
            return 'F'  # Fail
    
    @staticmethod
    def get_defect_criteria_info(defect_code: str) -> Dict[str, Any]:
        """
        Get detailed criteria information for a specific defect
        
        Args:
            defect_code: Defect code to look up
            
        Returns:
            dict: Defect information including point criteria
        """
        try:
            defect_doc = frappe.get_doc("Defect Master", defect_code)
            
            return {
                'code': defect_doc.defect_code,
                'name': defect_doc.defect_name,
                'description': defect_doc.defect_description,
                'category': defect_doc.defect_category,
                'criteria': {
                    '1_point': defect_doc.point_1_criteria,
                    '2_points': defect_doc.point_2_criteria,
                    '3_points': defect_doc.point_3_criteria,
                    '4_points': defect_doc.point_4_criteria
                },
                'inspection_area': defect_doc.inspection_area,
                'acceptable_limit': defect_doc.acceptable_limit
            }
        except:
            return None
    
    @staticmethod
    def get_all_fabric_defects() -> List[Dict]:
        """
        Get all fabric defects with their criteria
        
        Returns:
            list: List of all fabric defects with point criteria
        """
        try:
            defects = frappe.get_all(
                "Defect Master",
                fields=["defect_code", "defect_name", "defect_category", "point_1_criteria",
                       "point_2_criteria", "point_3_criteria", "point_4_criteria"],
                filters={
                    "inspection_type": "Fabric Inspection",
                    "is_active": 1
                },
                order_by="defect_category, defect_code"
            )
            
            return [dict(defect) for defect in defects]
        except:
            return []

# Convenience functions for direct use
def calculate_defect_points(defect_code: str, defect_size: str) -> int:
    """Convenience function for calculating defect points"""
    return FabricInspectionCalculator.calculate_defect_points(defect_code, defect_size)

def calculate_fabric_quality(defects: List[Dict]) -> Dict[str, Any]:
    """Convenience function for calculating overall fabric quality"""
    return FabricInspectionCalculator.calculate_total_points(defects)