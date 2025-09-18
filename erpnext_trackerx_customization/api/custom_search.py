import frappe
from frappe.desk.search import search_link as original_search_link
from .custom_item_query import custom_item_query

@frappe.whitelist()
def custom_search_link(doctype, txt, filters=None, as_dict=False):
    if doctype == "Item":
        # Call your custom query directly.
        # This will return the tuple with the custom fields.
        result = custom_item_query(
            doctype,
            txt,
            searchfield="name",
            start=0,
            page_len=10,
            filters=filters
        )

        # Format the result to include the supplier and custom item number in the description
        formatted_result = []
        for row in result:
            # Assuming row is a tuple like: 
            # ('Item Code', 'Item Name', 'Item Group', 'Description', 'Supplier', 'Custom Item Number')
            item_code = row[0]
            item_name = row[1]
            custom_item_number = row[5] # The new field is at index 5
            supplier = row[4]

            # Create a combined description
            combined_description = f"{item_name} - {custom_item_number} - {supplier}"

            # Append the formatted result
            formatted_result.append({
                "value": item_code,
                "description": combined_description
            })
        
        return formatted_result

    else:
        # For all other DocTypes, fall back to the original Frappe search function.
        return original_search_link(doctype, txt, filters, as_dict)
    


    