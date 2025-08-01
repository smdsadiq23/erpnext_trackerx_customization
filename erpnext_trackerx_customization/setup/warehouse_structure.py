from __future__ import unicode_literals
import frappe
from frappe import _

def create_warehouse_structure(company_name=None):
    """
    Usage:
        bench --site yoursite console
        >>> import your_custom_app.warehouse_structure as ws
        >>> ws.execute("Test Company")   # pass your Company name
    """
    if not company_name:
        # Get default company if not specified
        company_name = frappe.defaults.get_user_default("Company")
        if not company_name:
            frappe.throw(_("No company specified and no default company found."))

    abbr = get_company_abbr(company_name)
    parent_warehouse = f"All Warehouses - {abbr}"

    if not frappe.db.exists("Warehouse", parent_warehouse):
        frappe.throw(_("Parent warehouse '{0}' not found").format(parent_warehouse))

    # 1. Main Warehouses
    main_warehouses = [
        {"warehouse_name": "FAB-WH", "custom_warehouse_name": "Fabric Storage", "is_group": 1},
        {"warehouse_name": "TRM-WH", "custom_warehouse_name": "Trims Storage", "is_group": 1},
        {"warehouse_name": "ACC-WH", "custom_warehouse_name": "Accessories Storage", "is_group": 1},
        {"warehouse_name": "QC-WH",  "custom_warehouse_name": "Quality Control", "is_group": 1},
        {"warehouse_name": "MCH-WH", "custom_warehouse_name": "Machinery Storage", "is_group": 1}
    ]

    for wh in main_warehouses:
        wh_fullname = f"{wh['warehouse_name']} - {abbr}"
        if not frappe.db.exists("Warehouse", wh_fullname):
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": wh['warehouse_name'],
                "parent_warehouse": parent_warehouse,
                "company": company_name,
                "is_group": wh['is_group'],
            })
            warehouse.insert(ignore_permissions=True, ignore_mandatory=True)
            if "custom_warehouse_name" in wh:
                warehouse.set("custom_warehouse_name", wh["custom_warehouse_name"])
                warehouse.save()
            frappe.db.commit()

    # 2. Fabric Zones/Racks/Levels/Bins (FAB-WH)
    fab_wh_fullname = f"FAB-WH - {abbr}"
    if not frappe.db.exists("Warehouse", fab_wh_fullname):
        frappe.throw(_("Main Fabric Warehouse ({}) not found").format(fab_wh_fullname))
    create_fabric_zones(company_name, abbr)

    # 3. Quality Control Zones (QC-WH)
    qc_wh_fullname = f"QC-WH - {abbr}"
    if not frappe.db.exists("Warehouse", qc_wh_fullname):
        frappe.throw(_("Main Quality Control Warehouse ({}) not found").format(qc_wh_fullname))
    create_quality_warehouses(company_name, abbr)

    # 4. Add similar function calls for TRM/ACC/MCH if required

    frappe.db.commit()
    frappe.msgprint(_("Warehouse structure created successfully for company: {0}").format(company_name))

def create_fabric_zones(company_name, abbr):
    """Create fabric warehouse hierarchy with exact naming"""
    zones = {
        "A": {"type": "Cotton", "capacity": 500},
        "B": {"type": "Synthetic", "capacity": 500},
        "C": {"type": "Blended", "capacity": 500},
        "D": {"type": "Specialty", "capacity": 500}
    }
    fab_parent = f"FAB-WH - {abbr}"

    for zone_code, zone_data in zones.items():
        zone_warehouse = f"FAB-WH-{zone_code}"
        zone_warehouse_full = f"{zone_warehouse} - {abbr}"
        if not frappe.db.exists("Warehouse", zone_warehouse_full):
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": zone_warehouse,
                "parent_warehouse": fab_parent,
                "company": company_name,
                "is_group": 1
            })
            warehouse.insert(ignore_permissions=True, ignore_mandatory=True)
            warehouse.set("zone_type", zone_data["type"])
            warehouse.save()

        # Racks, Levels, Bins
        for rack in range(1, 3):
            rack_warehouse = f"{zone_warehouse}-R{rack:02}"
            rack_warehouse_full = f"{rack_warehouse} - {abbr}"
            if not frappe.db.exists("Warehouse", rack_warehouse_full):
                warehouse = frappe.get_doc({
                    "doctype": "Warehouse",
                    "warehouse_name": rack_warehouse,
                    "parent_warehouse": zone_warehouse_full,
                    "company": company_name,
                    "is_group": 1
                })
                warehouse.insert(ignore_permissions=True, ignore_mandatory=True)

            for level in range(1, 4):
                level_warehouse = f"{rack_warehouse}-L{level}"
                level_warehouse_full = f"{level_warehouse} - {abbr}"
                if not frappe.db.exists("Warehouse", level_warehouse_full):
                    warehouse = frappe.get_doc({
                        "doctype": "Warehouse",
                        "warehouse_name": level_warehouse,
                        "parent_warehouse": rack_warehouse_full,
                        "company": company_name,
                        "is_group": 1
                    })
                    warehouse.insert(ignore_permissions=True, ignore_mandatory=True)

                for bin_num in range(1, 5):
                    bin_warehouse = f"{level_warehouse}-B{bin_num}"
                    bin_warehouse_full = f"{bin_warehouse} - {abbr}"
                    if not frappe.db.exists("Warehouse", bin_warehouse_full):
                        warehouse = frappe.get_doc({
                            "doctype": "Warehouse",
                            "warehouse_name": bin_warehouse,
                            "parent_warehouse": level_warehouse_full,
                            "company": company_name,
                            "is_group": 0
                        })
                        warehouse.insert(ignore_permissions=True, ignore_mandatory=True)
                        warehouse.set("zone_type", zone_data["type"])
                        warehouse.set("rack_number", rack)
                        warehouse.set("level_number", level)
                        warehouse.set("bin_number", bin_num)
                        warehouse.set("capacity", zone_data["capacity"])
                        warehouse.set("capacity_unit", "Meter")
                        warehouse.set("temperature_min", 18)
                        warehouse.set("temperature_max", 22)
                        warehouse.set("humidity_min", 45)
                        warehouse.set("humidity_max", 55)
                        warehouse.save()

def create_quality_warehouses(company_name, abbr):
    """Create quality control warehouses with exact naming"""
    qc_zones = [
        {"code": "QC-IN", "name": "Incoming"},
        {"code": "QC-HOLD", "name": "Hold"},
        {"code": "QC-PASS", "name": "Approved"},
        {"code": "QC-FAIL", "name": "Rejected"}
    ]
    qc_parent = f"QC-WH - {abbr}"

    for zone in qc_zones:
        zone_warehouse = f"QC-WH-{zone['code']}"
        zone_warehouse_full = f"{zone_warehouse} - {abbr}"
        if not frappe.db.exists("Warehouse", zone_warehouse_full):
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": zone_warehouse,
                "parent_warehouse": qc_parent,
                "company": company_name,
                "is_group": 0
            })
            warehouse.insert(ignore_permissions=True, ignore_mandatory=True)
            warehouse.set("zone_type", zone["name"])
            warehouse.save()

def get_company_abbr(company_name):
    abbr = frappe.db.get_value("Company", company_name, "abbr")
    if not abbr:
        frappe.throw(_("No abbreviation found for company {0}").format(company_name))
    return abbr
