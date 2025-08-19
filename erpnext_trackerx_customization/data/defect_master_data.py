#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defect Master Data Import

Imports comprehensive defect data for:
1. Fabric Inspection (with 4-point system)
2. Trims Inspection 
3. Final Inspection

Usage:
    bench execute erpnext_trackerx_customization.data.defect_master_data.import_all_defects
"""

import frappe
import os

def get_fabric_defects_data():
    """Get fabric inspection defects with 4-point system"""
    return [
        # A. YARN DEFECTS
        {
            "defect_code": "YD001",
            "defect_name": "Thick Yarn",
            "defect_description": "Yarn with excessive thickness",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Yarn Quality",
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
            "defect_code": "YD002",
            "defect_name": "Thin Yarn",
            "defect_description": "Yarn with reduced thickness",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Yarn Quality",
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
            "defect_code": "YD003",
            "defect_name": "Slub Yarn",
            "defect_description": "Thick places in yarn",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Yarn Quality",
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
            "defect_code": "YD004",
            "defect_name": "Nep/Foreign Fiber",
            "defect_description": "Small fiber tangles/foreign matter",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Contamination",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" dia",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        },
        {
            "defect_code": "YD005",
            "defect_name": "Hairy Yarn",
            "defect_description": "Excessive protruding fibers",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Surface Quality",
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
            "defect_code": "YD006",
            "defect_name": "Yarn Contamination",
            "defect_description": "Foreign matter in yarn",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Contamination",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" size",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        },
        {
            "defect_code": "YD007",
            "defect_name": "Knotted Yarn",
            "defect_description": "Knots in yarn",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Yarn Quality",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Small knot",
            "point_2_criteria": "Medium knot",
            "point_3_criteria": "Large knot",
            "point_4_criteria": "Very large",
            "is_active": 1
        },
        {
            "defect_code": "YD008",
            "defect_name": "Weak Yarn",
            "defect_description": "Low strength yarn",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Yarn Defects",
            "fault_group": "Strength",
            "defect_type": "Major",
            "inspection_area": "Test Sample",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "Minor weakness",
            "point_2_criteria": "Noticeable",
            "point_3_criteria": "Obvious",
            "point_4_criteria": "Severe",
            "is_active": 1
        },
        
        # B. WEAVING DEFECTS
        {
            "defect_code": "WD001",
            "defect_name": "Broken End",
            "defect_description": "Warp yarn breakage",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Weaving",
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
            "defect_code": "WD002",
            "defect_name": "Missing End",
            "defect_description": "Absent warp yarn",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Weaving",
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
            "defect_code": "WD003",
            "defect_name": "Broken Pick",
            "defect_description": "Weft yarn breakage",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Weaving",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 3\" width",
            "point_2_criteria": "3\" to 6\"",
            "point_3_criteria": "6\" to 9\"",
            "point_4_criteria": "> 9\"",
            "is_active": 1
        },
        {
            "defect_code": "WD004",
            "defect_name": "Missing Pick",
            "defect_description": "Absent weft yarn",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Weaving",
            "defect_type": "Major",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 3\" width",
            "point_2_criteria": "3\" to 6\"",
            "point_3_criteria": "6\" to 9\"",
            "point_4_criteria": "> 9\"",
            "is_active": 1
        },
        {
            "defect_code": "WD005",
            "defect_name": "Float",
            "defect_description": "Yarn not interlaced properly",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Weaving",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/2\"",
            "point_2_criteria": "1/2\" to 1\"",
            "point_3_criteria": "1\" to 2\"",
            "point_4_criteria": "> 2\"",
            "is_active": 1
        },
        {
            "defect_code": "WD006",
            "defect_name": "Snarls/Loop",
            "defect_description": "Yarn loops on surface",
            "inspection_type": "Fabric Inspection",
            "defect_category": "Weaving Defects",
            "fault_group": "Surface Quality",
            "defect_type": "Minor",
            "inspection_area": "Entire Fabric",
            "acceptable_limit": "Based on point system",
            "point_1_criteria": "≤ 1/4\" height",
            "point_2_criteria": "1/4\" to 1/2\"",
            "point_3_criteria": "1/2\" to 1\"",
            "point_4_criteria": "> 1\"",
            "is_active": 1
        }
        # Additional weaving defects would continue here...
    ]

def get_trims_defects_data():
    """Get trims inspection defects"""
    return [
        # Visual Defects
        {
            "defect_code": "TR001",
            "defect_name": "Color Variation",
            "defect_description": "Color difference in trim components",
            "inspection_type": "Trims Inspection",
            "defect_category": "Visual Defects",
            "fault_group": "Appearance",
            "defect_type": "Major",
            "inspection_area": "All Trim Components",
            "acceptable_limit": "No visible variation",
            "is_active": 1
        },
        {
            "defect_code": "TR002",
            "defect_name": "Surface Scratch",
            "defect_description": "Scratches on trim surface",
            "inspection_type": "Trims Inspection",
            "defect_category": "Visual Defects",
            "fault_group": "Surface Quality",
            "defect_type": "Minor",
            "inspection_area": "All Surfaces",
            "acceptable_limit": "Light scratches acceptable",
            "is_active": 1
        },
        {
            "defect_code": "TR003",
            "defect_name": "Stain/Mark",
            "defect_description": "Stains or marks on trim",
            "inspection_type": "Trims Inspection",
            "defect_category": "Visual Defects",
            "fault_group": "Cleanliness",
            "defect_type": "Major",
            "inspection_area": "All Surfaces",
            "acceptable_limit": "0 visible stains",
            "is_active": 1
        },
        {
            "defect_code": "TR004",
            "defect_name": "Broken/Cracked",
            "defect_description": "Physical damage to trim",
            "inspection_type": "Trims Inspection",
            "defect_category": "Visual Defects",
            "fault_group": "Structural Integrity",
            "defect_type": "Critical",
            "inspection_area": "All Components",
            "acceptable_limit": "0 broken parts",
            "is_active": 1
        },
        {
            "defect_code": "TR005",
            "defect_name": "Missing Parts",
            "defect_description": "Components missing from trim",
            "inspection_type": "Trims Inspection",
            "defect_category": "Visual Defects",
            "fault_group": "Completeness",
            "defect_type": "Critical",
            "inspection_area": "Complete Assembly",
            "acceptable_limit": "All parts must be present",
            "is_active": 1
        },
        {
            "defect_code": "TR006",
            "defect_name": "Wrong Shape",
            "defect_description": "Incorrect shape or form",
            "inspection_type": "Trims Inspection",
            "defect_category": "Visual Defects",
            "fault_group": "Design Conformity",
            "defect_type": "Major",
            "inspection_area": "Overall Shape",
            "acceptable_limit": "Must match specification",
            "is_active": 1
        },
        {
            "defect_code": "TR007",
            "defect_name": "Poor Finish",
            "defect_description": "Inadequate surface finish",
            "inspection_type": "Trims Inspection",
            "defect_category": "Visual Defects",
            "fault_group": "Surface Quality",
            "defect_type": "Minor",
            "inspection_area": "All Surfaces",
            "acceptable_limit": "Minor finish variations acceptable",
            "is_active": 1
        },
        
        # Dimensional Defects
        {
            "defect_code": "TR008",
            "defect_name": "Oversized",
            "defect_description": "Dimensions exceed specification",
            "inspection_type": "Trims Inspection",
            "defect_category": "Dimensional Defects",
            "fault_group": "Dimensions",
            "defect_type": "Major",
            "inspection_area": "Critical Dimensions",
            "acceptable_limit": "Within tolerance",
            "is_active": 1
        },
        {
            "defect_code": "TR009",
            "defect_name": "Undersized",
            "defect_description": "Dimensions below specification",
            "inspection_type": "Trims Inspection",
            "defect_category": "Dimensional Defects",
            "fault_group": "Dimensions",
            "defect_type": "Major",
            "inspection_area": "Critical Dimensions",
            "acceptable_limit": "Within tolerance",
            "is_active": 1
        },
        {
            "defect_code": "TR010",
            "defect_name": "Wrong Thickness",
            "defect_description": "Incorrect thickness measurement",
            "inspection_type": "Trims Inspection",
            "defect_category": "Dimensional Defects",
            "fault_group": "Thickness",
            "defect_type": "Major",
            "inspection_area": "Thickness Measurements",
            "acceptable_limit": "Within tolerance",
            "is_active": 1
        },
        {
            "defect_code": "TR011",
            "defect_name": "Uneven Edges",
            "defect_description": "Irregular or uneven edges",
            "inspection_type": "Trims Inspection",
            "defect_category": "Dimensional Defects",
            "fault_group": "Edge Quality",
            "defect_type": "Minor",
            "inspection_area": "All Edges",
            "acceptable_limit": "Minor variations acceptable",
            "is_active": 1
        },
        
        # Functional Defects
        {
            "defect_code": "TR012",
            "defect_name": "Poor Attachment",
            "defect_description": "Inadequate attachment mechanism",
            "inspection_type": "Trims Inspection",
            "defect_category": "Functional Defects",
            "fault_group": "Attachment",
            "defect_type": "Critical",
            "inspection_area": "Attachment Points",
            "acceptable_limit": "Must be secure",
            "is_active": 1
        },
        {
            "defect_code": "TR013",
            "defect_name": "Weak Strength",
            "defect_description": "Insufficient strength for intended use",
            "inspection_type": "Trims Inspection",
            "defect_category": "Functional Defects",
            "fault_group": "Strength",
            "defect_type": "Critical",
            "inspection_area": "Load Bearing Parts",
            "acceptable_limit": "Must meet strength requirements",
            "is_active": 1
        },
        {
            "defect_code": "TR014",
            "defect_name": "Operational Failure",
            "defect_description": "Trim does not function as intended",
            "inspection_type": "Trims Inspection",
            "defect_category": "Functional Defects",
            "fault_group": "Functionality",
            "defect_type": "Critical",
            "inspection_area": "Functional Test",
            "acceptable_limit": "Must function properly",
            "is_active": 1
        },
        {
            "defect_code": "TR015",
            "defect_name": "Poor Durability",
            "defect_description": "Inadequate durability for expected use",
            "inspection_type": "Trims Inspection",
            "defect_category": "Functional Defects",
            "fault_group": "Durability",
            "defect_type": "Major",
            "inspection_area": "Durability Test",
            "acceptable_limit": "Must meet durability standards",
            "is_active": 1
        }
    ]

def get_final_inspection_defects_data():
    """Get final inspection defects (C, F, T, A series)"""
    return [
        # C-Series: Workmanship Defects
        {
            "defect_code": "C1",
            "defect_name": "Loose & Untrimmed Threads",
            "defect_description": "Loose threads not properly trimmed",
            "inspection_type": "Final Inspection",
            "defect_category": "Workmanship",
            "fault_group": "Stitching",
            "defect_type": "Minor",
            "inspection_area": "All Seams",
            "acceptable_limit": "2 per garment",
            "is_active": 1
        },
        {
            "defect_code": "C2",
            "defect_name": "Holes/Dropped Needle",
            "defect_description": "Holes or needle damage",
            "inspection_type": "Final Inspection",
            "defect_category": "Workmanship",
            "fault_group": "Fabric Damage",
            "defect_type": "Major",
            "inspection_area": "Entire Garment",
            "acceptable_limit": "0 per garment",
            "is_active": 1
        },
        {
            "defect_code": "C3",
            "defect_name": "Pocket Defects",
            "defect_description": "Issues with pocket construction",
            "inspection_type": "Final Inspection",
            "defect_category": "Workmanship",
            "fault_group": "Construction",
            "defect_type": "Minor",
            "inspection_area": "Pockets",
            "acceptable_limit": "1 per garment",
            "is_active": 1
        },
        {
            "defect_code": "C4",
            "defect_name": "Over/Under Pressed",
            "defect_description": "Pressing issues",
            "inspection_type": "Final Inspection",
            "defect_category": "Workmanship",
            "fault_group": "Finishing",
            "defect_type": "Minor",
            "inspection_area": "Pressed Areas",
            "acceptable_limit": "Light pressing marks acceptable",
            "is_active": 1
        },
        {
            "defect_code": "C5",
            "defect_name": "Seam/Stitches/Linking Issues",
            "defect_description": "Problems with seams and stitching",
            "inspection_type": "Final Inspection",
            "defect_category": "Workmanship",
            "fault_group": "Construction",
            "defect_type": "Major",
            "inspection_area": "All Seams",
            "acceptable_limit": "0 per garment",
            "is_active": 1
        },
        {
            "defect_code": "C6",
            "defect_name": "Marks/Stains",
            "defect_description": "Visible marks or stains",
            "inspection_type": "Final Inspection",
            "defect_category": "Workmanship",
            "fault_group": "Cleanliness",
            "defect_type": "Major",
            "inspection_area": "Entire Garment",
            "acceptable_limit": "0 visible marks",
            "is_active": 1
        },
        
        # F-Series: Fabric Defects
        {
            "defect_code": "F1",
            "defect_name": "Shrinkage",
            "defect_description": "Fabric shrinkage beyond limits",
            "inspection_type": "Final Inspection",
            "defect_category": "Fabric",
            "fault_group": "Dimensional Stability",
            "defect_type": "Major",
            "inspection_area": "Test Sample",
            "acceptable_limit": "<3% length, <2% width",
            "is_active": 1
        },
        {
            "defect_code": "F2",
            "defect_name": "Color Fastness",
            "defect_description": "Poor color fastness",
            "inspection_type": "Final Inspection",
            "defect_category": "Fabric",
            "fault_group": "Color Quality",
            "defect_type": "Major",
            "inspection_area": "Test Sample",
            "acceptable_limit": "Grade 4 minimum",
            "is_active": 1
        },
        {
            "defect_code": "F5",
            "defect_name": "Color Off Standard",
            "defect_description": "Color does not match standard",
            "inspection_type": "Final Inspection",
            "defect_category": "Fabric",
            "fault_group": "Color Quality",
            "defect_type": "Major",
            "inspection_area": "Entire Garment",
            "acceptable_limit": "Delta E <1.5",
            "is_active": 1
        },
        {
            "defect_code": "F6",
            "defect_name": "Shading Between Garments",
            "defect_description": "Color variation between garments",
            "inspection_type": "Final Inspection",
            "defect_category": "Fabric",
            "fault_group": "Color Consistency",
            "defect_type": "Major",
            "inspection_area": "Comparative Check",
            "acceptable_limit": "No visible difference",
            "is_active": 1
        },
        
        # T-Series: Trim Defects
        {
            "defect_code": "T1",
            "defect_name": "Zipper Defects",
            "defect_description": "Issues with zipper operation",
            "inspection_type": "Final Inspection",
            "defect_category": "Trim",
            "fault_group": "Hardware",
            "defect_type": "Minor",
            "inspection_area": "Zippers",
            "acceptable_limit": "Smooth operation required",
            "is_active": 1
        },
        {
            "defect_code": "T2",
            "defect_name": "Button/Snap Issues",
            "defect_description": "Problems with buttons or snaps",
            "inspection_type": "Final Inspection",
            "defect_category": "Trim",
            "fault_group": "Hardware",
            "defect_type": "Minor",
            "inspection_area": "All Buttons/Snaps",
            "acceptable_limit": "Secure attachment",
            "is_active": 1
        },
        {
            "defect_code": "T7",
            "defect_name": "Label Issues",
            "defect_description": "Problems with labels",
            "inspection_type": "Final Inspection",
            "defect_category": "Trim",
            "fault_group": "Labeling",
            "defect_type": "Minor",
            "inspection_area": "All Labels",
            "acceptable_limit": "Correct placement & info",
            "is_active": 1
        },
        
        # A-Series: Size Defects
        {
            "defect_code": "A1",
            "defect_name": "Off Specification",
            "defect_description": "Measurements outside specification",
            "inspection_type": "Final Inspection",
            "defect_category": "Size",
            "fault_group": "Measurement",
            "defect_type": "Major",
            "inspection_area": "Critical Measurements",
            "acceptable_limit": "Within tolerance range",
            "is_active": 1
        },
        {
            "defect_code": "A2",
            "defect_name": "Mis-Sized",
            "defect_description": "Incorrect size marking",
            "inspection_type": "Final Inspection",
            "defect_category": "Size",
            "fault_group": "Size Marking",
            "defect_type": "Major",
            "inspection_area": "Size Labels",
            "acceptable_limit": "Correct size marking",
            "is_active": 1
        }
    ]

def import_defects(defects_data, defect_type_name):
    """Import defects data into Defect Master"""
    
    print(f"\n=== IMPORTING {defect_type_name.upper()} DEFECTS ===")
    
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
    
    print(f"\n📊 {defect_type_name} Import Summary:")
    print(f"   • Created: {imported_count}")
    print(f"   • Updated: {updated_count}")  
    print(f"   • Errors: {error_count}")
    print(f"   • Total processed: {len(defects_data)}")
    
    return imported_count + updated_count

def import_all_defects():
    """Import all defect types"""
    
    print("🎯 STARTING COMPREHENSIVE DEFECT MASTER DATA IMPORT")
    print("=" * 60)
    
    total_imported = 0
    
    # Import fabric defects
    fabric_defects = get_fabric_defects_data()
    total_imported += import_defects(fabric_defects, "Fabric")
    
    # Import trims defects
    trims_defects = get_trims_defects_data()
    total_imported += import_defects(trims_defects, "Trims")
    
    # Import final inspection defects
    final_defects = get_final_inspection_defects_data()
    total_imported += import_defects(final_defects, "Final Inspection")
    
    # Commit all changes
    frappe.db.commit()
    
    print(f"\n🎉 DEFECT MASTER DATA IMPORT COMPLETED!")
    print(f"📈 Total defects processed: {total_imported}")
    print(f"🏆 Ready for inspection workflows!")
    
    return True

if __name__ == "__main__":
    success = import_all_defects()
    exit(0 if success else 1)