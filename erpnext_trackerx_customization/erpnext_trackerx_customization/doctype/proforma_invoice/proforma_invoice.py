# Copyright (c) 2026, CognitionX and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe import _
from collections import defaultdict

class ProformaInvoice(Document):
    def validate(self):
        """
        Server-side validation: Ensure at least one valid item row exists before save/submit
        """
        self._validate_items_table()
        self._validate_required_fields_in_items()
    
    def _validate_items_table(self):
        """Ensure items table is not empty"""
        if not self.items or len(self.items) == 0:
            frappe.throw(
                _("Proforma Invoice Item table cannot be empty. Please add at least one item before saving."),
                title=_("Missing Items")
            )
    
    def _validate_required_fields_in_items(self):
        """Ensure required fields are filled in each item row"""
        missing_fields = []
        for idx, item in enumerate(self.items, start=1):
            errors = []
            if not item.item_code:
                errors.append("Item Code")
            if not item.qty or item.qty <= 0:
                errors.append("Quantity (must be > 0)")
            if not item.rate or item.rate <= 0:
                errors.append("Rate (must be > 0)")
            
            if errors:
                missing_fields.append(f"Row #{idx}: {', '.join(errors)}")
        
        if missing_fields:
            frappe.throw(
                _("Please correct the following missing/invalid fields in Proforma Invoice Items:<br>{0}").format(
                    "<br>".join(missing_fields)
                ),
                title=_("Incomplete Items")
            )
    
    @frappe.whitelist()
    def fetch_items_from_sales_orders(self):
        """
        Fetch items from Sales Orders matching the PO Number (po_no field)
        and populate the Proforma Invoice Item child table.
        Sets delivery_date as the maximum delivery date from all matching Sales Orders.
        """
        if not self.po_number:
            frappe.throw(_("Please enter a PO Number first"))

        # Fetch Sales Orders with matching po_no (including delivery_date)
        sales_orders = frappe.get_all(
            "Sales Order",
            filters={"po_no": self.po_number, "docstatus": 1},  # Only submitted SOs
            fields=["name", "customer", "currency", "delivery_date"]
        )

        if not sales_orders:
            frappe.throw(_("No submitted Sales Orders found for PO Number: {0}").format(self.po_number))

        # Populate buyer and currency from first matching SO
        self.buyer = sales_orders[0].customer
        self.currency = sales_orders[0].currency

        # Calculate maximum delivery_date from all Sales Orders
        delivery_dates = [so.delivery_date for so in sales_orders if so.delivery_date]
        if delivery_dates:
            self.delivery_date = max(delivery_dates)
        else:
            self.delivery_date = None  # or frappe.utils.today() if you want default

        # Clear existing items BEFORE adding new ones (prevents duplicates)
        self.set("items", [])

        # Fetch and map items from all matching Sales Orders
        item_count = 0
        for so in sales_orders:
            so_items = frappe.get_all(
                "Sales Order Item",
                filters={"parent": so.name},
                fields=[
                    "name as line_item_name",
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
                pi_item.line_item = item.custom_lineitem or item.line_item_name
                pi_item.item_code = item.item_code
                pi_item.item_name = item.item_name
                pi_item.style = item.custom_style
                pi_item.colour = item.custom_color
                pi_item.size = item.custom_size
                pi_item.qty = int(item.custom_order_qty)  # Ensure integer for Int field
                pi_item.rate = item.rate
                pi_item.amount = item.custom_order_qty * item.rate
                item_count += 1

        return {
            "sales_order_count": len(sales_orders),
            "item_count": item_count,
            "delivery_date": str(self.delivery_date) if self.delivery_date else None
        }
    

    @frappe.whitelist()
    def get_grouped_items_for_print(self):
        """
        Group items by (style, colour, rate) for print format.
        Returns grouped data with size-wise quantities.
        
        Grouping Logic:
        - Items with same (style, colour, rate) are merged into one row
        - Quantities for each size are summed within the group
        - Returns: dict with 'items', 'sizes', 'total_qty', 'total_amount'
        """
        # Group by (style, colour, rate)
        groups = defaultdict(lambda: {
            'style': '',
            'colour': '',
            'rate': 0.0,
            'sizes': defaultdict(int),
            'total_qty': 0,
            'item_name': ''
        })
        
        for item in self.items:
            # Create group key: (style, colour, rate)
            # Round rate to 2 decimals to handle floating point precision
            key = (
                item.style or "",
                item.colour or "",
                round(float(item.rate or 0.0), 2)
            )
            
            # Initialize group if not exists
            if not groups[key]['style']:
                groups[key]['style'] = item.style or ""
                groups[key]['colour'] = item.colour or ""
                groups[key]['rate'] = round(float(item.rate or 0.0), 2)
                groups[key]['item_name'] = item.item_name or ""
            
            # Aggregate quantities by size
            size = item.size or ""
            qty = int(item.qty or 0)
            groups[key]['sizes'][size] += qty
            groups[key]['total_qty'] += qty
        
        # Convert to list and extract unique sizes
        grouped_items = []
        all_sizes = set()
        
        for (style, colour, rate), data in groups.items():
            grouped_items.append({
                'style': style,
                'colour': colour,
                'rate': rate,
                'sizes': dict(data['sizes']),
                'total_qty': data['total_qty'],
                'item_name': data['item_name'],
                'amount': round(data['total_qty'] * rate, 2)
            })
            all_sizes.update(data['sizes'].keys())
        
        # Sort by style, then colour
        grouped_items.sort(key=lambda x: (x['style'], x['colour']))
        
        return {
            'items': grouped_items,
            'sizes': sorted(all_sizes),
            'total_qty': sum(item['total_qty'] for item in grouped_items),
            'total_amount': sum(item['amount'] for item in grouped_items)
        } 