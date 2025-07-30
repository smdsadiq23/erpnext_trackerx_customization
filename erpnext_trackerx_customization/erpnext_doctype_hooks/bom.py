
import frappe

def validate_bom(doc, method):
    # validate_for_duplicate_bom_item_size(doc);
    pass

def before_save_bom(doc, method):
    calculate_custom_material_costs(doc);




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


def calculate_custom_material_costs(doc):
    from collections import defaultdict

    size_cost_map = defaultdict(list)

    for item in doc.items:
        key = (item.item_code, item.custom_size)
        size_cost_map[key].append(item.amount or 0)

    # Step 1: Group costs per size and item
    total_avg = 0
    max_cost = 0

    grouped_items = defaultdict(list)

    for (item_code, size), costs in size_cost_map.items():
        group_cost = sum(costs)
        grouped_items[item_code].append(group_cost)

    # Step 2: Calculate average and highest
    for item_code, cost_list in grouped_items.items():
        total_avg += sum(cost_list) / len(cost_list)
        max_cost += max(cost_list)

    doc.custom_raw_material_cost_avg = total_avg
    doc.custom_raw_material_cost_highest = max_cost
