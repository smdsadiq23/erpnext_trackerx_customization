# your_app/whitelabel.py
import frappe

APP_NAME   = "CognitionXLogic"
LOGO       = "/assets/erpnext_trackerx_customization/images/logo.png"
FAVICON    = "/assets/erpnext_trackerx_customization/images/logo.png"
BRAND_HTML = "CognitionXLogic"

def apply():
    _system_settings()
    _navbar_settings()
    _website_settings()
    _hide_frappe_help()
    frappe.clear_cache()

def _system_settings():
    ss = frappe.get_single("System Settings")
    # Desk/window title
    if hasattr(ss, "app_name"):
        ss.app_name = APP_NAME
    if hasattr(ss, "otp_issuer_name"):
        ss.app_name = APP_NAME
    ss.save()

    ws = frappe.get_single("Website Settings")
    # Desk/window title
    if hasattr(ws, "app_name"):
        ws.app_name = APP_NAME
    ws.save()

def _navbar_settings():
    ns = frappe.get_single("Navbar Settings")
    # In recent Frappe versions you can set a brand/logo here:
    if hasattr(ns, "app_logo"):
        ns.app_logo = LOGO
    if hasattr(ns, "brand_html"):
        ns.brand_html = BRAND_HTML
    # Remove default Frappe/ERPNext Help links (optional)
    # --- IMPORTANT: DO NOT DELETE STANDARD ROWS ---
    # Instead, mark standard items as hidden if you don't want them shown.
    # This covers common child tables across recent Frappe versions.
    # for childfield in ("navbar_items", "settings_dropdown", "help_dropdown"):
    #     if hasattr(ns, childfield):
    #         rows = ns.get(childfield) or []
    #         for row in rows:
    #             # Most recent child doctypes have either `is_standard` or `standard`
    #             is_standard = getattr(row, "is_standard", None)
    #             if is_standard is None:
    #                 is_standard = getattr(row, "standard", 0)
    #             if is_standard:
    #                 # Ensure there's a 'hidden' flag; if not, skip safely
    #                 if hasattr(row, "hidden"):
    #                     row.hidden = 0


    ns.save()

def _website_settings():
    ws = frappe.get_single("Website Settings")
    if hasattr(ws, "website_logo"):
        ws.website_logo = LOGO
    if hasattr(ws, "brand_html"):
        ws.brand_html = BRAND_HTML
    if hasattr(ws, "favicon"):
        ws.favicon = FAVICON
    # Hide “Powered by …” footer if your version exposes the toggle:
    for fld in ("hide_footer_powered_by", "hide_powered_by"):
        if hasattr(ws, fld):
            setattr(ws, fld, 1)
    ws.save()

def _hide_frappe_help():
    # Optional: prune desk help menu items if any customizations added them
    try:
        ns = frappe.get_single("Navbar Settings")
        ns.help_dropdown = []
        ns.save()
    except Exception:
        pass
