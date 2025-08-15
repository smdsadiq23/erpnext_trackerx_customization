import frappe
import json
from frappe import _


def get_context(context):
    """Get context for trims inspection UI page"""
    try:
        # Get inspection name from URL
        inspection_name = frappe.form_dict.get('inspection') or frappe.form_dict.get('name')
        if not inspection_name:
            frappe.throw(_("Inspection parameter missing"))
        
        # Get the inspection document
        if not frappe.db.exists("Trims Inspection", inspection_name):
            frappe.throw(_("Trims Inspection {0} not found").format(inspection_name))
        
        inspection_doc = frappe.get_doc("Trims Inspection", inspection_name)
        
        # Check permissions
        if not inspection_doc.has_permission("read"):
            frappe.throw(_("You do not have permission to view this inspection"))
        
        # Get inspection items (simulated from GRN or manual entry)
        inspection_items = get_inspection_items(inspection_doc)
        
        # Get defect categories for trims
        defect_categories = get_trims_defect_categories()
        
        # Get existing defects data
        defects_data = {}
        if inspection_doc.get('defects_data'):
            try:
                defects_data = json.loads(inspection_doc.defects_data)
            except:
                defects_data = {}
        
        # Check write permissions
        can_write = inspection_doc.has_permission("write")
        
        # Set context
        context.update({
            'page_title': f'Trims Inspection: {inspection_name}',
            'inspection_name': inspection_name,
            'inspection_doc': inspection_doc,
            'inspection_items': inspection_items,
            'defect_categories': defect_categories,
            'defects_data': defects_data,
            'can_write': can_write
        })
        
    except Exception as e:
        frappe.log_error(f"Error in trims inspection UI context: {str(e)}")
        frappe.throw(_("Error loading inspection: {0}").format(str(e)))


def get_inspection_items(inspection_doc):
    """Get items for inspection (simulated data for now)"""
    items = []
    
    # For now, create sample items based on total pieces
    total_pieces = inspection_doc.get('total_pieces', 100)
    pieces_per_item = max(1, total_pieces // 10)  # Divide into max 10 items
    
    for i in range(1, min(11, total_pieces + 1)):
        items.append({
            'item_number': f"ITEM-{i:03d}",
            'description': f"Sample item {i}",
            'pieces': pieces_per_item if i < 10 else (total_pieces - (pieces_per_item * 9)),
            'status': 'Pending'
        })
    
    return items


def get_trims_defect_categories():
    """Get defect categories for trims inspection"""
    return {
        'Critical Defects': [
            {'name': 'Broken', 'code': 'BROKEN'},
            {'name': 'Missing', 'code': 'MISSING'},
            {'name': 'Wrong Color', 'code': 'WRONG_COLOR'},
            {'name': 'Wrong Size', 'code': 'WRONG_SIZE'},
            {'name': 'Contamination', 'code': 'CONTAMINATION'}
        ],
        'Major Defects': [
            {'name': 'Scratch', 'code': 'SCRATCH'},
            {'name': 'Dent', 'code': 'DENT'},
            {'name': 'Discoloration', 'code': 'DISCOLORATION'},
            {'name': 'Rough Edge', 'code': 'ROUGH_EDGE'},
            {'name': 'Assembly Error', 'code': 'ASSEMBLY_ERROR'}
        ],
        'Minor Defects': [
            {'name': 'Surface Mark', 'code': 'SURFACE_MARK'},
            {'name': 'Slight Variation', 'code': 'SLIGHT_VARIATION'},
            {'name': 'Minor Scratch', 'code': 'MINOR_SCRATCH'},
            {'name': 'Polish Issue', 'code': 'POLISH_ISSUE'},
            {'name': 'Packaging Issue', 'code': 'PACKAGING_ISSUE'}
        ]
    }