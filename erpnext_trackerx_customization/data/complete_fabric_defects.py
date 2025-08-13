#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Fabric Defects Data Import

Adds remaining fabric defects from your comprehensive list:
- Remaining Weaving Defects (WD007-WD013)  
- Dyeing/Finishing Defects (DD001-DD012)
- Printing Defects (PD001-PD008)
- Physical Defects (PH001-PH008)

Usage:
    bench execute erpnext_trackerx_customization.data.complete_fabric_defects.import_remaining_fabric_defects
"""

import frappe

def get_remaining_fabric_defects():
    """Get remaining fabric defects data"""
    return [
        # Remaining B. WEAVING DEFECTS (WD007-WD013)
        {
            "defect_code": "WD007",
            "defect_name": "Tight End",
            "defect_description": "Excessive warp tension",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Tension",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 3\" length",
            "point_2_criteria": "3\" to 6\"",
            "point_3_criteria": "6\" to 9\"",
            "point_4_criteria": "> 9\"",
            "is_active": 1
        },
        {
            "defect_code": "WD008",
            "defect_name": "Slack End",
            "defect_description": "Insufficient warp tension",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Tension",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 3\" length",
            "point_2_criteria": "3\" to 6\"",
            "point_3_criteria": "6\" to 9\"",
            "point_4_criteria": "> 9\"",
            "is_active": 1
        },
        {
            "defect_code": "WD009",
            "defect_name": "Reed Mark",
            "defect_description": "Lines from damaged reed",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Equipment Marks",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Faint lines",
            "point_2_criteria": "Visible lines",
            "point_3_criteria": "Prominent",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "WD010",
            "defect_name": "Temple Mark",
            "defect_description": "Marks from temple pins",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Equipment Marks",
            "defect_type": "Minor",
            "inspection_area": "Fabric Edges",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/2\" from edge",
            "point_2_criteria": "1/2\" to 1\"",
            "point_3_criteria": "1\" to 2\"",
            "point_4_criteria": "> 2\"",
            "is_active": 1
        },
        {
            "defect_code": "WD011",
            "defect_name": "Leno/Weave Defect",
            "defect_description": "Incorrect weave pattern",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Pattern",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1\" area",
            "point_2_criteria": "1\" to 2\"",
            "point_3_criteria": "2\" to 4\"",
            "point_4_criteria": "> 4\"",
            "is_active": 1
        },
        {
            "defect_code": "WD012",
            "defect_name": "Starting Mark",
            "defect_description": "Beginning of weaving marks",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Process Marks",
            "defect_type": "Minor",
            "inspection_area": "Fabric Beginning",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "WD013",
            "defect_name": "Stop Mark",
            "defect_description": "Weaving stoppage marks",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Process Marks",
            "defect_type": "Minor",
            "inspection_area": "Throughout Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        
        # C. DYEING/FINISHING DEFECTS (DD001-DD012)
        {
            "defect_code": "DD001",
            "defect_name": "Shade Variation",
            "defect_description": "Color difference in fabric",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Color Quality",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Slight",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "DD002",
            "defect_name": "Color Streaks",
            "defect_description": "Lines of different color",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Color Quality",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 3\" length",
            "point_2_criteria": "3\" to 6\"",
            "point_3_criteria": "6\" to 9\"",
            "point_4_criteria": "> 9\"",
            "is_active": 1
        },
        {
            "defect_code": "DD003",
            "defect_name": "Uneven Dyeing",
            "defect_description": "Irregular color distribution",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Color Uniformity",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 2\" area",
            "point_2_criteria": "2\" to 4\"",
            "point_3_criteria": "4\" to 6\"",
            "point_4_criteria": "> 6\"",
            "is_active": 1
        },
        {
            "defect_code": "DD004",
            "defect_name": "Dye Spots",
            "defect_description": "Concentrated dye deposits",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Dye Application",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" dia",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        },
        {
            "defect_code": "DD005",
            "defect_name": "Stains/Oil Spots",
            "defect_description": "Foreign matter stains",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Contamination",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" dia",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        },
        {
            "defect_code": "DD006",
            "defect_name": "Water Marks",
            "defect_description": "Processing fluid marks",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Process Marks",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1\" area",
            "point_2_criteria": "1\" to 2\"",
            "point_3_criteria": "2\" to 4\"",
            "point_4_criteria": "> 4\"",
            "is_active": 1
        },
        {
            "defect_code": "DD007",
            "defect_name": "Crease Mark",
            "defect_description": "Permanent fold lines",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Finishing",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 3\" length",
            "point_2_criteria": "3\" to 6\"",
            "point_3_criteria": "6\" to 9\"",
            "point_4_criteria": "> 9\"",
            "is_active": 1
        },
        {
            "defect_code": "DD008",
            "defect_name": "Shading",
            "defect_description": "Gradual color variation",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Color Consistency",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Slight",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "DD009",
            "defect_name": "Chemical Stains",
            "defect_description": "Processing chemical marks",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Chemical Damage",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" area",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        },
        {
            "defect_code": "DD010",
            "defect_name": "Bleeding",
            "defect_description": "Color migration",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Color Stability",
            "defect_type": "Major",
            "inspection_area": "Color Boundaries",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "DD011",
            "defect_name": "Bronzing",
            "defect_description": "Metallic appearance",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Surface Appearance",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Slight",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "DD012",
            "defect_name": "Fading",
            "defect_description": "Color loss",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Dyeing/Finishing Defects",
            "fault_group": "Color Retention",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        
        # D. PRINTING DEFECTS (PD001-PD008)
        {
            "defect_code": "PD001",
            "defect_name": "Color Out of Register",
            "defect_description": "Misaligned print colors",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Print Registration",
            "defect_type": "Major",
            "inspection_area": "Printed Areas",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/8\" misalign",
            "point_2_criteria": "1/8\" to 1/4\"",
            "point_3_criteria": "1/4\" to 1/2\"",
            "point_4_criteria": "> 1/2\"",
            "is_active": 1
        },
        {
            "defect_code": "PD002",
            "defect_name": "Print Missing",
            "defect_description": "Incomplete print elements",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Print Coverage",
            "defect_type": "Major",
            "inspection_area": "Printed Areas",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/2\" area",
            "point_2_criteria": "1/2\" to 1\"",
            "point_3_criteria": "1\" to 2\"",
            "point_4_criteria": "> 2\"",
            "is_active": 1
        },
        {
            "defect_code": "PD003",
            "defect_name": "Print Smudging",
            "defect_description": "Blurred print design",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Print Clarity",
            "defect_type": "Minor",
            "inspection_area": "Printed Areas",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/2\" area",
            "point_2_criteria": "1/2\" to 1\"",
            "point_3_criteria": "1\" to 2\"",
            "point_4_criteria": "> 2\"",
            "is_active": 1
        },
        {
            "defect_code": "PD004",
            "defect_name": "Color Bleeding",
            "defect_description": "Print colors running",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Color Stability",
            "defect_type": "Major",
            "inspection_area": "Printed Areas",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" spread",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        },
        {
            "defect_code": "PD005",
            "defect_name": "Double Print",
            "defect_description": "Overlapped print pattern",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Print Registration",
            "defect_type": "Major",
            "inspection_area": "Printed Areas",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/2\" area",
            "point_2_criteria": "1/2\" to 1\"",
            "point_3_criteria": "1\" to 2\"",
            "point_4_criteria": "> 2\"",
            "is_active": 1
        },
        {
            "defect_code": "PD006",
            "defect_name": "Print Distortion",
            "defect_description": "Deformed print pattern",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Pattern Integrity",
            "defect_type": "Major",
            "inspection_area": "Printed Areas",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/2\" area",
            "point_2_criteria": "1/2\" to 1\"",
            "point_3_criteria": "1\" to 2\"",
            "point_4_criteria": "> 2\"",
            "is_active": 1
        },
        {
            "defect_code": "PD007",
            "defect_name": "Color Strike Through",
            "defect_description": "Print penetrating fabric",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Print Application",
            "defect_type": "Minor",
            "inspection_area": "Fabric Reverse",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "PD008",
            "defect_name": "Print Crack",
            "defect_description": "Cracks in printed area",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Printing Defects",
            "fault_group": "Print Durability",
            "defect_type": "Major",
            "inspection_area": "Printed Areas",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        
        # E. PHYSICAL DEFECTS (PH001-PH008)
        {
            "defect_code": "PH001",
            "defect_name": "Holes",
            "defect_description": "Physical openings",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Structural Damage",
            "defect_type": "Critical",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Pin hole",
            "point_2_criteria": "≤ 1/4\" dia",
            "point_3_criteria": "1/4\" to 1/2\"",
            "point_4_criteria": "> 1/2\"",
            "is_active": 1
        },
        {
            "defect_code": "PH002",
            "defect_name": "Cuts/Tears",
            "defect_description": "Physical damage",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Structural Damage",
            "defect_type": "Critical",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/2\" length",
            "point_2_criteria": "1/2\" to 1\"",
            "point_3_criteria": "1\" to 2\"",
            "point_4_criteria": "> 2\"",
            "is_active": 1
        },
        {
            "defect_code": "PH003",
            "defect_name": "Snags",
            "defect_description": "Pulled loops/threads",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Surface Damage",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" height",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        },
        {
            "defect_code": "PH004",
            "defect_name": "Puckering",
            "defect_description": "Unwanted gathering",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Surface Distortion",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1\" area",
            "point_2_criteria": "1\" to 2\"",
            "point_3_criteria": "2\" to 4\"",
            "point_4_criteria": "> 4\"",
            "is_active": 1
        },
        {
            "defect_code": "PH005",
            "defect_name": "Bow/Skew",
            "defect_description": "Fabric geometry distortion",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Geometric Distortion",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1%",
            "point_2_criteria": "1% to 2%",
            "point_3_criteria": "2% to 3%",
            "point_4_criteria": "> 3%",
            "is_active": 1
        },
        {
            "defect_code": "PH006",
            "defect_name": "Wrinkles",
            "defect_description": "Unwanted creases",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Surface Distortion",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 3\" length",
            "point_2_criteria": "3\" to 6\"",
            "point_3_criteria": "6\" to 9\"",
            "point_4_criteria": "> 9\"",
            "is_active": 1
        },
        {
            "defect_code": "PH007",
            "defect_name": "Moire",
            "defect_description": "Wavy pattern",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Surface Pattern",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        {
            "defect_code": "PH008",
            "defect_name": "Cockled Edge",
            "defect_description": "Wavy fabric edges",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Physical Defects",
            "fault_group": "Edge Quality",
            "defect_type": "Minor",
            "inspection_area": "Fabric Edges",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        }
    ]

def import_remaining_fabric_defects():
    """Import remaining fabric defects"""
    
    print("🎯 IMPORTING REMAINING FABRIC DEFECTS")
    print("=" * 50)
    
    defects_data = get_remaining_fabric_defects()
    
    imported_count = 0
    updated_count = 0
    error_count = 0
    
    for defect_data in defects_data:
        try:
            # Check if defect already exists
            if frappe.db.exists("Defect Master", defect_data["defect_code"]):
                # Update existing
                doc = frappe.get_doc("Defect Master", defect_data["defect_code"])
                for field, value in defect_data.items():
                    setattr(doc, field, value)
                doc.save()
                updated_count += 1
                print(f"✅ Updated: {defect_data['defect_code']} - {defect_data['defect_name']}")
            else:
                # Create new
                doc = frappe.new_doc("Defect Master")
                for field, value in defect_data.items():
                    setattr(doc, field, value)
                doc.insert()
                imported_count += 1
                print(f"✅ Created: {defect_data['defect_code']} - {defect_data['defect_name']}")
                
        except Exception as e:
            error_count += 1
            print(f"❌ Error with {defect_data['defect_code']}: {str(e)}")
    
    # Commit all changes
    frappe.db.commit()
    
    print(f"\n📊 Import Summary:")
    print(f"   • Created: {imported_count}")
    print(f"   • Updated: {updated_count}")
    print(f"   • Errors: {error_count}")
    print(f"   • Total processed: {len(defects_data)}")
    
    print(f"\n🎉 REMAINING FABRIC DEFECTS IMPORTED!")
    print(f"📈 Total new defects: {imported_count + updated_count}")
    
    return True

if __name__ == "__main__":
    success = import_remaining_fabric_defects()
    exit(0 if success else 1)