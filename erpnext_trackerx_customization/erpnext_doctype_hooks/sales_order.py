def validate(doc, method):
    copy_qty_pending_qty(doc, method)



def on_submit(doc, method):
    pass
    

def copy_qty_pending_qty(doc, method):
    for item in doc.items:
        item.custom_pending_qty_for_work_order = item.qty



