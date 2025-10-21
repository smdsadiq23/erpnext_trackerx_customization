import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def save_process_map(map_name, style_group, nodes, edges, process_map_number=None, description=None):
    """
    Save or update a Process Map for Style Group.
    - If a map with the given map_name already exists → update it.
    - Otherwise → insert a new one.
    """
    try:
        # Input validation
        if not map_name:
            frappe.throw(_("Map name is required"))
        if not style_group:
            frappe.throw(_("Style Group selection is required"))
        if not nodes:
            frappe.throw(_("Process map nodes are required"))
        if not edges:
            frappe.throw(_("Process map edges are required"))

        # Validate Style Group exists
        if not frappe.db.exists("Style Group", style_group):
            frappe.throw(_("Selected Style Group '{0}' does not exist").format(style_group))

        # Validate JSON data
        try:
            import json
            if isinstance(nodes, str):
                json.loads(nodes)
            if isinstance(edges, str):
                json.loads(edges)
        except json.JSONDecodeError as e:
            frappe.throw(_("Invalid JSON data in nodes or edges: {0}").format(str(e)))

        existing = frappe.db.exists("Process Map", {"map_name": map_name, "style_group": style_group})

        if existing:
            # Update existing map
            doc = frappe.get_doc("Process Map", existing)
            doc.process_map_number = process_map_number
            doc.style_group = style_group
            doc.nodes = nodes
            doc.edges = edges
            doc.description = description or ""
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            return {"success": True, "message": "Process Map updated successfully", "docname": doc.name}
        else:
            # Create new map
            doc = frappe.get_doc({
                "doctype": "Process Map",
                "process_map_number": process_map_number,
                "map_name": map_name,
                "style_group": style_group,
                "nodes": nodes,
                "edges": edges,
                "description": description or ""
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return {"success": True, "message": "Process Map saved successfully", "docname": doc.name}

    except Exception as e:
        frappe.log_error(f"Error saving process map: {str(e)}", "Process Map Save Error")
        return {"success": False, "message": str(e)}

@frappe.whitelist(allow_guest=False)
def get_style_group_data(style_group_name):
    """
    Get Style Group data including components for Process Map Builder
    """
    try:
        if not style_group_name:
            frappe.throw(_("Style Group name is required"))

        if not frappe.db.exists("Style Group", style_group_name):
            frappe.throw(_("Style Group '{0}' does not exist").format(style_group_name))

        style_group = frappe.get_doc("Style Group", style_group_name)

        return {
            "success": True,
            "data": {
                "name": style_group.name,
                "description": style_group.description or "",
                "image": style_group.image or "",
                "company": style_group.company or "",
                "components": [
                    {
                        "component_name": comp.component_name,
                        "description": comp.description or "",
                        "component_image": comp.component_image or ""
                    }
                    for comp in (style_group.components or [])
                ]
            }
        }
    except Exception as e:
        frappe.log_error(f"Error getting style group data: {str(e)}", "Style Group Data Error")
        return {"success": False, "message": str(e)}

@frappe.whitelist(allow_guest=False)
def get_style_group_process_maps(style_group_name):
    """
    Get all Process Maps for a specific Style Group
    """
    try:
        if not style_group_name:
            frappe.throw(_("Style Group name is required"))

        if not frappe.db.exists("Style Group", style_group_name):
            frappe.throw(_("Style Group '{0}' does not exist").format(style_group_name))

        process_maps = frappe.get_all("Process Map",
            filters={"style_group": style_group_name},
            fields=[
                "name",
                "map_name",
                "process_map_number",
                "description",
                "creation",
                "modified",
                "docstatus"
            ],
            order_by="modified desc"
        )

        # Format dates for frontend
        for pm in process_maps:
            if pm.creation:
                pm.creation = pm.creation.strftime("%Y-%m-%d %H:%M")
            if pm.modified:
                pm.modified = pm.modified.strftime("%Y-%m-%d %H:%M")

        return {
            "success": True,
            "data": process_maps,
            "total": len(process_maps)
        }
    except Exception as e:
        frappe.log_error(f"Error getting style group process maps: {str(e)}", "Style Group Process Maps Error")
        return {"success": False, "message": str(e)}

@frappe.whitelist(allow_guest=False)
def load_process_map(process_map_name):
    """
    Load a specific Process Map with its nodes and edges
    """
    try:
        if not process_map_name:
            frappe.throw(_("Process Map name is required"))

        if not frappe.db.exists("Process Map", process_map_name):
            frappe.throw(_("Process Map '{0}' does not exist").format(process_map_name))

        process_map = frappe.get_doc("Process Map", process_map_name)

        # Parse JSON data
        import json
        nodes = json.loads(process_map.nodes or "[]")
        edges = json.loads(process_map.edges or "[]")

        return {
            "success": True,
            "data": {
                "name": process_map.name,
                "map_name": process_map.map_name,
                "process_map_number": process_map.process_map_number,
                "style_group": process_map.style_group,
                "description": process_map.description or "",
                "nodes": nodes,
                "edges": edges,
                "docstatus": process_map.docstatus,
                "creation": process_map.creation.strftime("%Y-%m-%d %H:%M") if process_map.creation else "",
                "modified": process_map.modified.strftime("%Y-%m-%d %H:%M") if process_map.modified else ""
            }
        }
    except Exception as e:
        frappe.log_error(f"Error loading process map: {str(e)}", "Process Map Load Error")
        return {"success": False, "message": str(e)}
