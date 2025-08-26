# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LayCutCategory(Document):
    def validate(self):
        """Validate the category"""
        if self.scoring_weight and self.scoring_weight > 100:
            frappe.throw("Scoring weight cannot exceed 100%")
    
    def after_insert(self):
        """Create default checklist items if category is for checklists"""
        if self.category_type == "Checklist":
            self.create_default_items()
    
    def create_default_items(self):
        """Create default checklist items based on category"""
        default_items = self.get_default_items_for_category()
        
        for idx, item_text in enumerate(default_items, 1):
            self.append("default_checklist_items", {
                "item_text": item_text,
                "is_critical": False,
                "scoring_points": 1.0,
                "display_order": idx
            })
        
        self.save()
    
    def get_default_items_for_category(self):
        """Get default items based on category name"""
        default_mapping = {
            "Fabric Quality Check": [
                "No holes or tears",
                "No stains or marks",
                "No color variations", 
                "No wrinkles or creases",
                "Proper fabric roll condition"
            ],
            "Marker Verification": [
                "All pattern pieces present",
                "Marker not torn or damaged",
                "Clear cutting lines",
                "Proper pattern orientation",
                "Notches clearly marked"
            ],
            "Lay Setup Inspection": [
                "Even fabric tension",
                "Proper layer alignment", 
                "No wrinkles between layers",
                "Straight lay edges",
                "Consistent layer thickness"
            ],
            "Pattern Placement": [
                "Centered on fabric lay",
                "Proper grain alignment",
                "Pattern matching aligned",
                "Adequate seam allowances",
                "Special markings visible"
            ]
        }
        
        return default_mapping.get(self.category_name, [])