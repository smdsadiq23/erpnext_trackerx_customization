/**
 * Trims Inspection UI JavaScript
 * Handles count-based inspection system with checklist integration
 */

// Global state
let trimsInspectionState = {
    defectsData: {},
    itemsData: {},
    checklistData: {},
    isDirty: false,
    isCalculating: false,
    materialType: null
};

// Initialize inspection data from the server
async function loadTrimsData() {
    try {
        // Load fresh defects data from inspection document
        await loadExistingDefectsData();
        
        // Load items data
        if (inspectionData.items) {
            trimsInspectionState.itemsData = {};
            inspectionData.items.forEach(item => {
                trimsInspectionState.itemsData[item.item_number] = item;
            });
        }
        
        // Load material type for checklist
        trimsInspectionState.materialType = inspectionData.material_type || 'Trims';
        
        // Initialize AQL configuration
        updateAQLConfiguration();
        
        // Load checklist data
        loadChecklistData();
        
        // Check inspection status and apply UI updates if needed
        checkInspectionStatusOnLoad();
        
        console.log('Trims inspection data loaded successfully');
    } catch (error) {
        console.error('Error loading trims data:', error);
        showMessage('Error loading inspection data', 'error');
    }
}

// Load existing defects data from inspection document
async function loadExistingDefectsData() {
    try {
        const response = await fetch(`/api/method/erpnext_trackerx_customization.api.trims_inspection.get_inspection_data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name
            })
        });
        
        const result = await response.json();
        
        if (result.message && result.message.defects) {
            trimsInspectionState.defectsData = result.message.defects;
            
            // Populate the form with existing defects data
            setTimeout(() => {
                populateDefectsUI();
            }, 500); // Small delay to ensure DOM is ready
            
        } else if (inspectionData.defects) {
            // Fallback to initial data
            trimsInspectionState.defectsData = inspectionData.defects;
            setTimeout(() => {
                populateDefectsUI();
            }, 500);
        }
        
        console.log('Existing defects data loaded:', trimsInspectionState.defectsData);
        
    } catch (error) {
        console.error('Error loading existing defects data:', error);
        // Fallback to initial data
        if (inspectionData.defects) {
            trimsInspectionState.defectsData = inspectionData.defects;
            setTimeout(() => {
                populateDefectsUI();
            }, 500);
        }
    }
}

// Populate the defects UI with existing data
function populateDefectsUI() {
    if (!trimsInspectionState.defectsData) return;
    
    console.log('Populating trims defects UI with data:', trimsInspectionState.defectsData);
    
    // Clear all inputs first
    document.querySelectorAll('.defect-input').forEach(input => {
        input.value = '';
    });
    
    // Populate with saved data
    for (const itemNumber in trimsInspectionState.defectsData) {
        const itemDefects = trimsInspectionState.defectsData[itemNumber];
        
        for (const defectKey in itemDefects) {
            let countValue = itemDefects[defectKey];
            
            // Skip if no value or invalid value
            if (!countValue || countValue === 0 || countValue === "0") continue;
            
            // Clean the count value - handle malformed data
            if (typeof countValue === 'string') {
                // Remove non-numeric characters
                countValue = countValue.replace(/[^0-9]/g, '');
            }
            
            // Convert to number and validate
            const cleanCount = parseInt(countValue);
            if (isNaN(cleanCount) || cleanCount <= 0) {
                console.warn(`Invalid count value for ${defectKey}: ${itemDefects[defectKey]} -> cleaned: ${countValue} -> parsed: ${cleanCount}`);
                continue;
            }
            
            // Extract defect code from key
            const parts = defectKey.split('_');
            const defectCode = parts[parts.length - 1];
            
            // Find the input element
            const input = document.querySelector(`input[data-item="${itemNumber}"][data-defect="${defectCode}"]`);
            if (input) {
                input.value = cleanCount;
                console.log(`Set defect ${defectCode} for item ${itemNumber} to ${cleanCount} (original: ${itemDefects[defectKey]})`);
                
                // Also update the total count display
                const totalElement = document.getElementById(`total-${itemNumber}-${defectCode}`);
                if (totalElement) totalElement.textContent = cleanCount;
                
            } else {
                console.warn(`Input not found for item ${itemNumber}, defect ${defectCode}`);
            }
        }
    }
    
    // Recalculate totals after populating
    setTimeout(() => {
        calculateTotals();
    }, 100);
}

// Load checklist data based on material type
async function loadChecklistData() {
    try {
        const response = await fetch('/api/method/erpnext_trackerx_customization.erpnext_trackerx_customization.doctype.master_checklist.master_checklist.get_checklist_for_material', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                material_type: trimsInspectionState.materialType
            })
        });
        
        const result = await response.json();
        
        if (result.message) {
            // Handle different response formats
            let checklistData = result.message;
            if (result.message.checklist_items) {
                checklistData = result.message.checklist_items;
            }
            
            trimsInspectionState.checklistData = Array.isArray(checklistData) ? checklistData : [];
            renderChecklistTable();
            
            // Load existing checklist results from the inspection document
            loadExistingChecklistData();
            
            console.log('Trims checklist data loaded:', trimsInspectionState.checklistData);
        }
        
    } catch (error) {
        console.error('Error loading checklist data:', error);
        showMessage('Error loading checklist data', 'error');
    }
}

// Load existing checklist data from inspection document
async function loadExistingChecklistData() {
    try {
        const response = await fetch(`/api/method/erpnext_trackerx_customization.api.trims_inspection.get_inspection_data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name
            })
        });
        
        const result = await response.json();
        
        if (result.message && result.message.checklist_items) {
            const existingData = result.message.checklist_items;
            
            // Map existing data to checklist items
            existingData.forEach(savedItem => {
                // Find the corresponding checklist item
                const index = trimsInspectionState.checklistData.findIndex(item => 
                    item.test_parameter === savedItem.test_parameter
                );
                
                if (index !== -1) {
                    // Store the saved results
                    if (!trimsInspectionState.checklistData[index].results) {
                        trimsInspectionState.checklistData[index].results = {};
                    }
                    trimsInspectionState.checklistData[index].results = {
                        actual_result: savedItem.actual_result || '',
                        status: savedItem.status || '',
                        remarks: savedItem.remarks || ''
                    };
                }
            });
            
            // Update the UI with existing data
            populateChecklistUI();
            
            console.log('Existing checklist data loaded');
        }
        
    } catch (error) {
        console.error('Error loading existing checklist data:', error);
        // Don't show error message as this is optional loading
    }
}

// Populate the UI with existing checklist data
function populateChecklistUI() {
    if (!Array.isArray(trimsInspectionState.checklistData)) return;
    
    trimsInspectionState.checklistData.forEach((item, index) => {
        const itemId = `checklist-${index}`;
        const results = item.results || {};
        
        // Fill actual result
        const actualResultInput = document.querySelector(`input[data-checklist-id="${itemId}"]`);
        if (actualResultInput && results.actual_result) {
            actualResultInput.value = results.actual_result;
        }
        
        // Set radio button status
        if (results.status) {
            const radioButton = document.querySelector(`input[name="status-${itemId}"][value="${results.status}"]`);
            if (radioButton) {
                radioButton.checked = true;
            }
        }
        
        // Fill remarks
        const remarksTextarea = document.querySelector(`textarea[data-checklist-id="${itemId}"]`);
        if (remarksTextarea && results.remarks) {
            remarksTextarea.value = results.remarks;
        }
    });
    
    // Update summary after populating
    updateChecklistSummary();
}

// Render the checklist table
function renderChecklistTable() {
    const checklistContainer = document.getElementById('checklist-container');
    if (!checklistContainer || !trimsInspectionState.checklistData) return;
    
    let tableHTML = `
        <div class="checklist-section">
            <h4>Physical Testing Results - ${trimsInspectionState.materialType}</h4>
            <table class="table table-bordered checklist-table">
                <thead>
                    <tr>
                        <th style="width: 25%">Test Parameter</th>
                        <th style="width: 25%">Standard Requirement</th>
                        <th style="width: 20%">Actual Result</th>
                        <th style="width: 15%">Status</th>
                        <th style="width: 15%">Remarks</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    trimsInspectionState.checklistData.forEach((item, index) => {
        const itemId = `checklist-${index}`;
        tableHTML += `
            <tr data-checklist-id="${itemId}">
                <td>
                    <strong>${item.test_parameter}</strong>
                    ${item.test_category ? `<br><small class="text-muted">${item.test_category}</small>` : ''}
                    ${item.is_mandatory ? '<span class="badge badge-danger ms-2">Required</span>' : ''}
                </td>
                <td>${item.standard_requirement}</td>
                <td>
                    <input type="text" class="form-control checklist-actual-result" 
                           data-checklist-id="${itemId}" 
                           placeholder="Enter result"
                           onchange="updateChecklistItem('${itemId}', 'actual_result', this.value)">
                </td>
                <td>
                    <div class="radio-group">
                        <label class="radio-label">
                            <input type="radio" name="status-${itemId}" value="Pass" 
                                   onchange="updateChecklistItem('${itemId}', 'status', this.value)">
                            <span class="radio-text">☑ Pass</span>
                        </label>
                        <label class="radio-label">
                            <input type="radio" name="status-${itemId}" value="Fail" 
                                   onchange="updateChecklistItem('${itemId}', 'status', this.value)">
                            <span class="radio-text">☒ Fail</span>
                        </label>
                    </div>
                </td>
                <td>
                    <textarea class="form-control checklist-remarks" 
                              data-checklist-id="${itemId}" 
                              rows="2" 
                              placeholder="Remarks"
                              onchange="updateChecklistItem('${itemId}', 'remarks', this.value)"></textarea>
                </td>
            </tr>
        `;
    });
    
    tableHTML += `
                </tbody>
            </table>
            <div class="checklist-summary mt-3">
                <div class="row">
                    <div class="col-md-3">
                        <div class="status-summary pass">
                            <strong>Passed: </strong>
                            <span id="checklist-pass-count">0</span>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="status-summary fail">
                            <strong>Failed: </strong>
                            <span id="checklist-fail-count">0</span>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="status-summary na">
                            <strong>N/A: </strong>
                            <span id="checklist-na-count">0</span>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="status-summary pending">
                            <strong>Pending: </strong>
                            <span id="checklist-pending-count">${trimsInspectionState.checklistData.length}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    checklistContainer.innerHTML = tableHTML;
}

// Update checklist item
function updateChecklistItem(itemId, field, value) {
    if (!trimsInspectionState.checklistData) return;
    
    const index = parseInt(itemId.split('-')[1]);
    const checklistItem = trimsInspectionState.checklistData[index];
    
    if (!checklistItem.results) {
        checklistItem.results = {};
    }
    
    checklistItem.results[field] = value;
    trimsInspectionState.isDirty = true;
    
    // Update checklist summary
    updateChecklistSummary();
    
    // Recalculate final decision
    const criticalElement = document.getElementById('total-critical-defects');
    const majorElement = document.getElementById('total-major-defects');
    const minorElement = document.getElementById('total-minor-defects');
    
    if (criticalElement && majorElement && minorElement) {
        const critical = parseInt(criticalElement.textContent) || 0;
        const major = parseInt(majorElement.textContent) || 0;
        const minor = parseInt(minorElement.textContent) || 0;
        updateFinalDecision(critical, major, minor);
    }
    
    // Check submit button status
    checkTrimsSubmitButtonStatus();
    
    console.log(`Updated checklist item ${itemId}: ${field} = ${value}`);
}

// Update checklist summary counts
function updateChecklistSummary() {
    if (!Array.isArray(trimsInspectionState.checklistData)) return;
    
    let passCount = 0, failCount = 0, naCount = 0, pendingCount = 0;
    
    trimsInspectionState.checklistData.forEach(item => {
        const status = item.results?.status;
        if (status === 'Pass') passCount++;
        else if (status === 'Fail') failCount++;
        else if (status === 'N/A') naCount++;
        else pendingCount++;
    });
    
    updateElement('checklist-pass-count', passCount);
    updateElement('checklist-fail-count', failCount);
    updateElement('checklist-na-count', naCount);
    updateElement('checklist-pending-count', pendingCount);
    
    // Update overall inspection status based on checklist results
    updateOverallInspectionStatus(failCount > 0);
}

// Update overall inspection status
function updateOverallInspectionStatus(hasFailures) {
    const statusElement = document.getElementById('overall-inspection-status');
    if (!statusElement) return;
    
    if (hasFailures) {
        statusElement.className = 'status-badge status-danger';
        statusElement.textContent = 'Failed - Check Failures';
    } else {
        statusElement.className = 'status-badge status-ok';
        statusElement.textContent = 'Passed';
    }
}

// Toggle item section
function toggleItem(itemNumber) {
    const itemBody = document.getElementById(`item-body-${itemNumber}`);
    if (itemBody) {
        itemBody.classList.toggle('expanded');
    }
}

// Expand all item sections
function expandAllItems() {
    document.querySelectorAll('.item-body').forEach(body => {
        body.classList.add('expanded');
    });
}

// Collapse all item sections
function collapseAllItems() {
    document.querySelectorAll('.item-body').forEach(body => {
        body.classList.remove('expanded');
    });
}

// Update AQL configuration
async function updateAQLConfiguration() {
    try {
        const inspectionType = document.getElementById('inspection-type')?.value || 'AQL Based';
        const aqlLevel = document.getElementById('aql-level')?.value || 'II';
        const aqlValue = document.getElementById('aql-value')?.value || '2.5';
        const inspectionRegime = document.getElementById('inspection-regime')?.value || 'Normal';
        
        // Get total pieces from inspection data
        const totalPieces = inspectionData.total_pieces || 0;
        
        // Calculate AQL sample size
        const aqlConfig = calculateAQLSampleSize(totalPieces, aqlLevel, aqlValue, inspectionRegime, inspectionType);
        
        // Update displays
        if (document.getElementById('sample-size-display')) {
            document.getElementById('sample-size-display').value = aqlConfig.samplePieces;
        }
        if (document.getElementById('sample-percentage-display')) {
            document.getElementById('sample-percentage-display').value = aqlConfig.samplePercentage + '%';
        }
        
        console.log('AQL configuration updated for trims inspection');
        
    } catch (error) {
        console.error('Error updating AQL configuration:', error);
        showMessage('Error updating AQL configuration: ' + error.message, 'error');
    }
}

// Calculate AQL sample size for count-based inspection
function calculateAQLSampleSize(totalPieces, aqlLevel, aqlValue, inspectionRegime, inspectionType) {
    // For 100% inspection, inspect all pieces
    if (inspectionType === '100% Inspection') {
        return {
            samplePieces: totalPieces,
            samplePercentage: 100
        };
    }
    
    // AQL Level to sample size mapping for count-based inspection
    const aqlSampleMap = {
        'I': { base: 5, multiplier: 1.0 },
        'II': { base: 8, multiplier: 1.2 },
        'III': { base: 13, multiplier: 1.5 },
        'S-1': { base: 3, multiplier: 0.8 },
        'S-2': { base: 5, multiplier: 0.9 },
        'S-3': { base: 8, multiplier: 1.1 },
        'S-4': { base: 13, multiplier: 1.3 }
    };
    
    // AQL Value impact on sample size
    const aqlValueMultiplier = {
        '0.4': 1.5,
        '0.65': 1.3,
        '1.0': 1.2,
        '1.5': 1.1,
        '2.5': 1.0,
        '4.0': 0.9,
        '6.5': 0.8,
        '10.0': 0.7
    };
    
    // Inspection regime impact
    const regimeMultiplier = {
        'Normal': 1.0,
        'Tightened': 1.3,
        'Reduced': 0.7
    };
    
    const levelConfig = aqlSampleMap[aqlLevel] || aqlSampleMap['II'];
    const valueMultiplier = aqlValueMultiplier[aqlValue] || 1.0;
    const regimeMultiplier_ = regimeMultiplier[inspectionRegime] || 1.0;
    
    // Calculate sample size
    let sampleSize = Math.ceil(levelConfig.base * levelConfig.multiplier * valueMultiplier * regimeMultiplier_);
    
    // Ensure we don't exceed total pieces
    sampleSize = Math.min(sampleSize, totalPieces);
    
    // Minimum 1 piece if any pieces exist
    if (totalPieces > 0 && sampleSize < 1) {
        sampleSize = 1;
    }
    
    const samplePercentage = totalPieces > 0 ? Math.round((sampleSize / totalPieces) * 100) : 0;
    
    return {
        samplePieces: sampleSize,
        samplePercentage: samplePercentage
    };
}

// Update defect count when input changes
function updateDefectCount(input) {
    if (trimsInspectionState.isCalculating) return;
    
    const itemNumber = input.dataset.item;
    const defectCode = input.dataset.defect;
    const category = input.dataset.category;
    const count = parseInt(input.value) || 0;
    
    // Create defect key
    const defectKey = `${category.toLowerCase().replace(/\s+/g, '_')}_${defectCode}`;
    
    // Initialize item data if needed
    if (!trimsInspectionState.defectsData[itemNumber]) {
        trimsInspectionState.defectsData[itemNumber] = {};
    }
    
    // Store the count
    trimsInspectionState.defectsData[itemNumber][defectKey] = count;
    trimsInspectionState.isDirty = true;
    
    // Recalculate totals
    debounce(calculateTotals, 300)();
}

// Update item meta data
function updateItemMeta(input) {
    const itemNumber = input.dataset.item;
    const field = input.dataset.field;
    const value = input.value;
    
    // Update the item data
    if (!trimsInspectionState.itemsData[itemNumber]) {
        trimsInspectionState.itemsData[itemNumber] = { item_number: itemNumber };
    }
    
    trimsInspectionState.itemsData[itemNumber][field] = value;
    trimsInspectionState.isDirty = true;
    
    // Recalculate totals
    debounce(calculateTotals, 300)();
}

// Calculate all totals
function calculateTotals() {
    if (trimsInspectionState.isCalculating) return;
    trimsInspectionState.isCalculating = true;
    
    try {
        let totalCriticalDefects = 0;
        let totalMajorDefects = 0;
        let totalMinorDefects = 0;
        let totalItems = 0;
        
        // Calculate for each item
        for (const itemNumber in trimsInspectionState.defectsData) {
            const itemDefects = trimsInspectionState.defectsData[itemNumber];
            const itemData = trimsInspectionState.itemsData[itemNumber] || {};
            
            let itemCritical = 0;
            let itemMajor = 0;
            let itemMinor = 0;
            
            // Calculate item totals
            for (const defectKey in itemDefects) {
                const count = parseInt(itemDefects[defectKey]) || 0;
                if (count > 0) {
                    // Extract defect code from key
                    const parts = defectKey.split('_');
                    const defectCode = parts[parts.length - 1];
                    
                    // Get defect severity
                    const severity = getDefectSeverity(defectCode);
                    
                    if (severity === 'Critical') {
                        itemCritical += count;
                    } else if (severity === 'Major') {
                        itemMajor += count;
                    } else {
                        itemMinor += count;
                    }
                }
            }
            
            // Update item summary displays
            updateElement(`item-critical-${itemNumber}`, itemCritical);
            updateElement(`item-major-${itemNumber}`, itemMajor);
            updateElement(`item-minor-${itemNumber}`, itemMinor);
            
            // Update item status
            updateItemStatus(itemNumber, itemCritical, itemMajor, itemMinor);
            
            // Add to final totals
            totalCriticalDefects += itemCritical;
            totalMajorDefects += itemMajor;
            totalMinorDefects += itemMinor;
            totalItems++;
        }
        
        // Update final displays
        updateElement('total-critical-defects', totalCriticalDefects);
        updateElement('total-major-defects', totalMajorDefects);
        updateElement('total-minor-defects', totalMinorDefects);
        updateElement('total-items-inspected', totalItems);
        
        // Update final decision
        updateFinalDecision(totalCriticalDefects, totalMajorDefects, totalMinorDefects);
        
        console.log('Trims inspection totals calculated successfully');
        
    } catch (error) {
        console.error('Error calculating totals:', error);
        showMessage('Error calculating totals', 'error');
    } finally {
        trimsInspectionState.isCalculating = false;
    }
}

// Get defect severity
function getDefectSeverity(defectCode) {
    // Critical defects that cause immediate rejection
    const criticalDefects = ['BROKEN', 'MISSING', 'WRONG_COLOR', 'WRONG_SIZE', 'CONTAMINATION'];
    
    // Major defects that significantly impact quality
    const majorDefects = ['SCRATCH', 'DENT', 'DISCOLORATION', 'ROUGH_EDGE', 'ASSEMBLY_ERROR'];
    
    const upperDefectCode = defectCode.toUpperCase();
    
    if (criticalDefects.some(critical => upperDefectCode.includes(critical))) {
        return 'Critical';
    } else if (majorDefects.some(major => upperDefectCode.includes(major))) {
        return 'Major';
    } else {
        return 'Minor';
    }
}

// Update item status
function updateItemStatus(itemNumber, critical, major, minor) {
    const statusElement = document.getElementById(`item-status-${itemNumber}`);
    if (!statusElement) return;
    
    let statusClass, statusText;
    
    if (critical > 0) {
        statusClass = 'status-danger';
        statusText = 'Rejected';
    } else if (major > 2 || minor > 5) {
        statusClass = 'status-warning';
        statusText = 'Conditional';
    } else {
        statusClass = 'status-ok';
        statusText = 'Accepted';
    }
    
    statusElement.className = `pill status-badge ${statusClass}`;
    statusElement.textContent = statusText;
}

// Update final decision (combines defect results with checklist results)
function updateFinalDecision(critical, major, minor) {
    const decisionElement = document.getElementById('final-decision');
    if (!decisionElement) return;
    
    // Check checklist failures
    let checklistHasFailures = false;
    if (Array.isArray(trimsInspectionState.checklistData)) {
        checklistHasFailures = trimsInspectionState.checklistData.some(item => {
            return item.results?.status === 'Fail';
        });
    }
    
    let statusClass, statusText;
    
    // If checklist has failures, override defect-based decision
    if (checklistHasFailures) {
        statusClass = 'status-danger';
        statusText = 'Failed - Checklist Failures';
    } else if (critical > 0) {
        statusClass = 'status-danger';
        statusText = 'Rejected - Critical Defects';
    } else if (major > 5 || minor > 10) {
        statusClass = 'status-warning';
        statusText = 'Conditional Accept';
    } else {
        statusClass = 'status-ok';
        statusText = 'Accepted';
    }
    
    decisionElement.className = `status-badge ${statusClass}`;
    decisionElement.style.fontSize = '16px';
    decisionElement.style.padding = '10px 20px';
    decisionElement.textContent = statusText;
}

// Clear all defects
function clearAllDefects() {
    if (!confirm('Are you sure you want to clear all defects? This action cannot be undone.')) {
        return;
    }
    
    // Clear the state
    trimsInspectionState.defectsData = {};
    trimsInspectionState.isDirty = true;
    
    // Clear all input fields
    document.querySelectorAll('.defect-input').forEach(input => {
        input.value = '';
    });
    
    // Recalculate totals
    calculateTotals();
    
    showMessage('All defects cleared', 'success');
}

// Save inspection data
async function saveTrimsInspection() {
    if (!inspectionData.canWrite) {
        showMessage('You do not have permission to save', 'error');
        return;
    }
    
    if (!trimsInspectionState.isDirty) {
        showMessage('No changes to save', 'info');
        return;
    }
    
    try {
        showMessage('Saving...', 'info');
        
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.trims_inspection.save_progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name,
                defects_data: trimsInspectionState.defectsData || {},
                items_data: trimsInspectionState.itemsData || {},
                checklist_data: trimsInspectionState.checklistData || []
            })
        });
        
        const result = await response.json();
        
        if (result.message) {
            trimsInspectionState.isDirty = false;
            showMessage('Trims inspection progress saved successfully', 'success');
            // Update inspection status automatically
            await updateTrimsInspectionStatus('In Progress');
            // Check if submit button should be enabled
            checkTrimsSubmitButtonStatus();
        } else {
            throw new Error(result.exc || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Save error:', error);
        showMessage('Error saving inspection: ' + error.message, 'error');
    }
}

// Hold trims inspection with reason
async function holdTrimsInspection() {
    if (!inspectionData.canWrite) {
        showMessage('You do not have permission to hold inspection', 'error');
        return;
    }
    
    // Show hold reason dialog
    const reason = prompt('Please provide a reason for holding this inspection:');
    if (!reason || reason.trim() === '') {
        showMessage('Hold reason is mandatory', 'warning');
        return;
    }
    
    try {
        showMessage('Holding inspection...', 'info');
        
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.trims_inspection.hold_inspection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name,
                hold_reason: reason.trim()
            })
        });
        
        const result = await response.json();
        
        if (result.message) {
            showMessage('Trims inspection placed on hold', 'warning');
            
            // Update UI immediately to reflect hold status
            updateUIForHoldStatus();
            
            // Update page header status immediately
            const statusElement = document.querySelector('.meta');
            if (statusElement) {
                statusElement.innerHTML = statusElement.innerHTML.replace(/Status: [^|]*/, 'Status: Hold');
            }
            
            // Update the global inspection data to reflect new status
            inspectionData.status = 'Hold';
            
            console.log('Trims inspection successfully placed on hold - no page refresh needed');
        } else {
            throw new Error(result.exc || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Hold error:', error);
        showMessage('Error holding inspection: ' + error.message, 'error');
    }
}

// Resume trims inspection from hold status
async function resumeTrimsInspection() {
    if (!inspectionData.canWrite) {
        showMessage('You do not have permission to resume inspection', 'error');
        return;
    }
    
    // Confirm resume action
    if (!confirm('Are you sure you want to resume this inspection? It will be moved back to In Progress status.')) {
        return;
    }
    
    try {
        showMessage('Resuming inspection...', 'info');
        
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.trims_inspection.update_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name,
                status: 'In Progress'
            })
        });
        
        const result = await response.json();
        
        if (result.message && result.message.success) {
            showMessage('Inspection resumed successfully', 'success');
            
            // Update UI immediately without page refresh
            updateUIForResumeStatus();
            
            // Update page header status immediately
            const statusElement = document.querySelector('.meta');
            if (statusElement) {
                statusElement.innerHTML = statusElement.innerHTML.replace(/Status: [^|]*/, 'Status: In Progress');
            }
            
        } else {
            showMessage('Error resuming inspection', 'error');
        }
        
    } catch (error) {
        console.error('Error resuming inspection:', error);
        showMessage('Error resuming inspection: ' + error.message, 'error');
    }
}

// Submit trims inspection for completion
async function submitTrimsInspection() {
    if (!inspectionData.canWrite) {
        showMessage('You do not have permission to submit inspection', 'error');
        return;
    }
    
    // Check if inspection is ready for submission
    const isReady = checkTrimsInspectionCompleteness();
    if (!isReady.ready) {
        showMessage(`Cannot submit: ${isReady.reason}`, 'warning');
        return;
    }
    
    // Confirm submission
    if (!confirm('Are you sure you want to submit this inspection for completion? This action cannot be undone.')) {
        return;
    }
    
    try {
        showMessage('Submitting inspection...', 'info');
        
        // Save current data first
        await saveTrimsInspection();
        
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.trims_inspection.submit_inspection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name
            })
        });
        
        const result = await response.json();
        
        if (result.message) {
            showMessage('Trims inspection submitted successfully', 'success');
            // Disable all editing capabilities
            disableTrimsEditingUI();
            // Refresh page to show completed status
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            throw new Error(result.exc || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Submit error:', error);
        showMessage('Error submitting inspection: ' + error.message, 'error');
    }
}

// Update trims inspection status
async function updateTrimsInspectionStatus(status) {
    try {
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.trims_inspection.update_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name,
                status: status
            })
        });
        
        const result = await response.json();
        if (!result.message) {
            console.error('Failed to update trims inspection status:', result.exc);
        }
    } catch (error) {
        console.error('Trims status update error:', error);
    }
}

// Check if trims inspection is complete and ready for submission
function checkTrimsInspectionCompleteness() {
    // Check if mandatory physical testing results are completed
    let mandatoryChecklistCompleted = true;
    let mandatoryFailures = 0;
    
    if (Array.isArray(trimsInspectionState.checklistData)) {
        for (const item of trimsInspectionState.checklistData) {
            if (item.is_mandatory) {
                const status = item.results?.status;
                if (!status || status === '') {
                    mandatoryChecklistCompleted = false;
                    break;
                }
                if (status === 'Fail') {
                    mandatoryFailures++;
                }
            }
        }
    }
    
    if (!mandatoryChecklistCompleted) {
        return { ready: false, reason: 'Mandatory physical testing results are not completed' };
    }
    
    // Check if there are any defects or checklist data entered
    const hasDefects = Object.keys(trimsInspectionState.defectsData).length > 0;
    const hasChecklistData = Array.isArray(trimsInspectionState.checklistData) && 
                            trimsInspectionState.checklistData.some(item => item.results?.status);
    
    if (!hasDefects && !hasChecklistData) {
        return { ready: false, reason: 'No inspection data has been recorded' };
    }
    
    return { ready: true };
}

// Check if submit button should be enabled for trims
function checkTrimsSubmitButtonStatus() {
    const submitBtn = document.getElementById('submit-trims-inspection-btn');
    if (!submitBtn) return;
    
    const completeness = checkTrimsInspectionCompleteness();
    submitBtn.disabled = !completeness.ready;
    
    if (completeness.ready) {
        submitBtn.title = 'Submit inspection for completion';
        submitBtn.classList.remove('btn-secondary');
        submitBtn.classList.add('btn-success');
    } else {
        submitBtn.title = completeness.reason;
        submitBtn.classList.remove('btn-success');
        submitBtn.classList.add('btn-secondary');
    }
}


// Disable editing UI when trims inspection is completed
function disableTrimsEditingUI() {
    // Disable all input fields
    document.querySelectorAll('input, select, textarea').forEach(element => {
        element.disabled = true;
    });
    
    // Disable all action buttons
    document.querySelectorAll('.btn:not([href])').forEach(button => {
        button.disabled = true;
    });
}

// Utility functions
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
        console.log(`Updated element ${id} with value: ${value}`);
    } else {
        console.warn(`Element with ID '${id}' not found. Value: ${value}`);
        
        // Try to find element by class or other attributes if ID doesn't work
        const altElement = document.querySelector(`[data-id="${id}"], .${id}, [name="${id}"]`);
        if (altElement) {
            altElement.textContent = value;
            console.log(`Updated alternative element for ${id} with value: ${value}`);
        }
    }
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('message-container');
    if (!container) return;
    
    const messageEl = document.createElement('div');
    messageEl.className = `alert alert-${type} alert-dismissible fade show`;
    messageEl.style.marginBottom = '10px';
    messageEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    container.appendChild(messageEl);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageEl.parentElement) {
            messageEl.remove();
        }
    }, 5000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Warning before leaving if there are unsaved changes
window.addEventListener('beforeunload', function(e) {
    if (trimsInspectionState.isDirty) {
        e.preventDefault();
        e.returnValue = '';
        return '';
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+S to save
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        saveTrimsInspection();
    }
    
    // Ctrl+R to recalculate
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        calculateTotals();
    }
});

// Check inspection status on page load and apply UI updates if needed
async function checkInspectionStatusOnLoad() {
    try {
        // Get current inspection status from the page
        const statusElement = document.querySelector('.meta');
        if (!statusElement) return;
        
        const statusText = statusElement.textContent || statusElement.innerText;
        const statusMatch = statusText.match(/Status:\s*([^|]*)/);
        if (!statusMatch) return;
        
        const currentStatus = statusMatch[1].trim();
        console.log('Current trims inspection status:', currentStatus);
        
        // Apply appropriate UI updates based on status
        if (currentStatus === 'Hold') {
            updateUIForHoldStatus();
            showMessage('This inspection is currently on hold', 'warning');
        } else if (currentStatus === 'Completed') {
            updateUIForCompletedStatus();
            showMessage('This inspection has been completed', 'info');
        }
        
    } catch (error) {
        console.error('Error checking trims inspection status on load:', error);
    }
}

// Update UI for hold status
function updateUIForHoldStatus() {
    // Disable all input elements
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.disabled = true;
    });
    
    // Add hold notice to page header
    const pageHeader = document.querySelector('.page-header');
    if (pageHeader) {
        let holdNotice = pageHeader.querySelector('.hold-notice');
        if (!holdNotice) {
            holdNotice = document.createElement('div');
            holdNotice.className = 'hold-notice';
            holdNotice.style.cssText = `
                background: #fff3cd; 
                color: #856404; 
                padding: 10px; 
                margin-top: 10px; 
                border-radius: 6px; 
                border: 1px solid #ffeaa7;
                text-align: center;
                font-weight: 500;
            `;
            holdNotice.innerHTML = '⏸️ This inspection is on hold - Click Resume to continue working';
            pageHeader.appendChild(holdNotice);
        }
    }
    
    // Update action buttons - show Resume button and hide others
    const holdBtn = document.querySelector('button[onclick*="holdTrimsInspection"]');
    const submitBtn = document.querySelector('button[onclick*="submitTrimsInspection"]');
    const saveBtn = document.querySelector('button[onclick*="saveTrimsInspection"]');
    
    // Hide all regular action buttons
    if (holdBtn) holdBtn.style.display = 'none';
    if (submitBtn) submitBtn.style.display = 'none';
    if (saveBtn) saveBtn.style.display = 'none';
    
    // Create and show Resume button if it doesn't exist
    let resumeBtn = document.querySelector('button[onclick*="resumeTrimsInspection"]');
    if (!resumeBtn) {
        resumeBtn = document.createElement('button');
        resumeBtn.className = 'btn btn-info';
        resumeBtn.onclick = resumeTrimsInspection;
        resumeBtn.innerHTML = '▶️ Resume';
        
        // Insert the Resume button in the actions container
        const actionsContainer = holdBtn?.parentElement || submitBtn?.parentElement || saveBtn?.parentElement;
        if (actionsContainer) {
            actionsContainer.insertBefore(resumeBtn, actionsContainer.firstChild);
        }
    } else {
        resumeBtn.style.display = 'inline-block';
    }
}

// Update UI when resuming from hold status
function updateUIForResumeStatus() {
    // Re-enable all input elements
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.disabled = false;
    });
    
    // Remove hold notice from page header
    const holdNotice = document.querySelector('.hold-notice');
    if (holdNotice) {
        holdNotice.remove();
    }
    
    // Hide Resume button and show normal action buttons
    const resumeBtn = document.querySelector('button[onclick*="resumeTrimsInspection"]');
    const holdBtn = document.querySelector('button[onclick*="holdTrimsInspection"]');
    const submitBtn = document.querySelector('button[onclick*="submitTrimsInspection"]');
    const saveBtn = document.querySelector('button[onclick*="saveTrimsInspection"]');
    
    if (resumeBtn) resumeBtn.style.display = 'none';
    if (holdBtn) holdBtn.style.display = 'inline-block';
    if (submitBtn) submitBtn.style.display = 'inline-block';
    if (saveBtn) saveBtn.style.display = 'inline-block';
}

// Update UI for completed status
function updateUIForCompletedStatus() {
    // Disable all editing inputs but keep read-only access
    const inputs = document.querySelectorAll('input:not([readonly]), select, textarea');
    inputs.forEach(input => {
        input.disabled = true;
    });
    
    // Hide all action buttons for completed status
    const actionButtons = document.querySelectorAll('button:not([href])');
    actionButtons.forEach(btn => {
        btn.style.display = 'none';
    });
    
    // Add completion notice
    const pageHeader = document.querySelector('.page-header');
    if (pageHeader) {
        let completionNotice = pageHeader.querySelector('.completion-notice');
        if (!completionNotice) {
            completionNotice = document.createElement('div');
            completionNotice.className = 'completion-notice';
            completionNotice.style.cssText = `
                background: #d4edda; 
                color: #155724; 
                padding: 10px; 
                margin-top: 10px; 
                border-radius: 6px; 
                border: 1px solid #c3e6cb;
                text-align: center;
                font-weight: 500;
            `;
            completionNotice.innerHTML = '✅ This inspection has been completed';
            pageHeader.appendChild(completionNotice);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTrimsData();
});