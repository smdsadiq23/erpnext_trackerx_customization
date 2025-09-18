# In custom_search.py

import frappe
from frappe.desk.search import search_link as original_search_link
from .custom_item_query import custom_item_query

@frappe.whitelist()
def custom_search_link(doctype, txt, filters=None, as_dict=False):
    if filters is False:
        filters = None

    if doctype == "Item":
        result = custom_item_query(
            doctype,
            txt,
            searchfield="name",
            start=0,
            page_len=10,
            filters=filters,
            as_dict=as_dict # Your custom query is fine with as_dict
        )
        formatted_result = []
        for row in result:
            item_code = row[0]
            item_name = row[1] or ""
            custom_item_number = (row[5] or "").strip()
            supplier = (row[4] or "").strip()
            parts = [item_name]
            if custom_item_number:
                parts.append(custom_item_number)
            if supplier:
                parts.append(supplier)
            combined_description = " - ".join(parts)
            formatted_result.append({
                "value": item_code,
                "description": combined_description
            })
        return formatted_result
    else:
        # Create a dictionary of arguments to pass to the original function
        args = {
            "doctype": doctype,
            "txt": txt,
            # as_dict is NOT passed to original_search_link
        }
        if filters is not False:
            args["filters"] = filters
        return original_search_link(**args)