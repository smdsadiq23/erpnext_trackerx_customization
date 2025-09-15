from erpnext.manufacturing.doctype.bom.bom import BOM as BaseBOM
from collections import defaultdict
import frappe
from frappe.utils import flt

class CustomBOM(BaseBOM):
    def before_save(self):
        self.calculate_operation_summary()
        super().before_save()

    def calculate_operation_summary(self):
        # Clear existing rows
        self.set("custom_operations_summary", [])

        if not self.operations:
            return

        grouped = {}
        for op in self.operations:
            op_group = op.custom_operation_group  # ← Updated field name
            if not op_group:
                continue  # skip if not set

            if op_group not in grouped:
                grouped[op_group] = {
                    "operation_group": op_group,      # ← Updated field name
                    "time_in_mins": 0,
                    "operating_cost": 0
                }
            grouped[op_group]["time_in_mins"] += op.time_in_mins or 0
            grouped[op_group]["operating_cost"] += op.operating_cost or 0

        # Add to child table
        for data in grouped.values():
            self.append("custom_operations_summary", {
                "operation_group": data["operation_group"],    # ← Updated
                "operation_time": data["time_in_mins"],
                "operating_cost": data["operating_cost"]
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
