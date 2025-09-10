import frappe
from frappe.model.document import Document

class CustomItem(Document):
    def before_save(self):
        frappe.msgprint("reached here")
        self.set_fg_component_names()

    def set_fg_component_names(self):
        if not self.get("custom_fg_components"):
            return

        parent_name = self.name
        seen = set()

        for row in self.custom_fg_components:
            if not row.component_name:
                frappe.throw(f"Component Name is mandatory in row {row.idx}")

            if row.component_name in seen:
                frappe.throw(f"Duplicate Component Name '{row.component_name}' in row {row.idx}. Must be unique per Item.")

            seen.add(row.component_name)

            row.name = f"{parent_name}-{row.component_name}"