/**
 * Fixed Custom List View Behavior for Fabric Inspection
 * Redirects to the fabric inspection UI instead of the standard form
 */

frappe.listview_settings['Fabric Inspection'] = {
    onload: function(listview) {
        console.log('🎯 Fabric Inspection List View Loaded');
        
        // Setup redirect behavior with multiple approaches
        setup_fabric_inspection_redirect_v2(listview);
        
        // Add custom button to list view
        listview.page.add_inner_button(__('🔍 Open Selected Inspections'), function() {
            open_selected_inspections(listview);
        });
    },
    
    // Override get_form_link to redirect to custom UI
    get_form_link: function(doc) {
        return `/fabric_inspection_ui?name=${encodeURIComponent(doc.name)}`;
    },
    
    // Custom formatting for the list view
    formatters: {
        inspection_status: function(value) {
            const status_colors = {
                'Draft': 'gray',
                'In Progress': 'orange', 
                'Hold': 'yellow',
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
    
    // Custom filters
    filters: [
        ['inspection_status', '!=', 'Cancelled']
    ],
    
    // Default sorting
    order_by: 'modified desc'
};

function setup_fabric_inspection_redirect_v2(listview) {
    try {
        console.log('🔧 Setting up Fabric Inspection redirect...');
        
        // Wait for listview to be fully rendered
        setTimeout(() => {
            // Approach 1: Override the get_form_link method if it exists
            if (listview.get_form_link) {
                const original_get_form_link = listview.get_form_link.bind(listview);
                listview.get_form_link = function(doc) {
                    console.log('🎯 Redirecting via get_form_link for:', doc.name);
                    return `/fabric_inspection_ui?name=${encodeURIComponent(doc.name)}`;
                };
            }
            
            // Approach 2: Override row click events
            setupRowClickRedirect(listview);
            
            // Approach 3: Override form navigation
            overrideFormNavigation(listview);
            
            console.log('✅ Fabric Inspection redirect setup complete');
            
        }, 1000);
        
    } catch (error) {
        console.error('❌ Error setting up fabric inspection redirect:', error);
    }
}

function setupRowClickRedirect(listview) {
    try {
        // Remove existing click handlers
        if (listview.$result) {
            listview.$result.off('click', '.list-row-container');
            listview.$result.off('click', '.list-row');
            listview.$result.off('click', '.list-subject');
            
            // Add new click handler
            listview.$result.on('click', '.list-row-container, .list-row', function(e) {
                // Don't interfere with checkboxes, buttons, etc.
                if ($(e.target).is('input[type="checkbox"], .btn, button, .dropdown-toggle, .list-row-checkbox')) {
                    return true;
                }
                
                e.preventDefault();
                e.stopPropagation();
                
                const doc_name = getDocNameFromRow($(this));
                
                if (doc_name) {
                    console.log('🎯 Row clicked, redirecting to fabric inspection UI for:', doc_name);
                    open_fabric_inspection_ui(doc_name, e.ctrlKey || e.metaKey);
                } else {
                    console.warn('⚠️  Could not determine document name from row click');
                }
                
                return false;
            });
            
            // Also handle subject link clicks specifically
            listview.$result.on('click', '.list-subject a', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const href = $(this).attr('href') || '';
                const doc_name = href.split('/').pop() || $(this).text().trim();
                
                if (doc_name) {
                    console.log('🎯 Subject link clicked, redirecting for:', doc_name);
                    open_fabric_inspection_ui(doc_name, e.ctrlKey || e.metaKey);
                }
                
                return false;
            });
            
            // Add visual indicators
            listview.$result.on('mouseenter', '.list-row-container', function() {
                $(this).attr('title', 'Click to open Four-Point Inspection Interface')
                       .css('cursor', 'pointer');
            });
        }
        
    } catch (error) {
        console.error('Error setting up row click redirect:', error);
    }
}

function overrideFormNavigation(listview) {
    try {
        // Override the open_form method if it exists
        if (listview.open_form) {
            const original_open_form = listview.open_form.bind(listview);
            listview.open_form = function(doc_name) {
                console.log('🎯 Form navigation intercepted for:', doc_name);
                open_fabric_inspection_ui(doc_name, false);
            };
        }
        
        // Override navigate_to_document if it exists
        if (listview.navigate_to_document) {
            const original_navigate = listview.navigate_to_document.bind(listview);
            listview.navigate_to_document = function(doc_name) {
                console.log('🎯 Document navigation intercepted for:', doc_name);
                open_fabric_inspection_ui(doc_name, false);
            };
        }
        
    } catch (error) {
        console.error('Error overriding form navigation:', error);
    }
}

function getDocNameFromRow($row) {
    try {
        console.log('🔍 Getting document name from row:', $row);
        
        // Method 1: data-name attribute (most reliable)
        let doc_name = $row.attr('data-name') || $row.data('name');
        if (doc_name && !doc_name.includes('fabric_inspection_ui')) {
            console.log('✅ Found doc_name via data-name:', doc_name);
            return doc_name;
        }
        
        // Method 2: find in data-docname
        doc_name = $row.attr('data-docname') || $row.data('docname');
        if (doc_name && !doc_name.includes('fabric_inspection_ui')) {
            console.log('✅ Found doc_name via data-docname:', doc_name);
            return doc_name;
        }
        
        // Method 3: Look for subject link with standard Frappe format
        const $subject_link = $row.find('.list-subject a, .bold a');
        if ($subject_link.length) {
            const href = $subject_link.attr('href') || '';
            console.log('🔗 Subject link href:', href);
            
            // Only extract from standard Frappe form URLs, not our custom UI URLs
            if (href.includes('/app/fabric-inspection/') && !href.includes('fabric_inspection_ui')) {
                doc_name = href.split('/').pop();
                if (doc_name) {
                    console.log('✅ Found doc_name via subject link href:', doc_name);
                    return doc_name;
                }
            }
            
            // Try text content (document name should be in the link text)
            doc_name = $subject_link.text().trim();
            if (doc_name && doc_name.match(/^[A-Z]+-\d{4}-\d{5,}$/)) {
                console.log('✅ Found doc_name via subject link text:', doc_name);
                return doc_name;
            }
        }
        
        // Method 4: Find first cell with document name pattern
        const $cells = $row.find('td, .list-item-container, .list-row-col');
        let found_doc_name = null;
        
        $cells.each(function() {
            const text = $(this).text().trim();
            // Look for pattern like FINSP-2025-00007
            if (text && text.match(/^[A-Z]+-\d{4}-\d{5,}$/)) {
                found_doc_name = text;
                return false; // Break out of loop
            }
        });
        
        if (found_doc_name) {
            console.log('✅ Found doc_name via cell text pattern:', found_doc_name);
            return found_doc_name;
        }
        
        console.warn('⚠️  Could not determine document name from row');
        return null;
        
    } catch (error) {
        console.error('❌ Error getting document name from row:', error);
        return null;
    }
}

function open_fabric_inspection_ui(doc_name, new_tab = false) {
    try {
        if (!doc_name) {
            console.warn('No document name provided to open_fabric_inspection_ui');
            return;
        }
        
        // Clean up the document name - remove any URL encoding issues
        doc_name = doc_name.trim();
        
        // If doc_name already contains our URL, extract just the document name
        if (doc_name.includes('fabric_inspection_ui?name=')) {
            const match = doc_name.match(/name=([^&]+)/);
            if (match) {
                doc_name = decodeURIComponent(match[1]);
                console.log('🔧 Extracted document name from URL:', doc_name);
            }
        }
        
        // Validate document name format
        if (!doc_name.match(/^[A-Z]+-\d{4}-\d{5,}$/)) {
            console.warn('⚠️  Invalid document name format:', doc_name);
            // Try to extract valid document name pattern
            const match = doc_name.match(/([A-Z]+-\d{4}-\d{5,})/);
            if (match) {
                doc_name = match[1];
                console.log('🔧 Extracted valid document name:', doc_name);
            } else {
                console.error('❌ Could not extract valid document name from:', doc_name);
                return;
            }
        }
        
        console.log(`🚀 Opening fabric inspection UI for: ${doc_name}${new_tab ? ' (new tab)' : ''}`);
        
        // Show loading indicator
        frappe.show_progress(__('Opening Fabric Inspection...'), 50, 100);
        
        // Create the inspection URL with clean document name
        const inspection_url = `/fabric_inspection_ui?name=${encodeURIComponent(doc_name)}`;
        console.log('📍 Inspection URL:', inspection_url);
        
        // Hide progress after a short delay
        setTimeout(() => frappe.hide_progress(), 500);
        
        if (new_tab) {
            window.open(inspection_url, '_blank');
            frappe.show_alert({
                message: __('Opening Four-Point Inspection in new tab...'),
                indicator: 'blue'
            });
        } else {
            window.location.href = inspection_url;
        }
        
    } catch (error) {
        console.error('❌ Error opening fabric inspection UI:', error);
        frappe.hide_progress();
        
        // Fallback to standard form
        const form_url = `/app/fabric-inspection/${doc_name}`;
        console.log('🔄 Falling back to standard form:', form_url);
        
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
    try {
        const selected = listview.get_checked_items();
        
        if (selected.length === 0) {
            frappe.msgprint(__('Please select at least one inspection'));
            return;
        }
        
        if (selected.length > 5) {
            frappe.msgprint(__('Please select maximum 5 inspections to avoid performance issues'));
            return;
        }
        
        console.log('🎯 Opening selected inspections:', selected.map(item => item.name));
        
        // Open each selected inspection in a new tab with delay
        selected.forEach((item, index) => {
            setTimeout(() => {
                open_fabric_inspection_ui(item.name, true);
            }, index * 300); // 300ms delay between each
        });
        
    } catch (error) {
        console.error('Error opening selected inspections:', error);
        frappe.msgprint(__('Error opening selected inspections. Please try again.'));
    }
}

// Debug helper - can be called from console
window.test_fabric_inspection_redirect = function(doc_name) {
    console.log('🧪 Testing fabric inspection redirect...');
    open_fabric_inspection_ui(doc_name || 'FINSP-2025-00007', false);
};

// Add CSS for better visual feedback - use proper event-based approach
$(document).ready(function() {
    checkAndAddFabricInspectionStyles();
    
    // Also check on page changes
    $(document).on('page-change', checkAndAddFabricInspectionStyles);
});

function checkAndAddFabricInspectionStyles() {
    try {
        if (typeof frappe !== 'undefined' && frappe.get_route) {
            const route = frappe.get_route();
            if (route[0] === 'List' && route[1] === 'Fabric Inspection') {
                add_fabric_inspection_list_styles();
            }
        }
    } catch (error) {
        console.log('Fabric inspection styles check skipped:', error.message);
    }
}

function add_fabric_inspection_list_styles() {
    if (!document.getElementById('fabric-inspection-list-styles')) {
        const style = document.createElement('style');
        style.id = 'fabric-inspection-list-styles';
        style.textContent = `
            .list-row-container {
                cursor: pointer !important;
                transition: all 0.2s ease;
            }
            
            .list-row-container:hover {
                background-color: #f8f9fa !important;
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            }
            
            .list-row-container:before {
                content: "🎯";
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                opacity: 0.3;
                font-size: 14px;
                z-index: 1;
            }
            
            .list-row-container:hover:before {
                opacity: 0.8;
            }
            
            .list-subject a {
                color: #007bff !important;
                text-decoration: none;
            }
            
            .list-subject a:hover {
                color: #0056b3 !important;
                text-decoration: underline;
            }
        `;
        document.head.appendChild(style);
    }
}