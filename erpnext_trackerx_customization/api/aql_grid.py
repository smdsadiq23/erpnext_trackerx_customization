# erpnext_trackerx_customization/api.py
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Tuple

import frappe
from frappe import _
from erpnext_trackerx_customization.utils.constants import get_constants


# ---------------------------
# Helpers: parsing & casting
# ---------------------------

LOT_RANGE_PATTERNS = [
    r"^\s*(\d+)\s*[-–—]\s*(\d+)\s*$",      # 1-8 or 1–8
    r"^\s*(\d+)\s*(?:to|TO)\s*(\d+)\s*$",  # 1 to 8
    r"^\s*(>=|≤|<=|>|<)\s*(\d+)\s*$",      # >= 500, < 5
    r"^\s*(\d+)\s*\+\s*$",                 # 500+
]

def _parse_lot_range(range_str: str | None) -> Tuple[int, int]:
    s = (range_str or "").strip()
    if not s:
        return (0, 0)
    for pat in LOT_RANGE_PATTERNS:
        m = re.match(pat, s)
        if not m:
            continue
        # explicit lo-hi
        if len(m.groups()) == 2 and m.groups()[0].isdigit() and m.groups()[1].isdigit():
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo > hi:
                lo, hi = hi, lo
            return (lo, hi)
        # operator + value
        if len(m.groups()) == 2 and not m.groups()[0].isdigit():
            op, val = m.group(1), int(m.group(2))
            if op in (">=",):
                return (val, 10**12)
            if op in (">",):
                return (val + 1, 10**12)
            if op in ("<",):
                return (0, val - 1 if val > 0 else 0)
            if op in ("<=", "≤"):
                return (0, val)
        # 500+
        if len(m.groups()) == 1 and m.group(1).isdigit():
            return (int(m.group(1)), 10**12)
    # salvage numbers if possible
    nums = re.findall(r"\d+", s)
    if len(nums) >= 2:
        lo, hi = int(nums[0]), int(nums[1])
        if lo > hi:
            lo, hi = hi, lo
        return (lo, hi)
    if len(nums) == 1:
        val = int(nums[0])
        return (val, val)
    return (0, 0)

def _to_decimal(txt: Any, default: Decimal = Decimal("0")) -> Decimal:
    if txt is None:
        return default
    try:
        return Decimal(str(txt).strip())
    except (InvalidOperation, ValueError):
        return default

def _has_column(doctype: str, column: str) -> bool:
    try:
        return frappe.db.has_column(doctype, column)
    except Exception:
        return False


# ---------------------------
# Public API
# ---------------------------

@frappe.whitelist()
def get_item_constants():
    return get_constants()


@frappe.whitelist()
def update_aql_table_entries(changes):
    """
    Batch update multiple AQL Table entries.
    Accepts JSON string or list of dicts:
    [{name, acceptance_number, rejection_number}, ...]
    """
    try:
        if isinstance(changes, str):
            changes = json.loads(changes)
        if not isinstance(changes, list):
            frappe.throw(_("Changes must be a list or JSON list"))

        updated_count = 0
        for row in changes:
            if not all(k in row for k in ("name", "acceptance_number", "rejection_number")):
                continue
            name = row["name"]
            a = int(row["acceptance_number"])
            r = int(row["rejection_number"])
            frappe.db.set_value("AQL Table", name, {"acceptance_number": a, "rejection_number": r})
            updated_count += 1

        frappe.db.commit()
        return {
            "success": True,
            "updated_count": updated_count,
            "message": _("Successfully updated {0} AQL table entries").format(updated_count),
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error updating AQL table entries: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)  # remove allow_guest if this page is behind login
def get_aql_grid_data(regime: str = "Normal", level: str = "II"):
    """
    Returns grid data keyed by sample_code_letter with robust numeric sorting.

    Response:
    {
      success: True,
      aql_grid_data: {
        "J": {
          sample_size: 80,
          lot_size_range: "151 - 280",
          values: {
            "0.010": { acceptance, rejection, doc_name },
            ...
          }
        },
        ...
      },
      aql_standards: [{ aql_value, description }, ...],
      regime, level
    }
    """
    try:
        # standards (for columns), sorted by decimal
        standards = frappe.get_all(
            "AQL Standard",
            fields=["aql_value", "description", "name"],
            filters={"is_active": 1},
        )
        for s in standards:
            s["_aql_decimal"] = _to_decimal(s.get("aql_value"))
        standards.sort(key=lambda x: x["_aql_decimal"])

        # base rows (we sort in Python to avoid fragile SQL)
        rows = frappe.get_all(
            "AQL Table",
            fields=[
                "name",
                "inspection_level",
                "inspection_regime",
                "lot_size_range",
                "sample_code_letter",
                "sample_size",
                "aql_value",
                "acceptance_number",
                "rejection_number",
                "is_active",
            ],
            filters={"inspection_regime": regime, "inspection_level": level, "is_active": 1},
        )

        # sort by (lot_from, lot_to, code, decimal aql)
        def _sort_key(r):
            lo, hi = _parse_lot_range(r.get("lot_size_range"))
            aql_dec = _to_decimal(r.get("aql_value"))
            return (lo, hi, str(r.get("sample_code_letter") or ""), aql_dec)

        rows.sort(key=_sort_key)

        # build grid
        grid: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            code = r["sample_code_letter"]
            aql_val = str(r["aql_value"])
            if code not in grid:
                grid[code] = {
                    "sample_size": r.get("sample_size"),
                    "lot_size_range": r.get("lot_size_range"),
                    "values": {},
                }
            grid[code]["values"][aql_val] = {
                "acceptance": r.get("acceptance_number"),
                "rejection": r.get("rejection_number"),
                "doc_name": r.get("name"),
            }

        return {
            "success": True,
            "aql_grid_data": grid,
            "aql_standards": [{"aql_value": s["aql_value"], "description": s.get("description")} for s in standards],
            "regime": regime,
            "level": level,
        }

    except Exception as e:
        frappe.log_error(f"Error getting AQL grid data: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_aql_rows_sorted(regime: str = "Normal", level: str = "II"):
    """
    Optional: flat list with helper keys (_lot_from/_lot_to) for custom clients.
    """
    try:
        rows = frappe.get_all(
            "AQL Table",
            fields=[
                "name",
                "inspection_level",
                "inspection_regime",
                "lot_size_range",
                "sample_code_letter",
                "sample_size",
                "aql_value",
                "acceptance_number",
                "rejection_number",
                "is_active",
            ],
            filters={"inspection_regime": regime, "inspection_level": level, "is_active": 1},
        )
        out = []
        for r in rows:
            lo, hi = _parse_lot_range(r.get("lot_size_range"))
            aql_dec = _to_decimal(r.get("aql_value"))
            r["_lot_from"] = lo
            r["_lot_to"] = hi
            r["_aql_decimal"] = aql_dec
            out.append(r)

        out.sort(key=lambda r: (r["_lot_from"], r["_lot_to"], str(r.get("sample_code_letter") or ""), r["_aql_decimal"]))
        for r in out:
            r.pop("_aql_decimal", None)

        return {"success": True, "rows": out, "regime": regime, "level": level}
    except Exception as e:
        frappe.log_error(f"Error getting sorted AQL rows: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def backfill_lot_bounds_if_columns_exist():
    """
    Optional: if you later add columns 'lot_from' & 'lot_to' to AQL Table, this fills them.
    """
    try:
        if not (_has_column("AQL Table", "lot_from") and _has_column("AQL Table", "lot_to")):
            return {"success": True, "updated": 0, "message": "Columns lot_from/lot_to not present; skipped."}

        names = frappe.get_all("AQL Table", pluck="name")
        updated = 0
        for name in names:
            rng = frappe.db.get_value("AQL Table", name, "lot_size_range")
            lo, hi = _parse_lot_range(rng)
            frappe.db.set_value("AQL Table", name, {"lot_from": lo, "lot_to": hi})
            updated += 1

        frappe.db.commit()
        return {"success": True, "updated": updated}
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error backfilling lot bounds: {str(e)}")
        return {"success": False, "error": str(e)}
