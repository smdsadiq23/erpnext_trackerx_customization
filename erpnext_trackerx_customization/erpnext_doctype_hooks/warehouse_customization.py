from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

def execute():
    """Add custom fields to Warehouse doctype with precise positioning"""
    # Fields to insert after is_rejected_warehouse
    post_rejected_fields = [
        {
            "fieldname": "bin_location",
            "label": "Bin Location",
            "fieldtype": "Data",
            "insert_after": "is_rejected_warehouse",
            "description": "Specific bin location identifier"
        },
        {
            "fieldname": "zone_type",
            "label": "Zone Type",
            "fieldtype": "Select",
            "options": "\nCotton\nSynthetic\nBlended\nSpecialty\nThreads\nZippers\nLabels\nElastic\nButtons\nHardware\nPackaging\nIncoming\nHold\nApproved\nRejected\nSewing\nCutting\nPressing\nMaintenance",
            "insert_after": "bin_location"
        },
        {
            "fieldname": "rack_number",
            "label": "Rack Number",
            "fieldtype": "Int",
            "insert_after": "zone_type"
        },
        {
            "fieldname": "level_number",
            "label": "Level Number",
            "fieldtype": "Int",
            "insert_after": "rack_number"
        },
        {
            "fieldname": "bin_number",
            "label": "Bin Number",
            "fieldtype": "Int",
            "insert_after": "level_number"
        }
    ]

    # Fields to insert after company
    post_company_fields = [
         {
            "fieldname": "capacity",
            "label": "Capacity",
            "fieldtype": "Float",
            "insert_after": "company"
        },
        {
            "fieldname": "capacity_unit",
            "label": "Capacity Unit",
            "fieldtype": "Data",
            "default": "Meter",
            "insert_after": "capacity"
        },
        {
            "fieldname": "temperature_min",
            "label": "Min Temperature (°C)",
            "fieldtype": "Float",
            "insert_after": "capacity_unit"
        },
        {
            "fieldname": "temperature_max",
            "label": "Max Temperature (°C)",
            "fieldtype": "Float",
            "insert_after": "temperature_min"
        },
        {
            "fieldname": "humidity_min",
            "label": "Min Humidity (%)",
            "fieldtype": "Float",
            "insert_after": "temperature_max"
        },
        {
            "fieldname": "humidity_max",
            "label": "Max Humidity (%)",
            "fieldtype": "Float",
            "insert_after": "humidity_min"
        },
        {
            "fieldname": "supports_shade_segregation",
            "label": "Supports Shade Segregation",
            "fieldtype": "Check",
            "insert_after": "humidity_max",
            "description": "Enable for warehouses requiring shade separation"
        }
    ]

    # First create fields after is_rejected_warehouse
    for field in post_rejected_fields:
        if not frappe.db.exists("Custom Field", f"Warehouse-{field['fieldname']}"):
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Warehouse",
                **field
            }).insert()

    # Then create fields after company
    for field in post_company_fields:
        if not frappe.db.exists("Custom Field", f"Warehouse-{field['fieldname']}"):
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Warehouse",
                **field
            }).insert()