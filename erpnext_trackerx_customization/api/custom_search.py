# erpnext_trackerx_customization/api/custom_search.py
import inspect
import frappe
from frappe.desk.search import search_link as original_search_link
from erpnext_trackerx_customization.api.custom_item_query import custom_item_query

@frappe.whitelist()
def custom_search_link(
    doctype: str,
    txt: str,
    query: str | None = None,
    filters: str | dict | list | None = None,
    page_length: int = 10,
    searchfield: str | None = None,
    reference_doctype: str | None = None,
    ignore_user_permissions: bool = False,
):
    # Some builds pass filters=False
    if isinstance(filters, bool):
        filters = None

    # ✅ Our custom rendering only for Item doctype
    if doctype == "Item":
        rows = custom_item_query(
            doctype=doctype,
            txt=txt,
            searchfield=searchfield or "name",
            start=0,
            page_len=page_length,
            filters=filters,
            as_dict=True,   # IMPORTANT: use keys, not indexes
        ) or []

        out = []
        for r in rows:
            item_code = (r.get("name") or "").strip()
            cust_no   = (r.get("custom_item_number") or "").strip()
            supp      = (r.get("custom_preferred_supplier") or "").strip()

            # Build exactly: item_code - custom_item_number - custom_preferred_supplier
            parts = [p for p in [item_code, cust_no, supp] if p]
            desc  = " - ".join(parts)

            # value must remain the actual name/item_code
            out.append({"value": item_code, "description": desc})
        return out

    # 🔁 Everything else → stock behaviour (version-safe passthrough)
    sig = inspect.signature(original_search_link)
    allowed = set(sig.parameters.keys())
    passthrough = {
        k: v for k, v in {
            "doctype": doctype,
            "txt": txt.strip(),
            "query": query,
            "filters": filters,
            "page_length": page_length,
            "searchfield": searchfield,
            "reference_doctype": reference_doctype,
            "ignore_user_permissions": ignore_user_permissions,
        }.items() if k in allowed
    }

    # ✅ FIX: Ensure `user` is passed if expected by original_search_link
    if "user" in allowed:
        passthrough.setdefault("user", frappe.session.user)
     
    return original_search_link(**passthrough)
