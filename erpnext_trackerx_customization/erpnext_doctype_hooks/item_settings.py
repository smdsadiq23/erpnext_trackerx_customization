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
    v = _clean(v)
    v = re.sub(r"[^A-Za-z0-9]+", "", v)
    return v or "X"

# def _get_style_group(doc) -> str:
#     style_master = getattr(doc, "custom_style_master", None) or doc.get("custom_style_master")
#     if not style_master:
#         return ""
#     try:
#         sm = frappe.get_cached_doc("Style Master", style_master)
#         return _clean(getattr(sm, "style_group", "") or sm.name)
#     except Exception:
#         return ""

def _get_doc_value(doc, fieldname: str) -> str:
    return _clean(getattr(doc, fieldname, None) or doc.get(fieldname))

def _build_token_rules(settings) -> dict:
    """
    token_rules[token_name] = {
      source_field, transform_type, param_1, uppercase
    }
    """
    out = {}
    for r in (getattr(settings, "table_item_code_token_rule", None) or []):
        token_name = _clean(getattr(r, "token_name", ""))
        if not token_name:
            continue
        out[token_name] = {
            "source_field": _clean(getattr(r, "source_field", "")),
            "transform_type": _clean(getattr(r, "transform_type", "")) or "Direct",
            "param_1": _clean(getattr(r, "param_1", "")),
            "uppercase": int(getattr(r, "uppercase", 0)),
        }
    return out

def _build_value_map(settings) -> dict:
    """
    value_map[token_name][source_value] = shortcode
    """
    out = {}
    for m in (getattr(settings, "table_item_code_value_map", None) or []):
        token_name = _clean(getattr(m, "token_name", ""))
        source_value = _clean(getattr(m, "source_value", ""))
        shortcode = _clean(getattr(m, "shortcode", ""))
        if not (token_name and source_value and shortcode):
            continue
        out.setdefault(token_name, {})[source_value] = shortcode
    return out

def _apply_transform(raw: str, transform_type: str, param_1: str, uppercase: int, value_map_for_token: dict) -> str:
    raw = _clean(raw)

    if transform_type == "Direct":
        val = raw

    elif transform_type == "Slice":
        try:
            n = int(param_1 or 0)
        except Exception:
            n = 0
        val = raw[:n] if (raw and n > 0) else ""

    elif transform_type == "Initials":
        if not raw:
            val = ""
        else:
            words = raw.split()
            val = "".join(w[0] for w in words if w)

    elif transform_type == "Regex":
        if not raw or not param_1:
            val = ""
        else:
            m = re.search(param_1, raw)
            if not m:
                val = ""
            else:
                val = m.group(1) if m.groups() else m.group(0)

    elif transform_type == "Lookup":
        # ✅ FIX:
        # If mapped -> shortcode
        # If not mapped -> fallback to first N chars (param_1), else blank
        if raw and raw in value_map_for_token:
            val = value_map_for_token[raw]
        else:
            try:
                n = int(param_1 or 0)
            except Exception:
                n = 0
            val = raw[:n] if (raw and n > 0) else ""

    elif transform_type == "LinkField":
        # param_1 format: "Doctype:fieldname"  e.g. "Style Master:style_group"
        if not raw or not param_1 or ":" not in param_1:
            val = ""
        else:
            dt, fieldname = [x.strip() for x in param_1.split(":", 1)]
            try:
                val = _clean(frappe.get_cached_value(dt, raw, fieldname))
            except Exception:
                val = ""            

    else:
        val = raw

    val = _clean(val)
    if uppercase and val:
        val = val.upper()

    return val

def _resolve_token(doc, token: str, prefix: str, settings, token_rules: dict, value_map: dict) -> str:
    # Built-ins
    if token == "prefix":
        return _clean(prefix)

    # # Derived
    # if token == "style_group":
    #     return _get_style_group(doc)

    # Generic suffix slicing still supported: item_name_3, custom_field_5, etc.
    m = re.match(r"^(.+)_([0-9]+)$", token)
    if m:
        base_field = m.group(1)
        n = int(m.group(2))
        base_val = _get_doc_value(doc, base_field)
        return _clean(base_val[:n]).upper() if base_val and n > 0 else ""

    # Settings-driven token rule
    if token in token_rules:
        rule = token_rules[token]
        source_field = rule.get("source_field") or token
        raw = _get_doc_value(doc, source_field)
        transform_type = rule.get("transform_type") or "Direct"
        param_1 = rule.get("param_1") or ""
        uppercase = int(rule.get("uppercase") or 0)
        vm = value_map.get(token, {})
        return _apply_transform(raw, transform_type, param_1, uppercase, vm)

    # Default: read directly from doc
    return _get_doc_value(doc, token)

def _render_pattern(doc, pattern: str, prefix: str, settings, token_rules: dict, value_map: dict) -> str:
    def repl(m):
        token = m.group(1)
        return _resolve_token(doc, token, prefix, settings, token_rules, value_map)

    return TOKEN_RE.sub(repl, pattern or "")

def generate_item_code_from_settings(doc):
    settings = frappe.get_single("Item Settings")
    if not int(getattr(settings, "enable_custom_item_code", 0)):
        return None

    master = _clean(getattr(doc, "custom_select_master", None) or doc.get("custom_select_master"))
    if not master:
        return None

    token_rules = _build_token_rules(settings)
    value_map = _build_value_map(settings)

    rule = None
    for r in (getattr(settings, "table_item_code_rule", None) or []):
        if _clean(getattr(r, "master", "")) == master:
            rule = r
            break
    if not rule:
        return None

    prefix = _clean(getattr(rule, "prefix", "")) or master
    sep = "-"  # ignore separator for now
    pattern = _clean(getattr(rule, "pattern", ""))

    base = _clean(_render_pattern(doc, pattern, prefix, settings, token_rules, value_map))
    base = re.sub(rf"{re.escape(sep)}+", sep, base).strip(sep).strip()
    if not base:
        return None

    # ✅ sequence is optional
    seq_digits_raw = getattr(rule, "sequence_digits", None)

    try:
        seq_digits = int(seq_digits_raw) if seq_digits_raw not in (None, "", 0) else 0
    except Exception:
        seq_digits = 0

    if seq_digits > 0:
        series_key = f"{_slug(prefix)}{sep}{_slug(master)}{sep}"
        seq = getseries(series_key, seq_digits)
        return f"{base}{sep}{seq}"

    return base
