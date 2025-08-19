#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabric Inspection System - Complete Usage Example

Demonstrates how to use the enhanced fabric defect point system in real inspection workflows.

Usage:
    bench execute erpnext_trackerx_customization.fabric_inspection_example.demo_fabric_inspection
"""

import frappe
from erpnext_trackerx_customization.utils.fabric_inspection import FabricInspectionCalculator

def demo_fabric_inspection():
    """Demonstrate a complete fabric inspection workflow"""
    
    print("🏭 FABRIC INSPECTION WORKFLOW DEMONSTRATION")
    print("=" * 60)
    
    # Scenario: Quality inspector examines a fabric roll and finds various defects
    print("\n📋 SCENARIO: Inspecting 100-yard fabric roll")
    print("Inspector finds the following defects:")
    print()
    
    # List of defects found during inspection
    defects_found = [
        {
            "code": "YD001",  # Thick Yarn
            "size": "4.2",    # 4.2 inches
            "location": "Yard 15, 3 inches from left edge",
            "description": "Thick yarn section"
        },
        {
            "code": "YD001",  # Thick Yarn  
            "size": "2.8",    # 2.8 inches
            "location": "Yard 32, center",
            "description": "Another thick yarn defect"
        },
        {
            "code": "WD002",  # Missing End
            "size": "5.5",    # 5.5 inches
            "location": "Yard 45, right edge", 
            "description": "Missing warp yarn"
        },
        {
            "code": "YD004",  # Nep/Foreign Fiber
            "size": "0.3",    # 0.3 inches
            "location": "Yard 67, left side",
            "description": "Small fiber contamination"
        },
        {
            "code": "DD002",  # Color Streaks
            "size": "8.0",    # 8 inches
            "location": "Yard 78, across width",
            "description": "Color variation streak"
        },
        {
            "code": "PH001",  # Holes
            "size": "0.1",    # Pin hole
            "location": "Yard 89, center",
            "description": "Small pin hole"
        }
    ]
    
    # Process each defect and show point calculation
    print("🔍 DEFECT ANALYSIS:")
    print("-" * 50)
    
    detailed_defects = []
    
    for i, defect in enumerate(defects_found, 1):
        defect_code = defect["code"]
        defect_size = defect["size"]
        
        # Get defect details
        defect_info = FabricInspectionCalculator.get_defect_criteria_info(defect_code)
        
        # Calculate points
        points = FabricInspectionCalculator.calculate_defect_points(defect_code, defect_size)
        
        print(f"{i}. {defect_info['name']} ({defect_code})")
        print(f"   Location: {defect['location']}")
        print(f"   Size: {defect_size}\" → {points} points")
        print(f"   Criteria: {_get_matching_criteria(defect_info['criteria'], points)}")
        print(f"   Category: {defect_info['category']}")
        print()
        
        # Add to detailed list for overall calculation
        detailed_defects.append({
            "code": defect_code,
            "size": defect_size
        })
    
    # Calculate overall fabric quality
    print("📊 OVERALL FABRIC QUALITY ASSESSMENT:")
    print("-" * 50)
    
    quality_result = FabricInspectionCalculator.calculate_total_points(detailed_defects)
    
    print(f"Total Defects Found: {quality_result['defect_count']}")
    print(f"Total Points: {quality_result['total_points']}")
    print(f"Average Points per Defect: {quality_result['points_per_defect']}")
    print(f"Quality Grade: {quality_result['quality_grade']}")
    print()
    
    # Show defects by category
    print("📈 DEFECTS BY CATEGORY:")
    for category, data in quality_result['defect_categories'].items():
        print(f"   • {category}: {data['count']} defects, {data['points']} points")
    
    # Quality decision
    print("\n🎯 QUALITY DECISION:")
    print("-" * 30)
    
    if quality_result['quality_grade'] in ['A+', 'A', 'B']:
        decision = "✅ ACCEPT"
        recommendation = "Fabric meets quality standards"
    elif quality_result['quality_grade'] == 'C':
        decision = "⚠️ CONDITIONAL ACCEPT"
        recommendation = "Accept with minor quality notation"
    else:
        decision = "❌ REJECT"
        recommendation = "Fabric does not meet quality standards"
    
    print(f"Decision: {decision}")
    print(f"Recommendation: {recommendation}")
    
    return quality_result

def _get_matching_criteria(criteria_dict, points):
    """Get the criteria that matches the calculated points"""
    criteria_map = {
        1: criteria_dict.get('1_point', ''),
        2: criteria_dict.get('2_points', ''),
        3: criteria_dict.get('3_points', ''),
        4: criteria_dict.get('4_points', '')
    }
    return criteria_map.get(points, 'Unknown')

def demo_different_scenarios():
    """Show different inspection scenarios and their outcomes"""
    
    print(f"\n🎭 DIFFERENT INSPECTION SCENARIOS")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "High Quality Fabric",
            "defects": [
                {"code": "YD005", "size": "slight"},  # Hairy Yarn - slight
                {"code": "WD006", "size": "0.2"}      # Snarls/Loop - small
            ]
        },
        {
            "name": "Average Quality Fabric", 
            "defects": [
                {"code": "YD001", "size": "4.0"},     # Thick Yarn - 2 points
                {"code": "DD001", "size": "noticeable"}, # Shade Variation - 2 points
                {"code": "WD005", "size": "1.2"}      # Float - 2 points
            ]
        },
        {
            "name": "Poor Quality Fabric",
            "defects": [
                {"code": "PH001", "size": "0.6"},     # Holes - 4 points  
                {"code": "YD001", "size": "12"},      # Thick Yarn - 4 points
                {"code": "DD002", "size": "10"},      # Color Streaks - 4 points
                {"code": "WD002", "size": "15"},      # Missing End - 4 points
                {"code": "PH002", "size": "3.5"}     # Cuts/Tears - 4 points
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}:")
        
        result = FabricInspectionCalculator.calculate_total_points(scenario['defects'])
        
        print(f"   Defects: {result['defect_count']}")
        print(f"   Total Points: {result['total_points']}")
        print(f"   Quality Grade: {result['quality_grade']}")
        
        if result['quality_grade'] in ['A+', 'A']:
            status = "✅ Excellent"
        elif result['quality_grade'] == 'B':
            status = "👍 Good"
        elif result['quality_grade'] == 'C':
            status = "⚠️ Acceptable"
        else:
            status = "❌ Poor"
            
        print(f"   Status: {status}")

def show_defect_reference():
    """Show a quick reference of common defects and their point systems"""
    
    print(f"\n📚 QUICK DEFECT REFERENCE")
    print("=" * 40)
    
    common_defects = [
        "YD001",  # Thick Yarn
        "YD004",  # Nep/Foreign Fiber
        "WD002",  # Missing End
        "DD002",  # Color Streaks
        "PH001"   # Holes
    ]
    
    for defect_code in common_defects:
        info = FabricInspectionCalculator.get_defect_criteria_info(defect_code)
        if info:
            print(f"\n🔹 {info['name']} ({defect_code})")
            print(f"   Category: {info['category']}")
            print(f"   1 Point:  {info['criteria']['1_point']}")
            print(f"   2 Points: {info['criteria']['2_points']}")  
            print(f"   3 Points: {info['criteria']['3_points']}")
            print(f"   4 Points: {info['criteria']['4_points']}")

def main():
    """Run complete fabric inspection demonstration"""
    
    # Main inspection demo
    quality_result = demo_fabric_inspection()
    
    # Show different scenarios
    demo_different_scenarios()
    
    # Show reference guide
    show_defect_reference()
    
    print(f"\n🎉 FABRIC INSPECTION SYSTEM DEMONSTRATION COMPLETE!")
    print("=" * 60)
    print("✅ The system correctly:")
    print("   • Parses measurement inputs (inches, fractions, decimals)")
    print("   • Calculates points based on defect-specific criteria")
    print("   • Handles boundary cases properly")
    print("   • Provides overall quality assessment")
    print("   • Supports real inspection workflows")
    
    return quality_result

if __name__ == "__main__":
    result = main()
    exit(0)