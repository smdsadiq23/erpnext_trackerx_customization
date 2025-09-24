from frappe import _

def get_data():
    return [
        {
            "module_name": "ERPNext TrackerX Customization",
            "color": "grey",
            "icon": "octicon octicon-file-directory",
            "type": "module",
            "label": _("ERPNext TrackerX Customization"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Operator Attendance",
                    "label": _("Operator Attendance List"),
                },
                {
                    "type": "page",
                    "name": "operator-attendance-grid",
                    "label": _("Operator Attendance Grid"),
                },
            ]
        }
    ]