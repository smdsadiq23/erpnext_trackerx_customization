# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
import re


class FabricRoll(Document):
    def validate(self):
        self.validate_roll_data()
        self.calculate_defect_totals()
        self.determine_grade_and_result()

    def before_save(self):
        if not self.roll_id or self.roll_id == "New":
            self.roll_id = self.generate_roll_id()

    def validate_roll_data(self):
        """Validate basic roll data"""
        if flt(self.width) <= 0:
            frappe.throw("Roll width must be greater than 0")
        
        if flt(self.length) <= 0:
            frappe.throw("Roll length must be greater than 0")
            
        if self.inspected_length and flt(self.inspected_length) > flt(self.length):
            frappe.throw("Inspected length cannot be greater than roll length")

    def calculate_defect_totals(self):
        """Calculate total defect points and points per 100 sqm"""
        if not self.defects:
            self.total_defect_points = 0
            self.points_per_100_sqm = 0
            return

        # Calculate each defect's points based on size
        total_points = 0
        for defect in self.defects:
            if defect.defect_size:
                points = self.calculate_single_defect_points(defect.defect_size)
                defect.defect_points = points
                
                # Set severity based on points
                if points >= 3:
                    defect.severity = "Critical"
                elif points >= 2:
                    defect.severity = "Major"
                else:
                    defect.severity = "Minor"
                    
                total_points += points

        self.total_defect_points = total_points

        # Calculate points per 100 square meters
        if self.width and self.inspected_length:
            width_meters = flt(self.width) * 0.0254  # Convert inches to meters
            area_sqm = width_meters * flt(self.inspected_length)
            if area_sqm > 0:
                self.points_per_100_sqm = (total_points * 100) / area_sqm
            else:
                self.points_per_100_sqm = 0

    def calculate_single_defect_points(self, size_str):
        """Calculate points for a single defect based on 4-point system"""
        size_inches = self.parse_measurement(size_str)
        
        if size_inches is None:
            return 0

        # 4-point system
        if size_inches <= 1:
            return 1
        elif size_inches <= 3:
            return 2
        elif size_inches <= 6:
            return 3
        else:
            return 4

    def parse_measurement(self, size_str):
        """Parse measurement string (handles fractions, decimals, mixed numbers)"""
        if not size_str:
            return None
            
        size_str = str(size_str).strip()
        
        # Handle fractions (e.g., "1/2", "3/4")
        if '/' in size_str:
            if ' ' in size_str and '/' in size_str:
                # Mixed number (e.g., "1 1/2")
                parts = size_str.split(' ')
                if len(parts) == 2:
                    try:
                        whole = float(parts[0])
                        fraction_parts = parts[1].split('/')
                        if len(fraction_parts) == 2:
                            numerator = float(fraction_parts[0])
                            denominator = float(fraction_parts[1])
                            if denominator != 0:
                                return whole + (numerator / denominator)
                    except ValueError:
                        return None
            else:
                # Simple fraction (e.g., "1/2")
                parts = size_str.split('/')
                if len(parts) == 2:
                    try:
                        numerator = float(parts[0])
                        denominator = float(parts[1])
                        if denominator != 0:
                            return numerator / denominator
                    except ValueError:
                        return None
        
        # Handle decimals
        try:
            return float(size_str)
        except ValueError:
            return None

    def determine_grade_and_result(self):
        """Determine fabric grade and final result based on points per 100 sqm"""
        points = flt(self.points_per_100_sqm)
        
        # Determine grade
        if points > 40:
            self.fabric_grade = "D (Rejected)"
            self.final_result = "Rejected"
        elif points > 20:
            self.fabric_grade = "C"
            self.final_result = "Second Quality"
        elif points > 10:
            self.fabric_grade = "B"
            self.final_result = "First Quality"
        else:
            self.fabric_grade = "A"
            self.final_result = "First Quality"

    def generate_roll_id(self):
        """Generate a unique roll ID"""
        if self.item_code:
            # Use item code prefix + auto increment
            prefix = frappe.scrub(self.item_code)[:4].upper()
            count = frappe.db.count("Fabric Roll", {"item_code": self.item_code}) + 1
            return f"{prefix}-R{count:04d}"
        else:
            return f"ROLL-{frappe.utils.now()}".replace(" ", "-").replace(":", "-")[:20]

    @frappe.whitelist()
    def get_defect_summary(self):
        """Get summary of defects by category"""
        if not self.defects:
            return {}
            
        summary = {}
        for defect in self.defects:
            category = defect.defect_category or "Uncategorized"
            if category not in summary:
                summary[category] = {
                    "count": 0,
                    "total_points": 0,
                    "defects": []
                }
            
            summary[category]["count"] += 1
            summary[category]["total_points"] += flt(defect.defect_points)
            summary[category]["defects"].append({
                "name": defect.defect_name,
                "points": defect.defect_points,
                "location": f"{defect.location_yard} yds" if defect.location_yard else "",
                "position": defect.location_position
            })
        
        return summary

    @frappe.whitelist()
    def start_inspection(self):
        """Start inspection process"""
        if self.inspection_status != "Pending":
            frappe.throw("Inspection can only be started for pending rolls")
        
        self.inspection_status = "In Progress"
        self.inspection_date = frappe.utils.nowdate()
        self.inspector_name = frappe.session.user_fullname
        
        if self.length and not self.inspected_length:
            self.inspected_length = self.length
            
        self.save()
        return "Inspection started successfully"

    @frappe.whitelist()
    def complete_inspection(self):
        """Complete inspection and finalize results"""
        if not self.defects:
            frappe.throw("Please add defects found during inspection")
        
        self.calculate_defect_totals()
        self.determine_grade_and_result()
        
        # Update inspection status based on final result
        if self.final_result == "Rejected":
            self.inspection_status = "Rejected"
        else:
            self.inspection_status = "Passed"
            
        self.save()
        
        return {
            "message": "Inspection completed successfully",
            "final_result": self.final_result,
            "fabric_grade": self.fabric_grade,
            "points_per_100_sqm": self.points_per_100_sqm,
            "total_defect_points": self.total_defect_points
        }