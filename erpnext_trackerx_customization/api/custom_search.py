import frappe
from frappe.desk.search import search_link as original_search_link
from .custom_item_query import custom_item_query

@frappe.whitelist()
def custom_search_link(doctype, txt, filters=None, as_dict=False):
    if doctype == "Item":
        # Call your custom query
        result = custom_item_query(
            doctype,
            txt,
            searchfield="name",
            start=0,
            page_len=10,
            filters=filters
        )

        formatted_result = []
        for row in result:
            item_code = row[0]
            item_name = row[1] or ""
            custom_item_number = (row[5] or "").strip()
            supplier = (row[4] or "").strip()

            # Build parts only if they exist
            parts = [item_name]
            if custom_item_number:
                parts.append(custom_item_number)
            if supplier:
                parts.append(supplier)

            # Join with " - " only between non-empty parts
            combined_description = " - ".join(parts)

            formatted_result.append({
                "value": item_code,
                "description": combined_description
            })

        return formatted_result

    else:
        # Fallback to original
        return original_search_link(doctype, txt, filters, as_dict)