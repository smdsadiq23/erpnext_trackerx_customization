import frappe

def get_context(context):
    """Simple test page for fabric inspection redirection"""
    context.update({
        'title': 'Fabric Inspection Redirection Test',
        'show_sidebar': False
    })
    return context