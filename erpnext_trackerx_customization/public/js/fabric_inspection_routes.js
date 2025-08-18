/**
 * Route override for Fabric Inspection
 * Redirects form routes to the inspection UI
 */

frappe.router.on('before_route', function(route) {
    // Check if it's a Fabric Inspection form route
    if (route && route.length >= 2) {
        const doctype = route[0];
        const docname = route[1];
        
        // If it's a Fabric Inspection form route, redirect to inspection UI
        if (doctype === 'fabric-inspection' && docname && docname !== 'new') {
            // Prevent the default route
            frappe.router.navigate = function() {};
            
            // Redirect to inspection UI
            setTimeout(() => {
                const inspection_url = `/fabric_inspection_ui?name=${encodeURIComponent(docname)}`;
                window.location.href = inspection_url;
            }, 100);
            
            return false; // Cancel the route
        }
    }
});

// Also handle direct URL access - use proper event-based approach
$(document).ready(function() {
    // Check on initial load
    checkFabricInspectionRoute();
    
    // Check on route changes
    $(document).on('page-change', checkFabricInspectionRoute);
});

function checkFabricInspectionRoute() {
    try {
        if (typeof frappe !== 'undefined' && frappe.get_route) {
            const route = frappe.get_route();
            
            // Check if user directly accessed a Fabric Inspection form URL
            if (route[0] === 'Form' && route[1] === 'Fabric Inspection' && route[2] && route[2] !== 'new') {
                const doc_name = route[2];
                
                // Show a message and offer redirect
                frappe.msgprint({
                    title: __('Fabric Inspection Redirect'),
                    message: __('Fabric Inspection has a dedicated interface. Would you like to open it?<br><br><button class="btn btn-primary btn-sm" onclick="window.open(\'/fabric_inspection_ui?name=' + doc_name + '\', \'_blank\')">🎯 Open Four-Point Inspection</button><br><br><small>Or <a href="/app/fabric-inspection/' + doc_name + '">continue to standard form</a></small>'),
                    indicator: 'blue'
                });
            }
        }
    } catch (error) {
        console.log('Fabric inspection route check skipped:', error.message);
    }
}