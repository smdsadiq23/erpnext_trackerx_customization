/**
 * Fabric Inspection UI JavaScript
 * Handles the four-point inspection system
 */

// Global state
let fabricInspectionState = {
    defectsData: {},
    rollsData: {},
    isDirty: false,
    isCalculating: false
};

// Initialize defects data from the server
function loadDefectsData() {
    try {
        if (inspectionData.defects) {
            fabricInspectionState.defectsData = inspectionData.defects;
            
            // Populate the form with existing data
            for (const rollNumber in fabricInspectionState.defectsData) {
                const rollDefects = fabricInspectionState.defectsData[rollNumber];
                
                for (const defectKey in rollDefects) {
                    const size = rollDefects[defectKey];
                    if (size > 0) {
                        // Find the input element and set its value
                        const parts = defectKey.split('_');
                        const defectCode = parts[parts.length - 1];
                        const input = document.querySelector(`input[data-roll="${rollNumber}"][data-defect="${defectCode}"]`);
                        if (input) {
                            input.value = size;
                        }
                    }
                }
            }
        }
        
        // Load rolls data
        if (inspectionData.rolls) {
            fabricInspectionState.rollsData = {};
            inspectionData.rolls.forEach(roll => {
                fabricInspectionState.rollsData[roll.roll_number] = roll;
            });
        }
        
        // Initialize AQL configuration on page load
        updateAQLConfiguration();
        
        console.log('Defects data loaded successfully');
    } catch (error) {
        console.error('Error loading defects data:', error);
        showMessage('Error loading inspection data', 'error');
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
async function updateAQLConfiguration() {
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
        
        // Mark as dirty
        fabricInspectionState.isDirty = true;
        
        showMessage(`AQL configuration updated: ${aqlConfig.sampleRolls} rolls selected for inspection`, 'success');
        
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
    const categories = {
        'Holes & Yarn Defects': ['HOLE', 'PROC_HOLE', 'THIN_YARN', 'THICK_YARN'],
        'Stains & Marks': ['BLACK_DOT', 'GREASE', 'RUST']
    };
    
    let categoryIndex = 1;
    for (const categoryName in categories) {
        const defectCodes = categories[categoryName];
        let categorySize = 0;
        let categoryPoints = 0;
        
        defectCodes.forEach(defectCode => {
            const defectKey = `${categoryName.toLowerCase().replace(/\s+/g, '_')}_${defectCode}`;
            const sizeInches = parseFloat(rollDefects[defectKey]) || 0;
            
            if (sizeInches > 0) {
                const points = calculateDefectPointsFromSize(defectCode, sizeInches);
                categorySize += sizeInches;
                categoryPoints += points;
            }
        });
        
        // Update category totals
        updateElement(`cat-size-${rollNumber}-${categoryIndex}`, categorySize.toFixed(1));
        updateElement(`cat-points-${rollNumber}-${categoryIndex}`, categoryPoints.toFixed(1));
        
        categoryIndex++;
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

// Update final decision
function updateFinalDecision(penaltyPer100) {
    const decisionElement = document.getElementById('final-decision');
    if (!decisionElement) return;
    
    let statusClass, statusText;
    
    if (penaltyPer100 <= 25) {
        statusClass = 'status-ok';
        statusText = 'Accepted';
    } else if (penaltyPer100 <= 50) {
        statusClass = 'status-warning';
        statusText = 'Conditional Accept';
    } else {
        statusClass = 'status-danger';
        statusText = 'Rejected';
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

// Duplicate roll (placeholder)
function duplicateRoll(rollNumber) {
    showMessage(`Duplicate roll ${rollNumber} - Feature coming soon`, 'info');
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
                rolls_data: fabricInspectionState.rollsData
            })
        });
        
        const result = await response.json();
        
        if (result.message) {
            fabricInspectionState.isDirty = false;
            showMessage('Inspection saved successfully', 'success');
        } else {
            throw new Error(result.exc || 'Unknown error occurred');
        }
        
    } catch (error) {
        console.error('Save error:', error);
        showMessage('Error saving inspection: ' + error.message, 'error');
    }
}

// Utility functions
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
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