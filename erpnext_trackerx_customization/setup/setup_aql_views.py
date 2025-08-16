#!/usr/bin/env python3
"""
Setup Default AQL Table Views

Creates default AQL table views for different inspection regimes.
"""

import frappe

def create_default_aql_views():
    """Create default AQL table views"""
    
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    
    print("=== CREATING DEFAULT AQL TABLE VIEWS ===")
    
    # Define default views
    default_views = [
        {
            "view_name": "Normal Inspection - Standard",
            "description": "Standard AQL table for normal inspection regime with common AQL values",
            "inspection_regime": "Normal",
            "inspection_levels": 1,
            "aql_values_selection": "Common Values Only",
            "show_lot_size_ranges": 1,
            "show_sample_sizes": 1,
            "show_acceptance_rejection": 1,
            "table_style": "Standard",
            "is_default_view": 1,
            "is_public": 1
        },
        {
            "view_name": "Tightened Inspection - Standard", 
            "description": "AQL table for tightened inspection regime with common AQL values",
            "inspection_regime": "Tightened",
            "inspection_levels": 1,
            "aql_values_selection": "Common Values Only",
            "show_lot_size_ranges": 1,
            "show_sample_sizes": 1,
            "show_acceptance_rejection": 1,
            "table_style": "Standard",
            "is_default_view": 0,
            "is_public": 1
        },
        {
            "view_name": "Reduced Inspection - Standard",
            "description": "AQL table for reduced inspection regime with common AQL values", 
            "inspection_regime": "Reduced",
            "inspection_levels": 1,
            "aql_values_selection": "Common Values Only",
            "show_lot_size_ranges": 1,
            "show_sample_sizes": 1,
            "show_acceptance_rejection": 1,
            "table_style": "Standard",
            "is_default_view": 0,
            "is_public": 1
        },
        {
            "view_name": "Complete AQL Chart - All Regimes",
            "description": "Complete AQL chart showing all inspection regimes and AQL values",
            "inspection_regime": "All",
            "inspection_levels": 1,
            "aql_values_selection": "All Values",
            "show_lot_size_ranges": 1,
            "show_sample_sizes": 1,
            "show_acceptance_rejection": 1,
            "table_style": "Detailed",
            "is_default_view": 0,
            "is_public": 1
        },
        {
            "view_name": "Compact AQL Chart - Level 2 Only",
            "description": "Compact view showing only General Inspection Level 2 (most common)",
            "inspection_regime": "Normal", 
            "inspection_levels": 0,  # Will default to Level 2 only
            "aql_values_selection": "Common Values Only",
            "show_lot_size_ranges": 1,
            "show_sample_sizes": 1,
            "show_acceptance_rejection": 1,
            "table_style": "Compact",
            "is_default_view": 0,
            "is_public": 1
        }
    ]
    
    created_count = 0
    
    for view_data in default_views:
        try:
            # Check if view already exists
            if not frappe.db.exists("AQL Table View", view_data["view_name"]):
                doc = frappe.get_doc({
                    "doctype": "AQL Table View",
                    **view_data
                })
                doc.insert(ignore_permissions=True)
                print(f"   ✅ Created view: {view_data['view_name']}")
                created_count += 1
            else:
                print(f"   ⚠️  View already exists: {view_data['view_name']}")
                
        except Exception as e:
            print(f"   ❌ Error creating view {view_data['view_name']}: {str(e)}")
    
    frappe.db.commit()
    
    print(f"\n✅ Created {created_count} AQL table views")
    print(f"📊 Total views available: {frappe.db.count('AQL Table View')}")
    
    # Display summary
    views = frappe.get_all("AQL Table View", 
                         fields=["view_name", "inspection_regime", "table_style", "is_default_view"],
                         order_by="is_default_view DESC, view_name")
    
    print(f"\n=== AQL TABLE VIEWS SUMMARY ===")
    print(f"{'View Name':<35} {'Regime':<12} {'Style':<10} {'Default'}")
    print("-" * 70)
    
    for view in views:
        default_mark = "✓" if view.is_default_view else " "
        print(f"{view.view_name:<35} {view.inspection_regime:<12} {view.table_style:<10} {default_mark}")
    
    return created_count

def test_aql_table_views():
    """Test the AQL table views functionality"""
    
    print(f"\n=== TESTING AQL TABLE VIEWS ===")
    
    try:
        # Get the default view
        default_view = frappe.get_doc("AQL Table View", {"is_default_view": 1})
        print(f"✅ Default view found: {default_view.view_name}")
        
        # Test generating AQL data
        aql_data = default_view.get_aql_data()
        print(f"✅ AQL data generated successfully")
        print(f"   - AQL Values: {len(aql_data['aql_values'])} values")
        print(f"   - Inspection Levels: {len(aql_data['levels'])} levels")
        print(f"   - Table Data: {len(aql_data['table_data'])} level datasets")
        
        # Show sample data structure
        if aql_data['table_data']:
            first_level = list(aql_data['table_data'].keys())[0]
            level_data = aql_data['table_data'][first_level]
            print(f"   - Sample level ({first_level}): {len(level_data)} lot size ranges")
            
            if level_data:
                first_range = list(level_data.keys())[0]
                range_data = level_data[first_range]
                print(f"   - Sample range ({first_range}): Code {range_data['sample_code']}, Size {range_data['sample_size']}")
        
        print(f"✅ AQL table views are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing AQL table views: {str(e)}")
        return False

def main():
    """Main function"""
    try:
        created_count = create_default_aql_views()
        test_success = test_aql_table_views()
        
        print(f"\n=== SETUP COMPLETE ===")
        print(f"✅ {created_count} new views created")
        print(f"✅ Web interface ready at:")
        print(f"   - /aql_grid (AQL Grid - Editable Table)")
        
        if test_success:
            print(f"✅ All tests passed - system ready for use!")
        else:
            print(f"⚠️  Some tests failed - please check configuration")
            
        return test_success
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)