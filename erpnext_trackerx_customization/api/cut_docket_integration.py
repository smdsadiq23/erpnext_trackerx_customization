# -*- coding: utf-8 -*-
"""
Cut Docket Integration Module

Provides hooks and integration functions for Cut Docket workflow
to auto-create Cutting Lay Inspection when required.
"""

from __future__ import unicode_literals
import frappe
from frappe import _


def on_cut_docket_submit(doc, method=None):
    """
    Hook function to be called when Cut Docket is submitted.
    
    Add this to hooks.py in cuttingx app:
    
    doc_events = {
        "Cut Docket": {
            "on_submit": "erpnext_trackerx_customization.api.cut_docket_integration.on_cut_docket_submit"
        }
    }
    """
    
    if doc.lay_cut_inspection == 1:
        create_cutting_lay_inspection(doc)


def create_cutting_lay_inspection(cut_docket_doc):
    """Create Cutting Lay Inspection from Cut Docket"""
    try:
        # Check if inspection already exists
        existing = frappe.db.exists("Cutting Lay Inspection", {
            "cut_docket_reference": cut_docket_doc.name
        })
        
        if existing:
            frappe.msgprint(
                _("Cutting Lay Inspection {0} already exists for this Cut Docket").format(existing),
                alert=True
            )
            return existing
        
        # Create new Cutting Lay Inspection
        inspection = frappe.new_doc("Cutting Lay Inspection")
        inspection.cut_docket_reference = cut_docket_doc.name
        
        # The controller will auto-populate all other fields
        inspection.insert(ignore_permissions=True)
        
        frappe.msgprint(
            _("Cutting Lay Inspection {0} created successfully").format(inspection.name),
            alert=True
        )
        
        return inspection.name
        
    except Exception as e:
        frappe.log_error(f"Error creating Cutting Lay Inspection: {str(e)}")
        frappe.throw(_("Failed to create Cutting Lay Inspection: {0}").format(str(e)))


@frappe.whitelist()
def manual_create_inspection(cut_docket_name):
    """Manually create inspection for Cut Docket"""
    try:
        cut_docket = frappe.get_doc("Cut Docket", cut_docket_name)
        
        if not cut_docket.lay_cut_inspection:
            return {
                "success": False,
                "message": "Cut Docket does not require lay cut inspection"
            }
        
        inspection_name = create_cutting_lay_inspection(cut_docket)
        
        return {
            "success": True,
            "message": "Inspection created successfully",
            "inspection_name": inspection_name
        }
        
    except Exception as e:
        return {"success": False, "message": str(e)}


def on_cut_docket_cancel(doc, method=None):
    """
    Hook function when Cut Docket is cancelled.
    Cancel associated Cutting Lay Inspection if exists.
    """
    try:
        # Find associated inspection
        inspections = frappe.get_all(
            "Cutting Lay Inspection",
            filters={
                "cut_docket_reference": doc.name,
                "docstatus": 1
            }
        )
        
        for inspection in inspections:
            inspection_doc = frappe.get_doc("Cutting Lay Inspection", inspection.name)
            inspection_doc.cancel()
            
        if inspections:
            frappe.msgprint(
                _("{0} associated Cutting Lay Inspection(s) cancelled").format(len(inspections)),
                alert=True
            )
            
    except Exception as e:
        frappe.log_error(f"Error cancelling associated inspections: {str(e)}")


@frappe.whitelist()
def get_cut_docket_inspection_status(cut_docket_name):
    """Get inspection status for a Cut Docket"""
    try:
        inspection = frappe.db.get_value(
            "Cutting Lay Inspection",
            {"cut_docket_reference": cut_docket_name},
            ["name", "inspection_status", "final_status", "progress_percentage"],
            as_dict=True
        )
        
        if inspection:
            return {
                "has_inspection": True,
                "inspection_name": inspection.name,
                "status": inspection.inspection_status,
                "final_status": inspection.final_status,
                "progress": inspection.progress_percentage
            }
        else:
            return {"has_inspection": False}
            
    except Exception as e:
        frappe.log_error(f"Error getting inspection status: {str(e)}")
        return {"error": str(e)}


# Utility functions for Cut Docket enhancement
@frappe.whitelist()
def add_inspection_button_to_cut_docket():
    """Add custom button to Cut Docket for creating inspection"""
    
    client_script = """
    frappe.ui.form.on('Cut Docket', {
        refresh: function(frm) {
            // Add inspection button if lay_cut_inspection is checked
            if (frm.doc.lay_cut_inspection && frm.doc.docstatus === 1) {
                // Check if inspection exists
                frappe.call({
                    method: 'erpnext_trackerx_customization.api.cut_docket_integration.get_cut_docket_inspection_status',
                    args: {
                        cut_docket_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.has_inspection) {
                            // Show View Inspection button
                            frm.add_custom_button(__('View Lay Inspection'), function() {
                                frappe.set_route('Form', 'Cutting Lay Inspection', r.message.inspection_name);
                            });
                            
                            // Add status indicator
                            frm.dashboard.add_indicator(__('Inspection Status: ') + r.message.status, 
                                r.message.status === 'Completed' ? 'green' : 'orange');
                        } else {
                            // Show Create Inspection button
                            frm.add_custom_button(__('Create Lay Inspection'), function() {
                                frappe.call({
                                    method: 'erpnext_trackerx_customization.api.cut_docket_integration.manual_create_inspection',
                                    args: {
                                        cut_docket_name: frm.doc.name
                                    },
                                    callback: function(r) {
                                        if (r.message && r.message.success) {
                                            frappe.msgprint(r.message.message);
                                            frm.refresh();
                                        } else {
                                            frappe.msgprint(r.message ? r.message.message : 'Error creating inspection');
                                        }
                                    }
                                });
                            });
                        }
                    }
                });
            }
        }
    });
    """
    
    # Create client script
    if not frappe.db.exists("Client Script", {"name": "Cut Docket - Lay Inspection Integration"}):
        client_script_doc = frappe.new_doc("Client Script")
        client_script_doc.name = "Cut Docket - Lay Inspection Integration"
        client_script_doc.dt = "Cut Docket"
        client_script_doc.view = "Form"
        client_script_doc.script = client_script
        client_script_doc.enabled = 1
        client_script_doc.insert(ignore_permissions=True)
        
        return {"success": True, "message": "Client script added successfully"}
    else:
        return {"success": False, "message": "Client script already exists"}


# Hook functions for data synchronization
def sync_inspection_with_cut_docket(inspection_doc, method):
    """Sync inspection status back to Cut Docket"""
    if inspection_doc.cut_docket_reference and method in ["on_update", "on_submit"]:
        try:
            cut_docket = frappe.get_doc("Cut Docket", inspection_doc.cut_docket_reference)
            
            # Update Cut Docket based on inspection status
            if inspection_doc.final_status == "Approved - Proceed to Cutting":
                new_status = "Inspection Approved"
            elif inspection_doc.final_status in ["Rejected - Rework Required", "On Hold - Further Review"]:
                new_status = "Inspection Failed"
            elif inspection_doc.final_status == "Conditional Approval":
                new_status = "Inspection Conditional"
            else:
                new_status = "Inspection Pending"
            
            # Only update if status actually changed
            if cut_docket.status != new_status:
                frappe.db.set_value("Cut Docket", cut_docket.name, "status", new_status)
                
        except Exception as e:
            frappe.log_error(f"Error syncing inspection with Cut Docket: {str(e)}")


# Installation and setup functions
@frappe.whitelist()
def setup_cut_docket_integration():
    """Setup integration between Cut Docket and Cutting Lay Inspection"""
    
    try:
        # Add client script for Cut Docket form
        add_inspection_button_to_cut_docket()
        
        # Create property setter to add inspection status field to Cut Docket list view
        if not frappe.db.exists("Property Setter", {
            "doctype_or_field": "DocType",
            "doc_type": "Cut Docket",
            "property": "title_field",
            "value": "name"
        }):
            property_setter = frappe.new_doc("Property Setter")
            property_setter.doctype_or_field = "DocType"
            property_setter.doc_type = "Cut Docket"  
            property_setter.property = "title_field"
            property_setter.value = "name"
            property_setter.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "message": "Cut Docket integration setup completed successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error setting up Cut Docket integration: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_integration_instructions():
    """Get instructions for manual integration setup"""
    
    instructions = """
    # Cut Docket Integration Instructions
    
    To complete the integration, add the following to cuttingx app's hooks.py:
    
    ## 1. Add doc_events in hooks.py:
    ```python
    doc_events = {
        "Cut Docket": {
            "on_submit": "erpnext_trackerx_customization.api.cut_docket_integration.on_cut_docket_submit",
            "on_cancel": "erpnext_trackerx_customization.api.cut_docket_integration.on_cut_docket_cancel"
        }
    }
    ```
    
    ## 2. Add to fixtures in hooks.py (if needed):
    ```python
    fixtures = [
        {
            "dt": "Client Script",
            "filters": [
                ["name", "in", ["Cut Docket - Lay Inspection Integration"]]
            ]
        }
    ]
    ```
    
    ## 3. Run bench migrate to apply changes:
    ```bash
    bench migrate
    ```
    
    ## 4. Restart bench:
    ```bash
    bench restart
    ```
    """
    
    return {"instructions": instructions}