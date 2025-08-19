# your_app_name/your_module/api.py
import frappe

@frappe.whitelist()
def get_bom_required_items(bom_no, production_qty, source_warehouse):
    """
    Fetch BOM items and calculate required quantities
    """
    try:
        production_qty = float(production_qty)
        
        bom_items = frappe.get_all('BOM Item', 
            filters={'parent': bom_no},
            fields=['item_code', 'qty', 'uom', 'rate', 'amount', 'stock_qty', 'original_item']
        )
        
        required_items = []
        for bom_item in bom_items:
            required_items.append({
                'item_code': bom_item.item_code,
                'required_qty': bom_item.qty * production_qty,
                'stock_qty': bom_item.stock_qty * production_qty,
                'uom': bom_item.uom,
                'rate': bom_item.rate,
                'amount': bom_item.amount * production_qty,
                'source_warehouse': source_warehouse
            })
        
        return required_items
        
    except Exception as e:
        frappe.throw(f"Error fetching BOM items: {str(e)}")