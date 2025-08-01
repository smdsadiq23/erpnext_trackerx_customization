__version__ = "0.0.1"

import erpnext.stock.doctype.pick_list.pick_list as pick_list_module
import erpnext_trackerx_customization.patches.pick_list_patch as pick_list_patch

def custom_patch():

    pick_list_module.validate_picked_materials = pick_list_patch.custom_validate_picked_materials

# 👇 This line forces execution on app load
custom_patch()
