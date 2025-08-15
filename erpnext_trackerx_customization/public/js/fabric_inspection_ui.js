/**
 * Fabric Inspection UI JavaScript
 * Handles the four-point inspection system
 */

// Global state
let fabricInspectionState = {
    defectsData: {},
    rollsData: {},
    checklistData: {},
    isDirty: false,
    isCalculating: false,
    materialType: null
};

// Initialize defects data from the server
async function loadDefectsData() {
    try {
        // Load fresh defects data from inspection document
        await loadExistingDefectsData();
        
        // Load rolls data
        if (inspectionData.rolls) {
            fabricInspectionState.rollsData = {};
            inspectionData.rolls.forEach(roll => {
                fabricInspectionState.rollsData[roll.roll_number] = roll;
            });
        }
        
        // Initialize AQL configuration on page load (silently)
        updateAQLConfiguration(false); // false = don't show toast message
        
        // Load material type for checklist
        fabricInspectionState.materialType = inspectionData.material_type || 'Fabrics';
        
        // Load checklist data
        loadChecklistData();
        
        // Check inspection status and apply UI updates if needed
        checkInspectionStatusOnLoad();
        
        console.log('Defects data loaded successfully');
    } catch (error) {
        console.error('Error loading defects data:', error);
        showMessage('Error loading inspection data', 'error');
    }
}

// Load existing defects data from inspection document
async function loadExistingDefectsData() {
    try {
        const response = await fetch(`/api/method/erpnext_trackerx_customization.api.fabric_inspection.get_inspection_data`, {
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
            fabricInspectionState.defectsData = result.message.defects;
            
            // Populate the form with existing defects data
            setTimeout(() => {
                populateDefectsUI();
            }, 500); // Small delay to ensure DOM is ready
            
        } else if (inspectionData.defects) {
            // Fallback to initial data
            fabricInspectionState.defectsData = inspectionData.defects;
            setTimeout(() => {
                populateDefectsUI();
            }, 500);
        }
        
        console.log('Existing defects data loaded:', fabricInspectionState.defectsData);
        
    } catch (error) {
        console.error('Error loading existing defects data:', error);
        // Fallback to initial data
        if (inspectionData.defects) {
            fabricInspectionState.defectsData = inspectionData.defects;
            setTimeout(() => {
                populateDefectsUI();
            }, 500);
        }
    }
}

// Populate the defects UI with existing data
function populateDefectsUI() {
    if (!fabricInspectionState.defectsData) return;
    
    console.log('Populating defects UI with data:', fabricInspectionState.defectsData);
    
    // Clear all inputs first
    document.querySelectorAll('.defect-input').forEach(input => {
        input.value = '';
    });
    
    // Populate with saved data
    for (const rollNumber in fabricInspectionState.defectsData) {
        const rollDefects = fabricInspectionState.defectsData[rollNumber];
        
        for (const defectKey in rollDefects) {
            let sizeValue = rollDefects[defectKey];
            
            // Skip if no value or invalid value
            if (!sizeValue || sizeValue === 0 || sizeValue === "0") continue;
            
            // Clean the size value - handle malformed data like "6No0" or concatenated values
            if (typeof sizeValue === 'string') {
                // Remove non-numeric characters except decimal point
                sizeValue = sizeValue.replace(/[^0-9.]/g, '');
                
                // Handle cases where multiple numbers are concatenated
                if (sizeValue.includes('.')) {
                    // Keep only the first decimal number
                    const match = sizeValue.match(/^\d*\.?\d+/);
                    sizeValue = match ? match[0] : sizeValue;
                }
            }
            
            // Convert to number and validate
            const cleanSize = parseFloat(sizeValue);
            if (isNaN(cleanSize) || cleanSize <= 0) {
                console.warn(`Invalid size value for ${defectKey}: ${rollDefects[defectKey]} -> cleaned: ${sizeValue} -> parsed: ${cleanSize}`);
                continue;
            }
            
            // Extract defect code from key
            const parts = defectKey.split('_');
            const defectCode = parts[parts.length - 1];
            
            // Find the input element
            const input = document.querySelector(`input[data-roll="${rollNumber}"][data-defect="${defectCode}"]`);
            if (input) {
                input.value = cleanSize;
                console.log(`Set defect ${defectCode} for roll ${rollNumber} to ${cleanSize} (original: ${rollDefects[defectKey]})`);
                
                // Also update the points and total displays
                const points = calculateDefectPointsFromSize(defectCode, cleanSize);
                const pointsElement = document.getElementById(`points-${rollNumber}-${defectCode}`);
                const totalElement = document.getElementById(`total-${rollNumber}-${defectCode}`);
                
                if (pointsElement) pointsElement.textContent = points;
                if (totalElement) totalElement.textContent = points.toFixed(1);
                
            } else {
                console.warn(`Input not found for roll ${rollNumber}, defect ${defectCode}`);
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
                material_type: fabricInspectionState.materialType
            })
        });
        
        const result = await response.json();
        
        if (result.message) {
            // Handle different response formats
            let checklistData = result.message;
            if (result.message.checklist_items) {
                checklistData = result.message.checklist_items;
            }
            
            fabricInspectionState.checklistData = Array.isArray(checklistData) ? checklistData : [];
            renderChecklistTable();
            
            // Load existing checklist results from the inspection document
            loadExistingChecklistData();
            
            console.log('Fabric checklist data loaded:', fabricInspectionState.checklistData);
        }
        
    } catch (error) {
        console.error('Error loading checklist data:', error);
        showMessage('Error loading checklist data', 'error');
    }
}

// Load existing checklist data from inspection document
async function loadExistingChecklistData() {
    try {
        const response = await fetch(`/api/method/erpnext_trackerx_customization.api.fabric_inspection.get_inspection_data`, {
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
                const index = fabricInspectionState.checklistData.findIndex(item => 
                    item.test_parameter === savedItem.test_parameter
                );
                
                if (index !== -1) {
                    // Store the saved results
                    if (!fabricInspectionState.checklistData[index].results) {
                        fabricInspectionState.checklistData[index].results = {};
                    }
                    fabricInspectionState.checklistData[index].results = {
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
    if (!Array.isArray(fabricInspectionState.checklistData)) return;
    
    fabricInspectionState.checklistData.forEach((item, index) => {
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
    if (!checklistContainer || !fabricInspectionState.checklistData) return;
    
    let tableHTML = `
        <div class="checklist-section">
            <h4>Physical Testing Results - ${fabricInspectionState.materialType}</h4>
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
    
    fabricInspectionState.checklistData.forEach((item, index) => {
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
                            <span id="checklist-pending-count">${fabricInspectionState.checklistData.length}</span>
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
    if (!fabricInspectionState.checklistData) return;
    
    const index = parseInt(itemId.split('-')[1]);
    const checklistItem = fabricInspectionState.checklistData[index];
    
    if (!checklistItem.results) {
        checklistItem.results = {};
    }
    
    checklistItem.results[field] = value;
    fabricInspectionState.isDirty = true;
    
    // Update checklist summary
    updateChecklistSummary();
    
    // Recalculate final decision
    const finalPenaltyElement = document.getElementById('final-penalty-per-100');
    if (finalPenaltyElement) {
        const currentPenalty = parseFloat(finalPenaltyElement.textContent) || 0;
        updateFinalDecision(currentPenalty);
    }
    
    // Check submit button status
    checkSubmitButtonStatus();
    
    console.log(`Updated checklist item ${itemId}: ${field} = ${value}`);
}

// Update checklist summary counts
function updateChecklistSummary() {
    if (!Array.isArray(fabricInspectionState.checklistData)) return;
    
    let passCount = 0, failCount = 0, naCount = 0, pendingCount = 0;
    
    fabricInspectionState.checklistData.forEach(item => {
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

// Toggle roll section
function toggleRoll(rollNumber) {
    const rollBody = document.getElementById(`roll-body-${rollNumber}`);
    if (rollBody) {
        rollBody.classList.toggle('expanded');
    }
}

// Expand all roll sections
function expandAllRolls() {
    document.querySelectorAll('.roll-body').forEach(body => {
        body.classList.add('expanded');
    });
}

// Collapse all roll sections
function collapseAllRolls() {
    document.querySelectorAll('.roll-body').forEach(body => {
        body.classList.remove('expanded');
    });
}

// Update AQL configuration when user changes settings
async function updateAQLConfiguration(showToast = true) {
    try {
        const inspectionType = document.getElementById('inspection-type').value;
        const aqlLevel = document.getElementById('aql-level').value;
        const aqlValue = document.getElementById('aql-value').value;
        const inspectionRegime = document.getElementById('inspection-regime').value;
        
        // Get total rolls from inspection data
        const totalRolls = inspectionData.rolls ? inspectionData.rolls.length : 0;
        
        // Calculate AQL sample size based on configuration
        const aqlConfig = calculateAQLSampleSize(totalRolls, aqlLevel, aqlValue, inspectionRegime, inspectionType);
        
        // Update displays
        document.getElementById('sample-size-display').value = aqlConfig.samplePercentage + '%';
        document.getElementById('sample-rolls-display').value = aqlConfig.sampleRolls;
        
        // Update summary text
        document.getElementById('aql-config-text').textContent = `${aqlLevel} level with ${aqlValue}% defect tolerance`;
        document.getElementById('sampling-text').textContent = `${aqlConfig.sampleRolls} rolls out of ${totalRolls} total rolls`;
        
        // Refresh the rolls display based on new AQL configuration
        await refreshRollsBasedOnAQL(aqlConfig);
        
        // Mark as dirty only if this is a user-triggered change
        if (showToast) {
            fabricInspectionState.isDirty = true;
        }
        
        // Only show toast message if requested (user interaction)
        if (showToast) {
            showMessage(`AQL configuration updated: ${aqlConfig.sampleRolls} rolls selected for inspection`, 'success');
        }
        
    } catch (error) {
        console.error('Error updating AQL configuration:', error);
        showMessage('Error updating AQL configuration: ' + error.message, 'error');
    }
}

// Calculate AQL sample size based on configuration
function calculateAQLSampleSize(totalRolls, aqlLevel, aqlValue, inspectionRegime, inspectionType) {
    // For 100% inspection, inspect all rolls
    if (inspectionType === '100% Inspection') {
        return {
            sampleRolls: totalRolls,
            samplePercentage: 100
        };
    }
    
    // AQL Level to sample size mapping (industry standard)
    const aqlSampleMap = {
        'I': { base: 5, multiplier: 1.0 },
        'II': { base: 10, multiplier: 1.2 },
        'III': { base: 15, multiplier: 1.5 },
        'S-1': { base: 3, multiplier: 0.8 },
        'S-2': { base: 5, multiplier: 0.9 },
        'S-3': { base: 8, multiplier: 1.1 },
        'S-4': { base: 12, multiplier: 1.3 }
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
    
    // Ensure we don't exceed total rolls
    sampleSize = Math.min(sampleSize, totalRolls);
    
    // Minimum 1 roll if any rolls exist
    if (totalRolls > 0 && sampleSize < 1) {
        sampleSize = 1;
    }
    
    const samplePercentage = totalRolls > 0 ? Math.round((sampleSize / totalRolls) * 100) : 0;
    
    return {
        sampleRolls: sampleSize,
        samplePercentage: samplePercentage
    };
}

// Refresh rolls display based on new AQL configuration
async function refreshRollsBasedOnAQL(aqlConfig) {
    try {
        // This would ideally call the server to get filtered rolls
        // For now, we'll simulate the selection
        const allRolls = inspectionData.rolls || [];
        const selectedRolls = selectRollsForInspection(allRolls, aqlConfig.sampleRolls);
        
        // Update the selected rolls display
        const rollNames = selectedRolls.map(roll => roll.roll_number).join(', ');
        document.getElementById('selected-rolls-text').textContent = 
            `${selectedRolls.length} rolls - ${rollNames}`;
        
        // Update fabricInspectionState with new roll selection
        fabricInspectionState.rollsData = {};
        selectedRolls.forEach(roll => {
            fabricInspectionState.rollsData[roll.roll_number] = roll;
        });
        
        console.log(`Selected ${selectedRolls.length} rolls for inspection based on AQL configuration`);
        
    } catch (error) {
        console.error('Error refreshing rolls:', error);
        throw error;
    }
}

// Select rolls for inspection using systematic sampling
function selectRollsForInspection(allRolls, sampleCount) {
    if (sampleCount >= allRolls.length) {
        return allRolls;
    }
    
    if (sampleCount <= 0) {
        return [];
    }
    
    const selectedRolls = [];
    const interval = Math.floor(allRolls.length / sampleCount);
    
    // Systematic sampling
    for (let i = 0; i < sampleCount; i++) {
        const index = i * interval;
        if (index < allRolls.length) {
            selectedRolls.push(allRolls[index]);
        }
    }
    
    // If we still need more rolls, add from remaining
    while (selectedRolls.length < sampleCount && selectedRolls.length < allRolls.length) {
        for (const roll of allRolls) {
            if (!selectedRolls.find(selected => selected.roll_number === roll.roll_number)) {
                selectedRolls.push(roll);
                if (selectedRolls.length >= sampleCount) break;
            }
        }
    }
    
    return selectedRolls;
}

// Update defect size when input changes - now with inch-based point calculation
function updateDefectSize(input) {
    if (fabricInspectionState.isCalculating) return;
    
    const rollNumber = input.dataset.roll;
    const defectCode = input.dataset.defect;
    const category = input.dataset.category;
    const sizeInches = parseFloat(input.value) || 0;
    
    // Calculate points based on defect size in inches (industry standard)
    const points = calculateDefectPointsFromSize(defectCode, sizeInches);
    
    // Update the points display
    const pointsElement = document.getElementById(`points-${rollNumber}-${defectCode}`);
    if (pointsElement) {
        pointsElement.textContent = points;
    }
    
    // Create defect key
    const defectKey = `${category.toLowerCase().replace(/\s+/g, '_')}_${defectCode}`;
    
    // Initialize roll data if needed
    if (!fabricInspectionState.defectsData[rollNumber]) {
        fabricInspectionState.defectsData[rollNumber] = {};
    }
    
    // Store the size in inches
    fabricInspectionState.defectsData[rollNumber][defectKey] = sizeInches;
    fabricInspectionState.isDirty = true;
    
    // Calculate total points for this defect
    const totalPoints = points; // Points are already calculated based on size
    
    // Update the total points display
    const totalElement = document.getElementById(`total-${rollNumber}-${defectCode}`);
    if (totalElement) {
        totalElement.textContent = totalPoints.toFixed(1);
    }
    
    // Recalculate totals
    debounce(calculateTotals, 300)();
}

// Calculate defect points based on size in inches (industry standard four-point system)
function calculateDefectPointsFromSize(defectCode, sizeInches) {
    if (sizeInches <= 0) return 0;
    
    // Industry standard four-point system based on defect size
    // These thresholds are configurable and should ideally come from defect master
    
    const defectType = defectCode.toLowerCase();
    
    // Critical defects (holes, cuts, tears) - stricter thresholds
    if (defectType.includes('hole') || defectType.includes('cut') || defectType.includes('tear')) {
        if (sizeInches <= 1) return 1;
        if (sizeInches <= 3) return 2;
        if (sizeInches <= 6) return 3;
        return 4;
    }
    
    // Stains and marks - moderate thresholds
    if (defectType.includes('stain') || defectType.includes('spot') || defectType.includes('mark')) {
        if (sizeInches <= 2) return 1;
        if (sizeInches <= 4) return 2;
        if (sizeInches <= 8) return 3;
        return 4;
    }
    
    // Yarn defects - lenient thresholds as they're often longer
    if (defectType.includes('yarn') || defectType.includes('thread')) {
        if (sizeInches <= 3) return 1;
        if (sizeInches <= 6) return 2;
        if (sizeInches <= 12) return 3;
        return 4;
    }
    
    // Default defect thresholds
    if (sizeInches <= 2) return 1;
    if (sizeInches <= 4) return 2;
    if (sizeInches <= 8) return 3;
    return 4;
}

// Update roll meta data
function updateRollMeta(input) {
    const rollNumber = input.dataset.roll;
    const field = input.dataset.field;
    const value = input.value;
    
    // Update the roll data
    if (!fabricInspectionState.rollsData[rollNumber]) {
        fabricInspectionState.rollsData[rollNumber] = { roll_number: rollNumber };
    }
    
    fabricInspectionState.rollsData[rollNumber][field] = value;
    fabricInspectionState.isDirty = true;
    
    // Update the header display if needed
    const rollHeader = document.querySelector(`[data-roll="${rollNumber}"] .roll-header`);
    if (rollHeader) {
        if (field === 'roll_width') {
            const widthPill = rollHeader.querySelector('.pill:nth-child(3)');
            if (widthPill) widthPill.textContent = `Width: ${value}"`;
        } else if (field === 'roll_length') {
            const lengthPill = rollHeader.querySelector('.pill:nth-child(2)');
            if (lengthPill) lengthPill.textContent = `Length: ${value}m`;
        } else if (field === 'gsm') {
            const gsmPill = rollHeader.querySelector('.pill:nth-child(4)');
            if (gsmPill) gsmPill.textContent = `GSM: ${value}`;
        }
    }
    
    // Recalculate totals
    debounce(calculateTotals, 300)();
}

// Calculate all totals
function calculateTotals() {
    if (fabricInspectionState.isCalculating) return;
    fabricInspectionState.isCalculating = true;
    
    try {
        let finalTotalPoints = 0;
        let finalTotalMeters = 0;
        let finalTotalWidth = 0;
        let rollCount = 0;
        
        // Calculate for each roll
        for (const rollNumber in fabricInspectionState.defectsData) {
            const rollDefects = fabricInspectionState.defectsData[rollNumber];
            const rollData = fabricInspectionState.rollsData[rollNumber] || {};
            
            let rollTotalSize = 0;
            let rollTotalPoints = 0;
            
            // Calculate roll totals - now using size-based point calculation
            for (const defectKey in rollDefects) {
                const sizeInches = parseFloat(rollDefects[defectKey]) || 0;
                if (sizeInches > 0) {
                    // Extract defect code from key
                    const parts = defectKey.split('_');
                    const defectCode = parts[parts.length - 1];
                    
                    // Calculate points based on size
                    const points = calculateDefectPointsFromSize(defectCode, sizeInches);
                    
                    rollTotalSize += sizeInches;
                    rollTotalPoints += points;
                }
            }
            
            // Update roll summary displays
            updateElement(`roll-total-size-${rollNumber}`, rollTotalSize.toFixed(1));
            updateElement(`roll-total-points-${rollNumber}`, rollTotalPoints.toFixed(1));
            
            // Calculate points per 100 sqm for this roll using industry standard formula
            const rollLength = parseFloat(rollData.roll_length) || 0;
            const rollWidth = parseFloat(rollData.roll_width) || 0;
            
            // Industry standard: Points per 100 sqm = (Total Points × 39.37 × 100) / (Length (m) × Width (inches))
            // The 39.37 factor converts inches to meters (39.37 inches = 1 meter)
            const pointsPer100 = (rollLength > 0 && rollWidth > 0) ? 
                (rollTotalPoints * 39.37 * 100) / (rollLength * rollWidth) : 0;
            
            updateElement(`roll-points-per-100-${rollNumber}`, pointsPer100.toFixed(1));
            
            // Update roll status
            updateRollStatus(rollNumber, pointsPer100);
            
            // Calculate category totals for this roll
            calculateCategoryTotals(rollNumber, rollDefects);
            
            // Add to final totals
            finalTotalPoints += rollTotalPoints;
            finalTotalMeters += rollLength;
            finalTotalWidth += rollWidth;
            rollCount++;
        }
        
        // Calculate final results using industry standard formula
        const avgDia = rollCount > 0 ? finalTotalWidth / rollCount : 0;
        
        // Industry standard: Final penalty per 100 sqm = (Total Points × 39.37 × 100) / (Total Length (m) × Average Width (inches))
        const finalPenaltyPer100 = (finalTotalMeters > 0 && avgDia > 0) ? 
            (finalTotalPoints * 39.37 * 100) / (finalTotalMeters * avgDia) : 0;
        
        // Update final displays
        updateElement('final-total-points', finalTotalPoints.toFixed(1));
        updateElement('final-total-meters', finalTotalMeters.toFixed(1));
        updateElement('final-avg-dia', avgDia.toFixed(1));
        updateElement('final-penalty-per-100', finalPenaltyPer100.toFixed(1));
        
        // Update final decision
        updateFinalDecision(finalPenaltyPer100);
        
        console.log('Totals calculated successfully');
        
    } catch (error) {
        console.error('Error calculating totals:', error);
        showMessage('Error calculating totals', 'error');
    } finally {
        fabricInspectionState.isCalculating = false;
    }
}

// Calculate category totals for a roll
function calculateCategoryTotals(rollNumber, rollDefects) {
    try {
        // Get all defect inputs for this roll to determine categories dynamically
        const defectInputs = document.querySelectorAll(`input[data-roll="${rollNumber}"]`);
        const categoriesFound = new Map();
        
        // Group defects by category
        defectInputs.forEach(input => {
            const category = input.dataset.category;
            const defectCode = input.dataset.defect;
            if (category && defectCode) {
                if (!categoriesFound.has(category)) {
                    categoriesFound.set(category, []);
                }
                categoriesFound.get(category).push(defectCode);
            }
        });
        
        let categoryIndex = 1;
        
        // Calculate totals for each category found
        categoriesFound.forEach((defectCodes, categoryName) => {
            let categorySize = 0;
            let categoryPoints = 0;
            
            defectCodes.forEach(defectCode => {
                // Create defect key using the same format as updateDefectSize function
                const defectKey = `${categoryName.toLowerCase().replace(/\s+/g, '_')}_${defectCode}`;
                const sizeInches = parseFloat(rollDefects[defectKey]) || 0;
                
                if (sizeInches > 0) {
                    const points = calculateDefectPointsFromSize(defectCode, sizeInches);
                    categorySize += sizeInches;
                    categoryPoints += points;
                }
            });
            
            // Update category totals - find elements by both possible ID formats
            const sizeElementId = `cat-size-${rollNumber}-${categoryIndex}`;
            const pointsElementId = `cat-points-${rollNumber}-${categoryIndex}`;
            
            updateElement(sizeElementId, categorySize.toFixed(1));
            updateElement(pointsElementId, categoryPoints.toFixed(1));
            
            // Also try alternative ID formats if the above don't exist
            const altSizeElementId = `category-size-total-${rollNumber}-${categoryIndex}`;
            const altPointsElementId = `category-points-total-${rollNumber}-${categoryIndex}`;
            
            updateElement(altSizeElementId, categorySize.toFixed(1));
            updateElement(altPointsElementId, categoryPoints.toFixed(1));
            
            // Try category-specific IDs
            const categorySlug = categoryName.toLowerCase().replace(/[^a-z0-9]/g, '-');
            const catSpecificSizeId = `${categorySlug}-size-total-${rollNumber}`;
            const catSpecificPointsId = `${categorySlug}-points-total-${rollNumber}`;
            
            updateElement(catSpecificSizeId, categorySize.toFixed(1));
            updateElement(catSpecificPointsId, categoryPoints.toFixed(1));
            
            console.log(`Category ${categoryName} totals - Size: ${categorySize.toFixed(1)}, Points: ${categoryPoints.toFixed(1)}`);
            
            categoryIndex++;
        });
        
        // Also update any grand category totals across all categories for this roll
        updateRollCategoryGrandTotals(rollNumber, rollDefects);
        
    } catch (error) {
        console.error('Error calculating category totals:', error);
    }
}

// Update grand totals for all categories in a roll
function updateRollCategoryGrandTotals(rollNumber, rollDefects) {
    try {
        let grandTotalSize = 0;
        let grandTotalPoints = 0;
        
        // Sum all defects for this roll
        for (const defectKey in rollDefects) {
            const sizeInches = parseFloat(rollDefects[defectKey]) || 0;
            if (sizeInches > 0) {
                const parts = defectKey.split('_');
                const defectCode = parts[parts.length - 1];
                const points = calculateDefectPointsFromSize(defectCode, sizeInches);
                
                grandTotalSize += sizeInches;
                grandTotalPoints += points;
            }
        }
        
        // Update grand total elements
        updateElement(`grand-category-size-total-${rollNumber}`, grandTotalSize.toFixed(1));
        updateElement(`grand-category-points-total-${rollNumber}`, grandTotalPoints.toFixed(1));
        updateElement(`all-categories-size-${rollNumber}`, grandTotalSize.toFixed(1));
        updateElement(`all-categories-points-${rollNumber}`, grandTotalPoints.toFixed(1));
        
    } catch (error) {
        console.error('Error calculating grand category totals:', error);
    }
}

// Get points for a defect key - now using server-side defect master calculation
function getPointsForDefectKey(defectKey) {
    // Extract defect code from key
    const parts = defectKey.split('_');
    const defectCode = parts[parts.length - 1];
    
    // First check if we have defect data from server with actual points
    if (window.defectCategoriesData) {
        for (const categoryName in window.defectCategoriesData) {
            const defects = window.defectCategoriesData[categoryName];
            const defect = defects.find(d => d.code === defectCode);
            if (defect) {
                return defect.points;
            }
        }
    }
    
    // Fallback to hardcoded mapping if server data not available
    const pointsMap = {
        'HOLE': 4,
        'holes': 4,
        'processing-holes': 4,
        'PROC_HOLE': 4,
        'thin-yarn': 2,
        'THIN_YARN': 2,
        'thick-yarn': 2,
        'THICK_YARN': 2,
        'black-dot-oil-stain': 3,
        'BLACK_DOT': 3,
        'grease-mark': 3,
        'GREASE': 3,
        'rust-stain': 3,
        'RUST': 3
    };
    
    return pointsMap[defectCode] || 2;
}

// Update roll status based on points per 100 sqm
function updateRollStatus(rollNumber, pointsPer100) {
    const statusElement = document.getElementById(`status-${rollNumber}`);
    if (!statusElement) return;
    
    let statusClass, statusText;
    
    if (pointsPer100 <= 25) {
        statusClass = 'status-ok';
        statusText = 'First Quality';
    } else if (pointsPer100 <= 50) {
        statusClass = 'status-warning';
        statusText = 'Second Quality';
    } else {
        statusClass = 'status-danger';
        statusText = 'Rejected';
    }
    
    statusElement.className = `pill status-badge ${statusClass}`;
    statusElement.textContent = statusText;
}

// Update final decision (combines defect results with checklist results)
function updateFinalDecision(penaltyPer100) {
    const decisionElement = document.getElementById('final-decision');
    if (!decisionElement) return;
    
    // Check checklist failures
    let checklistHasFailures = false;
    if (Array.isArray(fabricInspectionState.checklistData)) {
        checklistHasFailures = fabricInspectionState.checklistData.some(item => {
            return item.results?.status === 'Fail';
        });
    }
    
    let statusClass, statusText;
    
    // If checklist has failures, override defect-based decision
    if (checklistHasFailures) {
        statusClass = 'status-danger';
        statusText = 'Failed - Checklist Failures';
    } else if (penaltyPer100 <= 25) {
        statusClass = 'status-ok';
        statusText = 'Accepted';
    } else if (penaltyPer100 <= 50) {
        statusClass = 'status-warning';
        statusText = 'Conditional Accept';
    } else {
        statusClass = 'status-danger';
        statusText = 'Rejected - Defect Points';
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
    fabricInspectionState.defectsData = {};
    fabricInspectionState.isDirty = true;
    
    // Clear all input fields
    document.querySelectorAll('.defect-input').forEach(input => {
        input.value = '';
    });
    
    // Recalculate totals
    calculateTotals();
    
    showMessage('All defects cleared', 'success');
}

// Duplicate defect entry - allows multiple instances of same defect type
function duplicateDefectEntry(rollNumber, defectCode, categoryName, defectName) {
    // Find the target tbody to add the new row
    const originalRow = document.getElementById(`defect-row-${rollNumber}-${defectCode}`);
    if (!originalRow) {
        showMessage(`Could not find defect row for ${defectName}`, 'error');
        return;
    }
    
    const tbody = originalRow.closest('tbody');
    
    // Create unique ID for the duplicated row
    const timestamp = Date.now();
    const duplicateId = `${defectCode}_dup_${timestamp}`;
    
    // Clone the original row
    const newRow = originalRow.cloneNode(true);
    newRow.id = `defect-row-${rollNumber}-${duplicateId}`;
    
    // Keep the original defect name (no "(Copy)" suffix)
    const nameSpan = newRow.querySelector('span');
    nameSpan.textContent = defectName;
    
    // Update button onclick to use new duplicate ID but keep original defect name
    const duplicateBtn = newRow.querySelector('button');
    duplicateBtn.setAttribute('onclick', 
        `duplicateDefectEntry('${rollNumber}', '${duplicateId}', '${categoryName}', '${defectName}')`);
    
    // Update input field attributes
    const input = newRow.querySelector('input.defect-input');
    input.setAttribute('data-defect', duplicateId);
    input.value = ''; // Clear the value
    
    // Update points display elements
    const pointsCell = newRow.querySelector('.defect-points-auto');
    pointsCell.id = `points-${rollNumber}-${duplicateId}`;
    pointsCell.textContent = '0';
    
    const totalCell = newRow.querySelector('.defect-total-points');
    totalCell.id = `total-${rollNumber}-${duplicateId}`;
    totalCell.textContent = '0.0';
    
    // Add delete button to the duplicated entry
    const nameDiv = newRow.querySelector('div');
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-xs btn-danger';
    deleteBtn.style.cssText = 'padding: 2px 6px; font-size: 11px; margin-left: 4px;';
    deleteBtn.title = 'Remove this duplicate entry';
    deleteBtn.textContent = '🗑️';
    deleteBtn.onclick = function() { removeDuplicateDefectEntry(rollNumber, duplicateId); };
    nameDiv.appendChild(deleteBtn);
    
    // Insert the new row after the original row
    originalRow.parentNode.insertBefore(newRow, originalRow.nextSibling);
    
    showMessage(`Duplicated ${defectName} entry for Roll ${rollNumber}`, 'success');
}

// Remove duplicate defect entry
function removeDuplicateDefectEntry(rollNumber, defectCode) {
    const row = document.getElementById(`defect-row-${rollNumber}-${defectCode}`);
    if (row) {
        row.remove();
        
        // Recalculate totals after removing the row
        calculateTotals();
        
        showMessage(`Removed duplicate defect entry`, 'info');
    }
}

// Save inspection data
async function saveInspection() {
    if (!inspectionData.canWrite) {
        showMessage('You do not have permission to save', 'error');
        return;
    }
    
    if (!fabricInspectionState.isDirty) {
        showMessage('No changes to save', 'info');
        return;
    }
    
    try {
        showMessage('Saving...', 'info');
        
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.fabric_inspection.save_inspection_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                inspection_name: inspectionData.name,
                defects_data: fabricInspectionState.defectsData,
                rolls_data: fabricInspectionState.rollsData,
                checklist_data: fabricInspectionState.checklistData,
                action: 'save_progress'
            })
        });
        
        const result = await response.json();
        
        if (result.message) {
            fabricInspectionState.isDirty = false;
            showMessage('Inspection progress saved successfully', 'success');
            // Update inspection status automatically
            await updateInspectionStatus('In Progress');
            // Check if submit button should be enabled
            checkSubmitButtonStatus();
        } else {
            throw new Error(result.exc || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Save error:', error);
        showMessage('Error saving inspection: ' + error.message, 'error');
    }
}

// Hold inspection with reason
async function holdInspection() {
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
        
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.fabric_inspection.hold_inspection', {
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
            showMessage('Inspection placed on hold', 'warning');
            
            // Update UI immediately to reflect hold status
            updateUIForHoldStatus();
            
            // Update page header status immediately
            const statusElement = document.querySelector('.meta');
            if (statusElement) {
                statusElement.innerHTML = statusElement.innerHTML.replace(/Status: [^|]*/, 'Status: Hold');
            }
            
            // Update the global inspection data to reflect new status
            inspectionData.status = 'Hold';
            
            console.log('Inspection successfully placed on hold - no page refresh needed');
        } else {
            throw new Error(result.exc || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Hold error:', error);
        showMessage('Error holding inspection: ' + error.message, 'error');
    }
}

// Submit inspection for completion
async function submitInspection() {
    if (!inspectionData.canWrite) {
        showMessage('You do not have permission to submit inspection', 'error');
        return;
    }
    
    // Check if inspection is ready for submission
    const isReady = checkInspectionCompleteness();
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
        await saveInspection();
        
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.fabric_inspection.submit_inspection', {
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
            showMessage('Inspection submitted successfully', 'success');
            // Disable all editing capabilities
            disableEditingUI();
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

// Update inspection status
async function updateInspectionStatus(status) {
    try {
        const response = await fetch('/api/method/erpnext_trackerx_customization.api.fabric_inspection.update_status', {
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
            console.error('Failed to update status:', result.exc);
        }
    } catch (error) {
        console.error('Status update error:', error);
    }
}

// Check if inspection is complete and ready for submission
function checkInspectionCompleteness() {
    // Check if mandatory physical testing results are completed
    let mandatoryChecklistCompleted = true;
    let mandatoryFailures = 0;
    
    if (Array.isArray(fabricInspectionState.checklistData)) {
        for (const item of fabricInspectionState.checklistData) {
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
    const hasDefects = Object.keys(fabricInspectionState.defectsData).length > 0;
    const hasChecklistData = Array.isArray(fabricInspectionState.checklistData) && 
                            fabricInspectionState.checklistData.some(item => item.results?.status);
    
    if (!hasDefects && !hasChecklistData) {
        return { ready: false, reason: 'No inspection data has been recorded' };
    }
    
    return { ready: true };
}

// Check if submit button should be enabled
function checkSubmitButtonStatus() {
    const submitBtn = document.getElementById('submit-inspection-btn');
    if (!submitBtn) return;
    
    const completeness = checkInspectionCompleteness();
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


// Disable editing UI when inspection is completed
function disableEditingUI() {
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
    if (fabricInspectionState.isDirty) {
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
        saveInspection();
    }
    
    // Ctrl+R to recalculate
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        calculateTotals();
    }
});

// Debugging function to find category total elements
function debugCategoryTotalElements(rollNumber) {
    console.log(`=== Debugging Category Total Elements for Roll ${rollNumber} ===`);
    
    // Look for various possible element ID patterns
    const patterns = [
        `cat-size-${rollNumber}-`,
        `cat-points-${rollNumber}-`,
        `category-size-total-${rollNumber}-`,
        `category-points-total-${rollNumber}-`,
        `category-total-size-${rollNumber}`,
        `category-total-points-${rollNumber}`,
        `size-total-${rollNumber}`,
        `points-total-${rollNumber}`
    ];
    
    patterns.forEach(pattern => {
        // Try numbers 1-10 for category indices
        for (let i = 1; i <= 10; i++) {
            const id = pattern + (pattern.endsWith('-') ? i : '');
            const element = document.getElementById(id);
            if (element) {
                console.log(`Found element: ${id}`, element);
            }
        }
    });
    
    // Also look for elements with data attributes related to categories
    const categoryElements = document.querySelectorAll(`[data-roll="${rollNumber}"][data-category-total]`);
    if (categoryElements.length > 0) {
        console.log('Found elements with data-category-total:', categoryElements);
    }
    
    // Look for any element containing "total" in the ID for this roll
    const allElements = document.querySelectorAll(`[id*="${rollNumber}"][id*="total"]`);
    if (allElements.length > 0) {
        console.log('All elements with "total" in ID for this roll:', allElements);
    }
    
    console.log(`=== End Debug for Roll ${rollNumber} ===`);
}

// Add to global scope for manual debugging
window.debugCategoryTotals = debugCategoryTotalElements;

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
        console.log('Current inspection status:', currentStatus);
        
        // Apply appropriate UI updates based on status
        if (currentStatus === 'Hold') {
            updateUIForHoldStatus();
            showMessage('This inspection is currently on hold', 'warning');
        } else if (currentStatus === 'Completed') {
            updateUIForCompletedStatus();
            showMessage('This inspection has been completed', 'info');
        }
        
    } catch (error) {
        console.error('Error checking inspection status on load:', error);
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
            holdNotice.innerHTML = '⏸️ This inspection is on hold - You can still submit when ready';
            pageHeader.appendChild(holdNotice);
        }
    }
    
    // Update action buttons - keep submit button available during hold
    const holdBtn = document.querySelector('button[onclick*="holdInspection"]');
    const submitBtn = document.querySelector('button[onclick*="submitInspection"]');
    const saveBtn = document.querySelector('button[onclick*="saveInspection"]');
    
    if (holdBtn) holdBtn.style.display = 'none';
    // Keep submit button available - inspectors can submit from hold status
    if (submitBtn) {
        submitBtn.style.display = 'inline-block';
        submitBtn.disabled = false;
    }
    if (saveBtn) saveBtn.style.display = 'none';
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

// Force immediate recalculation - useful for debugging
function forceRecalculateAll() {
    console.log('=== Forcing complete recalculation ===');
    
    // Reset calculation lock
    fabricInspectionState.isCalculating = false;
    
    // Trigger calculation
    calculateTotals();
    
    console.log('Current defects data:', fabricInspectionState.defectsData);
    console.log('Current rolls data:', fabricInspectionState.rollsData);
}

// Add to global scope for manual debugging
window.forceRecalculate = forceRecalculateAll;