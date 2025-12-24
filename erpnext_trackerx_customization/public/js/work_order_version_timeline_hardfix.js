(function () {
  const MARK1 = "__trackerx_wo_hardfix_with_doc";
  const MARK2 = "__trackerx_wo_hardfix_call";

  function clear_versions_for_work_order(doctype, name, responseObj) {
    if (doctype !== "Work Order") return;

    try {
      // If response includes docinfo
      if (responseObj?.docinfo?.versions) {
        responseObj.docinfo.versions = [];
      }

      // If docinfo already stored in frappe.model.docinfo
      const stored = frappe?.model?.docinfo?.[doctype]?.[name];
      if (stored?.versions) {
        stored.versions = [];
      }

      // Optional: rare key
      if (responseObj?.docinfo?.version) {
        delete responseObj.docinfo.version;
      }
    } catch (e) {
      // Keep a single warning if something goes wrong
      console.warn("[TrackerX] Work Order version timeline hardfix failed:", e);
    }
  }

  // ---- Patch frappe.model.with_doc ----
  if (frappe?.model?.with_doc && !frappe.model.with_doc[MARK1]) {
    const orig_with_doc = frappe.model.with_doc;

    frappe.model.with_doc = function () {
      const doctype = arguments[0];
      const name = arguments[1];
      const user_cb = arguments[2];

      if (typeof user_cb === "function") {
        arguments[2] = function (r) {
          clear_versions_for_work_order(doctype, name, r);
          return user_cb.apply(this, arguments);
        };
      }

      return orig_with_doc.apply(this, arguments);
    };

    frappe.model.with_doc[MARK1] = true;
  }

  // ---- Patch frappe.call ----
  if (typeof frappe?.call === "function" && !frappe.call[MARK2]) {
    const orig_call = frappe.call;

    frappe.call = function (opts) {
      try {
        // string form: frappe.call(method, args, callback)
        if (typeof opts === "string") {
          const method = opts;
          const args = arguments[1] || {};
          const cb = arguments[2];

          return orig_call.call(this, {
            method,
            args,
            callback: function (r) {
              if (method === "frappe.desk.form.load.getdoc") {
                const dt = r?.docs?.[0]?.doctype;
                const dn = r?.docs?.[0]?.name;
                clear_versions_for_work_order(dt, dn, r);
              }
              if (typeof cb === "function") return cb(r);
            },
          });
        }

        // object form
        const method = opts?.method;
        const user_cb = opts?.callback;

        if (method === "frappe.desk.form.load.getdoc" && typeof user_cb === "function") {
          opts.callback = function (r) {
            const dt = r?.docs?.[0]?.doctype;
            const dn = r?.docs?.[0]?.name;
            clear_versions_for_work_order(dt, dn, r);
            return user_cb.apply(this, arguments);
          };
        }

        return orig_call.apply(this, arguments);
      } catch (e) {
        console.warn("[TrackerX] Work Order version timeline hardfix wrapper error:", e);
        return orig_call.apply(this, arguments);
      }
    };

    frappe.call[MARK2] = true;
  }
})();
