# -*- coding: utf-8 -*-
"""
Accessories Inspection

Complete inspection system for accessories with AQL integration.
"""

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
# from erpnext_trackerx_customization.utils.aql_calculator import AQLCalculator

class AccessoriesInspection(Document):
    def validate(self):
        """Validate accessories inspection"""
        self.calculate_sample_requirements()
        self.auto_populate_checklist()
        self.calculate_defect_summary()
        self.determine_inspection_result()

    def calculate_sample_requirements(self):
        """Calculate required sample size using AQL"""
        if self.aql_level and self.total_quantity:
            # Simple AQL calculation for now
            lot_size = int(self.total_quantity)
            
            # Basic sample size calculation based on lot size
            if lot_size <= 50:
                self.required_sample_size = max(5, int(lot_size * 0.2))
            elif lot_size <= 500:
                self.required_sample_size = max(20, int(lot_size * 0.1))
            else:
                self.required_sample_size = max(50, int(lot_size * 0.05))
            
            # For accessories, sample pieces = sample size
            sample_ratio = self.required_sample_size / max(self.total_quantity, 1)
            self.required_sample_pieces = min(
                max(int(self.total_pieces * sample_ratio), 1),
                self.total_pieces
            )

    def auto_populate_checklist(self):
        """Auto-populate inspection checklist for accessories"""
        if not self.inspection_checklist and self.material_type:
            checklist_items = self.get_accessories_checklist_items()
            
            for item in checklist_items:
                self.append("inspection_checklist", {
                    "inspection_parameter": item.get("parameter"),
                    "specification": item.get("specification"),
                    "result": "Pass"
                })

    def get_accessories_checklist_items(self):
        """Get standard checklist items for accessories inspection"""
        standard_items = [
            {"parameter": "Print Quality", "specification": "Clear, readable text and graphics"},
            {"parameter": "Color Accuracy", "specification": "Match approved color standards"},
            {"parameter": "Size/Dimensions", "specification": "±1mm tolerance"},
            {"parameter": "Material Quality", "specification": "No tears, holes, or defects"},
            {"parameter": "Adhesion (if applicable)", "specification": "Secure attachment, no peeling"},
            {"parameter": "Cut Quality", "specification": "Clean edges, no fraying"},
            {"parameter": "Overall Appearance", "specification": "Professional finish"},
            {"parameter": "Packaging", "specification": "Proper protective packaging"}
        ]
        
        # Add material-specific items based on material type
        material_type_lower = self.material_type.lower() if self.material_type else ""
        
        if "label" in material_type_lower:
            standard_items.extend([
                {"parameter": "Text Legibility", "specification": "All text clearly readable"},
                {"parameter": "Barcode Quality", "specification": "Scannable barcode (if present)"},
                {"parameter": "Adhesive Strength", "specification": "Proper adhesion without residue"}
            ])
        elif "tag" in material_type_lower:
            standard_items.extend([
                {"parameter": "Hanging Strength", "specification": "String/attachment secure"},
                {"parameter": "Information Accuracy", "specification": "Correct size, care instructions"}
            ])
        elif "packaging" in material_type_lower:
            standard_items.extend([
                {"parameter": "Seal Integrity", "specification": "Proper sealing if required"},
                {"parameter": "Transparency", "specification": "Clear visibility (if transparent)"}
            ])
            
        return standard_items

    def calculate_defect_summary(self):
        """Calculate defect summary from checklist and defects"""
        self.total_critical_defects = 0
        self.total_major_defects = 0 
        self.total_minor_defects = 0
        
        # Count defects from checklist
        for item in self.inspection_checklist or []:
            if item.defect_found:
                if item.defect_severity == "Critical":
                    self.total_critical_defects += 1
                elif item.defect_severity == "Major":
                    self.total_major_defects += 1
                else:
                    self.total_minor_defects += 1
        
        # Count defects from defects table
        for defect in self.accessories_defects or []:
            quantity = defect.quantity_affected or 1
            if defect.defect_severity == "Critical":
                self.total_critical_defects += quantity
            elif defect.defect_severity == "Major":
                self.total_major_defects += quantity
            else:
                self.total_minor_defects += quantity

    def determine_inspection_result(self):
        """Determine inspection result based on AQL and defects"""
        # Simple acceptance criteria based on defect counts
        # This would normally use AQL tables, but using simplified logic for now
        sample_size = self.required_sample_size or 1
        
        # Basic acceptance thresholds (can be refined later)
        critical_threshold = 0  # No critical defects allowed
        major_threshold = max(1, int(sample_size * 0.025))  # 2.5% of sample size
        minor_threshold = max(2, int(sample_size * 0.05))   # 5% of sample size
        
        if self.total_critical_defects > critical_threshold:
            self.inspection_result = "Rejected"
            self.quality_grade = "Rejected - Critical Defects"
        elif self.total_major_defects > major_threshold:
            self.inspection_result = "Rejected"  
            self.quality_grade = "Rejected - Major Defects"
        else:
            if self.total_minor_defects > minor_threshold:
                self.inspection_result = "Conditional Accept"
                self.quality_grade = "Grade B - Minor Issues"
            else:
                self.inspection_result = "Accepted"
                self.quality_grade = "Grade A - Excellent"

    @frappe.whitelist()
    def get_defect_categories(self):
        """Get available defect categories for accessories"""
        return frappe.get_all("Defect Master", 
            filters={"inspection_type": "Accessories"},
            fields=["name", "defect_description", "defect_category", "severity"],
            order_by="defect_category, defect_description"
        )