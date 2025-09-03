# -*- coding: utf-8 -*-
"""
Cutting Lay Inspection DocType Controller

Main controller for managing cutting lay inspection process with dynamic checklists,
progress tracking, and integration with Cut Docket workflow.
"""

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, now, cint, flt


class CuttingLayInspection(Document):
    """Main controller for Cutting Lay Inspection"""
    
    def validate(self):
        """Validate the document before saving"""
        self.validate_cut_docket_reference()
        self.populate_from_cut_docket()
        self.populate_checklists()
        self.calculate_progress()
        self.set_defaults()
    
    def validate_cut_docket_reference(self):
        """Validate Cut Docket reference"""
        if not self.cut_docket_reference:
            frappe.throw(_("Cut Docket Reference is required"))
        
        # Check if Cut Docket exists and has lay_cut_inspection enabled
        cut_docket = frappe.get_doc("Cut Docket", self.cut_docket_reference)
        if not cut_docket.lay_cut_inspection:
            frappe.throw(_("Cut Docket does not require lay cut inspection"))
    
    def populate_from_cut_docket(self):
        """Auto-populate fields from Cut Docket"""
        if not self.cut_docket_reference:
            return
        
        cut_docket = frappe.get_doc("Cut Docket", self.cut_docket_reference)
        
        # Skip if already populated (to avoid overwriting user changes)
        if self.style:
            return
        
        # Order Information
        self.style = cut_docket.style
        self.style_no = cut_docket.style_no
        self.color = cut_docket.color
        self.brand = cut_docket.brand
        self.bom_no = cut_docket.bom_no
        self.panel_type = cut_docket.panel_type
        self.panel_code = cut_docket.panel_code
        self.season = cut_docket.season
        self.garment_way = cut_docket.garment_way
        self.plant_code = cut_docket.plant_code
        
        # Fabric Details
        self.fabricmaterial_details = cut_docket.fabricmaterial_details
        self.raw_material_composition = cut_docket.raw_material_composition
        self.fabric_requirement_against_bom = cut_docket.fabric_requirement_against_bom
        self.fabric_requirement_against_marker = cut_docket.fabric_requirement_against_marker
        
        # Lay Information
        self.marker_length_meters = cut_docket.marker_length_meters
        self.marker_width_meters = cut_docket.marker_width_meters
        self.no_of_plies = cut_docket.no_of_plies
        self.marker_efficiency = cut_docket.marker_efficiency
        self.marker_image = cut_docket.marker_image
        
        # Audit Details
        self.work_center = cut_docket.work_center
        self.section = cut_docket.section
        self.cut_start_date = cut_docket.cut_start_date
        
        # Copy Child Table Data (Work Order Details and Size Ratio Quantity)
        self.copy_child_tables_from_cut_docket(cut_docket)
    
    def copy_child_tables_from_cut_docket(self, cut_docket):
        """Copy child table data from Cut Docket to read-only tables"""
        # Skip if tables already populated
        if self.work_order_details or self.table_size_ratio_qty:
            return
        
        try:
            # Copy Work Order Details
            for wo_detail in cut_docket.work_order_details:
                self.append("work_order_details", {
                    "work_order": wo_detail.work_order,
                    "work_order_quantity": wo_detail.work_order_quantity,
                    "already_cut_quantity": wo_detail.already_cut_quantity,
                    "balance_quantity": wo_detail.balance_quantity
                })
            
            # Copy Size Ratio Quantity Details  
            for size_ratio in cut_docket.table_size_ratio_qty:
                self.append("table_size_ratio_qty", {
                    "ref_work_order": size_ratio.ref_work_order,
                    "sales_order": size_ratio.sales_order,
                    "line_item_no": size_ratio.line_item_no,
                    "size": size_ratio.size,
                    "quantity": size_ratio.quantity,
                    "planned_cut_quantity": size_ratio.planned_cut_quantity,
                    "balance": size_ratio.balance
                })
                
        except Exception as e:
            frappe.log_error(f"Error copying child tables from Cut Docket: {str(e)}")
    
    def populate_checklists(self):
        """Auto-populate checklist items from master data"""
        # Skip if checklists already populated
        if self.pre_laying_checklist or self.during_laying_checklist or self.after_laying_checklist:
            return
        
        try:
            # Get active checklists grouped by category
            from erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.cut_lay_checklists.cut_lay_checklists import get_all_active_checklists
            
            checklists = get_all_active_checklists()
            
            # Populate Pre Laying checklist
            for checklist in checklists.get("Pre Laying", []):
                self.append("pre_laying_checklist", {
                    "checklist_master_reference": checklist["name"],
                    "checkpoint": checklist["checkpoint"],
                    "description": checklist["description"],
                    "category": checklist["category"],
                    "is_mandatory": checklist["is_mandatory"],
                    "status": "Pending"
                })
            
            # Populate During Laying checklist
            for checklist in checklists.get("During Laying", []):
                self.append("during_laying_checklist", {
                    "checklist_master_reference": checklist["name"],
                    "checkpoint": checklist["checkpoint"],
                    "description": checklist["description"],
                    "category": checklist["category"],
                    "is_mandatory": checklist["is_mandatory"],
                    "status": "Pending"
                })
            
            # Populate After Laying checklist
            for checklist in checklists.get("After Laying", []):
                self.append("after_laying_checklist", {
                    "checklist_master_reference": checklist["name"],
                    "checkpoint": checklist["checkpoint"],
                    "description": checklist["description"],
                    "category": checklist["category"],
                    "is_mandatory": checklist["is_mandatory"],
                    "status": "Pending"
                })
                
        except Exception as e:
            frappe.log_error(f"Error populating checklists: {str(e)}")
            frappe.msgprint(_("Warning: Could not load default checklists. Please add them manually."), alert=True)
    
    def calculate_progress(self):
        """Calculate inspection progress"""
        total_items = 0
        completed_items = 0
        
        # Count items in all three checklists
        for checklist in [self.pre_laying_checklist, self.during_laying_checklist, self.after_laying_checklist]:
            for item in checklist:
                total_items += 1
                if item.status != "Pending":
                    completed_items += 1
        
        self.total_checkpoints = total_items
        self.completed_checkpoints = completed_items
        
        if total_items > 0:
            self.progress_percentage = round((completed_items / total_items) * 100, 1)
        else:
            self.progress_percentage = 0
    
    def set_defaults(self):
        """Set default values"""
        if not self.inspector:
            self.inspector = frappe.session.user
        
        if not self.inspection_date:
            self.inspection_date = nowdate()
    
    def on_submit(self):
        """Actions when inspection is submitted"""
        self.validate_completion_requirements()
        self.inspection_status = "Completed"
        self.update_cut_docket_status()
    
    def on_cancel(self):
        """Actions when inspection is cancelled"""
        self.inspection_status = "Draft"
        # Reset Cut Docket status if needed
        self.reset_cut_docket_status()
    
    def validate_completion_requirements(self):
        """Validate that inspection is ready for submission"""
        # Check if all mandatory items are completed
        mandatory_pending = []
        
        for checklist_name, checklist in [
            ("Pre Laying", self.pre_laying_checklist),
            ("During Laying", self.during_laying_checklist), 
            ("After Laying", self.after_laying_checklist)
        ]:
            for item in checklist:
                if item.is_mandatory and item.status == "Pending":
                    mandatory_pending.append(f"{checklist_name}: {item.checkpoint}")
        
        if mandatory_pending:
            frappe.throw(_(
                "Cannot submit inspection. The following mandatory items are pending:\n{0}"
            ).format("\n".join(mandatory_pending)))
        
        # Check if final status is set
        if not self.final_status:
            frappe.throw(_("Final Status is required before submission"))
        
        # Check if overall audit rating is set
        if not self.overall_audit_rating:
            frappe.throw(_("Overall Audit Rating is required before submission"))
    
    def update_cut_docket_status(self):
        """Update Cut Docket status based on inspection result"""
        try:
            cut_docket = frappe.get_doc("Cut Docket", self.cut_docket_reference)
            
            if self.final_status == "Approved - Proceed to Cutting":
                cut_docket.status = "Approved"
            elif self.final_status in ["Rejected - Rework Required", "On Hold - Further Review"]:
                cut_docket.status = "On Hold"
            else:  # Conditional Approval
                cut_docket.status = "Conditional"
            
            cut_docket.save(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Error updating Cut Docket status: {str(e)}")
    
    def reset_cut_docket_status(self):
        """Reset Cut Docket status when inspection is cancelled"""
        try:
            cut_docket = frappe.get_doc("Cut Docket", self.cut_docket_reference)
            cut_docket.status = "Created"
            cut_docket.save(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Error resetting Cut Docket status: {str(e)}")
    
    def get_inspection_summary(self):
        """Get comprehensive inspection summary"""
        summary = {
            "inspection_details": {
                "inspection_number": self.name,
                "inspection_date": self.inspection_date,
                "inspector": self.inspector,
                "status": self.inspection_status
            },
            "progress": {
                "total_checkpoints": self.total_checkpoints,
                "completed_checkpoints": self.completed_checkpoints,
                "progress_percentage": self.progress_percentage
            },
            "checklist_summary": {},
            "final_assessment": {
                "overall_rating": self.overall_audit_rating,
                "final_status": self.final_status,
                "critical_issues": self.critical_issues_identified,
                "corrective_actions": self.corrective_actions_required
            }
        }
        
        # Get detailed checklist summaries
        for checklist_name, checklist in [
            ("Pre Laying", self.pre_laying_checklist),
            ("During Laying", self.during_laying_checklist),
            ("After Laying", self.after_laying_checklist)
        ]:
            category_summary = {
                "total": len(checklist),
                "completed": len([item for item in checklist if item.status != "Pending"]),
                "passed": len([item for item in checklist if item.status == "Pass"]),
                "failed": len([item for item in checklist if item.status == "Fail"]),
                "na": len([item for item in checklist if item.status == "N/A"]),
                "mandatory_failed": len([item for item in checklist if item.is_mandatory and item.status == "Fail"])
            }
            
            if category_summary["total"] > 0:
                category_summary["completion_rate"] = round(
                    (category_summary["completed"] / category_summary["total"]) * 100, 1
                )
            else:
                category_summary["completion_rate"] = 0
            
            summary["checklist_summary"][checklist_name] = category_summary
        
        return summary


# API Methods for external access
@frappe.whitelist()
def create_from_cut_docket(cut_docket_name):
    """Create Cutting Lay Inspection from Cut Docket"""
    try:
        # Check if inspection already exists
        existing = frappe.db.exists("Cutting Lay Inspection", {"cut_docket_reference": cut_docket_name})
        if existing:
            return {"success": False, "message": "Inspection already exists for this Cut Docket", "existing_doc": existing}
        
        # Create new inspection
        inspection = frappe.new_doc("Cutting Lay Inspection")
        inspection.cut_docket_reference = cut_docket_name
        inspection.insert()
        
        return {
            "success": True, 
            "message": "Cutting Lay Inspection created successfully",
            "inspection_name": inspection.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating inspection from Cut Docket: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_inspection_progress(inspection_name):
    """Get inspection progress details"""
    try:
        inspection = frappe.get_doc("Cutting Lay Inspection", inspection_name)
        return inspection.get_inspection_summary()
        
    except Exception as e:
        frappe.log_error(f"Error getting inspection progress: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def update_inspection_status(inspection_name, status):
    """Update inspection status"""
    try:
        inspection = frappe.get_doc("Cutting Lay Inspection", inspection_name)
        inspection.inspection_status = status
        inspection.save()
        
        return {"success": True, "message": f"Status updated to {status}"}
        
    except Exception as e:
        frappe.log_error(f"Error updating inspection status: {str(e)}")
        return {"success": False, "message": str(e)}