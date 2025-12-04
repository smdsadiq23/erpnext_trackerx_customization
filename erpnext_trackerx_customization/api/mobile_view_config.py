import frappe
"""
Configuration file for customizing mobile form and list views per doctype
"""
from typing import Dict, Optional, Any

# Default mobile component mapping
DEFAULT_MOBILE_COMPONENTS = {
    "Data": "text_input",
    "Small Text": "textarea",
    "Int": "number_input",
    "Float": "number_input",
    "Currency": "currency_input",
    "Check": "toggle",
    "Select": "dropdown",
    "Link": "autocomplete",
    "Date": "date_picker",
    "Time": "time_picker",
    "Datetime": "datetime_picker",
    "Table": "dynamic_table"
}

# Per-doctype configuration
DOCTYPE_VIEW_CONFIG = {
    "Goods Receipt Note": {
        "title": "New GRN",
        "layout": "tabs",
        "version": "1.0",
        "submit_endpoint": "/api/method/erpnext_trackerx_customization.api.mobile_form_generator.submit_mobile_form",
        "tabs": {
            "Details": {
                "title": "Details",
                "sections": {
                    "Basic Information": {
                        "title": "Basic Information",
                        "collapsible": False
                    },
                    "Options": {
                        "title": "Options",
                        "collapsible": False
                    }
                }
            }
        },
        "validation_rules": {
            "posting_date": {
                "required": True,
                "max_date": "today",
                "message": "Posting date cannot be in future"
            },
            "company": {
                "required": True,
                "link_exists": True
            },
            "items": {
                "required": True,
                "min_items": 1
            }
        },
        "conditional_logic": [
            {
                "field": "posting_time",
                "condition": "set_posting_time == 1",
                "action": "show"
            }
        ],
        "field_dependencies": {
            "item_name": {
                "depends_on": "item_code",
                "fetch_from": "item_code.item_name"
            }
        },
        "ui_settings": {
            "theme": {
                "primary_color": "#8BC34A",
                "secondary_color": "#4CAF50",
                "icon": "📦"
            }
        },
        "list_view": {
            "title": "Goods Receipt Note List",
            "default_sort": "posting_date",
            "default_sort_order": "desc",
            "per_page": 20
        }
    }
    # Add more doctype configurations here
}

def get_view_config(doctype: str) -> Dict:
    """
    Get view configuration for a doctype
    
    Args:
        doctype (str): Document type name
    
    Returns:
        dict: Configuration dictionary
    """
    return DOCTYPE_VIEW_CONFIG.get(doctype, {})

def get_field_mobile_config(fieldname: str, fieldtype: str, config: Dict, field: Optional[Any] = None) -> Dict:
    """
    Get mobile-specific configuration for a field
    
    Args:
        fieldname (str): Field name
        fieldtype (str): Field type
        config (dict): Doctype configuration
        field: Frappe field object (optional)
    
    Returns:
        dict: Mobile field configuration
    """
    # Get field-specific config from doctype config
    field_configs = config.get("field_configs", {})
    field_config = field_configs.get(fieldname, {})
    
    # Build default mobile config based on fieldtype
    component = DEFAULT_MOBILE_COMPONENTS.get(fieldtype, "text_input")
    
    mobile_config = {
        "component": field_config.get("component", component),
        "validation": field_config.get("validation", {}).copy(),
        "ui_props": field_config.get("ui_props", {}).copy()
    }
    
    # Add fieldtype-specific defaults
    if fieldtype == "Link":
        mobile_config["search_endpoint"] = "/api/method/frappe.desk.search.search_link"
        mobile_config.setdefault("ui_props", {})["searchable"] = True
        mobile_config.setdefault("ui_props", {})["create_new"] = False
        mobile_config.setdefault("ui_props", {})["min_search_length"] = 2
        mobile_config.setdefault("ui_props", {})["placeholder"] = f"Search {field.label if field else fieldname}..."
        mobile_config.setdefault("validation", {})["link_exists"] = True
        if field and field.options:
            mobile_config.setdefault("validation", {})["doctype"] = field.options
    
    elif fieldtype == "Date":
        mobile_config.setdefault("ui_props", {})["format"] = "DD-MM-YYYY"
        mobile_config.setdefault("ui_props", {})["show_calendar"] = True
        mobile_config.setdefault("ui_props", {})["placeholder"] = "Select date"
        mobile_config.setdefault("validation", {})["type"] = "date"
    
    elif fieldtype == "Time":
        mobile_config.setdefault("ui_props", {})["format"] = "HH:mm"
        mobile_config.setdefault("ui_props", {})["placeholder"] = "Select time"
    
    elif fieldtype == "Select":
        mobile_config.setdefault("ui_props", {})["searchable"] = False
    
    elif fieldtype == "Check":
        mobile_config.setdefault("ui_props", {})["style"] = "switch"
    
    elif fieldtype == "Currency":
        mobile_config.setdefault("ui_props", {})["currency"] = "INR"
        mobile_config.setdefault("ui_props", {})["decimal_places"] = 2
    
    elif fieldtype == "Small Text":
        mobile_config.setdefault("ui_props", {})["rows"] = 3
    
    elif fieldtype == "Data":
        mobile_config.setdefault("ui_props", {})["placeholder"] = f"Enter {field.label if field else fieldname}"
    
    # Add required message if field is required
    if field and field.reqd:
        if "required" not in mobile_config["validation"]:
            mobile_config["validation"]["required"] = True
        if "required_message" not in mobile_config["validation"]:
            mobile_config["validation"]["required_message"] = f"{field.label or fieldname} is required"
    
    # Remove empty validation dict if no validations
    if not mobile_config["validation"]:
        mobile_config["validation"] = {}
    
    # Remove empty ui_props dict if no props
    if not mobile_config["ui_props"]:
        mobile_config["ui_props"] = {}
    
    return mobile_config


def get_hide_settings(doctype: str) -> Dict:
    """
    Get hide settings for a doctype from Mobile Meta Layout
    
    Args:
        doctype (str): Document type name
    
    Returns:
        dict: Dictionary with keys 'tabs', 'sections', 'fields' containing sets of hidden items
    """
    try:
        hide_settings = {
            "tabs": set(),
            "sections": set(),
            "fields": set()
        }
        
        # Check if hide settings exist for this doctype
        if frappe.db.exists("Mobile Meta Layout", doctype):
            doc = frappe.get_doc("Mobile Meta Layout", doctype)
            
            for item in doc.hidden_items:
                if item.enabled:  # Only include if hide is enabled
                    item_type = item.item_type.lower()
                    if item_type == "tab":
                        hide_settings["tabs"].add(item.item_name)
                    elif item_type == "section":
                        hide_settings["sections"].add(item.item_name)
                    elif item_type == "field":
                        hide_settings["fields"].add(item.item_name)
        
        return hide_settings
    
    except Exception as e:
        frappe.log_error(f"Error getting hide settings for {doctype}: {str(e)}", "Mobile Meta Layout Error")
        return {"tabs": set(), "sections": set(), "fields": set()}