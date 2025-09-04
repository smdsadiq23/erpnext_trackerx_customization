# -*- coding: utf-8 -*-
"""
Cutting Lay Inspection Checklist Item Child DocType Controller

Represents individual checklist items within the cutting lay inspection process.
Links to master checklist data and tracks status, remarks, and evidence.
"""

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


class CuttingLayInspectionChecklistItem(Document):
    """Controller for individual checklist items"""
    
    def validate(self):
        """Validate checklist item before saving"""
        self.validate_checklist_reference()
        self.set_audit_trail()
        self.validate_mandatory_status()
    
    def validate_checklist_reference(self):
        """Validate that the checklist master reference exists and is active"""
        if self.checklist_master_reference:
            master = frappe.get_doc("Cut Lay Checklists", self.checklist_master_reference)
            if not master.is_active:
                frappe.throw(_("Selected checklist item is not active"))
    
    def set_audit_trail(self):
        """Set audit trail fields when status changes"""
        if self.status != "Pending" and not self.checked_by:
            self.checked_by = frappe.session.user
            self.checked_date = now()
    
    def validate_mandatory_status(self):
        """Validate that mandatory items are not marked as N/A without proper justification"""
        if self.is_mandatory and self.status == "N/A" and not self.remarks:
            frappe.throw(_("Remarks are required when marking mandatory items as N/A"))
    
    def on_update(self):
        """Actions when checklist item is updated"""
        # Update parent inspection progress
        self.update_parent_progress()
    
    def update_parent_progress(self):
        """Update progress calculation in parent Cutting Lay Inspection"""
        if self.parent and self.parenttype == "Cutting Lay Inspection":
            try:
                parent_doc = frappe.get_doc("Cutting Lay Inspection", self.parent)
                parent_doc.calculate_progress()
                parent_doc.save(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(f"Error updating parent progress: {str(e)}")
    
    def get_status_color(self):
        """Get color code for status display"""
        status_colors = {
            "Pending": "#ffa500",  # Orange
            "Pass": "#28a745",     # Green
            "Fail": "#dc3545",     # Red
            "N/A": "#6c757d"       # Gray
        }
        return status_colors.get(self.status, "#000000")
    
    def get_status_icon(self):
        """Get icon for status display"""
        status_icons = {
            "Pending": "⏳",
            "Pass": "✅", 
            "Fail": "❌",
            "N/A": "➖"
        }
        return status_icons.get(self.status, "❓")
    
    def is_completed(self):
        """Check if the checklist item is completed (not pending)"""
        return self.status != "Pending"
    
    def is_passed(self):
        """Check if the checklist item passed"""
        return self.status == "Pass"
    
    def is_failed(self):
        """Check if the checklist item failed"""
        return self.status == "Fail"


# Utility functions for checklist operations
@frappe.whitelist()
def update_checklist_status(checklist_item_name, status, remarks=None, photo_evidence=None):
    """Update checklist item status via API"""
    try:
        doc = frappe.get_doc("Cutting Lay Inspection Checklist Item", checklist_item_name)
        doc.status = status
        
        if remarks:
            doc.remarks = remarks
        
        if photo_evidence:
            doc.photo_evidence = photo_evidence
        
        doc.save()
        
        return {
            "success": True,
            "message": f"Checklist item updated to {status}",
            "status_color": doc.get_status_color(),
            "status_icon": doc.get_status_icon()
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating checklist status: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def bulk_update_checklist_status(checklist_items, status, remarks=None):
    """Bulk update multiple checklist items"""
    try:
        updated_count = 0
        
        for item_name in checklist_items:
            doc = frappe.get_doc("Cutting Lay Inspection Checklist Item", item_name)
            doc.status = status
            
            if remarks:
                if doc.remarks:
                    doc.remarks += f"\n\n{remarks}"
                else:
                    doc.remarks = remarks
            
            doc.save()
            updated_count += 1
        
        return {
            "success": True,
            "message": f"Updated {updated_count} checklist items to {status}",
            "updated_count": updated_count
        }
        
    except Exception as e:
        frappe.log_error(f"Error bulk updating checklist status: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_checklist_summary(parent_doc, parent_doctype="Cutting Lay Inspection"):
    """Get checklist summary for a parent document"""
    checklist_items = frappe.get_all(
        "Cutting Lay Inspection Checklist Item",
        filters={"parent": parent_doc, "parenttype": parent_doctype},
        fields=["name", "checkpoint", "category", "status", "is_mandatory"]
    )
    
    summary = {
        "total_items": len(checklist_items),
        "completed_items": 0,
        "passed_items": 0,
        "failed_items": 0,
        "na_items": 0,
        "mandatory_failed": 0,
        "categories": {
            "Pre Laying": {"total": 0, "completed": 0, "passed": 0, "failed": 0},
            "During Laying": {"total": 0, "completed": 0, "passed": 0, "failed": 0},
            "After Laying": {"total": 0, "completed": 0, "passed": 0, "failed": 0}
        }
    }
    
    for item in checklist_items:
        category = item.get("category", "Unknown")
        
        # Update category totals
        if category in summary["categories"]:
            summary["categories"][category]["total"] += 1
        
        # Update status counts
        if item.get("status") != "Pending":
            summary["completed_items"] += 1
            
            if category in summary["categories"]:
                summary["categories"][category]["completed"] += 1
        
        if item.get("status") == "Pass":
            summary["passed_items"] += 1
            if category in summary["categories"]:
                summary["categories"][category]["passed"] += 1
                
        elif item.get("status") == "Fail":
            summary["failed_items"] += 1
            if category in summary["categories"]:
                summary["categories"][category]["failed"] += 1
                
            # Check if mandatory item failed
            if item.get("is_mandatory"):
                summary["mandatory_failed"] += 1
                
        elif item.get("status") == "N/A":
            summary["na_items"] += 1
    
    # Calculate completion percentage
    if summary["total_items"] > 0:
        summary["completion_percentage"] = round(
            (summary["completed_items"] / summary["total_items"]) * 100, 2
        )
    else:
        summary["completion_percentage"] = 0
    
    return summary