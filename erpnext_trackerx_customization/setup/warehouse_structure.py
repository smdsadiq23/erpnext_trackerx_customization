from __future__ import unicode_literals
import frappe
from frappe import _

warehouse_configs = [
    {
        "warehouse_name": "FAB-WH",
        "custom_warehouse_name": "Fabric Storage",
        "is_group": 1,
        "zones": {
            "A": {"type": "Cotton", "capacity": 500},
            "B": {"type": "Synthetic", "capacity": 500},
            "C": {"type": "Blended", "capacity": 500},
            "D": {"type": "Specialty", "capacity": 500}
        }
    },
    {
        "warehouse_name": "TRM-WH",
        "custom_warehouse_name": "Trims Storage",
        "is_group": 1,
        "zones": {
            "A": {"type": "Threads", "capacity": 500},
            "B": {"type": "Zippers", "capacity": 500}
        }
    },
    {
        "warehouse_name": "ACC-WH",
        "custom_warehouse_name": "Accessories Storage",
        "is_group": 1,
        "zones": {
            "A": {"type": "Labels", "capacity": 500},
            "B": {"type": "Elastic", "capacity": 500}
        }
    },
    {
        "warehouse_name": "QC-WH",
        "custom_warehouse_name": "Quality Control",
        "is_group": 1
        # No zones
    },
    {
        "warehouse_name": "MCH-WH",
        "custom_warehouse_name": "Machinery Storage",
        "is_group": 1,
        "zones": {
            "A": {"type": "Pressing", "capacity": 500},
            "B": {"type": "Cutting", "capacity": 500}
        }
    }
]

def create_warehouse_structure(company_name=None):
    """
    Usage:
        bench --site yoursite console
        >>> import your_custom_app.warehouse_structure as ws
        >>> ws.create_warehouse_structure("Test Company")   # pass your Company name
    """
    if not company_name:
        company_name = frappe.defaults.get_user_default("Company")
        if not company_name:
            frappe.throw(_("No company specified and no default company found."))

    abbr = get_company_abbr(company_name)
    parent_warehouse = f"All Warehouses - {abbr}"

    if not frappe.db.exists("Warehouse", parent_warehouse):
        frappe.throw(_("Parent warehouse '{0}' not found").format(parent_warehouse))

    # 1. Create main warehouses and children
    for wh_cfg in warehouse_configs:
        wh_fullname = f"{wh_cfg['warehouse_name']} - {abbr}"
        if not frappe.db.exists("Warehouse", wh_fullname):
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": wh_cfg["warehouse_name"],
                "parent_warehouse": parent_warehouse,
                "company": company_name,
                "is_group": wh_cfg.get("is_group", 1),
            })
            warehouse.insert(ignore_permissions=True, ignore_mandatory=True)
            if "custom_warehouse_name" in wh_cfg:
                warehouse.set("custom_warehouse_name", wh_cfg["custom_warehouse_name"])
                warehouse.save()
            frappe.db.commit()

        # 2. If zones, create zones & children (racks/levels/bins)
        if wh_cfg.get("zones"):
            parent = wh_fullname
            for zone_code, zone_data in wh_cfg["zones"].items():
                zone_warehouse = f"{wh_cfg['warehouse_name']}-{zone_code}"
                zone_warehouse_full = f"{zone_warehouse} - {abbr}"
                if not frappe.db.exists("Warehouse", zone_warehouse_full):
                    warehouse = frappe.get_doc({
                        "doctype": "Warehouse",
                        "warehouse_name": zone_warehouse,
                        "parent_warehouse": parent,
                        "company": company_name,
                        "is_group": 1
                    })
                    warehouse.insert(ignore_permissions=True, ignore_mandatory=True)
                    if zone_data.get("type"):
                        warehouse.set("zone_type", zone_data["type"])
                        warehouse.save()
                # create racks/levels/bins under each zone
                create_rack_level_bin(
                    company_name=company_name,
                    abbr=abbr,
                    parent_warehouse=zone_warehouse,
                    parent_zone_type=zone_data.get("type"),
                    zone_data=zone_data
                )
        else:
            # For warehouses with NO zones, create racks/levels/bins directly
            create_rack_level_bin(
                company_name=company_name,
                abbr=abbr,
                parent_warehouse=wh_cfg['warehouse_name'],
                parent_zone_type=None,
                zone_data=None
            )

    frappe.db.commit()
    frappe.msgprint(_("Warehouse structure created successfully for company: {0}").format(company_name))


def create_rack_level_bin(company_name, abbr, parent_warehouse, parent_zone_type=None, zone_data=None):
    """Create rack/level/bin hierarchy under a parent warehouse"""
    # Allowed zone_type (blank if no type)
    zone_type = parent_zone_type or ""
    capacity = (zone_data or {}).get("capacity", 500)
    parent_fullname = f"{parent_warehouse} - {abbr}"

    for rack in range(1, 3):
        rack_warehouse = f"{parent_warehouse}-R{rack:02}"
        rack_warehouse_full = f"{rack_warehouse} - {abbr}"
        if not frappe.db.exists("Warehouse", rack_warehouse_full):
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": rack_warehouse,
                "parent_warehouse": parent_fullname,
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
                    # Only set zone_type if provided and valid
                    if zone_type:
                        warehouse.set("zone_type", zone_type)
                    warehouse.set("rack_number", rack)
                    warehouse.set("level_number", level)
                    warehouse.set("bin_number", bin_num)
                    warehouse.set("capacity", capacity)
                    warehouse.set("capacity_unit", "Meter")
                    warehouse.set("temperature_min", 18)
                    warehouse.set("temperature_max", 22)
                    warehouse.set("humidity_min", 45)
                    warehouse.set("humidity_max", 55)
                    warehouse.save()


def get_company_abbr(company_name):
    abbr = frappe.db.get_value("Company", company_name, "abbr")
    if not abbr:
        frappe.throw(_("No abbreviation found for company {0}").format(company_name))
    return abbr

