import frappe
import csv
import os

@frappe.whitelist()
def get_measurement_data(custom_size_filter, custom_size_standard):
    """
    Fetches measurement data from a CSV file based on user selections.
    """
    file_name = f"{custom_size_filter}_{custom_size_standard}.csv"
    file_path = frappe.get_app_path(
        "erpnext_trackerx_customization",
        "data",
        file_name
    )

    if not os.path.exists(file_path):
        frappe.throw(f"Data file for {custom_size_filter} and {custom_size_standard} not found.")

    data = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Add the 'type' field with a default value
            row['type'] = "Default"
            data.append(row)
    
    return data