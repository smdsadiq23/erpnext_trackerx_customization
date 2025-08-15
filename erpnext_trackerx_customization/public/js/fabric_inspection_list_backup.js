/**
 * Custom List View Behavior for Fabric Inspection
 * Redirects to the fabric inspection UI instead of the standard form
 */

frappe.listview_settings['Fabric Inspection'] = {
    onload: function(listview) {
        // Override the default row click behavior
        setup_fabric_inspection_redirect(listview);
        
        // Add custom button to list view
        listview.page.add_inner_button(__('🎯 Open Inspection UI'), function() {
            open_selected_inspections(listview);
        });
        
        // Add a notice about the redirection
        setTimeout(() => {
            if (listview.data && listview.data.length > 0) {
                frappe.show_alert({
                    message: __('Click any inspection to open Four-Point Inspection Interface'),
                    indicator: 'blue'
                }, 5);
            }
        }, 1000);
    },
    
    // Custom formatting for the list view
    formatters: {
        inspection_status: function(value) {
            const status_colors = {
                'Draft': 'gray',
                'In Progress': 'orange', 
                'Completed': 'green',
                'Approved': 'blue',
                'Rejected': 'red'
            };
            const color = status_colors[value] || 'gray';
            return `<span class="indicator ${color}">${value || 'Draft'}</span>`;
        },
        
        inspection_result: function(value) {
            const result_colors = {
                'Accepted': 'green',
                'Rejected': 'red',
                'Conditional Accept': 'orange',
                'Pending': 'gray'
            };
            const color = result_colors[value] || 'gray';
            return `<span class="indicator ${color}">${value || 'Pending'}</span>`;
        }
    },
    
    // Custom filters for the list view
    filters: [
        ['inspection_status', '!=', 'Cancelled']
    ],
    
    // Default sorting
    order_by: 'modified desc'
};

function setup_fabric_inspection_redirect(listview) {
    /**
     * Setup custom redirect behavior for fabric inspection rows
     */
    try {
        // Wait for the listview to be fully rendered
        setTimeout(() => {
            // Remove existing click handlers first
            listview.$result.off('click', '.list-row-container');
            listview.$result.off('click', '.list-row');
            
            // Add our custom click handler to the result container
            listview.$result.on('click', '.list-row-container, .list-row', function(e) {
                // Don't interfere with checkbox clicks or other controls
                if ($(e.target).is('input[type="checkbox"], .btn, button, .dropdown-toggle')) {
                    return true; // Let the default behavior handle these
                }
                
                // Special handling for inspection ID links
                if ($(e.target).is('a') && $(e.target).attr('href') && $(e.target).attr('href').includes('/app/fabric-inspection/')) {
                    e.preventDefault();
                    const doc_name = $(e.target).attr('href').split('/').pop();
                    if (doc_name) {
                        open_fabric_inspection_ui(doc_name, e.ctrlKey || e.metaKey);
                        return false;
                    }
                }
                
                e.preventDefault();
                e.stopPropagation();
                
                // Get the document name from the row
                const $row = $(this).closest('.list-row-container, .list-row');
                let doc_name = $row.attr('data-name') || $row.data('name');
                
                // Alternative way to get doc name from the row
                if (!doc_name) {
                    const $nameCell = $row.find('[data-field="name"], .list-subject a');
                    if ($nameCell.length) {
                        doc_name = $nameCell.text().trim() || $nameCell.attr('href')?.split('/').pop();
                    }
                }
                
                if (doc_name) {
                    console.log('Redirecting to fabric inspection UI for:', doc_name);
                    
                    // Check if it's a middle click or Ctrl+click (open in new tab)
                    // Default to current tab for better UX
                    const new_tab = e.ctrlKey || e.metaKey || e.which === 2;
                    open_fabric_inspection_ui(doc_name, new_tab);
                } else {
                    console.warn('Could not determine document name from row');
                    // Fallback to default behavior
                    return true;
                }
            });
            
            // Add visual indicators
            listview.$result.on('mouseenter', '.list-row-container, .list-row', function() {
                $(this).attr('title', 'Click to open Four-Point Inspection Interface')
                       .css('cursor', 'pointer');
            });
            
            // Add custom styling to indicate clickable rows
            if (!document.getElementById('fabric-inspection-redirect-style')) {
                const style = document.createElement('style');
                style.id = 'fabric-inspection-redirect-style';
                style.textContent = `
                    .list-row-container, .list-row {
                        position: relative;
                    }
                    .list-row-container:before, .list-row:before {
                        content: "🎯";
                        position: absolute;
                        right: 10px;
                        top: 50%;
                        transform: translateY(-50%);
                        opacity: 0.3;
                        font-size: 12px;
                    }
                    .list-row-container:hover:before, .list-row:hover:before {
                        opacity: 0.8;
                    }
                `;
                document.head.appendChild(style);
            }
            
            console.log('Fabric Inspection list view redirect setup complete');
        }, 500);
        
    } catch (error) {
        console.error('Error setting up fabric inspection redirect:', error);
    }
}

function open_fabric_inspection_ui(doc_name, new_tab = false) {
    /**
     * Open the fabric inspection UI for the given document
     */
    try {
        // Show loading indicator
        frappe.show_progress(__('Opening Fabric Inspection...'), 30, 100);
        
        // Open the traditional fabric inspection UI
        const inspection_url = `/fabric_inspection_ui?name=${encodeURIComponent(doc_name)}`;
        
        frappe.show_progress(__('Opening Fabric Inspection...'), 80, 100);
        
        if (new_tab) {
            // Open in new tab
            window.open(inspection_url, '_blank');
        } else {
            // Navigate in current tab
            window.location.href = inspection_url;
        }
        
        frappe.hide_progress();
        
        frappe.show_alert({
            message: __('Opening Four-Point Inspection Interface...'),
            indicator: 'blue'
        });
        
    } catch (error) {
        frappe.hide_progress();
        console.error('Error opening fabric inspection UI:', error);
        
        // Fallback to standard form
        const form_url = `/app/fabric-inspection/${doc_name}`;
        if (new_tab) {
            window.open(form_url, '_blank');
        } else {
            window.location.href = form_url;
        }
        
        frappe.show_alert({
            message: __('Opened standard form instead'),
            indicator: 'orange'
        });
    }
}

function open_selected_inspections(listview) {
    /**
     * Open selected inspections in the fabric inspection UI
     */
    const selected = listview.get_checked_items();
    
    if (selected.length === 0) {
        frappe.msgprint(__('Please select at least one inspection'));
        return;
    }
    
    if (selected.length > 5) {
        frappe.msgprint(__('Please select maximum 5 inspections to avoid performance issues'));
        return;
    }
    
    // Open each selected inspection in a new tab
    selected.forEach((item, index) => {
        setTimeout(() => {
            open_fabric_inspection_ui(item.name, true);
        }, index * 500); // Stagger the opening to avoid browser popup blocking
    });
}

// Add custom CSS for better list view appearance
frappe.ready(function() {
    if (frappe.get_route()[0] === 'List' && frappe.get_route()[1] === 'Fabric Inspection') {
        add_custom_list_styles();
    }
});

function add_custom_list_styles() {
    /**
     * Add custom CSS for fabric inspection list view
     */
    if (!document.getElementById('fabric-inspection-list-styles')) {
        const style = document.createElement('style');
        style.id = 'fabric-inspection-list-styles';
        style.textContent = `
            .list-row-container {
                cursor: pointer;
                transition: background-color 0.2s ease;
            }
            
            .list-row-container:hover {
                background-color: #f8f9fa !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .list-row-container[data-name] {
                border-left: 3px solid #007bff;
            }
            
            .list-row-container[data-name]:hover {
                border-left-color: #0056b3;
            }
            
            /* Status indicators */
            .indicator.green {
                background-color: #28a745;
                color: white;
            }
            
            .indicator.red {
                background-color: #dc3545;
                color: white;
            }
            
            .indicator.orange {
                background-color: #fd7e14;
                color: white;
            }
            
            .indicator.blue {
                background-color: #007bff;
                color: white;
            }
            
            .indicator.gray {
                background-color: #6c757d;
                color: white;
            }
        `;
        document.head.appendChild(style);
    }
}