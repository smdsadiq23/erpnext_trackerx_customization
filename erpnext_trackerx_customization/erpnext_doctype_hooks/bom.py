
import frappe
import re

def validate_bom(doc, method):
    # validate_for_duplicate_bom_item_size(doc);
    generate_panel_code(doc, method)
    

def before_save_bom(doc, method):
    #calculate_custom_material_costs(doc);
    pass




def validate_for_duplicate_bom_item_size(doc):
    seen_items = set()
    seen_item_codes_no_size = set()

    for row in doc.items:
        item_code = row.item_code
        size = row.custom_size.strip() if row.custom_size else ""

        key = f"{item_code}::{size}"

        if size:
            if key in seen_items:
                frappe.throw(f"Duplicate item with same Item Code and Size found: {item_code} - {size}. Increase the quantity instead")
            seen_items.add(key)
        else:
            if item_code in seen_item_codes_no_size:
                frappe.throw(f"Item Code {item_code} without Size can be added only once. Increase the quantity instead")
            seen_item_codes_no_size.add(item_code)



@frappe.whitelist()
def generate_panel_code(doc, method):
    item_tables = [
        "custom_fabrics_items",
        "custom_trims_items",
        "custom_accessories_items",
        "custom_labels_items",
        "custom_packing_materials_items"
    ]

    item_tables_to_name = {
        "custom_fabrics_items": "Fabrics",
        "custom_trims_items": "Trims",
        "custom_accessories_items": "Accessories",
        "custom_labels_items": "Labels",
        "custom_packing_materials_items": "Packing Materials"
    }

    panel_code_map = {}

    global_index = 1

    for table_name in item_tables:
        child_items = getattr(doc, table_name, [])
        for item in child_items:
            if item.custom_panel_code:
                continue  # skip if already set

            # 1st value - from BOM Item.custom_fg_link
            fg_code = ""
            if item.custom_fg_link:
                fg_words = item.custom_fg_link.strip().split()
                fg_code = "".join(word[0] for word in fg_words[:2]).upper()

            # 2nd value - BOM.custom_style_number
            item_number = doc.custom_style_number or ""

            # 3rd value - BOM Item.custom_colour_code (fallback to BOM if not available)
            color_code = ""
            raw_color = doc.custom_colour_code or ""
            if raw_color:
                color_words = re.findall(r'\w+', raw_color)
                color_code = "".join(word[0] for word in color_words[:3]).upper()

            # 4th value - BOM Item.custom_size
            size = item.custom_size or ""

            # Generate base code
            parts = []
            if fg_code:
                parts.append(fg_code)
            if item_number:
                parts.append(item_number)
            if color_code:
                parts.append(color_code)
            # if size:
            #     parts.append(size)

            base_code = "-".join(parts)
    
            # Find existing panel codes for this base within current table
            matching_codes = [
                itm.custom_panel_code
                for itm in child_items
                if itm.custom_panel_code and itm.custom_panel_code.startswith(base_code)
            ]

            next_index = len(matching_codes) + 1
            suffix = f"{global_index:02d}"  # pad to 2 digits
            global_index += 1

            item.custom_panel_code = f"{base_code}-{suffix}"

            key = f"{item_tables_to_name.get(table_name)}||{item.item_code}||{(item.custom_size or '').strip().lower()}||{item.custom_article_no}||{item.qty}"

            panel_code_map[key]=item.custom_panel_code 


    # copy panel code for items
    for item in doc.items:
        key = f"{item.custom_item_type}||{item.item_code}||{(item.custom_size or '').strip().lower()}||{item.custom_article_no}||{item.qty}"
        item.custom_panel_code = panel_code_map[key] or "XX"


