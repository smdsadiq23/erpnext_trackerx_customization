#!/usr/bin/env python3

import frappe
from frappe import _

def create_lay_cut_categories():
    """Create default Lay Cut Categories with dummy data"""
    
    categories_data = [
        {
            "category_name": "Fabric Quality Check",
            "category_type": "Checklist",
            "scoring_weight": 25.0,
            "display_order": 1,
            "is_active": 1,
            "description": "Check fabric condition and quality before cutting",
            "default_items": [
                {"item_text": "No holes or tears", "is_critical": 1, "scoring_points": 2.0, "display_order": 1},
                {"item_text": "No stains or marks", "is_critical": 0, "scoring_points": 1.5, "display_order": 2},
                {"item_text": "No color variations", "is_critical": 1, "scoring_points": 2.0, "display_order": 3},
                {"item_text": "No wrinkles or creases", "is_critical": 0, "scoring_points": 1.0, "display_order": 4},
                {"item_text": "Proper fabric roll condition", "is_critical": 0, "scoring_points": 1.0, "display_order": 5}
            ]
        },
        {
            "category_name": "Marker Verification",
            "category_type": "Checklist", 
            "scoring_weight": 20.0,
            "display_order": 2,
            "is_active": 1,
            "description": "Verify marker quality and completeness",
            "default_items": [
                {"item_text": "All pattern pieces present", "is_critical": 1, "scoring_points": 2.0, "display_order": 1},
                {"item_text": "Marker not torn or damaged", "is_critical": 1, "scoring_points": 2.0, "display_order": 2},
                {"item_text": "Clear cutting lines", "is_critical": 1, "scoring_points": 1.5, "display_order": 3},
                {"item_text": "Proper pattern orientation", "is_critical": 1, "scoring_points": 1.5, "display_order": 4},
                {"item_text": "Notches clearly marked", "is_critical": 0, "scoring_points": 1.0, "display_order": 5}
            ]
        },
        {
            "category_name": "Lay Setup Inspection", 
            "category_type": "Checklist",
            "scoring_weight": 25.0,
            "display_order": 3,
            "is_active": 1,
            "description": "Inspect lay setup and fabric spreading quality",
            "default_items": [
                {"item_text": "Even fabric tension", "is_critical": 1, "scoring_points": 2.0, "display_order": 1},
                {"item_text": "Proper layer alignment", "is_critical": 1, "scoring_points": 2.0, "display_order": 2},
                {"item_text": "No wrinkles between layers", "is_critical": 1, "scoring_points": 1.5, "display_order": 3},
                {"item_text": "Straight lay edges", "is_critical": 0, "scoring_points": 1.0, "display_order": 4},
                {"item_text": "Consistent layer thickness", "is_critical": 0, "scoring_points": 1.0, "display_order": 5}
            ]
        },
        {
            "category_name": "Pattern Placement",
            "category_type": "Checklist",
            "scoring_weight": 20.0, 
            "display_order": 4,
            "is_active": 1,
            "description": "Check pattern placement and grain alignment",
            "default_items": [
                {"item_text": "Centered on fabric lay", "is_critical": 0, "scoring_points": 1.0, "display_order": 1},
                {"item_text": "Proper grain alignment", "is_critical": 1, "scoring_points": 2.0, "display_order": 2},
                {"item_text": "Pattern matching aligned", "is_critical": 1, "scoring_points": 1.5, "display_order": 3},
                {"item_text": "Adequate seam allowances", "is_critical": 1, "scoring_points": 1.5, "display_order": 4},
                {"item_text": "Special markings visible", "is_critical": 0, "scoring_points": 1.0, "display_order": 5}
            ]
        },
        {
            "category_name": "Surface Quality Assessment",
            "category_type": "Scoring",
            "scoring_weight": 10.0,
            "display_order": 5, 
            "is_active": 1,
            "description": "Overall surface quality evaluation",
            "default_items": [
                {"item_text": "Smooth surface", "is_critical": 0, "scoring_points": 1.0, "display_order": 1},
                {"item_text": "No air bubbles", "is_critical": 0, "scoring_points": 1.0, "display_order": 2},
                {"item_text": "Proper compression", "is_critical": 0, "scoring_points": 1.0, "display_order": 3},
                {"item_text": "No loose layers", "is_critical": 1, "scoring_points": 1.5, "display_order": 4},
                {"item_text": "No tight spots", "is_critical": 0, "scoring_points": 1.0, "display_order": 5}
            ]
        }
    ]
    
    for cat_data in categories_data:
        if not frappe.db.exists("Lay Cut Category", cat_data["category_name"]):
            # Create category
            cat = frappe.get_doc({
                "doctype": "Lay Cut Category",
                "category_name": cat_data["category_name"],
                "category_type": cat_data["category_type"],
                "scoring_weight": cat_data["scoring_weight"],
                "display_order": cat_data["display_order"],
                "is_active": cat_data["is_active"],
                "description": cat_data["description"]
            })
            
            # Add default items
            for item_data in cat_data["default_items"]:
                cat.append("default_checklist_items", {
                    "item_text": item_data["item_text"],
                    "is_critical": item_data["is_critical"],
                    "scoring_points": item_data["scoring_points"],
                    "display_order": item_data["display_order"]
                })
            
            cat.insert()
            print(f"Created category: {cat_data['category_name']}")
    
    frappe.db.commit()


def create_sample_lay_cut_inspection():
    """Create a sample Lay Cut Inspection with comprehensive dummy data"""
    
    # Check if sample already exists
    if frappe.db.exists("Lay Cut Inspection", {"lay_cut_number": "LC-TEST-001"}):
        return frappe.get_doc("Lay Cut Inspection", {"lay_cut_number": "LC-TEST-001"})
    
    doc = frappe.get_doc({
        "doctype": "Lay Cut Inspection",
        "lay_cut_number": "LC-TEST-001",
        "inspection_date": frappe.utils.today(),
        "inspection_time": "09:30:00",
        "inspector_name": "Administrator",
        "inspector_id": "INS001", 
        "order_number": "ORD-2025-001",
        "style_number": "STY-SHIRT-001",
        "fabric_code": "FAB-COT-NAVY-001",
        "color": "Navy Blue",
        "total_layers": 75,
        "marker_length": 3.2,
        "marker_area": 32.5,
        "fabric_used": 38.2,
        "target_efficiency": 85.0,
        
        # Enhanced measurements
        "length_start": 320.0,
        "length_center": 320.3,
        "length_end": 319.8,
        "width_left": 150.0,
        "width_center": 150.2,
        "width_right": 149.9,
        "height_inches": 3.75,
        "actual_layers": 75,
        "end_waste_inches": 2.5,
        "side_waste_inches": 1.8,
        
        # Assessment and authorization
        "lay_status": "Approved for Cutting",
        "cutting_authorization": "Authorized Immediately",
        "authorized_by": "Quality Supervisor",
        "authorization_date": frappe.utils.now(),
        
        # Enhanced scoring
        "spreading_quality_score": 88.5,
        "technical_accuracy_score": 92.0,
        "defect_deduction_score": 85.0,
        "surface_quality_rating": 4,
        
        # Comprehensive notes
        "inspector_comments": "High quality lay with excellent fabric condition. Minor wrinkles detected in middle layers but within acceptable limits. Efficient marker utilization achieved.",
        "quality_manager_review": "Approved for cutting with commendation for quality standards. Monitor layer alignment for future improvements.",
        "corrective_actions": "1. Implement additional tension control for middle layers\n2. Review spreading technique for layers 40-50\n3. Document best practices for team training",
        "special_cutting_instructions": "Use sharp blades for precision cutting. Pay attention to pattern matching on front panels. Mark notches clearly for assembly team.",
        
        # Signatures
        "inspector_signature_date": frappe.utils.now(),
        "quality_supervisor": "Quality Manager",
        "quality_supervisor_date": frappe.utils.now(),
        "cutting_supervisor": "Cutting Floor Supervisor",
        "cutting_supervisor_date": frappe.utils.now()
    })
    
    # Add fabric quality checks
    fabric_checks = [
        {"check_item": "No holes or tears", "status": "Pass", "comments": "Clean fabric", "is_critical": 1, "scoring_points": 2.0},
        {"check_item": "No stains or marks", "status": "Pass", "comments": "", "is_critical": 0, "scoring_points": 1.5},
        {"check_item": "No color variations", "status": "Pass", "comments": "Uniform color", "is_critical": 1, "scoring_points": 2.0},
        {"check_item": "No wrinkles or creases", "status": "Pass", "comments": "", "is_critical": 0, "scoring_points": 1.0},
        {"check_item": "Proper fabric roll condition", "status": "Pass", "comments": "Good roll", "is_critical": 0, "scoring_points": 1.0}
    ]
    
    for check in fabric_checks:
        doc.append("fabric_quality_checks", check)
    
    # Add marker verification checks
    marker_checks = [
        {"check_item": "All pattern pieces present", "status": "Pass", "comments": "Complete set", "is_critical": 1, "scoring_points": 2.0},
        {"check_item": "Marker not torn or damaged", "status": "Pass", "comments": "", "is_critical": 1, "scoring_points": 2.0},
        {"check_item": "Clear cutting lines", "status": "Pass", "comments": "Clear marks", "is_critical": 1, "scoring_points": 1.5},
        {"check_item": "Proper pattern orientation", "status": "Pass", "comments": "", "is_critical": 1, "scoring_points": 1.5},
        {"check_item": "Notches clearly marked", "status": "Pass", "comments": "All notches visible", "is_critical": 0, "scoring_points": 1.0}
    ]
    
    for check in marker_checks:
        doc.append("marker_verification_checks", check)
    
    # Add lay setup checks
    lay_checks = [
        {"check_item": "Even fabric tension", "status": "Pass", "comments": "Good tension", "is_critical": 1, "scoring_points": 2.0},
        {"check_item": "Proper layer alignment", "status": "Pass", "comments": "Well aligned", "is_critical": 1, "scoring_points": 2.0},
        {"check_item": "No wrinkles between layers", "status": "Fail", "comments": "Minor wrinkles in layer 25", "is_critical": 1, "scoring_points": 1.5},
        {"check_item": "Straight lay edges", "status": "Pass", "comments": "", "is_critical": 0, "scoring_points": 1.0},
        {"check_item": "Consistent layer thickness", "status": "Pass", "comments": "Uniform thickness", "is_critical": 0, "scoring_points": 1.0}
    ]
    
    for check in lay_checks:
        doc.append("lay_setup_checks", check)
    
    # Add pattern placement checks  
    pattern_checks = [
        {"check_item": "Centered on fabric lay", "status": "Pass", "comments": "Well centered", "is_critical": 0, "scoring_points": 1.0},
        {"check_item": "Proper grain alignment", "status": "Pass", "comments": "Perfect grain", "is_critical": 1, "scoring_points": 2.0},
        {"check_item": "Pattern matching aligned", "status": "Pass", "comments": "Good matching", "is_critical": 1, "scoring_points": 1.5},
        {"check_item": "Adequate seam allowances", "status": "Pass", "comments": "", "is_critical": 1, "scoring_points": 1.5},
        {"check_item": "Special markings visible", "status": "Pass", "comments": "All marks clear", "is_critical": 0, "scoring_points": 1.0}
    ]
    
    for check in pattern_checks:
        doc.append("pattern_placement_checks", check)
    
    # Add comprehensive defects
    critical_defects = [
        {"defect_name": "Small hole in cutting area", "count": 1, "action_taken": "Marked and avoided during cutting", "scoring_impact": -10.0},
        {"defect_name": "Major color variation", "count": 1, "action_taken": "Replaced affected section", "scoring_impact": -8.0}
    ]
    
    for defect in critical_defects:
        doc.append("critical_defects", defect)
    
    major_defects = [
        {"defect_name": "Slight color differences", "count": 3, "action_taken": "Documented for pattern matching", "scoring_impact": -2.5},
        {"defect_name": "Yarn irregularities", "count": 2, "action_taken": "Within tolerance limits", "scoring_impact": -1.5},
        {"defect_name": "Fabric tension variations", "count": 1, "action_taken": "Adjusted spreading technique", "scoring_impact": -3.0},
        {"defect_name": "Minor wrinkles", "count": 4, "action_taken": "Steam pressed affected areas", "scoring_impact": -2.0}
    ]
    
    for defect in major_defects:
        doc.append("major_defects", defect)
    
    minor_defects = [
        {"defect_name": "Small fabric knots", "count": 5, "action_taken": "Noted for cutting precision", "scoring_impact": -0.5},
        {"defect_name": "Minor slubs", "count": 3, "action_taken": "Acceptable quality level", "scoring_impact": -0.3},
        {"defect_name": "Slight texture variation", "count": 2, "action_taken": "Documented for QC", "scoring_impact": -0.4},
        {"defect_name": "Edge irregularities", "count": 1, "action_taken": "Trimmed excess material", "scoring_impact": -0.2}
    ]
    
    for defect in minor_defects:
        doc.append("minor_defects", defect)
    
    # Add dynamic layer quality assessments
    layer_assessments = [
        {"layer_number": 5, "quality_rating": "Good", "comments": "Excellent layer alignment", "inspector_notes": "Perfect tension and positioning"},
        {"layer_number": 15, "quality_rating": "Good", "comments": "Clean layer with proper alignment", "inspector_notes": "No issues detected"},
        {"layer_number": 23, "quality_rating": "Fair", "comments": "Minor wrinkle detected", "inspector_notes": "Small wrinkle on left edge, acceptable level"},
        {"layer_number": 35, "quality_rating": "Good", "comments": "Good quality layer", "inspector_notes": "Proper fabric spreading"},
        {"layer_number": 42, "quality_rating": "Poor", "comments": "Tension issue detected", "inspector_notes": "Required adjustment and re-spreading of this layer"},
        {"layer_number": 58, "quality_rating": "Good", "comments": "Improved after adjustment", "inspector_notes": "Quality restored after tension correction"},
        {"layer_number": 67, "quality_rating": "Good", "comments": "Consistent quality maintained", "inspector_notes": "Excellent layer condition"},
        {"layer_number": 72, "quality_rating": "Fair", "comments": "Minor edge irregularity", "inspector_notes": "Edge slightly uneven but within tolerance"}
    ]
    
    for assessment in layer_assessments:
        doc.append("layer_quality_assessments", assessment)
    
    # Set standard layer statuses (every 10th layer)
    doc.layer_10_status = "Good"
    doc.layer_20_status = "Good" 
    doc.layer_30_status = "Fair"
    doc.layer_40_status = "Good"
    doc.layer_50_status = "Good"
    doc.layer_60_status = "Good"
    doc.layer_70_status = "Fair"
    doc.surface_quality_rating = 4
    
    # Set some scoring values
    doc.spreading_quality_score = 85.0
    doc.technical_accuracy_score = 90.0 
    doc.defect_deduction_score = 78.0
    
    doc.inspector_comments = "Overall good quality lay. Minor wrinkles detected in layer 25 but within acceptable limits."
    doc.quality_manager_review = "Approved for cutting with noted observations."
    doc.corrective_actions = "Monitor layer alignment more closely for future lays."
    
    doc.insert()
    frappe.db.commit()
    
    print(f"Created sample inspection: {doc.name}")
    return doc


if __name__ == "__main__":
    frappe.init()
    create_lay_cut_categories()
    create_sample_lay_cut_inspection()
    print("Dummy data creation completed!")