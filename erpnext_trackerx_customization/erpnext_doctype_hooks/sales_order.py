def validate(doc, method):
    pass



def on_submit(doc, method):
    for item in doc.items:
        item.custom_pending_qty_for_work_order = item.qty


