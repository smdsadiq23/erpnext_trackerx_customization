import frappe

def get_context(context):
    context.no_cache = 1
    # Add any server-side context if needed
    return context
