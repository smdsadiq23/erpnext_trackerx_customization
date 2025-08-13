# -*- coding: utf-8 -*-
"""
Defect Master DocType

Manages defect definitions for different inspection types:
- Fabric Inspection (with point system)
- Trims Inspection 
- Final Inspection
"""

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class DefectMaster(Document):
    def validate(self):
        """Validate defect master data"""
        
        # Validate defect code format based on inspection type
        if self.inspection_type == "Final Inspection":
            if not self.defect_code.startswith(('C', 'F', 'T', 'A')):
                frappe.throw("Final Inspection defect codes must start with C, F, T, or A")
        
        # Validate point criteria for fabric inspection
        if self.inspection_type == "Fabric Inspection":
            if not self.point_1_criteria:
                frappe.throw("1 Point Criteria is required for Fabric Inspection")
        
        # Set defect category based on inspection type for consistency
        if self.inspection_type == "Final Inspection" and self.defect_code.startswith('C'):
            self.defect_category = "Workmanship"
        elif self.inspection_type == "Final Inspection" and self.defect_code.startswith('F'):
            self.defect_category = "Fabric"
        elif self.inspection_type == "Final Inspection" and self.defect_code.startswith('T'):
            self.defect_category = "Trim"
        elif self.inspection_type == "Final Inspection" and self.defect_code.startswith('A'):
            self.defect_category = "Size"
    
    def get_point_value(self, defect_size_measurement):
        """
        Calculate point value based on actual defect size measurement for fabric inspection
        
        Args:
            defect_size_measurement: Float or string with measurement (e.g., 2.5, "4.2", "5 inches")
            
        Returns:
            int: Point value (1-4) based on criteria comparison
        """
        if self.inspection_type != "Fabric Inspection":
            return 0
        
        # Parse the measurement value
        measurement = self._parse_measurement(defect_size_measurement)
        if measurement is None:
            return 1  # Default to 1 point if can't parse
        
        # Check against criteria in descending order (4, 3, 2, 1)
        # Important: Check higher points first to handle overlapping ranges correctly
        if self.point_4_criteria and self._meets_criteria(measurement, self.point_4_criteria):
            return 4
        elif self.point_3_criteria and self._meets_criteria(measurement, self.point_3_criteria):
            return 3
        elif self.point_2_criteria and self._meets_criteria(measurement, self.point_2_criteria):
            return 2
        elif self.point_1_criteria and self._meets_criteria(measurement, self.point_1_criteria):
            return 1
        
        return 1  # Default to 1 point
    
    def _parse_measurement(self, measurement_input):
        """
        Parse measurement from various input formats
        
        Args:
            measurement_input: String or number representing measurement
            
        Returns:
            float: Parsed measurement in inches, or None if can't parse
        """
        import re
        
        if isinstance(measurement_input, (int, float)):
            return float(measurement_input)
        
        measurement_str = str(measurement_input).lower().strip()
        
        # Handle common fraction formats
        fraction_patterns = {
            '1/4': 0.25, '1/2': 0.5, '3/4': 0.75,
            '1/8': 0.125, '3/8': 0.375, '5/8': 0.625, '7/8': 0.875,
            '1/3': 0.333, '2/3': 0.667
        }
        
        for fraction, value in fraction_patterns.items():
            if fraction in measurement_str:
                # Handle mixed numbers like "2 1/4"
                mixed_match = re.search(r'(\d+)\s*' + re.escape(fraction), measurement_str)
                if mixed_match:
                    whole = int(mixed_match.group(1))
                    return whole + value
                else:
                    return value
        
        # Extract decimal numbers
        number_match = re.search(r'(\d+(?:\.\d+)?)', measurement_str)
        if number_match:
            return float(number_match.group(1))
        
        return None
    
    def _meets_criteria(self, measurement, criteria):
        """
        Check if measurement meets the given criteria
        
        Args:
            measurement: Float measurement in inches
            criteria: String criteria (e.g., "≤ 3\" length", "> 9\"", "1/4\" to 1/2\"")
            
        Returns:
            bool: True if measurement meets criteria
        """
        import re
        
        criteria_str = criteria.lower().strip()
        
        # Handle range criteria (e.g., "3\" to 6\"", "1/4\" to 1/2\"")
        # For fabric defects, ranges are typically exclusive on the lower bound, inclusive on upper
        range_match = re.search(r'([\d./]+)"?\s*to\s*([\d./]+)"?', criteria_str)
        if range_match:
            min_val = self._parse_measurement(range_match.group(1))
            max_val = self._parse_measurement(range_match.group(2))
            if min_val is not None and max_val is not None:
                # Range is typically exclusive on lower bound (e.g., "3 to 6" means > 3 and <= 6)
                return min_val < measurement <= max_val
        
        # Handle greater than criteria (e.g., "> 9\"", "> 1\"")
        gt_match = re.search(r'>\s*([\d./]+)"?', criteria_str)
        if gt_match:
            threshold = self._parse_measurement(gt_match.group(1))
            if threshold is not None:
                return measurement > threshold
        
        # Handle less than or equal criteria (e.g., "≤ 3\"", "<= 1/4\"")
        lte_match = re.search(r'[≤<=]\s*([\d./]+)"?', criteria_str)
        if lte_match:
            threshold = self._parse_measurement(lte_match.group(1))
            if threshold is not None:
                return measurement <= threshold
        
        # Handle less than criteria (e.g., "< 3\"")
        lt_match = re.search(r'<\s*([\d./]+)"?', criteria_str)
        if lt_match:
            threshold = self._parse_measurement(lt_match.group(1))
            if threshold is not None:
                return measurement < threshold
        
        # Handle greater than or equal criteria (e.g., ">= 3\"")
        gte_match = re.search(r'[≥>=]\s*([\d./]+)"?', criteria_str)
        if gte_match:
            threshold = self._parse_measurement(gte_match.group(1))
            if threshold is not None:
                return measurement >= threshold
        
        # Handle severity levels (for non-measurement based defects)
        if any(keyword in criteria_str for keyword in ['slight', 'minor']):
            return measurement <= 1.0  # Arbitrary threshold for "slight"
        elif any(keyword in criteria_str for keyword in ['noticeable', 'medium']):
            return 1.0 < measurement <= 3.0
        elif any(keyword in criteria_str for keyword in ['obvious', 'large']):
            return 3.0 < measurement <= 6.0
        elif any(keyword in criteria_str for keyword in ['severe', 'very large']):
            return measurement > 6.0
        
        return False
    
    @staticmethod
    def get_defects_by_inspection_type(inspection_type, category=None):
        """
        Get defects filtered by inspection type and optional category
        
        Args:
            inspection_type: Fabric Inspection, Trims Inspection, Final Inspection
            category: Optional defect category filter
            
        Returns:
            list: List of defect records
        """
        filters = {
            "inspection_type": inspection_type,
            "is_active": 1
        }
        
        if category:
            filters["defect_category"] = category
        
        return frappe.get_all(
            "Defect Master",
            fields=["*"],
            filters=filters,
            order_by="defect_code"
        )
    
    @staticmethod
    def get_fabric_defect_points(defect_code, defect_size):
        """
        Calculate points for fabric defect
        
        Args:
            defect_code: Defect code
            defect_size: Size/severity description
            
        Returns:
            int: Point value
        """
        defect = frappe.get_doc("Defect Master", defect_code)
        return defect.get_point_value(defect_size)