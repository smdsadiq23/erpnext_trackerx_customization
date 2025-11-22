import frappe
from frappe import _
from frappe.utils import getdate, nowdate, now_datetime
import json
from typing import Dict, List, Optional, Any
from .mobile_view_config import get_view_config, get_field_mobile_config

@frappe.whitelist()
def get_mobile_view(doctype: str, action: str = "form", docname: Optional[str] = None):
    """
    Dynamic API to generate form or list view JSON for any doctype
    
    Args:
        doctype (str): Document type name
        action (str): "form" or "list"
        docname (str, optional): Document name for edit mode
    
    Returns:
        dict: Form or list view configuration in mobile format
    """
    try:
        # Validate doctype exists
        if not frappe.db.exists("DocType", doctype):
            return {
                "message": {
                    "success": False,
                    "error": f"DocType '{doctype}' not found"
                }
            }
        
        # Check permissions
        if not frappe.has_permission(doctype, "read"):
            return {
                "message": {
                    "success": False,
                    "error": f"Permission denied for {doctype}"
                }
            }
        
        if action == "form":
            return _get_form_view(doctype, docname)
        elif action == "list":
            return _get_list_view(doctype)
        else:
            return {
                "message": {
                    "success": False,
                    "error": f"Invalid action: {action}. Use 'form' or 'list'"
                }
            }
    
    except Exception as e:
        frappe.log_error(f"Error generating mobile view for {doctype}: {str(e)}", "Mobile Form Generator Error")
        return {
            "message": {
                "success": False,
                "error": str(e)
            }
        }

def _get_form_view(doctype: str, docname: Optional[str] = None) -> Dict:
    """Generate form view configuration"""
    try:
        meta = frappe.get_meta(doctype)
        config = get_view_config(doctype)
        
        # Determine mode
        mode = "edit" if docname and frappe.db.exists(doctype, docname) else "create"
        
        # Get document if editing
        doc = None
        if docname and mode == "edit":
            doc = frappe.get_doc(doctype, docname)
            if not doc.has_permission("read"):
                raise frappe.PermissionError(f"Permission denied to read {doctype} {docname}")
        
        # Build form meta
        form_meta = {
            "doctype": doctype,
            "title": config.get("title", f"New {meta.name}") if mode == "create" else docname,
            "mode": mode,
            "layout": config.get("layout", "tabs"),
            "version": config.get("version", "1.0"),
            "submit_endpoint": config.get("submit_endpoint", f"/api/method/erpnext_trackerx_customization.api.mobile_form_generator.submit_mobile_form")
        }
        
        # Build tabs from meta
        tabs = _build_tabs_from_meta(meta, config, doc)
        
        # Build validation rules
        validation_rules = _build_validation_rules(meta, config)
        
        # Build UI settings
        ui_settings = config.get("ui_settings", _get_default_ui_settings())
        
        # Build conditional logic
        conditional_logic = config.get("conditional_logic", [])
        
        # Build field dependencies
        field_dependencies = _build_field_dependencies(meta, config)
        
        # Build permissions
        permissions = _build_permissions(doctype, docname)
        
        return {
            "message": {
                "success": True,
                "data": {
                    "form_meta": form_meta,
                    "tabs": tabs,
                    "validation_rules": validation_rules,
                    "ui_settings": ui_settings,
                    "conditional_logic": conditional_logic,
                    "field_dependencies": field_dependencies,
                    "permissions": permissions
                }
            }
        }
    
    except Exception as e:
        frappe.log_error(f"Error building form view: {str(e)}", "Mobile Form Generator Error")
        raise

def _build_tabs_from_meta(meta, config: Dict, doc: Optional[Any] = None) -> List[Dict]:
    """Build tabs structure from doctype meta"""
    tabs = []
    tab_config = config.get("tabs", {})
    
    # Get all fields grouped by section
    fields_by_section = {}
    current_tab = None
    current_section = None
    
    for field in meta.fields:
        # Skip system fields
        if field.fieldtype in ["Section Break", "Column Break", "Tab Break"]:
            if field.fieldtype == "Tab Break":
                current_tab = field.label or field.fieldname
                current_section = None
            elif field.fieldtype == "Section Break":
                current_section = field.label or field.fieldname
            continue
        
        # Skip hidden fields unless configured
        if field.hidden and not config.get("include_hidden_fields", False):
            continue
        
        # Determine tab and section
        tab_name = current_tab or "details"
        section_name = current_section or "basic_info"
        
        if tab_name not in fields_by_section:
            fields_by_section[tab_name] = {}
        if section_name not in fields_by_section[tab_name]:
            fields_by_section[tab_name][section_name] = []
        
        # Build field config
        field_config = _build_field_config(field, meta, config, doc)
        if field_config:
            fields_by_section[tab_name][section_name].append(field_config)
    
    # Convert to tabs structure
    tab_idx = 0
    for tab_name, sections in fields_by_section.items():
        tab_id = f"tab_{tab_idx}"
        tab_config_data = tab_config.get(tab_name, {})
        
        sections_list = []
        section_idx = 0
        for section_name, fields in sections.items():
            if not fields:  # Skip empty sections
                continue
            
            section_id = f"section_{section_idx}"
            section_config = tab_config_data.get("sections", {}).get(section_name, {})
            
            sections_list.append({
                "id": section_id,
                "name": section_name.lower().replace(" ", "_"),
                "title": section_config.get("title", section_name),
                "collapsible": section_config.get("collapsible", False),
                "collapsed": section_config.get("collapsed", False),
                "fields": fields
            })
            section_idx += 1
        
        if sections_list:  # Only add tab if it has sections
            tabs.append({
                "id": tab_id,
                "name": tab_name.lower().replace(" ", "_"),
                "title": tab_config_data.get("title", tab_name),
                "active": tab_idx == 0,
                "sections": sections_list
            })
            tab_idx += 1
    
    # If no tabs found, create a default one
    if not tabs:
        tabs.append({
            "id": "tab_0",
            "name": "details",
            "title": "Details",
            "active": True,
            "sections": [{
                "id": "section_0",
                "name": "basic_info",
                "title": "Basic Information",
                "collapsible": False,
                "collapsed": False,
                "fields": []
            }]
        })
    
    return tabs

def _build_field_config(field, meta, config: Dict, doc: Optional[Any] = None) -> Optional[Dict]:
    """Build field configuration for mobile"""
    try:
        # Get field value if document exists
        current_value = None
        if doc and hasattr(doc, field.fieldname):
            current_value = getattr(doc, field.fieldname)
            # Format dates and datetimes
            if field.fieldtype == "Date" and current_value:
                current_value = str(current_value)
            elif field.fieldtype == "Datetime" and current_value:
                current_value = current_value.isoformat() if hasattr(current_value, 'isoformat') else str(current_value)
        
        # Get default value
        default_value = field.default
        if default_value == "Today":
            default_value = nowdate()
        elif default_value == "now":
            default_value = now_datetime()
        
        # Parse options for Select fields
        options = None
        if field.fieldtype == "Select" and field.options:
            options = [opt.strip() for opt in field.options.split("\n") if opt.strip()]
        
        # Build base field config
        field_config = {
            "fieldname": field.fieldname,
            "fieldtype": field.fieldtype,
            "label": field.label or field.fieldname,
            "required": bool(field.reqd),
            "read_only": bool(field.read_only),
            "hidden": bool(field.hidden),
            "current_value": current_value
        }
        
        # Add fieldtype-specific properties
        if field.fieldtype == "Link":
            field_config["options"] = field.options
        elif field.fieldtype == "Select":
            if options:
                field_config["options"] = options
        elif field.fieldtype == "Table":
            field_config["options"] = field.options
            # Get child table fields
            child_meta = frappe.get_meta(field.options)
            child_fields = []
            for child_field in child_meta.fields:
                if child_field.fieldtype not in ["Section Break", "Column Break", "Tab Break"]:
                    child_field_config = _build_child_field_config(child_field, child_meta)
                    if child_field_config:
                        child_fields.append(child_field_config)
            field_config["mobile_config"] = {
                "component": "dynamic_table",
                "child_fields": child_fields,
                "validation": {
                    "required": bool(field.reqd),
                    "min_items": 1 if field.reqd else 0
                },
                "ui_props": {
                    "add_button_text": f"Add {field.label or 'Item'}",
                    "allow_bulk_edit": True,
                    "show_totals": True
                }
            }
            return field_config
        
        # Add default value
        if default_value is not None:
            field_config["default"] = default_value
        
        # Get mobile-specific config
        mobile_config = get_field_mobile_config(field.fieldname, field.fieldtype, config)
        
        # Merge with field-specific config
        field_config["mobile_config"] = mobile_config
        
        return field_config
    
    except Exception as e:
        frappe.log_error(f"Error building field config for {field.fieldname}: {str(e)}", "Mobile Form Generator Error")
        return None

def _build_child_field_config(field, meta) -> Optional[Dict]:
    """Build configuration for child table field"""
    try:
        config = {
            "fieldname": field.fieldname,
            "fieldtype": field.fieldtype,
            "label": field.label or field.fieldname,
            "required": bool(field.reqd),
            "read_only": bool(field.read_only)
        }
        
        if field.fieldtype == "Link":
            config["options"] = field.options
        
        # Get mobile component
        component = _get_mobile_component(field.fieldtype)
        config["mobile_config"] = {
            "component": component,
            "inline": True
        }
        
        return config
    
    except Exception as e:
        frappe.log_error(f"Error building child field config: {str(e)}", "Mobile Form Generator Error")
        return None

def _get_mobile_component(fieldtype: str) -> str:
    """Map Frappe fieldtype to mobile component"""
    mapping = {
        "Data": "text_input",
        "Small Text": "textarea",
        "Text Editor": "rich_text",
        "Int": "number_input",
        "Float": "number_input",
        "Currency": "currency_input",
        "Percent": "number_input",
        "Check": "toggle",
        "Select": "dropdown",
        "Link": "autocomplete",
        "Date": "date_picker",
        "Time": "time_picker",
        "Datetime": "datetime_picker",
        "Attach": "file_upload",
        "Attach Image": "image_upload",
        "Color": "color_picker",
        "Table": "dynamic_table"
    }
    return mapping.get(fieldtype, "text_input")

def _build_validation_rules(meta, config: Dict) -> Dict:
    """Build validation rules from meta and config"""
    validation_rules = {}
    
    # Add field-level validations
    for field in meta.fields:
        if field.reqd:
            rule = {"required": True}
            if field.fieldtype == "Date":
                rule["max_date"] = "today"
            elif field.fieldtype == "Link":
                rule["link_exists"] = True
                rule["doctype"] = field.options
            
            validation_rules[field.fieldname] = rule
    
    # Merge with config validations
    config_validations = config.get("validation_rules", {})
    validation_rules.update(config_validations)
    
    return validation_rules

def _build_field_dependencies(meta, config: Dict) -> Dict:
    """Build field dependencies"""
    dependencies = {}
    
    # Add from config
    config_deps = config.get("field_dependencies", {})
    dependencies.update(config_deps)
    
    return dependencies

def _build_permissions(doctype: str, docname: Optional[str] = None) -> Dict:
    """Build permissions for the document"""
    doc = None
    if docname:
        try:
            doc = frappe.get_doc(doctype, docname)
        except:
            pass
    
    return {
        "can_create": frappe.has_permission(doctype, "create"),
        "can_read": frappe.has_permission(doctype, "read"),
        "can_write": frappe.has_permission(doctype, "write") if not doc else doc.has_permission("write"),
        "can_delete": frappe.has_permission(doctype, "delete") if not doc else doc.has_permission("delete"),
        "can_submit": frappe.has_permission(doctype, "submit") if not doc else doc.has_permission("submit"),
        "can_cancel": frappe.has_permission(doctype, "cancel") if not doc else doc.has_permission("cancel"),
        "can_print": frappe.has_permission(doctype, "print") if not doc else doc.has_permission("print"),
        "can_email": frappe.has_permission(doctype, "email") if not doc else doc.has_permission("email")
    }

def _get_default_ui_settings() -> Dict:
    """Get default UI settings"""
    return {
        "theme": {
            "primary_color": "#8BC34A",
            "secondary_color": "#4CAF50",
            "background_color": "#F5F5F5",
            "text_color": "#333333",
            "border_color": "#E0E0E0",
            "icon": "📦",
            "accent_color": "#689F38"
        },
        "layout": {
            "field_spacing": "16px",
            "section_spacing": "24px",
            "border_radius": "8px",
            "font_size": "16px",
            "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
        },
        "form": {
            "show_progress": True,
            "sticky_header": True,
            "floating_labels": True,
            "compact_mode": False
        },
        "buttons": {
            "style": "filled",
            "size": "large",
            "full_width": True
        }
    }

def _get_list_view(doctype: str) -> Dict:
    """Generate list view configuration"""
    try:
        meta = frappe.get_meta(doctype)
        config = get_view_config(doctype)
        
        # Get list view config
        list_config = config.get("list_view", {})
        
        # Build columns from meta
        columns = []
        for field in meta.fields:
            if field.in_list_view and not field.hidden:
                columns.append({
                    "fieldname": field.fieldname,
                    "label": field.label or field.fieldname,
                    "fieldtype": field.fieldtype,
                    "width": field.width or 100
                })
        
        # Add default columns if none found
        if not columns:
            default_fields = ["name", "creation", "modified", "owner"]
            for fieldname in default_fields:
                field = meta.get_field(fieldname)
                if field:
                    columns.append({
                        "fieldname": fieldname,
                        "label": field.label or fieldname,
                        "fieldtype": field.fieldtype,
                        "width": 100
                    })
        
        return {
            "message": {
                "success": True,
                "data": {
                    "doctype": doctype,
                    "title": list_config.get("title", f"{doctype} List"),
                    "columns": columns,
                    "filters": list_config.get("filters", []),
                    "default_sort": list_config.get("default_sort", "creation"),
                    "default_sort_order": list_config.get("default_sort_order", "desc"),
                    "per_page": list_config.get("per_page", 20),
                    "endpoint": list_config.get("endpoint", f"/api/method/erpnext_trackerx_customization.api.mobile_utils.manage_document_list")
                }
            }
        }
    
    except Exception as e:
        frappe.log_error(f"Error building list view: {str(e)}", "Mobile Form Generator Error")
        raise

@frappe.whitelist()
def submit_mobile_form(doctype: str, data: Dict):
    """
    Submit form data from mobile app
    
    Args:
        doctype (str): Document type
        data (dict): Form data
    
    Returns:
        dict: Submission result
    """
    try:
        data = frappe.parse_json(data) if isinstance(data, str) else data
        
        # Use existing manage_document function
        from .mobile_utils import manage_document
        
        docname = data.get("name")
        if docname:
            action = "update"
        else:
            action = "new"
        
        # Remove name from data for new documents
        if action == "new":
            data.pop("name", None)
        
        result = manage_document(doctype, action, doc_id=docname, data=data)
        return result
    
    except Exception as e:
        frappe.log_error(f"Error submitting mobile form: {str(e)}", "Mobile Form Generator Error")
        return {
            "success": False,
            "error": str(e)
        }
