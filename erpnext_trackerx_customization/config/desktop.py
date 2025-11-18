from frappe import _

def get_data():
    return [
        {
            "module_name": "Warehouse Management",
            "color": "#96be37",
            "icon": "fa fa-warehouse",
            "type": "module",
            "label": _("Warehouse Management"),
            "description": _("Warehouse capacity and analytics management"),
            "items": [
                {
                    "type": "page",
                    "name": "warehouse-capacity-d",
                    "label": _("Warehouse Capacity Dashboard"),
                    "description": _("Real-time warehouse capacity monitoring and analytics")
                }
            ]
        }
    ]