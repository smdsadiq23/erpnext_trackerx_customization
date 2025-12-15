import re
import frappe
from frappe.model.naming import getseries

TOKEN_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")

def _clean(v) -> str:
    v = (v or "")
    v = str(v).strip()
    v = re.sub(r"\s+", " ", v)
    return v

def _slug(v: str) -> str:
    # safe for series key
    v = _clean(v)
    v = re.sub(r"[^A-Za-z0-9]+", "", v)
    return v or "X"

def _get_style_group(doc) -> str:
    # derived token: {style_group}
    style_master = getattr(doc, "custom_style_master", None) or doc.get("custom_style_master")
    if not style_master:
        return ""
    try:
        sm = frappe.get_cached_doc("Style Master", style_master)
        return _clean(getattr(sm, "style_group", "") or sm.name)
    except Exception:
        return ""

def _resolve_token(doc, token: str, prefix: str) -> str:
    # 1) built-in token
    if token == "prefix":
        return _clean(prefix)

    # 2) derived token(s)
    if token == "style_group":
        return _get_style_group(doc)

    # 3) generic suffix slicing: item_name_3 => first 3 chars of item_name (UPPERCASE)
    m = re.match(r"^(.+)_([0-9]+)$", token)
    if m:
        base_field = m.group(1)
        n = int(m.group(2))
        base_val = _clean(getattr(doc, base_field, None) or doc.get(base_field))
        if base_val and n > 0:
            return _clean(base_val[:n]).upper()
        return ""

    # 4) default: read from doc field
    return _clean(getattr(doc, token, None) or doc.get(token))

def _render_pattern(doc, pattern: str, prefix: str) -> str:
    def repl(m):
        token = m.group(1)
        return _resolve_token(doc, token, prefix)

    return TOKEN_RE.sub(repl, pattern or "")

def generate_item_code_from_settings(doc):
    settings = frappe.get_single("Item Settings")
    if not int(getattr(settings, "enable_custom_item_code", 0)):
        return None

    master = _clean(getattr(doc, "custom_select_master", None) or doc.get("custom_select_master"))
    if not master:
        return None

    # find matching rule
    rule = None
    for r in (getattr(settings, "table_item_code_rule", None) or []):
        if _clean(getattr(r, "master", "")) == master:
            rule = r
            break
    if not rule:
        return None

    prefix = _clean(getattr(rule, "prefix", "")) or master
    sep = _clean(getattr(rule, "separator", "")) or _clean(getattr(settings, "separator", "")) or "-"
    pattern = _clean(getattr(rule, "pattern", ""))

    base = _clean(_render_pattern(doc, pattern, prefix))

    # Clean up accidental double separators (optional)
    base = re.sub(rf"{re.escape(sep)}+", sep, base).strip(sep).strip()
    if not base:
        return None

    digits = int(getattr(rule, "sequence_digits", 0) or getattr(settings, "sequence_digits", 6) or 6)

    # per-rule series key (prevents collisions)
    series_key = f"{_slug(prefix)}{sep}{_slug(master)}{sep}"   # e.g. "FG-FinishedGoods-"
    seq = getseries(series_key, digits)

    return f"{base}{sep}{seq}"
