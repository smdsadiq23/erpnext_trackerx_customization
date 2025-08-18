# Copyright (c) 2025, CognitionX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MasterChecklist(Document):
    def before_save(self):
        # Set audit fields
        if self.is_new():
            self.created_by = frappe.session.user
            self.created_on = frappe.utils.now()
        else:
            self.modified_by = frappe.session.user
            self.modified_on = frappe.utils.now()
    
    def validate(self):
        # Validate material type exists in constants
        if self.material_type:
            from erpnext_trackerx_customization.utils import get_material_types
            valid_types = get_material_types()
            if self.material_type not in valid_types:
                frappe.throw(f"Material Type {self.material_type} is not valid. Valid types are: {', '.join(valid_types)}")
        
        # Set default display order if not provided
        if not self.display_order:
            # Get the maximum display order for this material type
            max_order = frappe.db.sql("""
                SELECT IFNULL(MAX(display_order), 0) as max_order 
                FROM `tabMaster Checklist` 
                WHERE material_type = %s
            """, (self.material_type,), as_dict=True)[0].max_order
            
            self.display_order = max_order + 10


@frappe.whitelist()
def get_checklist_for_material(material_type):
    """
    Get active checklist items for a specific material type
    """
    try:
        checklist_items = frappe.get_all(
            "Master Checklist",
            filters={
                "material_type": material_type,
                "is_active": 1
            },
            fields=[
                "name", "test_parameter", "standard_requirement", 
                "test_method", "unit_of_measurement", "tolerance",
                "is_mandatory", "test_category", "description", "display_order"
            ],
            order_by="display_order asc, test_category asc, test_parameter asc"
        )
        
        return {
            "success": True,
            "checklist_items": checklist_items
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching checklist for material {material_type}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def save_checklist_results(inspection_name, inspection_type, checklist_data):
    """
    Save checklist results for an inspection
    """
    try:
        # Get the inspection document
        inspection_doc = frappe.get_doc(inspection_type, inspection_name)
        
        # Clear existing checklist data
        if hasattr(inspection_doc, 'checklist_items'):
            inspection_doc.checklist_items = []
        
        # Add new checklist items
        for item_data in checklist_data:
            if inspection_type == "Fabric Inspection":
                inspection_doc.append("fabric_checklist_items", {
                    "test_parameter": item_data.get("test_parameter"),
                    "standard_requirement": item_data.get("standard_requirement"), 
                    "actual_result": item_data.get("actual_result"),
                    "status": item_data.get("status"),
                    "remarks": item_data.get("remarks"),
                    "test_method": item_data.get("test_method"),
                    "is_mandatory": item_data.get("is_mandatory"),
                    "test_category": item_data.get("test_category")
                })
            elif inspection_type == "Trims Inspection":
                inspection_doc.append("trims_checklist_items", {
                    "test_parameter": item_data.get("test_parameter"),
                    "standard_requirement": item_data.get("standard_requirement"),
                    "actual_result": item_data.get("actual_result"), 
                    "status": item_data.get("status"),
                    "remarks": item_data.get("remarks"),
                    "test_method": item_data.get("test_method"),
                    "is_mandatory": item_data.get("is_mandatory"),
                    "test_category": item_data.get("test_category")
                })
        
        # Save the inspection document
        inspection_doc.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": "Checklist results saved successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error saving checklist results: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def create_test_data():
	"""Create test data for demonstration"""
	try:
		# No need to create Material Master - using constants from config
		
		# Create checklist items for Fabrics
		fabric_items = [
			{
				"material_type": "Fabrics",
				"test_parameter": "Tensile Strength",
				"standard_requirement": "≥ 500 N (Warp), ≥ 400 N (Weft)",
				"test_category": "Physical Testing",
				"test_method": "ASTM D5034",
				"is_mandatory": 1
			},
			{
				"material_type": "Fabrics", 
				"test_parameter": "Color Fastness to Washing",
				"standard_requirement": "Grade 4-5 (Staining), Grade 4 (Fading)",
				"test_category": "Color Matching",
				"test_method": "AATCC 61",
				"is_mandatory": 1
			},
			{
				"material_type": "Fabrics",
				"test_parameter": "Shrinkage",
				"standard_requirement": "≤ 3% (Length), ≤ 3% (Width)",
				"test_category": "Dimensional Check", 
				"test_method": "AATCC 135",
				"is_mandatory": 1
			}
		]
		
		# Create checklist items for Trims
		trims_items = [
			{
				"material_type": "Trims",
				"test_parameter": "Pull Strength", 
				"standard_requirement": "≥ 250 N for buttons, ≥ 150 N for snaps",
				"test_category": "Physical Testing",
				"test_method": "ASTM D2061",
				"is_mandatory": 1
			},
			{
				"material_type": "Trims",
				"test_parameter": "Color Fastness",
				"standard_requirement": "Grade 4 minimum (no bleeding)",
				"test_category": "Color Matching", 
				"test_method": "AATCC 8",
				"is_mandatory": 1
			},
			{
				"material_type": "Trims",
				"test_parameter": "Corrosion Resistance",
				"standard_requirement": "No visible corrosion after 24h salt spray",
				"test_category": "Chemical Testing",
				"test_method": "ASTM B117", 
				"is_mandatory": 0
			}
		]
		
		# Create all checklist items
		all_items = fabric_items + trims_items
		created_count = 0
		
		for item_data in all_items:
			existing = frappe.db.exists("Master Checklist", {
				"material_type": item_data["material_type"],
				"test_parameter": item_data["test_parameter"]
			})
			
			if not existing:
				checklist = frappe.new_doc("Master Checklist")
				checklist.update(item_data)
				checklist.is_active = 1
				checklist.save()
				created_count += 1
		
		frappe.db.commit()
		
		return {
			"success": True,
			"message": f"Created {created_count} test checklist items",
			"fabric_items": len(fabric_items),
			"trims_items": len(trims_items)
		}
		
	except Exception as e:
		frappe.log_error(f"Error creating test data: {str(e)}")
		return {"success": False, "error": str(e)}