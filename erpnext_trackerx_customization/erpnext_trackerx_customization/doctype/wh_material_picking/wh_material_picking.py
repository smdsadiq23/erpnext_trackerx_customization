# Copyright (c) 2025, TrackerX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WhMaterialPicking(Document):
	def validate(self):
		"""Validate the document before saving"""
		self.validate_picked_quantity_against_roll_length()

	def validate_picked_quantity_against_roll_length(self):
		"""Validate that picked_quantity does not exceed roll_length"""
		for row in self.table_roll_details:
			if row.picked_quantity and row.roll_length:
				try:
					# Convert to float for comparison
					picked_qty = float(row.picked_quantity)
					roll_length = float(row.roll_length)

					if picked_qty > roll_length:
						frappe.throw(
							f"Row {row.idx}: Picked Quantity ({picked_qty}) cannot be more than Roll Length ({roll_length}) for Roll Number {row.roll_number}"
						)
				except (ValueError, TypeError):
					# Skip validation if values are not numeric
					pass

	def on_submit(self):
		"""Actions to perform when document is submitted"""
		self.db_set('status', 'In Progress')
		self.create_material_transfer_requests()

	def create_material_transfer_requests(self):
		"""Create Material Transfer Requests for all roll allocations with picked quantities"""
		material_requests = []

		for row in self.table_roll_details:
			if row.target_warehouse and row.picked_quantity and float(row.picked_quantity) > 0:
				# Create Material Request for Stock Transfer
				mr = frappe.new_doc("Material Request")
				mr.material_request_type = "Material Transfer"
				mr.transaction_date = frappe.utils.today()
				mr.schedule_date = frappe.utils.add_days(frappe.utils.today(), 1)  # Required by date
				mr.company = frappe.defaults.get_user_default("Company")
				mr.set_from_warehouse = row.location  # From warehouse (current location)
				mr.remarks = f"Material Transfer for Wh Material Picking: {self.name}, Roll: {row.roll_number}"

				# Get item code from fabricmaterial_details or use a default
				item_code = self.fabricmaterial_details if hasattr(self, 'fabricmaterial_details') and self.fabricmaterial_details else "FABRIC-ROLL"

				# Get item details for UOM information
				item_doc = None
				try:
					if frappe.db.exists("Item", item_code):
						item_doc = frappe.get_doc("Item", item_code)
				except:
					pass

				# Set UOM and conversion factor
				if item_doc:
					uom = item_doc.stock_uom
					stock_uom = item_doc.stock_uom
					conversion_factor = 1.0  # Default conversion factor for same UOM
				else:
					uom = "Meter"  # Default UOM for fabric rolls
					stock_uom = "Meter"
					conversion_factor = 1.0

				# Add item to Material Request
				mr.append("items", {
					"item_code": item_code,
					"qty": float(row.picked_quantity),
					"uom": uom,
					"stock_uom": stock_uom,
					"conversion_factor": conversion_factor,
					"warehouse": row.location,  # From warehouse
					"target_warehouse": row.target_warehouse,  # To warehouse
					"description": f"Roll {row.roll_number} - {row.shade} - Batch {row.batch_number}",
				})

				# Save and submit the Material Request
				mr.insert(ignore_permissions=True)
				mr.submit()

				material_requests.append(mr.name)

				# Update the roll allocation row with the created Material Request
				frappe.db.set_value(
					"Wh Material Picking Roll Allocation",
					row.name,
					"material_request",
					mr.name
				)

		if material_requests:
			frappe.msgprint(
				f"Created Material Transfer Requests: {', '.join(material_requests)}",
				title="Material Transfer Requests Created"
			)

	def on_cancel(self):
		"""Actions to perform when document is cancelled"""
		self.db_set('status', 'Cancelled')
		self.cancel_material_transfer_requests()

	def cancel_material_transfer_requests(self):
		"""Cancel related Material Transfer Requests when document is cancelled"""
		for row in self.table_roll_details:
			if hasattr(row, 'material_request') and row.material_request:
				try:
					mr = frappe.get_doc("Material Request", row.material_request)
					if mr.docstatus == 1:  # If submitted
						mr.cancel()
						frappe.msgprint(f"Cancelled Material Request: {mr.name}")
				except Exception as e:
					frappe.log_error(f"Error cancelling Material Request {row.material_request}: {str(e)}")