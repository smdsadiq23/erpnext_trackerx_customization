# Copyright (c) 2026, CognitionX and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document

class ProformaInvoice(Document):
    def validate(self):
        if not self.items or len(self.items) == 0:
            frappe.throw(_("Please add at least one item in the Proforma Invoice Item table before saving."))
        
        for item in self.items:
            if not item.item_code or not item.qty or not item.rate:
                frappe.throw(_("Row #{0}: Please ensure Item Code, Quantity, and Rate are filled.").format(item.idx))

    @frappe.whitelist()
    def fetch_items_from_sales_orders(self):
        """
        Fetch items from Sales Orders matching the PO Number (po_no field)
        and populate the Proforma Invoice Item child table.
        """
        if not self.po_number:
            frappe.throw("Please enter a PO Number first")

        # Fetch Sales Orders with matching po_no
        sales_orders = frappe.get_all(
            "Sales Order",
            filters={"po_no": self.po_number, "docstatus": 1},  # Only submitted SOs
            fields=["name", "customer", "currency"]
        )

        if not sales_orders:
            frappe.throw(f"No submitted Sales Orders found for PO Number: {self.po_number}")

        # Populate buyer and currency from first matching SO (all should be same buyer)
        self.buyer = sales_orders[0].customer
        self.currency = sales_orders[0].currency

        # Clear existing items
        self.set("items", [])

        # Fetch and map items from all matching Sales Orders
        for so in sales_orders:
            so_items = frappe.get_all(
                "Sales Order Item",
                filters={"parent": so.name},
                fields=[
                    "custom_lineitem",
                    "item_code",
                    "item_name",
                    "custom_style",
                    "custom_color",
                    "custom_size",
                    "custom_order_qty",
                    "rate"
                ],
                order_by="idx"
            )

            for item in so_items:
                if not item.custom_order_qty or item.custom_order_qty <= 0:
                    continue  # Skip zero/negative qty items

                pi_item = self.append("items", {})
                pi_item.sales_order = so.name
                pi_item.line_item = item.custom_lineitem
                pi_item.item_code = item.item_code
                pi_item.item_name = item.item_name
                pi_item.style = item.custom_style
                pi_item.colour = item.custom_color
                pi_item.size = item.custom_size
                pi_item.qty = int(item.custom_order_qty)
                pi_item.rate = item.rate
                pi_item.amount = item.custom_order_qty * item.rate

        return {
            "sales_order_count": len(sales_orders),
            "item_count": len(self.items)
        }
    

