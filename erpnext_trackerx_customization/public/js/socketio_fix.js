(function () {
  function patch_socketio() {
    // Wait until frappe + socketio are available
    if (!window.frappe || !frappe.socketio || !frappe.socketio.get_host) {
      return false;
    }

    // Only patch in dev_server + HTTPS scenario
    if (!(window.dev_server && window.location.protocol === "https:")) {
      return true; // nothing to do, but stop retrying
    }

    console.log("[socketio_fix] Patching frappe.socketio.get_host for HTTPS dev_server");

    const original_get_host = frappe.socketio.get_host.bind(frappe.socketio);

    frappe.socketio.get_host = function (port = 9000) {
      // For HTTPS behind reverse proxy, DO NOT add :9000
      const host = window.location.origin;

      if (frappe.boot && frappe.boot.sitename) {
        return host + `/${frappe.boot.sitename}`;
      }

      // Fallback: just origin
      return host;
    };

    // If a socket already exists, disconnect and re-init with new host
    try {
      if (frappe.socketio.socket) {
        try {
          frappe.socketio.socket.disconnect();
        } catch (e) {
          console.warn("[socketio_fix] Error disconnecting old socket.io", e);
        }
        frappe.socketio.socket = null;
        frappe.socketio.init();
      }
    } catch (e) {
      console.warn("[socketio_fix] Error re-initializing socket.io", e);
    }

    return true;
  }

  // Try immediately…
  if (!patch_socketio()) {
    // …and keep retrying until frappe.socketio is ready
    const interval = setInterval(function () {
      if (patch_socketio()) {
        clearInterval(interval);
      }
    }, 500);
  }
})();
