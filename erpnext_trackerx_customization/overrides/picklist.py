import frappe
from erpnext.stock.doctype.pick_list.pick_list import PickList

class CustomPickList(PickList):
	def before_save(self):
		self.update_status()

		# ✅ Skip this to prevent overwriting locations
		# if not self.pick_manually:
		#     self.set_item_locations()

		if self.get("locations"):
			self.validate_sales_order_percentage()
