# -*- coding: utf-8 -*-
"""
Cut Lay Checklists DocType Controller

Master data for cutting lay inspection checklists.
Contains standard checkpoints for Pre Laying, During Laying, and After Laying phases.
"""

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document


class CutLayChecklists(Document):
    """Controller for Cut Lay Checklists master data"""
    
    def validate(self):
        """Validate the checklist item before saving"""
        self.validate_mandatory_fields()
        self.set_defaults()
        self.validate_sort_order()
    
    def validate_mandatory_fields(self):
        """Validate required fields"""
        if not self.checklist_name:
            frappe.throw(_("Checklist Name is required"))
        
        if not self.category:
            frappe.throw(_("Category is required"))
        
        if not self.checkpoint:
            frappe.throw(_("Checkpoint is required"))
        
        if not self.description:
            frappe.throw(_("Description is required"))
    
    def set_defaults(self):
        """Set default values"""
        if not self.created_by:
            self.created_by = frappe.session.user
        
        if not self.creation_date:
            self.creation_date = frappe.utils.today()
        
        # Auto-generate checklist_name if not provided
        if not self.checklist_name:
            self.checklist_name = f"{self.category} - {self.checkpoint}"
    
    def validate_sort_order(self):
        """Validate and set sort order"""
        if not self.sort_order:
            # Auto-assign sort order based on existing records in same category
            last_order = frappe.db.sql("""
                SELECT COALESCE(MAX(sort_order), 0) as max_order 
                FROM `tabCut Lay Checklists` 
                WHERE category = %s AND name != %s
            """, (self.category, self.name or ""))
            
            if last_order:
                self.sort_order = last_order[0][0] + 10
            else:
                self.sort_order = 10
    
    def on_update(self):
        """Actions after updating the document"""
        # Update any existing inspection records that reference this checklist
        self.update_existing_inspections()
    
    def update_existing_inspections(self):
        """Update existing inspection checklist items if this master is updated"""
        try:
            # Find all checklist items that reference this master
            checklist_items = frappe.get_all(
                "Cutting Lay Inspection Checklist Item",
                filters={"checklist_master_reference": self.name},
                fields=["name", "parent"]
            )
            
            for item in checklist_items:
                # Update the checklist item with latest master data
                frappe.db.set_value(
                    "Cutting Lay Inspection Checklist Item",
                    item.name,
                    {
                        "checkpoint": self.checkpoint,
                        "description": self.description,
                        "category": self.category,
                        "is_mandatory": self.is_mandatory
                    }
                )
            
            if checklist_items:
                frappe.msgprint(
                    _("Updated {0} existing checklist items").format(len(checklist_items)),
                    alert=True
                )
                
        except Exception as e:
            frappe.log_error(f"Error updating existing inspections: {str(e)}")


# Utility functions for external use
@frappe.whitelist()
def get_checklists_by_category(category):
    """Get active checklists for a specific category"""
    checklists = frappe.get_all(
        "Cut Lay Checklists",
        filters={
            "category": category,
            "is_active": 1
        },
        fields=[
            "name", "checklist_name", "checkpoint", "description", 
            "is_mandatory", "sort_order"
        ],
        order_by="sort_order ASC"
    )
    
    return checklists


@frappe.whitelist()
def get_all_active_checklists():
    """Get all active checklists grouped by category"""
    checklists = frappe.get_all(
        "Cut Lay Checklists",
        filters={"is_active": 1},
        fields=[
            "name", "checklist_name", "checkpoint", "description", 
            "category", "is_mandatory", "sort_order"
        ],
        order_by="category, sort_order ASC"
    )
    
    # Group by category
    grouped_checklists = {
        "Pre Laying": [],
        "During Laying": [],
        "After Laying": []
    }
    
    for checklist in checklists:
        category = checklist.get("category")
        if category in grouped_checklists:
            grouped_checklists[category].append(checklist)
    
    return grouped_checklists


@frappe.whitelist()
def create_default_checklists():
    """Create default checklist items - used for initial setup"""
    
    default_checklists = [
        # Pre Laying Checklists
        {
            "category": "Pre Laying",
            "checkpoint": "Fabric Receiving & Storage",
            "description": "Check fabric rolls arrive without defects and are stored in appropriate conditions. Verify fabric quality, color consistency, and storage environment.",
            "sort_order": 10,
            "is_mandatory": 1
        },
        {
            "category": "Pre Laying", 
            "checkpoint": "Cutting Tools & Storage",
            "description": "Inspect cutting tools for sharpness and functionality. Ensure proper storage and maintenance of cutting equipment.",
            "sort_order": 20,
            "is_mandatory": 1
        },
        {
            "category": "Pre Laying",
            "checkpoint": "Fabric Inspection Report", 
            "description": "Review fabric inspection report for any defects or quality issues that may affect cutting process.",
            "sort_order": 30,
            "is_mandatory": 1
        },
        {
            "category": "Pre Laying",
            "checkpoint": "Fabric Allocation Table",
            "description": "Verify fabric allocation matches cutting requirements and marker specifications.",
            "sort_order": 40,
            "is_mandatory": 1
        },
        {
            "category": "Pre Laying",
            "checkpoint": "Marker Paper Condition",
            "description": "Check marker paper for accuracy, completeness, and proper condition before laying.",
            "sort_order": 50,
            "is_mandatory": 1
        },
        
        # During Laying Checklists
        {
            "category": "During Laying",
            "checkpoint": "Fabric Tension Control",
            "description": "Monitor and maintain appropriate fabric tension during spreading to avoid stretching or puckering.",
            "sort_order": 10,
            "is_mandatory": 1
        },
        {
            "category": "During Laying",
            "checkpoint": "Ply Height Monitoring",
            "description": "Continuously monitor ply height and ensure uniform spreading across the cutting table.",
            "sort_order": 20,
            "is_mandatory": 1
        },
        {
            "category": "During Laying",
            "checkpoint": "Edge Alignment Accuracy",
            "description": "Verify proper edge alignment of fabric plies to ensure accurate cutting dimensions.",
            "sort_order": 30,
            "is_mandatory": 1
        },
        {
            "category": "During Laying",
            "checkpoint": "Splice Joint Quality",
            "description": "Check quality of splice joints and ensure seamless fabric connections where required.",
            "sort_order": 40,
            "is_mandatory": 1
        },
        {
            "category": "During Laying",
            "checkpoint": "Defect Avoidance Check",
            "description": "Identify and avoid fabric defects during laying process to minimize waste and quality issues.",
            "sort_order": 50,
            "is_mandatory": 1
        },
        
        # After Laying Checklists
        {
            "category": "After Laying",
            "checkpoint": "Final Ply Count Verification",
            "description": "Verify final ply count matches the specified requirements and marker specifications.",
            "sort_order": 10,
            "is_mandatory": 1
        },
        {
            "category": "After Laying",
            "checkpoint": "Lay Dimensional Accuracy",
            "description": "Check lay dimensions for accuracy against marker specifications and cutting requirements.",
            "sort_order": 20,
            "is_mandatory": 1
        },
        {
            "category": "After Laying",
            "checkpoint": "Edge Squareness Check",
            "description": "Verify edges are square and properly aligned for accurate cutting operations.",
            "sort_order": 30,
            "is_mandatory": 1
        },
        {
            "category": "After Laying",
            "checkpoint": "Ply Stagger Assessment",
            "description": "Assess ply stagger and ensure uniform distribution across the lay for optimal cutting.",
            "sort_order": 40,
            "is_mandatory": 1
        },
        {
            "category": "After Laying",
            "checkpoint": "Marker Placement Accuracy",
            "description": "Verify marker is placed accurately on the lay with proper alignment and positioning.",
            "sort_order": 50,
            "is_mandatory": 1
        }
    ]
    
    created_count = 0
    
    for checklist_data in default_checklists:
        # Check if already exists
        existing = frappe.db.exists("Cut Lay Checklists", {
            "category": checklist_data["category"],
            "checkpoint": checklist_data["checkpoint"]
        })
        
        if not existing:
            doc = frappe.new_doc("Cut Lay Checklists")
            doc.update(checklist_data)
            doc.checklist_name = f"{checklist_data['category']} - {checklist_data['checkpoint']}"
            doc.insert(ignore_permissions=True)
            created_count += 1
    
    frappe.db.commit()
    
    return {
        "success": True,
        "message": f"Created {created_count} default checklist items",
        "created_count": created_count
    }