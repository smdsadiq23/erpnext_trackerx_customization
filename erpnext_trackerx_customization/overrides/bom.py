from erpnext.manufacturing.doctype.bom.bom import BOM as BaseBOM
from collections import defaultdict
import frappe
from frappe.utils import flt
from frappe.utils import cint, cstr, flt, today

class CustomBOM(BaseBOM):
    def before_save(self):
        self.calculate_operation_summary()

    def before_submit(self):
        # Optional: in case ERPNext or an app re-triggers costing during submit
        self.calculate_order_method_costs()

    
    def validate_materials(self):
        """Validate raw material entries"""

        # if not self.get("items"):
        #     frappe.throw(_("Raw Materials cannot be blank."))

        check_list = []
        for m in self.get("items"):
            if m.bom_no:
                validate_bom_no(m.item_code, m.bom_no)
            if flt(m.qty) <= 0:
                frappe.throw(_("Quantity required for Item {0} in row {1}").format(m.item_code, m.idx))
            check_list.append(m)


    def calculate_operation_summary(self):
        # Clear existing rows
        self.set("custom_operations_summary", [])

        if not self.operations:
            return

        grouped = {}  # key: (group, method)
        for op in self.operations:
            op_group = getattr(op, "custom_operation_group", None)
            order_method = getattr(op, "custom_order_method", None)
            if not op_group or not order_method:
                continue  # skip if either is not set

            key = (op_group, order_method)
            if key not in grouped:
                grouped[key] = {
                    "operation_group": op_group,
                    "order_method": order_method,
                    "time_in_mins": 0.0,
                    "operating_cost": 0.0,
                }

            grouped[key]["time_in_mins"] += flt(getattr(op, "time_in_mins", 0))
            # use operating_cost (company currency). If you need base, swap to base_operating_cost.
            grouped[key]["operating_cost"] += flt(getattr(op, "operating_cost", 0))

        # Add to child table (optionally sorted by group, then method)
        for _, data in sorted(grouped.items(), key=lambda k: (k[0][0], k[0][1])):
            self.append("custom_operations_summary", {
                "order_method": data["order_method"],
                "operation_group": data["operation_group"],
                "operation_time": data["time_in_mins"],
                "operating_cost": data["operating_cost"],
            })       

    def calculate_cost(self, *args, **kwargs):
        # Step 1: Standard ERPNext costing logic
        super().calculate_cost(*args, **kwargs)

        # Step 2: Custom BOM Item Costing Logic
        self.calculate_custom_table_costs()
        self.calculate_custom_material_costs()


        # Recalculate total_cost after modifying raw_material_cost
        self.total_cost = (
            flt(self.raw_material_cost)
            + flt(self.operating_cost)
            + flt(self.scrap_material_cost)
        )

        self.calculate_order_method_costs()

    def calculate_order_method_costs(self):
        self.set("custom_cost_by_order_method", [])
        if not self.operations:
            return

        # company currency fields
        raw = flt(self.raw_material_cost) or 0
        scrap = flt(self.scrap_material_cost) or 0

        grouped = {}
        for op in self.operations:
            om = op.custom_order_method
            if not om:
                continue
            grouped.setdefault(om, {"order_method": om, "operating_cost": 0})
            grouped[om]["operating_cost"] += flt(op.operating_cost) or 0  # company currency

        for data in grouped.values():
            total_cost = data["operating_cost"] + raw + scrap
            self.append("custom_cost_by_order_method", {
                "omc_order_method": data["order_method"],
                "omc_operating_cost": data["operating_cost"],
                "omc_total_cost": total_cost,
            })         

    def calculate_custom_table_costs(self):
        custom_tables = [
            "custom_fabrics_items",
            "custom_trims_items",
            "custom_accessories_items",
            "custom_labels_items",
            "custom_packing_materials_items"
        ]

        for table in custom_tables:
            for d in self.get(table):
                old_rate = d.rate

                # Optionally fetch rate like standard BOM items
                if not self.bom_creator and getattr(d, "is_stock_item", 1):  # fallback to 1
                    d.rate = self.get_rm_rate(
                        {
                            "company": self.company,
                            "item_code": d.item_code,
                            "bom_no": getattr(d, "bom_no", None),
                            "qty": d.qty,
                            "uom": d.uom,
                            "stock_uom": d.stock_uom,
                            "conversion_factor": getattr(d, "conversion_factor", 1),
                            "sourced_by_supplier": getattr(d, "sourced_by_supplier", 0),
                        }
                    )

                d.base_rate = flt(d.rate) * flt(self.conversion_rate)
                d.amount = flt(d.rate, d.precision("rate")) * flt(d.qty, d.precision("qty"))
                d.base_amount = d.amount * flt(self.conversion_rate)
                d.qty_consumed_per_unit = (
                    flt(getattr(d, "stock_qty", d.qty), d.precision("stock_qty"))
                    / flt(self.quantity, self.precision("quantity"))
                )

    def calculate_custom_material_costs(self):
        size_cost_map = defaultdict(list)

        for item in self.items:
            key = (item.item_code, item.custom_size)
            size_cost_map[key].append(flt(item.amount or 0))

        total_avg = 0
        max_cost = 0
        grouped_items = defaultdict(list)
        all_amount = 0

        for (item_code, size), costs in size_cost_map.items():
            group_cost = sum(costs)
            grouped_items[item_code].append(group_cost)
            all_amount += group_cost

        for item_code, cost_list in grouped_items.items():
            total_avg += sum(cost_list) / len(cost_list)
            max_cost += max(cost_list)

        formula = self.custom_costing_formula or "Sum of all Items"
        if formula == "Average by Sizes":
            self.raw_material_cost = total_avg
        elif formula == "Highest by Sizes":
            self.raw_material_cost = max_cost
        elif formula == "By Size":
            size_selected = self.custom_costing_size
            size_cost = 0
            for item in self.items:
                if item.custom_size == size_selected:
                    size_cost += flt(item.amount or 0)
            self.raw_material_cost = size_cost
        else:
            self.raw_material_cost = all_amount



def validate_bom_no(item, bom_no):
	"""Validate BOM No of sub-contracted items"""
	bom = frappe.get_doc("BOM", bom_no)
	if not bom.is_active:
		frappe.throw(_("BOM {0} must be active").format(bom_no))
	if bom.docstatus != 1:
		if not getattr(frappe.flags, "in_test", False):
			frappe.throw(_("BOM {0} must be submitted").format(bom_no))
	if item:
		rm_item_exists = False
		for d in bom.items:
			if d.item_code.lower() == item.lower():
				rm_item_exists = True
		for d in bom.scrap_items:
			if d.item_code.lower() == item.lower():
				rm_item_exists = True
		if (
			bom.item.lower() == item.lower()
			or bom.item.lower() == cstr(frappe.db.get_value("Item", item, "variant_of")).lower()
		):
			rm_item_exists = True
		if not rm_item_exists:
			frappe.throw(_("BOM {0} does not belong to Item {1}").format(bom_no, item))

