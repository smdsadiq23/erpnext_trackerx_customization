import frappe
from erpnext.stock.doctype.pick_list.pick_list import PickList
from erpnext_trackerx_customization.patches.pick_list_patch import custom_validate_picked_materials  # adjust if different path

class CustomPickList(PickList):
    def on_submit(self):
        super().on_submit()
        


    def before_save(self):
        super().update_status()
        # Skip auto-location fill to retain manual ones
        # if not self.pick_manually:
        #     self.set_item_locations()
        if self.get("locations"):
            super().validate_sales_order_percentage()
