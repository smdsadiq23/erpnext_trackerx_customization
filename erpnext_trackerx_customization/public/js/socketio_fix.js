// socketio_fix.js
(function () {
  function patch_socketio() {
    // Wait until frappe + socketio client are loaded
    if (!window.frappe || !frappe.socketio || !frappe.socketio.get_host) {
      return false;
    }

    // Only patch when:
    // - We're on HTTPS
    // - Frappe thinks this is a dev server (bench start style)
    if (!(window.location.protocol === "https:" && window.dev_server)) {
      console.log("[socketio_fix] Not HTTPS dev_server, skipping patch");
      return true;
    }

    console.log(
      "[socketio_fix] Patching frappe.socketio.get_host for HTTPS dev_server on",
      window.location.origin
    );

    const original_get_host = frappe.socketio.get_host.bind(frappe.socketio);

    // Override get_host so it ALWAYS uses the browser origin,
    // and lets socket.io use its default /socket.io path.
    frappe.socketio.get_host = function (port = 9000) {
      const host = window.location.origin; // e.g. https://classicapparel.trackerx.cloud
      console.log("[socketio_fix] get_host() ->", host);
      return host;
    };

    // If there is already a socket created, kill it and re-init with the new host
    try {
      if (frappe.socketio.socket) {
        try {
          frappe.socketio.socket.disconnect();
        } catch (e) {
          console.warn("[socketio_fix] Error disconnecting old socket", e);
        }
        frappe.socketio.socket = null;
      }

      // Force a fresh connect using the patched get_host()
      frappe.socketio.init();
    } catch (e) {
      console.warn("[socketio_fix] Error re-initializing socket.io", e);
    }

    return true;
  }

  // Try immediately; if frappe isn't ready yet, keep retrying
  if (!patch_socketio()) {
    const interval = setInterval(function () {
      if (patch_socketio()) {
        clearInterval(interval);
      }
    }, 500);
  }
})();
