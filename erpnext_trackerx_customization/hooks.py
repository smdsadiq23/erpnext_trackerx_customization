app_name = "erpnext_trackerx_customization"
app_title = "CognitionX Logic"
app_publisher = "CognitionX"
app_description = "Customization for ERPNext"
app_email = "support@cognitionx.tech"
app_license = "mit"



# Apps
# ------------------
app_logo_url = "/assets/erpnext_trackerx_customization/images/logo.svg"
brand_html = "CognitionXLogic"
website_context = {
    "brand_html": "CognitionXLogic",
    "favicon": "/assets/erpnext_trackerx_customization/images/logo.png",
    "splash_image": "/assets/erpnext_trackerx_customization/images/logo.png"
}



required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "erpnext_trackerx_customization",
# 		"logo": "/assets/erpnext_trackerx_customization/logo.png",
# 		"title": "Erpnext Trackerx Customization",
# 		"route": "/erpnext_trackerx_customization",
# 		"has_permission": "erpnext_trackerx_customization.api.permission.has_app_permission"
# 	}
# ]


#Fixtures
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "dt", "in", ["Item", "BOM", "BOM Item", 'BOM Operation', "Supplier", "Sales Order", "Sales Order Item", "Goods Receipt Note", "Material Request", "Material Request Item", "Material Request item Summary",
                          "Work Order", "Work Order Item", "Warehouse", "Purchase Receipt", "Pick List", "Pick List Item", "Purchase Order", "Purchase Order Item", "Purchase Receipt Item", "Operation"
                          ],
            ],
            [
                "module", "=", "Erpnext Trackerx Customization"
            ]
        ],
        "order_by": "modified asc"
    },
    {
        "dt": "Property Setter",
        "filters": [
            [
                "doc_type", "in", ["Item", "BOM", "BOM Item", 'BOM Operation', "Supplier", "Sales Order", "Sales Order Item", "Goods Receipt Note", "Material Request", "Material Request Item", "Material Request item Summary",
                          "Work Order", "Work Order Item", "Warehouse", "Purchase Receipt", "Pick List", "Pick List Item", "Purchase Order", "Purchase Order Item", "Purchase Receipt Item", "Operation", 'Factory OCR'
                            ]
            ],
            [
                "module", "=", "Erpnext Trackerx Customization"
            ]
        ],
        "order_by": "modified asc"
    },
    {
        "doctype": "DocField",
        "filters": [
            ["parent", "=", "Supplier"],
            ["fieldname", "=", "supplier_type"]
        ]
    },
    {
        "doctype": "Role",
        "filters": [
            [
                "name",
                "in",
                [
                "Merchant",
                "Merchant Manager",
                "Spare Parts Master",
                "Packing Materials Master",
                "Labels Master",
                "Machine Master",
                "Accessories Master",
                "Trims Master",
                "Fabrics Master",
                "Finished Goods Master"
                ]
            ]
        ]
    }, 
    {
        "doctype": "Operation Group",
        "filters": [
            [
                "name", "in",["QR/Barcode Cut Bundle Activation"]
            ]
        ]
    },    
    {
        "doctype": "Operation",
        "filters": [
            [
                "name", "in",["QR/Barcode Cut Bundle Activation"]
            ]
        ]
    },    
    {
        "doctype": "Workstation",
        "filters": [
            [
                "name", "in",["QR/Barcode Cut Bundle Activation"]
            ]
        ]
    },    
    {
        "doctype": "Physical Cell",
        "filters": [
            [
                "name", "in",["QR/Barcode Cut Bundle Activation"]
            ]
        ]
    },
    # {
    #     "doctype": "Physical Cell Operation",
    #     "filters": [
    #         [
    #             "operation", "in",["QR/Barcode Cut Bundle Activation"]
    #         ]
    #     ]
    # },
]

# AQL data fixtures for import during migration
aql_fixtures = [
    "erpnext_trackerx_customization/fixtures/aql_level.json",
    "erpnext_trackerx_customization/fixtures/aql_standard.json",
    "erpnext_trackerx_customization/fixtures/aql_table.json"
]


after_migrate = [
    #"erpnext_trackerx_customization.erpnext_doctype_hooks.warehouse_customization.execute",
    #"erpnext_trackerx_customization.setup.warehouse_structure.create_warehouse_structure"
    "erpnext_trackerx_customization.setup.purchase_receipt_custom_fields.execute",
    "erpnext_trackerx_customization.setup.migrate_quality_roles.execute",
    "erpnext_trackerx_customization.setup.aql_data_setup.import_aql_fixtures",
    "erpnext_trackerx_customization.whitelabel.apply"
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_trackerx_customization/css/erpnext_trackerx_customization.css"
app_include_css = [
    "/assets/erpnext_trackerx_customization/css/erpnext_trackerx_customization.css",
    "/assets/erpnext_trackerx_customization/css/xystyle.css"
]
app_include_js = [
    "/assets/erpnext_trackerx_customization/js/fabric_inspection_routes.js",
    "/assets/erpnext_trackerx_customization/js/process_map.js"
]


# include js, css files in header of web template
# web_include_css = "/assets/erpnext_trackerx_customization/css/erpnext_trackerx_customization.css"
# web_include_js = "/assets/erpnext_trackerx_customization/js/erpnext_trackerx_customization.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_trackerx_customization/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Item" : "public/js/item.js",
    "BOM": "public/js/bom.js",
    "Material Request": "public/js/material_request.js",
    "Sales Order": "public/js/sales_order.js",
    "Work Order": "public/js/work_order.js",
    "Pick List": "public/js/pick_list.js",
    "Trims Order": "public/js/trims_order.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Purchase Receipt": "public/js/purchase_receipt.js",
}
# include js in doctype list views
doctype_list_js = {
    "Fabric Inspection": "public/js/fabric_inspection_list.js",
    "Sales Order": "public/js/sales_order_list.js",
    "Pick List": "public/js/pick_list_list.js"
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "erpnext_trackerx_customization/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "erpnext_trackerx_customization.utils.jinja_methods",
# 	"filters": "erpnext_trackerx_customization.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "erpnext_trackerx_customization.install.before_install"
# after_install = "erpnext_trackerx_customization.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "erpnext_trackerx_customization.uninstall.before_uninstall"
# after_uninstall = "erpnext_trackerx_customization.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "erpnext_trackerx_customization.utils.before_app_install"
# after_app_install = "erpnext_trackerx_customization.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "erpnext_trackerx_customization.utils.before_app_uninstall"
# after_app_uninstall = "erpnext_trackerx_customization.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_trackerx_customization.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }
permission_query_conditions = {
    "Item": "erpnext_trackerx_customization.erpnext_doctype_hooks.item_hooks.get_item_permission_query_conditions"
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }
override_doctype_class = {
    "Item": "erpnext_trackerx_customization.overrides.item.CustomItem",
    "BOM": "erpnext_trackerx_customization.overrides.bom.CustomBOM",
    "Pick List": "erpnext_trackerx_customization.overrides.pick_list.CustomPickList"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events= {
    "Item Group": {
        "on_trash": "erpnext_trackerx_customization.erpnext_doctype_hooks.item_group_hooks.prevent_item_group_deletion"
    },
    "Role": {
        "on_trash": "erpnext_trackerx_customization.erpnext_doctype_hooks.role_hooks.prevent_role_deletion"
    },
	"Item": {
        "before_insert": "erpnext_trackerx_customization.erpnext_doctype_hooks.item_hooks.set_item_code_before_insert",
        "validate": "erpnext_trackerx_customization.erpnext_doctype_hooks.item_hooks.validate_item"
    },
    "BOM": {
        "validate": "erpnext_trackerx_customization.erpnext_doctype_hooks.bom.validate_bom",
        "before_insert": "erpnext_trackerx_customization.erpnext_doctype_hooks.bom.before_save_bom",
        "on_submit": "erpnext_trackerx_customization.erpnext_doctype_hooks.bom.on_submit"
    },
    "Purchase Order": {
        "autoname": "erpnext_trackerx_customization.erpnext_doctype_hooks.purchase_order.autoname",
        "validate": "erpnext_trackerx_customization.erpnext_doctype_hooks.purchase_order.validate"
    },
    "Purchase Receipt": {
        "autoname": "erpnext_trackerx_customization.erpnext_doctype_hooks.purchase_receipt.autoname",
        "validate": "erpnext_trackerx_customization.erpnext_doctype_hooks.purchase_receipt.validate"
    },
    "Sales Order": {
        "autoname": "erpnext_trackerx_customization.erpnext_doctype_hooks.sales_order.autoname",
        "validate": "erpnext_trackerx_customization.erpnext_doctype_hooks.sales_order.validate",
        "on_submit": "erpnext_trackerx_customization.erpnext_doctype_hooks.sales_order.on_submit"
    },
     "Work Order": {
         "autoname": "erpnext_trackerx_customization.erpnext_doctype_hooks.work_order.autoname",
        "validate": "erpnext_trackerx_customization.erpnext_doctype_hooks.work_order.validate",
        "on_submit": "erpnext_trackerx_customization.erpnext_doctype_hooks.work_order.on_submit",
        "on_trash": "erpnext_trackerx_customization.erpnext_doctype_hooks.work_order.on_trash"
    },
    "Goods Receipt Note": {
        "on_submit": "erpnext_trackerx_customization.erpnext_doctype_hooks.workflow.grn_workflow.create_inspections_on_grn_submit"
    },
    "Supplier Group": {
        "on_trash": "erpnext_trackerx_customization.erpnext_doctype_hooks.supplier_group.before_delete"
    },
    "Warehouse": {
        "after_insert": "erpnext_trackerx_customization.warehouse_hooks.on_warehouse_create",
        "on_update": "erpnext_trackerx_customization.warehouse_hooks.on_warehouse_update",
    },
    "Operation": {
        "on_trash": "erpnext_trackerx_customization.erpnext_doctype_hooks.operation.on_trash",
        "before_save": "erpnext_trackerx_customization.erpnext_doctype_hooks.operation.before_save",
        "before_rename": "erpnext_trackerx_customization.erpnext_doctype_hooks.operation.before_rename",
    },
     "Workstation": {
        "on_trash": "erpnext_trackerx_customization.erpnext_doctype_hooks.workstation.on_trash",
        "before_save": "erpnext_trackerx_customization.erpnext_doctype_hooks.workstation.before_save",
        "before_rename": "erpnext_trackerx_customization.erpnext_doctype_hooks.workstation.before_rename",
    },

}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_trackerx_customization.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_trackerx_customization.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_trackerx_customization.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_trackerx_customization.tasks.weekly"
# 	],
# 	"monthly": [
# 		"erpnext_trackerx_customization.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "erpnext_trackerx_customization.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_trackerx_customization.event.get_events"
# }
override_whitelisted_methods = {
    "erpnext.manufacturing.doctype.work_order.work_order.create_pick_list": "erpnext_trackerx_customization.api.custom_pick_list.custom_create_pick_list",
    "frappe.desk.search.search_link": "erpnext_trackerx_customization.api.custom_search.custom_search_link"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnext_trackerx_customization.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["erpnext_trackerx_customization.utils.before_request"]
# after_request = ["erpnext_trackerx_customization.utils.after_request"]

# Job Events
# ----------
# before_job = ["erpnext_trackerx_customization.utils.before_job"]
# after_job = ["erpnext_trackerx_customization.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"erpnext_trackerx_customization.auth.validate"
# ]

# Login hooks
# -----------
# on_login = "erpnext_trackerx_customization.utils.quality_redirect.redirect_quality_users_on_login"

# Role-based home page redirection
# Removed - not working properly with custom pages, users can access Quality Dashboard through workspace
# role_home_page = {
#     "Quality Inspector": "/app/quality_dashboard",
#     "Quality Manager": "/app/quality_dashboard"
# }


# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


boot_session = "erpnext_trackerx_customization.utils.constants.boot_session"

# Background Jobs
# ---------------
scheduler_events = {
    "daily": [
        "erpnext_trackerx_customization.warehouse_hooks.daily_capacity_sync"
    ],
    "weekly": [
        "erpnext_trackerx_customization.warehouse_hooks.weekly_capacity_report"
    ],
    "cron": {
        "30 23 * * *": [
            "erpnext_trackerx_customization.erpnext_trackerx_customization.jobs.daily_jobs.copy_operator_attendance_for_next_day"
        ]
    }
}
