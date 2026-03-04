// Copyright (c) 2025, CognitionX and contributors
// For license information, please see license.txt

// ==============================
// Factory OCR Client Script (Full)
// - Single level approval
// - Only "Factory Manager" sees Approval Section + HTML card (ONLY while Pending)
// - Other users see normal doctype (no approval UI)
// - After Approved/Rejected => ONLY normal doctype for everyone
// - With Replenishment is selected ONLY inside HTML card (field should be Hidden in doctype)
// - Status auto set to "Pending for Approval" on first save
// - Pending/Approved/Rejected => readonly + no save for everyone
// ==============================

window.factory_ocr_script = window.factory_ocr_script || { executed_for: new Set() };

frappe.ui.form.on('Factory OCR', {
  onload: function(frm) {
    set_ocn_query(frm);

    if (frm.doc.__islocal) {
      hide_factory_approval_ui(frm, { hide_section: true });
    }
  },

  before_save: function(frm) {
    if (!frm.doc.status || frm.doc.status === 'Draft') {
      frm.set_value('status', 'Pending for Approval');
    }
  },

  buyer: function(frm) {
    if (frm.doc.ocn) {
      frappe.db.get_value('Sales Order', frm.doc.ocn, ['customer', 'docstatus'])
        .then(r => {
          const so = r.message;
          if (!so || so.customer !== frm.doc.buyer || so.docstatus != 1) {
            frm.set_value('ocn', '');
          }
        });
    }
    set_ocn_query(frm);
  },

  ocn: function(frm) {
    if (frm.doc.ocn) {
      frappe.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.factory_ocr.factory_ocr.fetch_sales_order_items_for_factory_ocr',
        args: { sales_order: frm.doc.ocn },
        callback: function(r) {
          frm.clear_table('table_ocn_details');

          if (r.message && r.message.length) {
            r.message.forEach(row => {
              let child = frm.add_child('table_ocn_details');
              child.style = row.style || '';
              child.line_item = row.lineitem || '';
              child.colour = row.colour || '';
              child.order_quantity = row.order_quantity;
              child.cut_quantity = row.cut_quantity || 0;
              child.scan_quantity = row.scan_quantity || 0;
              child.ship_quantity = row.ship_quantity || 0;
              child.rejected_garments = row.rejected_garments || 0;
              child.cut_to_ship_diff = 0;
              child.cut_to_ship = 0;
            });
          }

          calculate_totals(frm);
          frm.refresh_field('table_ocn_details');
        }
      });
    } else {
      frm.clear_table('table_ocn_details');
      frm.refresh_field('table_ocn_details');
      clear_totals(frm);
    }
  },

  refresh: function(frm) {
    if (!frm.doc || !frm.doc.name) return;

    // ✅ Same guard as Can Cut — prevent duplicate execution polluting model cache
    const docKey = `Factory OCR:${frm.doc.name}`;
    if (!frm.doc.__islocal && window.factory_ocr_script.executed_for.has(docKey)) {
      return;
    }
    if (!frm.doc.__islocal) {
      window.factory_ocr_script.executed_for.add(docKey);
    }    

    const status = frm.doc.status || 'Draft';
    const is_pending = (status === 'Pending for Approval');
    const is_done = (status === 'Approved' || status === 'Rejected');
    const is_factory_manager = frappe.user.has_role('Factory Manager');

    // ✅ Set custom status indicator in form header (mirrors Can Cut pattern)
    if (!frm.doc.__islocal) {
      frm.page.clear_indicator();

      if (status === 'Pending for Approval') {
        frm.page.set_indicator(__('Pending for Approval'), 'orange');
      } else if (status === 'Approved') {
        frm.page.set_indicator(__('Approved'), 'green');
      } else if (status === 'Rejected') {
        frm.page.set_indicator(__('Rejected'), 'red');
      } else if (frm.doc.docstatus === 2) {
        frm.page.set_indicator(__('Cancelled'), 'red');
      }
    }

    // Default: show normal doctype
    show_all_sections(frm);

    // RULE: Pending/Approved/Rejected => readonly + disable save for everyone
    if (!frm.doc.__islocal && (is_pending || is_done)) {
      set_form_readonly(frm, true);
      frm.disable_save();
    } else {
      set_form_readonly(frm, false);
      frm.enable_save();
    }

    // ✅ Approved/Rejected => normal doctype for everyone,
    // BUT do NOT hide the whole approval section because approver_remarks may be inside it.
    if (is_done) {
      // Hide only the HTML card; keep section visible
      hide_factory_approval_ui(frm, { hide_section: false });

      // Ensure approver remarks is visible in the form (if it was hidden via Customize Form)
      try {
        frm.set_df_property('approver_remarks', 'hidden', 0);
        frm.refresh_field('approver_remarks');
      } catch (e) {}

      // requester_remarks should remain visible (just in case)
      try {
        frm.set_df_property('requester_remarks', 'hidden', 0);
        frm.refresh_field('requester_remarks');
      } catch (e) {}

      // With replenishment stays hidden in doctype always
      try {
        frm.set_df_property('with_replenishment', 'hidden', 1);
        frm.refresh_field('with_replenishment');
      } catch (e) {}

      return;
    }

    // ✅ Pending:
    // - Factory Manager sees approval UI (only approval section, with card)
    // - Others see normal form readonly, no approval UI
    if (is_pending) {
      if (!is_factory_manager) {
        hide_factory_approval_ui(frm, { hide_section: true });
        return;
      }

      // Factory manager pending approval
      if (frm.fields_dict.approval_section) {
        frm.set_df_property('approval_section', 'hidden', false);
        frm.refresh_field('approval_section');
      }

      // Hide the doctype fields, show only approval section (card)
      hide_all_sections_except(frm, ['approval_section']);

      // In pending, approver_remarks should NOT show as a normal field (only inside card)
      try {
        frm.set_df_property('approver_remarks', 'hidden', 1);
        frm.refresh_field('approver_remarks');
      } catch (e) {}

      // With replenishment should be hidden in doctype
      try {
        frm.set_df_property('with_replenishment', 'hidden', 1);
        frm.refresh_field('with_replenishment');
      } catch (e) {}

      render_factory_ocr_card(frm, { readonly: false });
      return;
    }

    // ✅ Draft (or empty): normal doctype, no approval card
    hide_factory_approval_ui(frm, { hide_section: true });

    // Keep with_replenishment hidden in doctype always
    try {
      frm.set_df_property('with_replenishment', 'hidden', 1);
      frm.refresh_field('with_replenishment');
    } catch (e) {}
  }
});

// ==============================
// List View — status colour badges
// ==============================
frappe.listview_settings['Factory OCR'] = {
  get_indicator: function(doc) {
    const map = {
      'Pending for Approval': ['Pending for Approval', 'orange', 'status,=,Pending for Approval'],
      'Approved':             ['Approved',             'green',  'status,=,Approved'],
      'Rejected':             ['Rejected',             'red',    'status,=,Rejected'],
    };
    return map[doc.status] || ['Draft', 'gray', 'status,=,Draft'];
  },
  // ✅ Add status to list view columns so the badge renders
  add_fields: ['status'],
};

// ==============================
// Child Doctype Triggers
// ==============================
frappe.ui.form.on('Factory OCR Item', {
  order_quantity: function(frm, cdt, cdn) {
    recalculate_order_to_ship_field(cdt, cdn);
    calculate_totals(frm);
  },
  cut_quantity: function(frm, cdt, cdn) {
    recalculate_cut_to_ship_fields(cdt, cdn);
    calculate_totals(frm);
  },
  scan_quantity: function(frm) {
    calculate_totals(frm);
  },
  pack_quantity: function(frm) {
    calculate_totals(frm);
  },
  ship_quantity: function(frm, cdt, cdn) {
    recalculate_order_to_ship_field(cdt, cdn);
    recalculate_cut_to_ship_fields(cdt, cdn);
    calculate_totals(frm);
  },
  good_garments: function(frm) {
    calculate_totals(frm);
  },
  rejected_garments: function(frm) {
    calculate_totals(frm);
  },
  rejected_panels: function(frm) {
    calculate_totals(frm);
  },
  missing_units: function(frm){
    calculate_totals(frm);
  },
  table_ocn_details_add: function(frm) {
    calculate_totals(frm);
  },
  table_ocn_details_remove: function(frm) {
    calculate_totals(frm);
  }
});

// ==============================
// Query setup
// ==============================
function set_ocn_query(frm) {
  frm.set_query('ocn', function() {
    return {
      query: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.factory_ocr.factory_ocr.sales_order_query_for_factory_ocr',
      filters: { customer: frm.doc.buyer }
    };
  });
}

// ==============================
// Row calculations
// ==============================
function recalculate_order_to_ship_field(cdt, cdn) {
  let row = frappe.get_doc(cdt, cdn);
  let order = flt(row.order_quantity);
  let ship = flt(row.ship_quantity);

  let ratio = order > 0 ? (ship / order) * 100 : 0;
  frappe.model.set_value(cdt, cdn, 'order_to_ship', ratio);
}

function recalculate_cut_to_ship_fields(cdt, cdn) {
  let row = frappe.get_doc(cdt, cdn);
  let cut = flt(row.cut_quantity);
  let ship = flt(row.ship_quantity);

  let diff = ship - cut;
  let ratio = cut > 0 ? (ship / cut) * 100 : 0;

  frappe.model.set_value(cdt, cdn, 'cut_to_ship_diff', diff);
  frappe.model.set_value(cdt, cdn, 'cut_to_ship', ratio);
}

// ==============================
// Totals
// ==============================
function calculate_totals(frm) {
  let total_order_qty = 0;
  let total_cut_qty = 0;
  let total_scan_qty = 0;
  let total_pack_qty = 0;
  let total_ship_qty = 0;
  let total_good_garments = 0;
  let total_rejected_garments = 0;
  let total_rejected_panels = 0;
  let total_missing_units = 0;

  (frm.doc.table_ocn_details || []).forEach(row => {
    total_order_qty += row.order_quantity || 0;
    total_cut_qty += row.cut_quantity || 0;
    total_scan_qty += row.scan_quantity || 0;
    total_pack_qty += row.pack_quantity || 0;
    total_ship_qty += row.ship_quantity || 0;
    total_good_garments += row.good_garments || 0;
    total_rejected_garments += row.rejected_garments || 0;
    total_rejected_panels += row.rejected_panels || 0;
    total_missing_units += row.missing_units || 0;
  });

  frm.set_value('total_order_qty', total_order_qty);
  frm.set_value('total_cut_qty', total_cut_qty);
  frm.set_value('total_scan_qty', total_scan_qty);
  frm.set_value('total_pack_qty', total_pack_qty);
  frm.set_value('total_ship_qty', total_ship_qty);
  frm.set_value('total_good_garments', total_good_garments);
  frm.set_value('total_rejected_garments', total_rejected_garments);
  frm.set_value('total_rejected_panels', total_rejected_panels);
  frm.set_value('total_missing_units', total_missing_units);

  let cumulative_total = total_ship_qty + total_good_garments + total_rejected_garments + total_rejected_panels + total_missing_units;
  frm.set_value('cumulative_total', cumulative_total);

  let cut_to_ship_of_order = total_cut_qty > 0 ? (total_ship_qty / total_cut_qty * 100) : 0;
  frm.set_value('cut_to_ship_of_order', cut_to_ship_of_order);

  let order_to_ship_total = total_order_qty > 0 ? (total_ship_qty / total_order_qty * 100) : 0;
  frm.set_value('order_to_ship_total', order_to_ship_total);

  frm.refresh_fields([
    'total_order_qty', 'total_cut_qty', 'total_scan_qty', 'total_pack_qty', 'total_ship_qty',
    'total_good_garments', 'total_rejected_garments', 'total_rejected_panels', 'total_missing_units',
    'cumulative_total', 'cut_to_ship_of_order', 'order_to_ship_total'
  ]);

  // Re-render card totals ONLY while Pending and only for Factory Manager
  const status = frm.doc.status || '';
  if (!frm.doc.__islocal && status === 'Pending for Approval') {
    const is_factory_manager = frappe.user.has_role('Factory Manager');
    if (is_factory_manager && frm.fields_dict.approval_card_html) {
      setTimeout(() => {
        render_factory_ocr_card(frm, { readonly: false });
      }, 100);
    }
  }
}

function clear_totals(frm) {
  frm.set_value('total_order_qty', 0);
  frm.set_value('total_cut_qty', 0);
  frm.set_value('total_scan_qty', 0);
  frm.set_value('total_pack_qty', 0);
  frm.set_value('total_ship_qty', 0);
  frm.set_value('total_good_garments', 0);
  frm.set_value('total_rejected_garments', 0);
  frm.set_value('total_rejected_panels', 0);
  frm.set_value('total_missing_units', 0);
  frm.set_value('cumulative_total', 0);
  frm.set_value('cut_to_ship_of_order', 0);
  frm.set_value('order_to_ship_total', 0);

  frm.refresh_fields([
    'total_order_qty', 'total_cut_qty', 'total_scan_qty', 'total_pack_qty', 'total_ship_qty',
    'total_good_garments', 'total_rejected_garments', 'total_rejected_panels', 'total_missing_units',
    'cumulative_total', 'cut_to_ship_of_order', 'order_to_ship_total'
  ]);
}

// ==============================
// Approval UI helpers
// ==============================
function hide_factory_approval_ui(frm, opts) {
  opts = opts || {};
  const hide_section = (opts.hide_section !== false); // default true

  if (hide_section && frm.fields_dict.approval_section) {
    frm.set_df_property('approval_section', 'hidden', true);
    frm.refresh_field('approval_section');
  }

  if (frm.fields_dict.approval_card_html) {
    frm.set_df_property('approval_card_html', 'hidden', true);
    frm.refresh_field('approval_card_html');

    const f = frm.fields_dict.approval_card_html;
    if (f.$wrapper) f.$wrapper.empty();
  }
}

function render_factory_ocr_card(frm, { readonly }) {
  const html = readonly ? get_factory_ocr_readonly_card_html(frm) : get_factory_ocr_action_card_html(frm);

  frm.set_df_property('approval_card_html', 'hidden', false);
  frm.refresh_field('approval_card_html');

  const f = frm.fields_dict.approval_card_html;

  if (f && f.$wrapper && f.$wrapper.length) {
    f.$wrapper.html(html);
  } else {
    frm.set_df_property('approval_card_html', 'options', html);
    frm.refresh_field('approval_card_html');
  }

  if (!readonly) {
    setTimeout(() => attach_factory_ocr_approval_listeners(frm), 100);
  }
}

function get_factory_ocr_action_card_html(frm) {
  const kpiThreshold = 98;

  const cutToShip = flt(frm.doc.cut_to_ship_of_order);
  const orderToShip = flt(frm.doc.order_to_ship_total);

  const cutColor = cutToShip >= kpiThreshold ? '#28a745' : '#dc3545';
  const orderColor = orderToShip >= kpiThreshold ? '#28a745' : '#dc3545';

  const factoryName = frm.fields_dict.factory ?
    (frm.fields_dict.factory.get_label_value() || frm.doc.factory || '–') :
    (frm.doc.factory || '–');

  const uniqueStyles = [
    ...new Set(
      (frm.doc.table_ocn_details || [])
        .map(r => (r.style || '').trim())
        .filter(Boolean)
    )
  ].join(', ') || '–';    

  return `
    <div class="approval-card" style="border: 1px solid #4c9658; padding: 20px; border-radius: 8px; max-width: 1200px; margin: 0 auto; background: white; font-family: Arial, sans-serif;">
      <h3 style="color:#4c9658; text-align:center; margin:0 0 15px;">Factory OCR – Approval</h3>

      <div style="font-size:0.9em; line-height:1.6; margin-bottom:15px;">
        <b>Request ID:</b> ${frm.doc.name} &nbsp; | &nbsp;
        <b>Status:</b> ${frm.doc.status || '–'}<br>
        <b>Buyer:</b> ${frm.doc.buyer || '–'} &nbsp; | &nbsp;
        <b>OCN:</b> ${frm.doc.ocn || '–'} &nbsp; | &nbsp;
        <b>Style(s):</b> ${uniqueStyles}<br> 
        <b>Factory:</b> ${factoryName}<br>
        <b>Created On:</b> ${frappe.datetime.str_to_user(frm.doc.creation)}<br><br>

        <span style="color:#007bff;">
          <b>Requester Remarks:</b> ${frm.doc.requester_remarks ? frappe.utils.escape_html(String(frm.doc.requester_remarks)) : '–'}<br>
        </span>
      </div>

      <div style="margin:15px 0; border-top:1px solid #4c9658; padding-top:15px; overflow-x:auto; text-align:center;">
        <b>SUMMARY (TOTALS)</b><br>
        <table style="width:70%; border-collapse:collapse; margin:10px auto; table-layout:fixed; font-size:1em;">
          <thead>
            <tr>
              <th style="border:1px solid #4c9658; padding:6px; text-align:left; background:#f8f8f8; width:50%;">Parameter</th>
              <th style="border:1px solid #4c9658; padding:6px; text-align:center; background:#f8f8f8;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${rowHTML('Order Qty', flt(frm.doc.total_order_qty))}
            ${rowHTML('Cut Qty', flt(frm.doc.total_cut_qty))}
            ${rowHTML('Scan Qty', flt(frm.doc.total_scan_qty))}
            ${rowHTML('Pack Qty', flt(frm.doc.total_pack_qty))}
            ${rowHTML('Ship Qty', flt(frm.doc.total_ship_qty))}
            ${rowHTML('Good Garments', flt(frm.doc.total_good_garments))}
            ${rowHTML('Rejected Garments', flt(frm.doc.total_rejected_garments))}
            ${rowHTML('Rejected Panels', flt(frm.doc.total_rejected_panels))}
            ${rowHTML('Missing Units', flt(frm.doc.total_missing_units))}
            ${rowHTML('Cumulative Total', flt(frm.doc.cumulative_total))}
          </tbody>
        </table>
      </div>

      <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin: 15px 0;">
        <div style="text-align:center; min-width: 260px; color:${cutColor}; font-size:1.05em;">
          <b>Cut → Ship % (Total):</b>
          <span style="background-color:${cutColor}; color:white; padding:4px 10px; border-radius:4px; font-size:0.9em; margin-left:10px; font-weight:bold;">
            ${cutToShip.toFixed(2)}%
          </span>
        </div>

        <div style="text-align:center; min-width: 260px; color:${orderColor}; font-size:1.05em;">
          <b>Order → Ship % (Total):</b>
          <span style="background-color:${orderColor}; color:white; padding:4px 10px; border-radius:4px; font-size:0.9em; margin-left:10px; font-weight:bold;">
            ${orderToShip.toFixed(2)}%
          </span>
        </div>
      </div>

      <div style="margin:15px 0; border-top:1px solid #4c9658; padding-top:15px;">
        <label style="display:block; margin:15px 0 8px; font-size:0.9em;">Approver Remarks <span style="color:red;">*</span></label>
        <textarea class="approval-remarks" style="width:100%; height:80px; border:1px solid #ddd; padding:8px; border-radius:4px;"></textarea>
      </div>

      <div style="margin:15px 0; text-align:center;">
        <button type="button" class="btn-reject" style="background-color:#d9534f; color:white; border:none; padding:8px 16px; margin:0 10px; border-radius:4px; cursor:pointer;">Reject</button>
        <button type="button" class="btn-approve" style="background-color:#5cb85c; color:white; border:none; padding:8px 16px; margin:0 10px; border-radius:4px; cursor:pointer;">Approve</button>

        <label style="display:inline-flex; align-items:center; font-size:0.9em; margin-left: 16px;">
          <input type="checkbox" class="with-replenishment" ${frm.doc.with_replenishment ? 'checked' : ''} style="margin-right:8px;">
          With Replenishment
        </label>
      </div>
    </div>
  `;
}

function get_factory_ocr_readonly_card_html(frm) {
  const cutToShip = flt(frm.doc.cut_to_ship_of_order).toFixed(2);
  const orderToShip = flt(frm.doc.order_to_ship_total).toFixed(2);

  return `
    <div class="approval-card" style="border: 1px solid #4c9658; padding: 20px; border-radius: 8px; max-width: 1200px; margin: 0 auto; background: white; font-family: Arial, sans-serif;">
      <h3 style="color:#4c9658; text-align:center; margin:0 0 15px;">Factory OCR – ${frm.doc.status || ''}</h3>
      <div style="font-size:0.9em; line-height:1.6;">
        <b>Request ID:</b> ${frm.doc.name} &nbsp; | &nbsp;
        <b>Status:</b> ${frm.doc.status || '–'}<br>
      </div>
    </div>
  `;
}

function attach_factory_ocr_approval_listeners(frm) {
  const $wrapper = $(frm.fields_dict.approval_card_html.wrapper);
  const $card = $wrapper.find('.approval-card');
  if (!$card.length) return;

  $card.find('.btn-approve').off('click').on('click', function() {
    const remarks = ($card.find('.approval-remarks').val() || '').trim();
    if (!remarks) {
      frappe.msgprint(__('Please enter Approver Remarks.'));
      return;
    }
    const with_replenishment = $card.find('.with-replenishment').is(':checked') ? 1 : 0;

    frappe.confirm(__('Approve this Factory OCR?'), () => {
      frappe.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.factory_ocr.factory_ocr.approve',
        args: {
          docname: frm.doc.name,
          approver_remarks: remarks,
          with_replenishment: with_replenishment
        },
        callback: r => {
          if (!r.exc) location.reload();
        }
      });
    });
  });

  $card.find('.btn-reject').off('click').on('click', function() {
    const remarks = ($card.find('.approval-remarks').val() || '').trim();
    if (!remarks) {
      frappe.msgprint(__('Please enter remarks for rejection.'));
      return;
    }
    const with_replenishment = $card.find('.with-replenishment').is(':checked') ? 1 : 0;

    frappe.confirm(__('Reject this Factory OCR?'), () => {
      frappe.call({
        method: 'erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.factory_ocr.factory_ocr.reject',
        args: {
          docname: frm.doc.name,
          reason: remarks,
          with_replenishment: with_replenishment
        },
        callback: r => {
          if (!r.exc) location.reload();
        }
      });
    });
  });
}

// ==============================
// Generic helpers
// ==============================
function hide_all_sections_except(frm, visible_section_fields) {
  Object.keys(frm.fields_dict).forEach(fieldname => {
    const df = frm.fields_dict[fieldname];
    if (df && df.df && df.df.fieldtype === 'Section Break') {
      frm.set_df_property(fieldname, 'hidden', !visible_section_fields.includes(fieldname));
    }
  });
}

function show_all_sections(frm) {
  Object.keys(frm.fields_dict).forEach(fieldname => {
    const df = frm.fields_dict[fieldname];
    if (df && df.df && df.df.fieldtype === 'Section Break') {
      frm.set_df_property(fieldname, 'hidden', false);
    }
  });
}

function set_form_readonly(frm, makeReadonly) {
  Object.keys(frm.fields_dict || {}).forEach((fieldname) => {
    if (fieldname === 'approval_card_html') return;
    try {
      frm.set_df_property(fieldname, 'read_only', makeReadonly ? 1 : 0);
    } catch (e) {}
  });
}

function rowHTML(label, value) {
  return `
    <tr>
      <td style="border:1px solid #4c9658; padding:6px; text-align:left;">${label}</td>
      <td style="border:1px solid #4c9658; padding:6px; text-align:center;">${value}</td>
    </tr>
  `;
}

function flt(value, precision) {
  const val = parseFloat(value);
  if (isNaN(val)) return 0.0;
  const factor = precision ? Math.pow(10, precision) : 1000;
  return Math.round((val || 0) * factor) / factor;
}


frappe.listview_settings['Factory OCR'] = {
    add_fields: ["status", "docstatus"],
    has_indicator_for_draft: true,

    get_indicator: function(doc) {

        const status = (doc.status || "").trim();

        if (status === "Approved") {
            return ["Approved", "green"];
        }

        if (status === "Rejected") {
            return ["Rejected", "red"];
        }

        if (status === "Pending for Approval") {
            return ["Pending for Approval", "orange"];
        }

        // fallback
        return ["Draft", "gray"];
    }
};
