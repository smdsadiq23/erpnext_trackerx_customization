import frappe
import os
import json
from frappe import _

def import_aql_fixtures():
    """Import AQL fixtures if the tables are empty"""
    try:
        # Check if AQL data already exists
        aql_level_count = frappe.db.count("AQL Level")
        aql_standard_count = frappe.db.count("AQL Standard") 
        aql_table_count = frappe.db.count("AQL Table")
        
        # Only import if tables are empty
        if aql_level_count == 0 or aql_standard_count == 0 or aql_table_count == 0:
            print("Importing AQL fixtures...")
            
            # Get the app path
            app_path = frappe.get_app_path("erpnext_trackerx_customization")
            
            # Define fixture files
            fixtures = [
                "aql_level.json",
                "aql_standard.json", 
                "aql_table.json"
            ]
            
            for fixture_file in fixtures:
                fixture_path = os.path.join(app_path, "fixtures", fixture_file)
                
                if os.path.exists(fixture_path):
                    print(f"Importing {fixture_file}...")
                    
                    # Read and import the fixture
                    with open(fixture_path, 'r') as f:
                        data = json.load(f)
                    
                    # Import each document
                    for doc_data in data:
                        try:
                            # Check if document already exists
                            if not frappe.db.exists(doc_data['doctype'], doc_data['name']):
                                doc = frappe.get_doc(doc_data)
                                doc.insert(ignore_permissions=True)
                                print(f"Created {doc_data['doctype']}: {doc_data['name']}")
                            else:
                                print(f"{doc_data['doctype']} {doc_data['name']} already exists, skipping...")
                        except Exception as e:
                            print(f"Error importing {doc_data['doctype']} {doc_data['name']}: {str(e)}")
                            continue
                else:
                    print(f"Fixture file {fixture_path} not found")
            
            frappe.db.commit()
            print("AQL fixtures import completed successfully!")
        else:
            print("AQL data already exists. Skipping fixture import.")
            
    except Exception as e:
        print(f"Error during AQL fixtures import: {str(e)}")
        frappe.log_error(f"AQL fixtures import error: {str(e)}")

def execute():
    """Wrapper function for after_migrate hook"""
    import_aql_fixtures()