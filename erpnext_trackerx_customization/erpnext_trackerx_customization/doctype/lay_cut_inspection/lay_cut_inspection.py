# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LayCutInspection(Document):
    def validate(self):
        """Validate the Lay Cut Inspection document"""
        self.calculate_efficiency()
        self.calculate_quality_score()
        self.set_quality_grade()
    
    def calculate_efficiency(self):
        """Calculate marker efficiency percentage"""
        if self.marker_area and self.fabric_used:
            self.efficiency_percentage = (self.marker_area / self.fabric_used) * 100
        else:
            self.efficiency_percentage = 0
    
    def calculate_quality_score(self):
        """Calculate total quality score from weighted components"""
        spreading_score = self.spreading_quality_score or 0
        technical_score = self.technical_accuracy_score or 0
        defect_score = self.defect_deduction_score or 0
        
        # Calculate weighted total (40% + 35% + 25% = 100%)
        self.total_score = (spreading_score * 0.4) + (technical_score * 0.35) + (defect_score * 0.25)
    
    def set_quality_grade(self):
        """Set quality grade based on total score"""
        if not self.total_score:
            return
            
        if self.total_score >= 95:
            self.quality_grade = "A+ (Excellent 95-100%)"
            self.acceptable = 1
        elif self.total_score >= 85:
            self.quality_grade = "A (Good 85-94%)"
            self.acceptable = 1
        elif self.total_score >= 75:
            self.quality_grade = "B (Fair 75-84%)"
            self.acceptable = 1
        else:
            self.quality_grade = "C (Poor <75% - REJECT)"
            self.acceptable = 0
    
    def before_submit(self):
        """Validate before submission"""
        if not self.lay_status:
            frappe.throw("Lay Status is required before submission")
            
        if not self.inspector_signature_date:
            self.inspector_signature_date = frappe.utils.now()
    
    def on_submit(self):
        """Actions to perform on submission"""
        # Set authorization date if authorized
        if self.cutting_authorization == "Authorized Immediately":
            self.authorization_date = frappe.utils.now()
            
        # Create quality alert if rejected
        if self.lay_status == "Rejected - Redo Required":
            self.create_quality_alert()
    
    def create_quality_alert(self):
        """Create quality alert for rejected lay cuts"""
        frappe.get_doc({
            "doctype": "Communication",
            "communication_type": "Notification",
            "subject": f"Lay Cut Rejected: {self.lay_cut_number}",
            "content": f"Lay Cut {self.lay_cut_number} has been rejected and requires rework. Reason: {self.inspector_comments}",
            "reference_doctype": "Lay Cut Inspection",
            "reference_name": self.name,
            "sent_or_received": "Sent"
        }).insert(ignore_permissions=True)


@frappe.whitelist()
def get_default_checklists(category):
    """Get default checklist items for a category"""
    # This will be used by client scripts to populate default checklists
    default_checklists = {
        "Fabric Quality": [
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
        "Lay Setup": [
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
    
    return default_checklists.get(category, [])


@frappe.whitelist()
def get_default_defects(defect_category):
    """Get default defects for a category"""
    default_defects = {
        "Critical": [
            "Holes in cutting area",
            "Major color variations", 
            "Wrong fabric type",
            "Severe contamination"
        ],
        "Major": [
            "Minor holes outside pattern",
            "Slight color differences",
            "Yarn irregularities",
            "Small stains"
        ],
        "Minor": [
            "Small knots",
            "Minor slubs",
            "Slight marks",
            "Texture variations"
        ]
    }
    
    return default_defects.get(defect_category, [])