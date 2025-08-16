#!/usr/bin/env python3
"""
Migration script to create Quality Inspector and Quality Manager roles
Runs automatically during bench migrate if roles don't exist
"""

import frappe
from frappe import _

def execute():
    """Main migration function called by after_migrate hooks"""
    try:
        frappe.logger().info("Starting Quality System Migration...")
        create_quality_roles_if_missing()
        create_aql_data_if_missing()
        create_quality_workspace()
        frappe.logger().info("Quality System Migration completed successfully")
    except Exception as e:
        frappe.logger().error(f"Quality System Migration failed: {str(e)}")
        # Don't block migration if this fails
        pass

def create_quality_roles_if_missing():
    """Create Quality Inspector and Quality Manager roles with permissions if they don't exist"""
    
    print("=== QUALITY ROLES MIGRATION ===")
    
    # Define roles to create
    roles_to_create = [
        {
            "role_name": "Quality Inspector",
            "description": "Can perform fabric and trims inspections, view pending inspections",
            "permissions": {
                # Inspection DocTypes - Full access for pending, read for others
                "Fabric Inspection": ["read", "write", "create"],
                "Trims Inspection": ["read", "write", "create"],
                "Fabric Roll Inspection Item": ["read", "write", "create"],
                "Trims Checklist Item": ["read", "write", "create"],
                "Trims Defect Item": ["read", "write", "create"],
                "Fabric Defect Item": ["read", "write", "create"],
                "Fabric Checklist Item": ["read", "write", "create"],
                
                # Master Data - Read only
                "Defect Master": ["read"],
                "AQL Level": ["read"],
                "AQL Standard": ["read"],
                "AQL Table": ["read"],
                "Master Checklist": ["read"],
                
                # GRN and Items - Read only
                "Goods Receipt Note": ["read"],
                "Item": ["read"],
                "Supplier": ["read"],
                
                # Reports and logs
                "Error Log": ["read"],
                
                # System
                "User": ["read"]  # To see own profile
            }
        },
        {
            "role_name": "Quality Manager", 
            "description": "Can review completed inspections, approve/reject, view reports",
            "permissions": {
                # Inspection DocTypes - Full access
                "Fabric Inspection": ["read", "write", "submit", "cancel"],
                "Trims Inspection": ["read", "write", "submit", "cancel"],
                "Fabric Roll Inspection Item": ["read", "write"],
                "Trims Checklist Item": ["read", "write"],
                "Trims Defect Item": ["read", "write"],
                "Fabric Defect Item": ["read", "write"],
                "Fabric Checklist Item": ["read", "write"],
                
                # Master Data - Full access to configure
                "Defect Master": ["read", "write", "create", "delete"],
                "AQL Level": ["read", "write", "create"],
                "AQL Standard": ["read", "write", "create"],
                "AQL Table": ["read", "write", "create"],
                "Master Checklist": ["read", "write", "create"],
                
                # GRN and Items - Read access
                "Goods Receipt Note": ["read"],
                "Item": ["read"],
                "Supplier": ["read"],
                
                # Reports and logs
                "Error Log": ["read"],
                
                # Quality Certificates (if exists)
                "Quality Certificate": ["read", "write", "create"],
                
                # System
                "User": ["read"]
            }
        }
    ]
    
    created_roles = []
    updated_roles = []
    
    for role_config in roles_to_create:
        try:
            role_name = role_config["role_name"]
            
            # Check if role exists
            role_exists = frappe.db.exists("Role", role_name)
            
            if not role_exists:
                # Create new role
                role_doc = frappe.get_doc({
                    "doctype": "Role",
                    "role_name": role_name,
                    "description": role_config["description"],
                    "desk_access": 1,
                    "is_custom": 1
                })
                role_doc.insert(ignore_permissions=True)
                frappe.db.commit()
                print(f"   ✅ Created role: {role_name}")
                created_roles.append(role_name)
            else:
                print(f"   ⚠️  Role already exists: {role_name}")
                updated_roles.append(role_name)
            
            # Create/update permissions for each DocType
            permissions_created = 0
            permissions_updated = 0
            
            for doctype, perms in role_config["permissions"].items():
                if frappe.db.exists("DocType", doctype):
                    perm_result = create_or_update_doctype_permissions(doctype, role_name, perms)
                    if perm_result == "created":
                        permissions_created += 1
                    elif perm_result == "updated":
                        permissions_updated += 1
                else:
                    print(f"     ⚠️  DocType {doctype} does not exist, skipping permissions")
            
            if permissions_created > 0:
                print(f"     ✅ Created {permissions_created} new permissions for {role_name}")
            if permissions_updated > 0:
                print(f"     ✅ Updated {permissions_updated} existing permissions for {role_name}")
                    
        except Exception as e:
            print(f"   ❌ Error processing role {role_name}: {str(e)}")
            frappe.logger().error(f"Error creating/updating role {role_name}: {str(e)}")
    
    frappe.db.commit()
    
    # Summary
    print(f"\\n=== MIGRATION SUMMARY ===")
    if created_roles:
        print(f"✅ Created new roles: {', '.join(created_roles)}")
    if updated_roles:
        print(f"⚠️  Updated existing roles: {', '.join(updated_roles)}")
    
    print(f"✅ Quality roles migration completed successfully")
    
    return {"created": created_roles, "updated": updated_roles}

def create_or_update_doctype_permissions(doctype, role, permissions):
    """Create or update DocPerm records for a doctype and role"""
    
    try:
        # Check if permission already exists
        existing_perm = frappe.db.exists("DocPerm", {
            "parent": doctype,
            "role": role
        })
        
        if existing_perm:
            # Update existing permission
            perm_doc = frappe.get_doc("DocPerm", existing_perm)
            action = "updated"
        else:
            # Create new permission
            perm_doc = frappe.get_doc({
                "doctype": "DocPerm",
                "parent": doctype,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "idx": frappe.db.count("DocPerm", {"parent": doctype}) + 1
            })
            action = "created"
        
        # Set permissions
        perm_doc.read = 1 if "read" in permissions else 0
        perm_doc.write = 1 if "write" in permissions else 0
        perm_doc.create = 1 if "create" in permissions else 0
        perm_doc.delete = 1 if "delete" in permissions else 0
        perm_doc.submit = 1 if "submit" in permissions else 0
        perm_doc.cancel = 1 if "cancel" in permissions else 0
        perm_doc.report = 1 if "report" in permissions else 0
        perm_doc.share = 0
        perm_doc.print = 1 if "read" in permissions else 0
        perm_doc.email = 1 if "read" in permissions else 0
        
        if action == "updated":
            perm_doc.save(ignore_permissions=True)
        else:
            perm_doc.insert(ignore_permissions=True)
        
        return action
        
    except Exception as e:
        print(f"     ❌ Error setting permissions for {doctype} - {role}: {str(e)}")
        frappe.logger().error(f"Error setting permissions for {doctype} - {role}: {str(e)}")
        return "error"

def create_quality_workspace():
    """Create Quality Management workspace with dashboard and inspection links"""
    
    print("=== QUALITY WORKSPACE MIGRATION ===")
    
    try:
        workspace_name = "Quality Dashboard"
        
        # Check if workspace already exists
        if frappe.db.exists("Workspace", workspace_name):
            print(f"   ⚠️  Workspace '{workspace_name}' already exists")
            workspace = frappe.get_doc("Workspace", workspace_name)
        else:
            # Create new workspace
            workspace = frappe.new_doc("Workspace")
            workspace.title = workspace_name
            workspace.icon = "quality-management"
            workspace.indicator_color = "blue"
            workspace.is_default = 0
            workspace.parent_page = ""
            workspace.public = 1
            workspace.sequence_id = 20
            workspace.category = "Modules"
            workspace.content = ""
            workspace.insert(ignore_permissions=True)
            print(f"   ✅ Created workspace '{workspace_name}'")
        
        # Clear existing charts and shortcuts
        workspace.charts = []
        workspace.shortcuts = []
        
        # Add Quality Dashboard page as shortcut
        workspace.append("shortcuts", {
            "label": "Quality Dashboard",
            "url": "/app/quality_dashboard",
            "doc_view": "dashboard",
            "icon": "dashboard",
            "type": "Page",
            "color": "blue"
        })
        
        # Add Fabric Inspection shortcut
        workspace.append("shortcuts", {
            "label": "Fabric Inspections",
            "url": "/app/fabric-inspection",
            "doc_view": "List",
            "icon": "fabric",
            "type": "DocType",
            "color": "green"
        })
        
        # Add Trims Inspection shortcut
        workspace.append("shortcuts", {
            "label": "Trims Inspections", 
            "url": "/app/trims-inspection",
            "doc_view": "List",
            "icon": "trims",
            "type": "DocType",
            "color": "orange"
        })
        
        # Add AQL Level shortcut
        workspace.append("shortcuts", {
            "label": "AQL Levels",
            "url": "/app/aql-level",
            "doc_view": "List", 
            "icon": "aql",
            "type": "DocType",
            "color": "purple"
        })
        
        # Add Goods Receipt Note shortcut
        workspace.append("shortcuts", {
            "label": "Goods Receipt Notes",
            "url": "/app/goods-receipt-note",
            "doc_view": "List",
            "icon": "goods-receipt",
            "type": "DocType", 
            "color": "yellow"
        })
        
        workspace.save(ignore_permissions=True)
        
        # Set workspace permissions for Quality roles
        set_workspace_permissions(workspace)
        
        frappe.db.commit()
        print("   ✅ Quality workspace setup completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create Quality workspace: {str(e)}")
        frappe.log_error(f"Quality workspace creation failed: {str(e)}", "Workspace Creation")
        return False

def set_workspace_permissions(workspace):
    """Set permissions for the Quality workspace"""
    
    try:
        # Remove existing workspace permissions for quality roles
        frappe.db.delete("Workspace Role", {"parent": workspace.name})
        
        # Add Quality roles
        quality_roles = ["Quality Inspector", "Quality Manager", "System Manager", "Administrator"]
        
        for role in quality_roles:
            if frappe.db.exists("Role", role):
                workspace.append("roles", {"role": role})
        
        workspace.save(ignore_permissions=True)
        print(f"     ✅ Set workspace permissions for Quality roles")
        
    except Exception as e:
        print(f"     ❌ Error setting workspace permissions: {str(e)}")

# Test function for manual execution
def test_migration():
    """Test function to run migration manually"""
    try:
        print("=== TESTING QUALITY ROLES MIGRATION ===")
        result = create_quality_roles_if_missing()
        create_quality_workspace()
        print("✅ Migration test completed successfully")
        return result
    except Exception as e:
        print(f"❌ Migration test failed: {str(e)}")
        return None

def create_aql_data_if_missing():
    """Create comprehensive AQL data if missing"""
    
    print("=== AQL DATA MIGRATION ===")
    
    try:
        # Check if AQL data exists
        aql_levels_count = frappe.db.count("AQL Level")
        aql_standards_count = frappe.db.count("AQL Standard") 
        
        print(f"   Current AQL Levels: {aql_levels_count}")
        print(f"   Current AQL Standards: {aql_standards_count}")
        
        # Create AQL Levels if missing
        if aql_levels_count < 3:
            create_aql_levels()
        else:
            print("   ⚠️  AQL Levels already exist")
            
        # Create AQL Standards if missing or incomplete
        if aql_standards_count < 10:
            create_aql_standards()
        else:
            print("   ⚠️  AQL Standards already exist")
            
        # Create AQL Tables if missing
        create_aql_tables_if_missing()
        
        frappe.db.commit()
        print("✅ AQL data migration completed")
        
    except Exception as e:
        print(f"❌ AQL data migration failed: {str(e)}")
        frappe.logger().error(f"AQL data migration failed: {str(e)}")

def create_aql_levels():
    """Create standard AQL inspection levels"""
    
    aql_levels = [
        {"level_name": "Level I", "level_code": "1", "description": "Reduced inspection level"},
        {"level_name": "Level II", "level_code": "2", "description": "Normal inspection level"},
        {"level_name": "Level III", "level_code": "3", "description": "Tightened inspection level"},
        {"level_name": "S-1", "level_code": "S1", "description": "Special level S-1"},
        {"level_name": "S-2", "level_code": "S2", "description": "Special level S-2"},
        {"level_name": "S-3", "level_code": "S3", "description": "Special level S-3"},
        {"level_name": "S-4", "level_code": "S4", "description": "Special level S-4"}
    ]
    
    for level_data in aql_levels:
        if not frappe.db.exists("AQL Level", {"level_code": level_data["level_code"]}):
            aql_level = frappe.get_doc({
                "doctype": "AQL Level",
                "level_name": level_data["level_name"],
                "level_code": level_data["level_code"],
                "description": level_data["description"]
            })
            aql_level.insert(ignore_permissions=True)
            print(f"   ✅ Created AQL Level: {level_data['level_name']}")

def create_aql_standards():
    """Create standard AQL values"""
    
    aql_standards = [
        {"aql_value": "0.010", "description": "AQL 0.010 - Critical defects"},
        {"aql_value": "0.015", "description": "AQL 0.015 - Critical defects"},
        {"aql_value": "0.025", "description": "AQL 0.025 - Critical defects"},
        {"aql_value": "0.040", "description": "AQL 0.040 - Critical defects"},
        {"aql_value": "0.065", "description": "AQL 0.065 - Critical defects"},
        {"aql_value": "0.10", "description": "AQL 0.10 - Major defects"},
        {"aql_value": "0.15", "description": "AQL 0.15 - Major defects"},
        {"aql_value": "0.25", "description": "AQL 0.25 - Major defects"},
        {"aql_value": "0.40", "description": "AQL 0.40 - Major defects"},
        {"aql_value": "0.65", "description": "AQL 0.65 - Major defects"},
        {"aql_value": "1.0", "description": "AQL 1.0 - Major defects"},
        {"aql_value": "1.5", "description": "AQL 1.5 - Major defects"},
        {"aql_value": "2.5", "description": "AQL 2.5 - Major defects"},
        {"aql_value": "4.0", "description": "AQL 4.0 - Minor defects"},
        {"aql_value": "6.5", "description": "AQL 6.5 - Minor defects"},
        {"aql_value": "10", "description": "AQL 10 - Minor defects"},
        {"aql_value": "15", "description": "AQL 15 - Minor defects"},
        {"aql_value": "25", "description": "AQL 25 - Minor defects"}
    ]
    
    for std_data in aql_standards:
        if not frappe.db.exists("AQL Standard", {"aql_value": std_data["aql_value"]}):
            aql_standard = frappe.get_doc({
                "doctype": "AQL Standard",
                "aql_value": std_data["aql_value"],
                "description": std_data["description"]
            })
            aql_standard.insert(ignore_permissions=True)
            print(f"   ✅ Created AQL Standard: {std_data['aql_value']}")

def create_aql_tables_if_missing():
    """Create AQL sampling tables if missing"""
    
    try:
        aql_table_count = frappe.db.count("AQL Table")
        
        if aql_table_count < 10:
            # Create basic AQL table entries for common lot sizes
            aql_table_data = [
                {"lot_size_from": 2, "lot_size_to": 8, "sample_size_code": "A", "sample_size": 2},
                {"lot_size_from": 9, "lot_size_to": 15, "sample_size_code": "A", "sample_size": 2},
                {"lot_size_from": 16, "lot_size_to": 25, "sample_size_code": "B", "sample_size": 3},
                {"lot_size_from": 26, "lot_size_to": 50, "sample_size_code": "C", "sample_size": 5},
                {"lot_size_from": 51, "lot_size_to": 90, "sample_size_code": "D", "sample_size": 8},
                {"lot_size_from": 91, "lot_size_to": 150, "sample_size_code": "E", "sample_size": 13},
                {"lot_size_from": 151, "lot_size_to": 280, "sample_size_code": "F", "sample_size": 20},
                {"lot_size_from": 281, "lot_size_to": 500, "sample_size_code": "G", "sample_size": 32},
                {"lot_size_from": 501, "lot_size_to": 1200, "sample_size_code": "H", "sample_size": 50},
                {"lot_size_from": 1201, "lot_size_to": 3200, "sample_size_code": "J", "sample_size": 80}
            ]
            
            for table_data in aql_table_data:
                if not frappe.db.exists("AQL Table", {
                    "lot_size_from": table_data["lot_size_from"],
                    "lot_size_to": table_data["lot_size_to"]
                }):
                    aql_table = frappe.get_doc({
                        "doctype": "AQL Table",
                        "lot_size_from": table_data["lot_size_from"],
                        "lot_size_to": table_data["lot_size_to"],
                        "sample_size_code": table_data["sample_size_code"],
                        "sample_size": table_data["sample_size"]
                    })
                    aql_table.insert(ignore_permissions=True)
                    
            print(f"   ✅ Created AQL Table entries")
        else:
            print("   ⚠️  AQL Tables already exist")
            
    except Exception as e:
        print(f"   ❌ Error creating AQL tables: {str(e)}")

if __name__ == "__main__":
    frappe.init("trackerx.local")
    frappe.connect()
    frappe.set_user("Administrator")
    test_migration()