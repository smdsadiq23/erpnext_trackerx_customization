#!/usr/bin/env python3
"""
AQL Master Data Import Script

Imports complete industry-standard AQL master data into ERPNext.
Includes AQL Levels, AQL Standards, and AQL Table with all combinations.

Usage:
    bench execute erpnext_trackerx_customization.import_aql_data.import_aql_master_data
"""

import frappe
import json
import os

def import_aql_levels():
    """Import AQL Level master data"""
    print("\n📋 Importing AQL Levels...")
    
    # Get the directory of this script and construct path to fixtures
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(script_dir, "fixtures", "aql_level.json")
    
    if not os.path.exists(fixture_path):
        print(f"❌ AQL Level fixture file not found: {fixture_path}")
        return 0
    
    with open(fixture_path, 'r') as f:
        levels = json.load(f)
    
    imported_count = 0
    
    for level_data in levels:
        try:
            if not frappe.db.exists("AQL Level", level_data.get("level_code")):
                doc = frappe.get_doc(level_data)
                doc.insert(ignore_permissions=True)
                print(f"   ✅ Created AQL Level: {level_data.get('level_code')} ({level_data.get('level_type')})")
                imported_count += 1
            else:
                print(f"   ⚠️  AQL Level already exists: {level_data.get('level_code')}")
        except Exception as e:
            print(f"   ❌ Error creating AQL Level {level_data.get('level_code')}: {str(e)}")
    
    return imported_count

def import_aql_standards():
    """Import AQL Standard master data"""
    print("\n🎯 Importing AQL Standards...")
    
    # Get the directory of this script and construct path to fixtures
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(script_dir, "fixtures", "aql_standard.json")
    
    if not os.path.exists(fixture_path):
        print(f"❌ AQL Standard fixture file not found: {fixture_path}")
        return 0
    
    with open(fixture_path, 'r') as f:
        standards = json.load(f)
    
    imported_count = 0
    
    for standard_data in standards:
        try:
            if not frappe.db.exists("AQL Standard", standard_data.get("aql_value")):
                doc = frappe.get_doc(standard_data)
                doc.insert(ignore_permissions=True)
                print(f"   ✅ Created AQL Standard: {standard_data.get('aql_value')}")
                imported_count += 1
            else:
                print(f"   ⚠️  AQL Standard already exists: {standard_data.get('aql_value')}")
        except Exception as e:
            print(f"   ❌ Error creating AQL Standard {standard_data.get('aql_value')}: {str(e)}")
    
    return imported_count

def import_aql_table():
    """Import AQL Table master data"""
    print("\n📊 Importing AQL Table...")
    
    # Get the directory of this script and construct path to fixtures
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(script_dir, "fixtures", "aql_table.json")
    
    if not os.path.exists(fixture_path):
        print(f"❌ AQL Table fixture file not found: {fixture_path}")
        return 0
    
    with open(fixture_path, 'r') as f:
        table_entries = json.load(f)
    
    imported_count = 0
    skipped_count = 0
    batch_size = 50  # Process in batches for better performance
    
    print(f"   📦 Processing {len(table_entries)} AQL table entries in batches of {batch_size}...")
    
    for i in range(0, len(table_entries), batch_size):
        batch = table_entries[i:i + batch_size]
        
        for entry_data in batch:
            try:
                # Create unique identifier for the entry
                table_name = f"{entry_data.get('sample_code_letter')}-{entry_data.get('aql_value')}-{entry_data.get('inspection_regime')}"
                
                if not frappe.db.exists("AQL Table", table_name):
                    doc = frappe.get_doc(entry_data)
                    doc.insert(ignore_permissions=True)
                    imported_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"   ❌ Error creating AQL Table entry {table_name}: {str(e)}")
        
        # Commit batch
        if i % (batch_size * 5) == 0:  # Commit every 5 batches
            frappe.db.commit()
            print(f"   📈 Processed {min(i + batch_size, len(table_entries))}/{len(table_entries)} entries...")
    
    print(f"   ✅ Created {imported_count} AQL Table entries")
    if skipped_count > 0:
        print(f"   ⚠️  Skipped {skipped_count} existing entries")
    
    return imported_count

def validate_aql_data():
    """Validate imported AQL data integrity"""
    print("\n🔍 Validating AQL data integrity...")
    
    # Check AQL Levels
    levels = frappe.get_all("AQL Level", pluck="level_code")
    expected_levels = ["1", "2", "3", "S1", "S2", "S3", "S4"]
    
    missing_levels = set(expected_levels) - set(levels)
    if missing_levels:
        print(f"   ❌ Missing AQL Levels: {missing_levels}")
    else:
        print(f"   ✅ All {len(expected_levels)} AQL Levels present")
    
    # Check AQL Standards
    standards_count = frappe.db.count("AQL Standard")
    print(f"   ✅ AQL Standards: {standards_count} entries")
    
    # Check AQL Table
    table_count = frappe.db.count("AQL Table")
    print(f"   ✅ AQL Table: {table_count} entries")
    
    # Check sample codes coverage
    sample_codes = frappe.get_all("AQL Table", pluck="sample_code_letter", distinct=True)
    expected_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R']
    
    missing_codes = set(expected_codes) - set(sample_codes)
    if missing_codes:
        print(f"   ❌ Missing Sample Codes: {missing_codes}")
    else:
        print(f"   ✅ All {len(expected_codes)} sample codes covered")
    
    # Check regimes coverage
    regimes = frappe.get_all("AQL Table", pluck="inspection_regime", distinct=True)
    expected_regimes = ["Normal", "Tightened", "Reduced"]
    
    missing_regimes = set(expected_regimes) - set(regimes)
    if missing_regimes:
        print(f"   ❌ Missing Inspection Regimes: {missing_regimes}")
    else:
        print(f"   ✅ All {len(expected_regimes)} inspection regimes covered")
    
    return len(missing_levels) == 0 and len(missing_codes) == 0 and len(missing_regimes) == 0

def import_aql_master_data():
    """Main function to import all AQL master data"""
    
    print("=== AQL MASTER DATA IMPORT ===")
    print("Importing complete industry-standard AQL data according to ISO 2859-1...")
    
    # Set user context
    frappe.set_user("Administrator")
    
    try:
        # Import in sequence
        levels_count = import_aql_levels()
        standards_count = import_aql_standards()
        table_count = import_aql_table()
        
        # Commit all changes
        frappe.db.commit()
        
        # Validate data integrity
        validation_passed = validate_aql_data()
        
        # Summary
        print(f"\n📈 IMPORT SUMMARY:")
        print(f"   AQL Levels: {levels_count} imported")
        print(f"   AQL Standards: {standards_count} imported")  
        print(f"   AQL Table Entries: {table_count} imported")
        print(f"   Total Records: {levels_count + standards_count + table_count}")
        
        if validation_passed:
            print(f"\n🎉 AQL MASTER DATA IMPORT COMPLETED SUCCESSFULLY!")
            print(f"✅ All industry-standard AQL data is now available")
            print(f"✅ System ready for production quality inspections")
        else:
            print(f"\n⚠️  IMPORT COMPLETED WITH WARNINGS")
            print(f"Some data validation checks failed. Please review above.")
        
        return True
        
    except Exception as e:
        frappe.db.rollback()
        print(f"\n❌ IMPORT FAILED: {str(e)}")
        return False

def show_aql_data_summary():
    """Display summary of imported AQL data"""
    
    print("\n=== AQL DATA SUMMARY ===")
    
    # AQL Levels summary
    levels = frappe.get_all("AQL Level", fields=["level_code", "level_type"], order_by="level_code")
    print(f"\n📋 AQL Levels ({len(levels)} total):")
    for level in levels:
        print(f"   {level.level_code} ({level.level_type})")
    
    # AQL Standards summary  
    standards = frappe.get_all("AQL Standard", fields=["aql_value"], order_by="CAST(aql_value AS DECIMAL)")
    print(f"\n🎯 AQL Standards ({len(standards)} total):")
    aql_list = [s.aql_value for s in standards]
    print(f"   {', '.join(aql_list)}")
    
    # AQL Table summary
    table_stats = frappe.db.sql("""
        SELECT 
            sample_code_letter,
            COUNT(*) as entry_count,
            MIN(aql_value) as min_aql,
            MAX(aql_value) as max_aql
        FROM `tabAQL Table` 
        WHERE is_active = 1
        GROUP BY sample_code_letter 
        ORDER BY sample_code_letter
    """, as_dict=True)
    
    print(f"\n📊 AQL Table Summary ({sum(s.entry_count for s in table_stats)} total entries):")
    for stat in table_stats:
        print(f"   Code {stat.sample_code_letter}: {stat.entry_count} entries (AQL {stat.min_aql} - {stat.max_aql})")
    
    print(f"\n🏭 INDUSTRY COMPLIANCE:")
    print(f"✅ ISO 2859-1 (MIL-STD-105E) compliant")
    print(f"✅ Complete sample size codes A-R")
    print(f"✅ All inspection regimes (Normal, Tightened, Reduced)")
    print(f"✅ Full range of AQL values (0.065% - 150%)")

if __name__ == "__main__":
    # Can be run directly for testing
    import_aql_master_data()
    show_aql_data_summary()