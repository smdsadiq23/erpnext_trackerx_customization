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
        Also validates PO number availability
        """
        self._validate_items_table()
        self._validate_required_fields_in_items()
        self._validate_po_availability()
        self._calculate_totals()
    
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
    
    def _validate_po_availability(self):
        """Validate PO number is not already used in another submitted Proforma Invoice"""
        if not self.po_number:
            frappe.throw(_("PO Number is required"))
        
        # Check if already used in another submitted Proforma Invoice
        existing = frappe.db.exists("Proforma Invoice", {
            "po_number": self.po_number,
            "docstatus": 1,
            "name": ("!=", self.name) if self.name else None
        })
        
        if existing:
            frappe.throw(
                _("PO Number '{0}' is already used in another submitted Proforma Invoice: {1}").format(
                    self.po_number, existing
                ),
                title=_("Duplicate PO Number")
            )
    
    def _calculate_totals(self):
        """Calculate total taxes and grand total"""
        # Calculate total from items
        item_total = sum(flt(item.amount) for item in self.items)
        
        # Calculate total taxes
        tax_total = sum(flt(tax.tax_amount) for tax in self.taxes)
        
        self.total_taxes_and_charges = tax_total
        self.grand_total = item_total + tax_total
    
    @frappe.whitelist()
    def fetch_items_from_sales_orders(self):
        """
        Fetch items from Sales Orders matching the PO Number (po_no field)
        and populate the Proforma Invoice Item child table.
        Sets delivery_date as the maximum delivery date from all matching Sales Orders.
        Also fetches and consolidates taxes from Sales Orders.
        """
        if not self.po_number:
            frappe.throw(_("Please select a PO Number first"))

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
            self.delivery_date = None

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

        # Fetch and consolidate taxes from Sales Orders
        tax_count = self._fetch_and_consolidate_taxes(sales_orders)

        # Calculate totals
        self._calculate_totals()

        return {
            "sales_order_count": len(sales_orders),
            "item_count": item_count,
            "tax_count": tax_count,
            "delivery_date": str(self.delivery_date) if self.delivery_date else None
        }
    
    def _fetch_and_consolidate_taxes(self, sales_orders):
        """
        Fetch taxes from all Sales Orders and consolidate them
        Consolidation logic: Group by (account_head, charge_type, rate) and sum tax amounts
        """
        # Clear existing taxes
        self.set("taxes", [])
        
        # Dictionary to consolidate taxes: key = (account_head, charge_type, rate)
        tax_consolidation = defaultdict(lambda: {
            'charge_type': '',
            'account_head': '',
            'description': '',
            'rate': 0.0,
            'tax_amount': 0.0
        })
        
        # Fetch taxes from all Sales Orders
        for so in sales_orders:
            so_taxes = frappe.get_all(
                "Sales Taxes and Charges",
                filters={"parent": so.name},
                fields=[
                    "charge_type",
                    "account_head",
                    "description",
                    "rate",
                    "tax_amount"
                ],
                order_by="idx"
            )
            
            for tax in so_taxes:
                # Create consolidation key
                key = (
                    tax.account_head or "",
                    tax.charge_type or "",
                    round(float(tax.rate or 0.0), 2)
                )
                
                # Initialize or update consolidated tax
                if not tax_consolidation[key]['account_head']:
                    tax_consolidation[key]['charge_type'] = tax.charge_type or ""
                    tax_consolidation[key]['account_head'] = tax.account_head or ""
                    tax_consolidation[key]['description'] = tax.description or ""
                    tax_consolidation[key]['rate'] = round(float(tax.rate or 0.0), 2)
                
                # Sum tax amounts
                tax_consolidation[key]['tax_amount'] += float(tax.tax_amount or 0.0)
        
        # Add consolidated taxes to Proforma Invoice
        tax_count = 0
        for (account_head, charge_type, rate), tax_data in sorted(tax_consolidation.items()):
            pi_tax = self.append("taxes", {})
            pi_tax.charge_type = tax_data['charge_type']
            pi_tax.account_head = tax_data['account_head']
            pi_tax.description = tax_data['description']
            pi_tax.rate = tax_data['rate']
            pi_tax.tax_amount = round(tax_data['tax_amount'], 2)
            tax_count += 1
        
        return tax_count
    
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


def flt(value, precision=2):
    """Convert to float with precision"""
    try:
        return round(float(value or 0), precision)
    except (ValueError, TypeError):
        return 0.0


@frappe.whitelist()
def get_available_po_numbers():
    """
    Get unique PO numbers from submitted Sales Orders 
    that don't have a submitted Proforma Invoice
    Returns: List of available PO numbers
    """
    # Get all PO numbers used in submitted Proforma Invoices
    used_po_numbers = frappe.get_all(
        "Proforma Invoice",
        filters={"docstatus": 1},
        fields=["po_number"],
        pluck="po_number"
    )
    
    # Filter out empty values and make unique set
    used_po_set = set([po for po in used_po_numbers if po])
    
    # Build SQL query with dynamic IN clause
    if used_po_set:
        placeholders = ",".join(["%s"] * len(used_po_set))
        query = f"""
            SELECT DISTINCT po_no
            FROM `tabSales Order`
            WHERE docstatus = 1
              AND po_no IS NOT NULL
              AND po_no != ''
              AND po_no NOT IN ({placeholders})
            ORDER BY po_no DESC
        """
        results = frappe.db.sql(query, list(used_po_set), as_dict=False)
    else:
        query = """
            SELECT DISTINCT po_no
            FROM `tabSales Order`
            WHERE docstatus = 1
              AND po_no IS NOT NULL
              AND po_no != ''
            ORDER BY po_no DESC
        """
        results = frappe.db.sql(query, as_dict=False)
    
    # Flatten and return list
    return [row[0] for row in results if row[0]]
