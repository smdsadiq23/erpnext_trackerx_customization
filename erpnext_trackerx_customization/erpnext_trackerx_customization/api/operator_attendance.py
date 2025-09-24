
import frappe
from frappe import _
from datetime import datetime, timedelta
import json

@frappe.whitelist()
def get_operator_attendance_grid(date):
    """Get operator attendance data for grid view"""
    try:
        # Get all physical cells
        physical_cells = frappe.get_all("Physical Cell", 
            fields=["name", "cell_name", "start_time", "end_time", "operator_count"])
        
        if not physical_cells:
            return {"success": False, "message": "No physical cells found"}
        
        # Get existing attendance records for the date
        attendance_records = frappe.get_all("Operator Attendance",
            filters={
                "hour": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]
            },
            fields=["physical_cell", "hour", "value"])
        
        # Create attendance data dictionary
        attendance_data = {}
        for record in attendance_records:
            hour_obj = datetime.strptime(str(record.hour), "%Y-%m-%d %H:%M:%S")
            hour = hour_obj.hour
            key = f"{record.physical_cell}-{date}-{hour}"
            attendance_data[key] = record.value
        
        return {
            "success": True,
            "physical_cells": physical_cells,
            "attendance_data": attendance_data
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Operator Attendance Grid Error")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def save_operator_attendance_bulk(records):
    """Save multiple operator attendance records"""
    try:
        records = json.loads(records) if isinstance(records, str) else records
        
        for record in records:
            # Check if record already exists
            existing = frappe.get_all("Operator Attendance",
                filters={
                    "physical_cell": record["physical_cell"],
                    "hour": record["hour"]
                },
                fields=["name"])
            
            if existing:
                # Update existing record
                doc = frappe.get_doc("Operator Attendance", existing[0].name)
                doc.value = record["value"]
                doc.save(ignore_permissions=True)
            else:
                # Create new record
                doc = frappe.new_doc("Operator Attendance")
                doc.physical_cell = record["physical_cell"]
                doc.hour = record["hour"]
                doc.value = record["value"]
                doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
        return {"success": True, "message": f"Saved {len(records)} records successfully"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Operator Attendance Bulk Save Error")
        return {"success": False, "message": str(e)}
