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

// Load AQL options dynamically (same as fabric inspection)
async function loadAQLOptions() {
    try {
        const response = await frappe.call({
            method: 'erpnext_trackerx_customization.api.aql_data.get_aql_options'
        });
        if (response && response.message) {
            // Check if API call was successful
            if (!response.message.success) {
                console.error('AQL options API call failed:', response.message);
                throw new Error('API returned success: false');
            }
            
            const data = response.message.data;
            
            // Populate AQL Level dropdown
            const aqlLevelSelect = document.getElementById('aql-level');
            if (aqlLevelSelect && data.aql_levels) {
                // Store current value to restore it
                const currentLevel = inspectionData.aql_level || '';
                
                aqlLevelSelect.innerHTML = '';
                
                // Add default option
                const defaultLevelOption = document.createElement('option');
                defaultLevelOption.value = '';
                defaultLevelOption.textContent = 'Select AQL Level';
                aqlLevelSelect.appendChild(defaultLevelOption);
                
                // Add AQL level options - extract level_code from objects
                data.aql_levels.forEach(levelObj => {
                    const option = document.createElement('option');
                    option.value = levelObj.level_code;
                    option.textContent = levelObj.level_code;
                    if (levelObj.level_code === currentLevel) {
                        option.selected = true;
                    }
                    aqlLevelSelect.appendChild(option);
                });
                
                console.log('AQL Levels loaded:', data.aql_levels.map(l => l.level_code));
            }
            
            // Populate AQL Value dropdown - using aql_standards array
            const aqlValueSelect = document.getElementById('aql-value');
            if (aqlValueSelect && data.aql_standards) {
                // Store current value to restore it
                const currentValue = inspectionData.aql_value || '';
                
                aqlValueSelect.innerHTML = '';
                
                // Add default option
                const defaultValueOption = document.createElement('option');
                defaultValueOption.value = '';
                defaultValueOption.textContent = 'Select AQL Value';
                aqlValueSelect.appendChild(defaultValueOption);
                
                // Add AQL value options - extract aql_value from objects
                data.aql_standards.forEach(standardObj => {
                    const option = document.createElement('option');
                    option.value = standardObj.aql_value;
                    option.textContent = standardObj.aql_value;
                    if (standardObj.aql_value === currentValue) {
                        option.selected = true;
                    }
                    aqlValueSelect.appendChild(option);
                });
                
                console.log('AQL Standards loaded:', data.aql_standards.map(s => s.aql_value));
            }
            
            console.log('AQL options loaded successfully for trims inspection');
        }
    } catch (error) {
        console.error('Error loading AQL options:', error);
        
        // Fallback to hardcoded options if API fails
        const aqlLevelSelect = document.getElementById('aql-level');
        const aqlValueSelect = document.getElementById('aql-value');
        
        if (aqlLevelSelect) {
            aqlLevelSelect.innerHTML = `
                <option value="">Select AQL Level</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="S1">S1</option>
                <option value="S2">S2</option>
                <option value="S3">S3</option>
                <option value="S4">S4</option>
            `;
        }
        
        if (aqlValueSelect) {
            aqlValueSelect.innerHTML = `
                <option value="">Select AQL Value</option>
                <option value="0.065">0.065</option>
                <option value="0.10">0.10</option>
                <option value="0.15">0.15</option>
                <option value="0.25">0.25</option>
                <option value="0.40">0.40</option>
                <option value="0.65">0.65</option>
                <option value="1.0">1.0</option>
                <option value="1.5">1.5</option>
                <option value="2.5">2.5</option>
                <option value="4.0">4.0</option>
                <option value="6.5">6.5</option>
                <option value="10">10</option>
                <option value="15">15</option>
                <option value="25">25</option>
                <option value="40">40</option>
                <option value="65">65</option>
                <option value="100">100</option>
                <option value="150">150</option>
            `;
        }
    }
}

// Initialize inspection data from the server
async function loadTrimsData() {
    try {
        // Load fresh defects data from inspection document
        await loadExistingDefectsData();
        
        // Load items data
        if (inspectionData.items && Array.isArray(inspectionData.items) && inspectionData.items.length > 0) {
            trimsInspectionState.itemsData = {};
            inspectionData.items.forEach((item, index) => {
                if (item && item.item_number) {
                    trimsInspectionState.itemsData[item.item_number] = item;
                } else {
                    console.warn(`Invalid item at index ${index}:`, item);
                }
            });
            console.log(`✅ Loaded ${Object.keys(trimsInspectionState.itemsData).length} items from inspection data`);
        } else {
            console.warn('No valid items data found, trying DOM fallback');
            // Fallback: try to get items from DOM
            const itemElements = document.querySelectorAll('.item-section[data-item]');
            if (itemElements.length > 0) {
                trimsInspectionState.itemsData = {};
                itemElements.forEach(element => {
                    const itemNumber = element.getAttribute('data-item');
                    const piecesElement = element.querySelector('.pill');
                    const piecesText = piecesElement ? piecesElement.textContent : '';
                    const piecesMatch = piecesText.match(/Total Pieces: (\d+)/);
                    const pieces = piecesMatch ? parseInt(piecesMatch[1]) : 200;
                    
                    trimsInspectionState.itemsData[itemNumber] = {
                        item_number: itemNumber,
                        pieces: pieces,
                        quantity: pieces
                    };
                });
                console.log(`✅ Created ${Object.keys(trimsInspectionState.itemsData).length} items from DOM fallback`);
            }
        }
        
        // Load material type for checklist
        trimsInspectionState.materialType = inspectionData.material_type || 'Trims';
        
        // Load checklist data
        loadChecklistData();
        
        // Check inspection status and apply UI updates if needed
        checkInspectionStatusOnLoad();
        
        // Initialize AQL configuration from existing document data
        console.log('🔍 Checking for existing AQL configuration in document:', {
            aql_level: inspectionData.aql_level,
            aql_value: inspectionData.aql_value,
            inspection_type: inspectionData.inspection_type,
            inspection_regime: inspectionData.inspection_regime,
            required_sample_size: inspectionData.required_sample_size,
            required_sample_pieces: inspectionData.required_sample_pieces,
            total_pieces: inspectionData.total_pieces
        });
        
        if (inspectionData.aql_level && inspectionData.aql_value) {
            // Calculate lot size from items data or use total_pieces
            let calculatedLotSize = inspectionData.total_pieces || 0;
            if (!calculatedLotSize && trimsInspectionState.itemsData) {
                calculatedLotSize = Object.values(trimsInspectionState.itemsData).reduce((sum, item) => {
                    return sum + parseInt(item.pieces || item.quantity || 0);
                }, 0);
            }
            
            // If no sample size is calculated yet, trigger automatic calculation
            if (!inspectionData.required_sample_size && calculatedLotSize > 0) {
                console.log('🔄 No sample size found - automatically calculating AQL configuration...');
                
                // Delay the automatic calculation to ensure the page is fully loaded and reduce concurrency issues
                setTimeout(async () => {
                    try {
                        console.log('🔄 Starting automatic AQL calculation after page load delay...');
                        await calculateAQLSamplingAutomatically(inspectionData.aql_level, inspectionData.aql_value, calculatedLotSize);
                    } catch (error) {
                        console.error('Error in automatic AQL calculation:', error);
                        // Fallback: Initialize with 0 sample size but still show UI
                        initializeAQLConfigWithoutSampleSize();
                        
                        // Still update the UI even if calculation failed
                        setTimeout(() => {
                            selectItemsForInspection();
                            updateAQLSummaryDisplay();
                            updateSelectedItemsSummary();
                            updateItemInspectionPieces();
                            console.log('✅ Updated UI with fallback configuration');
                        }, 100);
                    }
                }, 2500); // Increased delay to 2.5 seconds to avoid concurrency issues
            } else {
                // Initialize with existing sample size
                initializeAQLConfigWithExistingSampleSize(calculatedLotSize);
            }
        } else {
            console.log('⚠️ No existing AQL configuration found in document - will need to set up AQL config');
        }
        
        // Helper function to initialize AQL config with existing sample size
        function initializeAQLConfigWithExistingSampleSize(calculatedLotSize) {
            trimsInspectionState.aqlConfiguration = {
                aql_level: inspectionData.aql_level,
                aql_value: inspectionData.aql_value,
                lot_size: calculatedLotSize,
                sample_size: inspectionData.required_sample_size || 0,
                acceptance_number: 0,
                rejection_number: 0,
                sample_code_letter: '',
                lot_size_range: '',
                calculation_method: 'aql_table',
                inspection_type: inspectionData.inspection_type || 'AQL Based',
                inspection_regime: inspectionData.inspection_regime || 'Normal'
            };
            console.log('✅ Initialized AQL configuration from document:', trimsInspectionState.aqlConfiguration);
            
            // Populate form fields
            setTimeout(() => {
                const aqlLevelSelect = document.getElementById('aql-level');
                const aqlValueSelect = document.getElementById('aql-value');
                const inspectionTypeSelect = document.getElementById('inspection-type');
                const sampleSizeDisplay = document.getElementById('sample-size-display');
                
                if (aqlLevelSelect) aqlLevelSelect.value = inspectionData.aql_level;
                if (aqlValueSelect) aqlValueSelect.value = inspectionData.aql_value;
                if (inspectionTypeSelect) inspectionTypeSelect.value = inspectionData.inspection_type || 'AQL Based';
                if (sampleSizeDisplay) sampleSizeDisplay.value = inspectionData.required_sample_size || 0;
                
                console.log('✅ Populated AQL form fields with existing values');
            }, 500);
        }
        
        // Helper function to initialize with 0 sample size
        function initializeAQLConfigWithoutSampleSize() {
            // Calculate lot size again since it's not in scope
            let lotSize = inspectionData.total_pieces || 0;
            if (!lotSize && trimsInspectionState.itemsData) {
                lotSize = Object.values(trimsInspectionState.itemsData).reduce((sum, item) => {
                    return sum + parseInt(item.pieces || item.quantity || 0);
                }, 0);
            }
            
            trimsInspectionState.aqlConfiguration = {
                aql_level: inspectionData.aql_level,
                aql_value: inspectionData.aql_value,
                lot_size: lotSize,
                sample_size: 0,
                acceptance_number: 0,
                rejection_number: 0,
                sample_code_letter: '',
                lot_size_range: '',
                calculation_method: 'aql_table',
                inspection_type: inspectionData.inspection_type || 'AQL Based',
                inspection_regime: inspectionData.inspection_regime || 'Normal'
            };
            console.log('⚠️ Initialized AQL configuration with 0 sample size');
        }
        
        // Automatic AQL calculation function
        async function calculateAQLSamplingAutomatically(aqlLevel, aqlValue, lotSize) {
            console.log(`🔄 Auto-calculating AQL sampling for: Level=${aqlLevel}, Value=${aqlValue}, LotSize=${lotSize}`);
            
            const inspectionRegime = inspectionData.inspection_regime || 'Normal';
            
            const response = await frappe.call({
                method: 'erpnext_trackerx_customization.api.aql_data.calculate_aql_sampling',
                args: {
                    total_quantity: lotSize,
                    aql_level: aqlLevel,
                    aql_value: aqlValue,
                    inspection_regime: inspectionRegime
                }
            });
            
            if (response && response.message) {
                let samplingData;
                if (response.message.data) {
                    samplingData = response.message.data;
                } else if (response.message.sample_size) {
                    samplingData = response.message;
                } else {
                    throw new Error('Invalid API response structure');
                }
                
                console.log('✅ Auto-calculated AQL sampling data:', samplingData);
                
                // Initialize AQL configuration with calculated values
                trimsInspectionState.aqlConfiguration = {
                    aql_level: aqlLevel,
                    aql_value: aqlValue,
                    lot_size: lotSize,
                    sample_size: samplingData.sample_size || 0,
                    acceptance_number: samplingData.acceptance_number || 0,
                    rejection_number: samplingData.rejection_number || 0,
                    sample_code_letter: samplingData.sample_code_letter || '',
                    lot_size_range: samplingData.lot_size_range || '',
                    calculation_method: samplingData.calculation_method || 'aql_table',
                    inspection_type: inspectionData.inspection_type || 'AQL Based',
                    inspection_regime: inspectionRegime
                };
                
                console.log('✅ Auto-initialized AQL configuration:', trimsInspectionState.aqlConfiguration);
                
                // Update the UI displays
                const sampleSizeDisplay = document.getElementById('sample-size-display');
                if (sampleSizeDisplay) {
                    sampleSizeDisplay.value = samplingData.sample_size || 0;
                }
                
                // Update form fields
                setTimeout(() => {
                    const aqlLevelSelect = document.getElementById('aql-level');
                    const aqlValueSelect = document.getElementById('aql-value');
                    const inspectionTypeSelect = document.getElementById('inspection-type');
                    
                    if (aqlLevelSelect) aqlLevelSelect.value = aqlLevel;
                    if (aqlValueSelect) aqlValueSelect.value = aqlValue;
                    if (inspectionTypeSelect) inspectionTypeSelect.value = inspectionData.inspection_type || 'AQL Based';
                    
                    console.log('✅ Auto-populated AQL form fields');
                }, 500);
                
                // Save the calculated values to the document with retry logic
                if (inspectionData && inspectionData.name) {
                    try {
                        await saveAQLConfigurationWithRetry(samplingData, inspectionRegime);
                        console.log('✅ Auto-saved AQL configuration to document');
                    } catch (error) {
                        console.warn('⚠️ Could not auto-save AQL configuration:', error.message);
                        console.log('💡 AQL configuration will be available in memory for this session');
                        // Still continue with UI updates even if save fails
                    }
                }
                
                // Trigger item selection and UI updates
                setTimeout(() => {
                    selectItemsForInspection();
                    updateAQLSummaryDisplay();
                    updateSelectedItemsSummary();
                    updateItemInspectionPieces();
                    console.log('✅ Auto-updated all AQL displays');
                }, 100);
                
            } else {
                throw new Error('No response from AQL calculation API');
            }
        }
        
        // Helper function to save AQL configuration with retry logic
        async function saveAQLConfigurationWithRetry(samplingData, inspectionRegime, maxRetries = 3) {
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    console.log(`💾 Attempting to save AQL configuration (attempt ${attempt}/${maxRetries})...`);
                    
                    await frappe.call({
                        method: 'frappe.client.set_value',
                        args: {
                            doctype: 'Trims Inspection',
                            name: inspectionData.name,
                            fieldname: {
                                'required_sample_size': samplingData.sample_size,
                                'required_sample_pieces': samplingData.sample_size,
                                'inspection_type': inspectionData.inspection_type || 'AQL Based',
                                'inspection_regime': inspectionRegime,
                                'sampling_plan': JSON.stringify(samplingData)
                            }
                        }
                    });
                    
                    console.log(`✅ Successfully saved AQL configuration on attempt ${attempt}`);
                    return; // Success, exit the retry loop
                    
                } catch (error) {
                    console.warn(`❌ Save attempt ${attempt} failed:`, error.message);
                    
                    if (attempt === maxRetries) {
                        // Last attempt failed, throw the error
                        throw new Error(`Failed to save AQL configuration after ${maxRetries} attempts: ${error.message}`);
                    }
                    
                    // Wait before retrying (exponential backoff)
                    const delay = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s
                    console.log(`⏳ Waiting ${delay}ms before retry...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        
        // Helper function to save manual AQL configuration with retry logic
        async function saveAQLConfigurationWithRetryManual(samplingData, inspectionRegime, aqlLevel, aqlValue, inspectionType, maxRetries = 3) {
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    console.log(`💾 Attempting to save manual AQL configuration (attempt ${attempt}/${maxRetries})...`);
                    
                    await frappe.call({
                        method: 'frappe.client.set_value',
                        args: {
                            doctype: 'Trims Inspection',
                            name: inspectionData.name,
                            fieldname: {
                                'aql_level': aqlLevel,
                                'aql_value': aqlValue,
                                'required_sample_size': samplingData.sample_size,
                                'required_sample_pieces': samplingData.sample_size,
                                'inspection_type': inspectionType,
                                'inspection_regime': inspectionRegime,
                                'sampling_plan': JSON.stringify(samplingData)
                            }
                        }
                    });
                    
                    console.log(`✅ Successfully saved manual AQL configuration on attempt ${attempt}`);
                    return; // Success, exit the retry loop
                    
                } catch (error) {
                    console.warn(`❌ Manual save attempt ${attempt} failed:`, error.message);
                    
                    if (attempt === maxRetries) {
                        // Last attempt failed, throw the error
                        throw new Error(`Failed to save manual AQL configuration after ${maxRetries} attempts: ${error.message}`);
                    }
                    
                    // Wait before retrying (shorter delays for manual actions)
                    const delay = 1000 * attempt; // 1s, 2s, 3s
                    console.log(`⏳ Waiting ${delay}ms before manual retry...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        
        // Initialize AQL summary displays and item selection
        // Only run if not auto-calculating (to avoid duplicate calls)
        if (inspectionData.required_sample_size || !inspectionData.aql_level || !inspectionData.aql_value) {
            setTimeout(() => {
                console.log('🔄 Initializing AQL displays with loaded data...');
                
                // First, select items based on current inspection type
                selectItemsForInspection();
                
                // Then update all displays with calculated values
                updateAQLSummaryDisplay();
                updateSelectedItemsSummary();
                updateItemInspectionPieces();
                
                console.log('✅ Initial AQL displays configured');
            }, 1000); // Delay to ensure AQL config is available
        } else {
            console.log('⏳ Skipping initial display setup - waiting for auto-calculation to complete');
        }
        
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
            
            // Skip if no value or invalid value (but allow zero counts)
            if (countValue === null || countValue === undefined || countValue === "") continue;
            
            // Clean the count value - handle malformed data
            if (typeof countValue === 'string') {
                // Remove non-numeric characters
                countValue = countValue.replace(/[^0-9]/g, '');
            }
            
            // Convert to number and validate (allow zero counts for trims)
            const cleanCount = parseInt(countValue);
            if (isNaN(cleanCount) || cleanCount < 0) {
                console.warn(`Invalid count value for ${defectKey}: ${itemDefects[defectKey]} -> cleaned: ${countValue} -> parsed: ${cleanCount}`);
                continue;
            }
            
            // Extract defect code from key
            const parts = defectKey.split('_');
            const defectCode = parts[parts.length - 1];
            
            // Find the input element with robust selector
            let input = document.querySelector(`input[data-item="${itemNumber}"][data-defect="${defectCode}"]`);
            
            // If not found, try escaping the item number
            if (!input) {
                try {
                    const escapedItemNumber = CSS.escape(itemNumber);
                    input = document.querySelector(`input[data-item="${escapedItemNumber}"][data-defect="${defectCode}"]`);
                } catch (error) {
                    console.warn(`CSS.escape failed for item number: ${itemNumber}`, error);
                }
            }
            
            if (input) {
                input.value = cleanCount;
                console.log(`Set defect ${defectCode} for item ${itemNumber} to ${cleanCount} (original: ${itemDefects[defectKey]})`);
                
                // Also update the total count display
                updateElement(`total-${itemNumber}-${defectCode}`, cleanCount);
                
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
    // Use more robust element finding for toggle
    let itemBody = document.getElementById(`item-body-${itemNumber}`);
    
    // If getElementById fails, try with CSS.escape
    if (!itemBody) {
        try {
            const escapedId = CSS.escape(`item-body-${itemNumber}`);
            itemBody = document.querySelector(`#${escapedId}`);
        } catch (error) {
            // Try attribute selector as fallback
            itemBody = document.querySelector(`[id="item-body-${itemNumber}"]`);
        }
    }
    
    if (itemBody) {
        itemBody.classList.toggle('expanded');
    } else {
        console.warn(`Could not find item body for: ${itemNumber}`);
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
    console.log('updateAQLConfiguration called');
    
    const aqlLevel = document.getElementById('aql-level').value;
    const aqlValue = document.getElementById('aql-value').value; // Keep as string to preserve format like "4.0"
    
    if (!aqlLevel || !aqlValue) {
        console.log('Missing AQL Level or AQL Value');
        return;
    }
    
    // Show loading state - declare originalText in proper scope
    const button = document.querySelector('[onclick="updateAQLConfiguration()"]');
    const originalText = button ? button.textContent : 'Update AQL Config';
    if (button) {
        button.textContent = 'Updating...';
        button.disabled = true;
    }
    
    try {
        
        // Ensure items data is loaded before calculating lot size
        if (!trimsInspectionState.itemsData || Object.keys(trimsInspectionState.itemsData).length === 0) {
            console.log('⚠️ Items data not loaded, attempting to reload...');
            
            // Try to reload items from inspection data
            if (inspectionData.items && Array.isArray(inspectionData.items) && inspectionData.items.length > 0) {
                trimsInspectionState.itemsData = {};
                inspectionData.items.forEach(item => {
                    if (item && item.item_number) {
                        trimsInspectionState.itemsData[item.item_number] = item;
                        console.log(`✅ Reloaded item ${item.item_number}`);
                    }
                });
            } else {
                // Final fallback: create items from inspection document data
                console.log('🔄 Creating fallback items from inspection document');
                const totalPieces = parseInt(inspectionData.total_pieces || 0);
                const totalBoxes = parseInt(inspectionData.total_boxes || 1);
                const piecesPerBox = Math.floor(totalPieces / totalBoxes) || totalPieces;
                
                trimsInspectionState.itemsData = {};
                for (let i = 1; i <= totalBoxes; i++) {
                    const itemNumber = `ITEM-${i.toString().padStart(3, '0')}`;
                    trimsInspectionState.itemsData[itemNumber] = {
                        item_number: itemNumber,
                        pieces: piecesPerBox,
                        quantity: piecesPerBox,
                        description: `Box ${i} of ${totalBoxes}`,
                        status: 'Pending'
                    };
                    console.log(`✅ Created fallback item ${itemNumber} with ${piecesPerBox} pieces`);
                }
            }
        }
        
        // Calculate lot size (total quantity from all items)
        let totalLotSize = 0;
        
        console.log('🔍 DEBUG: Final itemsData for calculation:', trimsInspectionState.itemsData);
        
        for (const itemData of Object.values(trimsInspectionState.itemsData || {})) {
            // Try different quantity field names
            const quantity = parseInt(itemData.quantity || itemData.pieces || itemData.total_pieces || 0);
            totalLotSize += quantity;
            console.log(`Item ${itemData.item_number}: quantity=${quantity}`);
        }
        
        // Final fallback: if still no items data or totalLotSize is 0, use inspection data
        if (totalLotSize === 0 && inspectionData.total_pieces) {
            totalLotSize = parseInt(inspectionData.total_pieces);
            console.log('Using final fallback total_pieces from inspectionData:', totalLotSize);
        }
        
        console.log('Total lot size calculated:', totalLotSize);
        
        // Get inspection regime from dropdown
        const inspectionRegime = document.getElementById('inspection-regime')?.value || 'Normal';
        
        // Get inspection type from dropdown
        const inspectionType = document.getElementById('inspection-type')?.value || 'trims';
        
        // Use the same API as fabric inspection with correct parameters
        const response = await frappe.call({
            method: 'erpnext_trackerx_customization.api.aql_data.calculate_aql_sampling',
            args: {
                total_quantity: totalLotSize,
                aql_level: aqlLevel,
                aql_value: aqlValue,
                inspection_regime: inspectionRegime
            }
        });
        
        if (response && response.message) {
            console.log('🔍 DEBUG: Full API response:', response);
            
            // Handle nested response structure: response.message.data
            let samplingData;
            if (response.message.data) {
                samplingData = response.message.data;
                console.log('✅ Using response.message.data structure');
            } else if (response.message.sample_size) {
                samplingData = response.message;
                console.log('✅ Using response.message structure');
            } else {
                console.error('❌ Unknown API response structure:', response.message);
                frappe.show_alert({message: 'Invalid API response structure', indicator: 'red'});
                return;
            }
            
            console.log('🔍 DEBUG: Parsed sampling data:', samplingData);
            
            // Update the configuration display
            const sampleSize = samplingData.sample_size || 0;
            document.getElementById('sample-size-display').value = sampleSize;
            console.log(`✅ Updated sample-size-display to: ${sampleSize}`);
            
            // Store AQL configuration in state for later use
            trimsInspectionState.aqlConfiguration = {
                aql_level: aqlLevel,
                aql_value: aqlValue,
                lot_size: totalLotSize,
                sample_size: sampleSize,
                acceptance_number: samplingData.acceptance_number || 0,
                rejection_number: samplingData.rejection_number || 0,
                sample_code_letter: samplingData.sample_code_letter || '',
                lot_size_range: samplingData.lot_size_range || '',
                calculation_method: samplingData.calculation_method || 'aql_table',
                inspection_type: inspectionType
            };
            
            console.log('✅ Updated AQL configuration:', trimsInspectionState.aqlConfiguration);
            
            // Update all AQL-related UI fields
            const aqlLevelSelect = document.getElementById('aql-level');
            if (aqlLevelSelect && aqlLevelSelect.value !== aqlLevel) {
                aqlLevelSelect.value = aqlLevel;
                console.log(`✅ Updated AQL Level dropdown to: ${aqlLevel}`);
            }
            
            const aqlValueSelect = document.getElementById('aql-value');
            if (aqlValueSelect && aqlValueSelect.value !== aqlValue) {
                aqlValueSelect.value = aqlValue;
                console.log(`✅ Updated AQL Value dropdown to: ${aqlValue}`);
            }
            
            const inspectionRegimeSelect = document.getElementById('inspection-regime');
            if (inspectionRegimeSelect) {
                console.log(`✅ Inspection Regime: ${inspectionRegimeSelect.value}`);
            }
            
            const inspectionTypeSelect = document.getElementById('inspection-type');
            if (inspectionTypeSelect) {
                console.log(`✅ Inspection Type: ${inspectionTypeSelect.value}`);
            }
            
            // Save to inspection document with retry mechanism
            if (inspectionData && inspectionData.name) {
                try {
                    await saveAQLConfigurationWithRetryManual(samplingData, inspectionRegime, aqlLevel, aqlValue, inspectionType);
                    console.log('✅ Successfully saved manual AQL configuration');
                } catch (error) {
                    console.warn('⚠️ Could not save manual AQL configuration:', error.message);
                    frappe.show_alert({message: 'Configuration updated in memory but save failed: ' + error.message, indicator: 'orange'});
                    // Continue with UI updates even if save fails
                }
            }
            
            console.log('AQL Configuration updated successfully:', trimsInspectionState.aqlConfiguration);
            
            // CRITICAL: Update all displays with the new AQL configuration
            console.log('🔄 Updating all displays with new AQL configuration...');
            
            // Step 1: Select items based on NEW AQL config (this uses trimsInspectionState.aqlConfiguration)
            selectItemsForInspection();
            console.log('✅ Items selected based on AQL config');
            
            // Step 2: Update item pieces display
            updateItemInspectionPieces();
            console.log('✅ Item inspection pieces updated');
            
            // Step 3: Update AQL summary display
            updateAQLSummaryDisplay();
            console.log('✅ AQL summary display updated');
            
            // Step 4: Update the main sampling summary (this should now show API values)
            updateSelectedItemsSummary();
            console.log('✅ Selected items summary updated');
            
            // Verify the final display
            const finalSamplingText = document.getElementById('sampling-text')?.textContent;
            const finalSelectedCount = document.getElementById('selected-item-count')?.textContent;
            console.log(`🎯 FINAL RESULT: Sampling text: "${finalSamplingText}"`);
            console.log(`🎯 FINAL RESULT: Selected count: "${finalSelectedCount}"`);
            
            frappe.show_alert({message: 'AQL Configuration updated successfully', indicator: 'green'});
        }
        
    } catch (error) {
        console.error('Error updating AQL configuration:', error);
        frappe.show_alert({message: 'Error updating AQL configuration: ' + error.message, indicator: 'red'});
    } finally {
        // Restore button state
        const button = document.querySelector('[onclick="updateAQLConfiguration()"]');
        if (button) {
            button.textContent = originalText || 'Update AQL Config';
            button.disabled = false;
        }
    }
}

// Update item inspection pieces based on AQL configuration
function updateItemInspectionPieces() {
    if (!trimsInspectionState.selectedItems) {
        console.log('No selected items available');
        return;
    }
    
    const selectedItems = trimsInspectionState.selectedItems;
    
    // Update each item's inspection pieces display based on selection results
    for (const itemNumber in trimsInspectionState.itemsData) {
        const itemData = trimsInspectionState.itemsData[itemNumber];
        const totalPieces = parseInt(itemData.pieces || itemData.quantity || 0);
        
        // Find this item in the selected items list
        const selectedItem = selectedItems.find(selected => selected.item_number === itemNumber);
        const inspectionPieces = selectedItem ? (selectedItem.inspection_pieces || 0) : 0;
        
        // Update the display using robust element finding
        let inspectionPiecesElement = document.getElementById(`inspection-pieces-${itemNumber}`);
        
        // If getElementById fails, try other methods
        if (!inspectionPiecesElement) {
            try {
                const escapedId = CSS.escape(`inspection-pieces-${itemNumber}`);
                inspectionPiecesElement = document.querySelector(`#${escapedId}`);
            } catch (error) {
                // Try attribute selector as fallback
                inspectionPiecesElement = document.querySelector(`[id="inspection-pieces-${itemNumber}"]`);
            }
        }
        
        if (inspectionPiecesElement) {
            if (inspectionPieces > 0) {
                inspectionPiecesElement.textContent = `Pieces to Inspect: ${inspectionPieces} of ${totalPieces}`;
            } else {
                inspectionPiecesElement.textContent = `Pieces to Inspect: 0 of ${totalPieces} (Not selected)`;
            }
            
            // Store inspection pieces in item data
            trimsInspectionState.itemsData[itemNumber].inspection_pieces = inspectionPieces;
        } else {
            console.warn(`Could not find inspection pieces element for item: ${itemNumber}`);
        }
        
        // Hide/show the entire item section based on inspection pieces
        // Only hide items if there's a valid AQL configuration, otherwise show all items
        const itemSection = document.querySelector(`[data-item="${itemNumber}"]`);
        if (itemSection) {
            const hasValidAQLConfig = trimsInspectionState.aqlConfiguration && 
                                    trimsInspectionState.aqlConfiguration.sample_size > 0;
            
            if (hasValidAQLConfig) {
                // Only hide items when we have a proper AQL configuration
                if (inspectionPieces > 0) {
                    itemSection.style.display = '';  // Show the item
                } else {
                    itemSection.style.display = 'none';  // Hide the item
                }
            } else {
                // No AQL config yet - show all items
                itemSection.style.display = '';  // Always show when no AQL config
            }
        }
    }
    
    const totalSelectedPieces = selectedItems.reduce((sum, item) => sum + (item.inspection_pieces || 0), 0);
    const selectedItemsCount = selectedItems.filter(item => item.selected_for_inspection).length;
    console.log(`Updated item inspection pieces: ${selectedItemsCount} items selected, ${totalSelectedPieces} total pieces to inspect`);
}

// Update AQL Summary Display
function updateAQLSummaryDisplay() {
    const aqlLevel = document.getElementById('aql-level')?.value || inspectionData.aql_level || '2';
    const aqlValue = document.getElementById('aql-value')?.value || inspectionData.aql_value || '2.5';
    const inspectionType = document.getElementById('inspection-type')?.value || inspectionData.inspection_type || 'AQL Based';
    
    // AQL Level display mapping
    const aqlLevelDisplayMap = {
        '1': 'I', '2': 'II', '3': 'III',
        'S1': 'S-1', 'S2': 'S-2', 'S3': 'S-3', 'S4': 'S-4'
    };
    
    // Update AQL configuration text
    const aqlLevelDisplay = aqlLevelDisplayMap[aqlLevel] || aqlLevel;
    const aqlConfigText = document.getElementById('aql-config-text');
    if (aqlConfigText) {
        aqlConfigText.textContent = `Level ${aqlLevelDisplay} with ${aqlValue}% defect tolerance`;
    }
    
    console.log(`Updated AQL summary: Level ${aqlLevelDisplay} with ${aqlValue}% defect tolerance`);
}

// Select items for inspection based on AQL configuration
function selectItemsForInspection() {
    console.log('🔍 selectItemsForInspection() called');
    
    const inspectionType = document.getElementById('inspection-type')?.value || 'AQL Based';
    const allItems = Object.values(trimsInspectionState.itemsData || {});
    const totalItems = allItems.length;
    
    console.log(`📊 Processing ${totalItems} items for ${inspectionType} inspection`);
    
    if (totalItems === 0) {
        console.error('❌ No items found - cannot perform sampling');
        trimsInspectionState.selectedItems = [];
        return [];
    }
    
    let selectedItems = [];
    
    if (inspectionType === '100% Inspection') {
        // Select ALL items for 100% inspection - all pieces in all items
        selectedItems = allItems.map(item => ({
            ...item,
            selected_for_inspection: true,
            inspection_pieces: parseInt(item.pieces || item.quantity || 0),
            inspection_reason: '100% Inspection - All pieces in all items'
        }));
        
    } else if (inspectionType === 'AQL Based') {
        // For AQL Based inspection, use API sample_size as total pieces to inspect
        const aqlConfig = trimsInspectionState.aqlConfiguration;
        const totalPiecesToInspect = (aqlConfig && aqlConfig.sample_size) ? aqlConfig.sample_size : 0; // This is the API response sample_size (e.g., 13)
        
        console.log(`AQL Based: Need to inspect ${totalPiecesToInspect} pieces total`);
        
        // If no AQL configuration yet, show placeholder message
        if (totalPiecesToInspect === 0) {
            selectedItems = allItems.map(item => ({
                ...item,
                selected_for_inspection: false,
                inspection_pieces: 0,
                inspection_reason: 'AQL configuration not set - Click "Update AQL Config" button'
            }));
        } else {
            // Calculate total available pieces across all items
            let totalAvailablePieces = 0;
            allItems.forEach(item => {
                const pieces = parseInt(item.pieces || item.quantity || 0);
                totalAvailablePieces += pieces;
            });
            
            console.log(`Total available pieces: ${totalAvailablePieces}`);
            
            if (totalPiecesToInspect >= totalAvailablePieces) {
                // If sample size >= total pieces, select all items with all pieces
                selectedItems = allItems.map(item => ({
                    ...item,
                    selected_for_inspection: true,
                    inspection_pieces: parseInt(item.pieces || item.quantity || 0),
                    inspection_reason: `AQL Based - All ${totalAvailablePieces} pieces (sample size ${totalPiecesToInspect})`
                }));
            } else {
                // Distribute the pieces to inspect across items proportionally
                let remainingPiecesToInspect = totalPiecesToInspect;
                
                // Sort items by piece count (descending) to prioritize larger lots
                const sortedItems = [...allItems].sort((a, b) => {
                    const aPieces = parseInt(a.pieces || a.quantity || 0);
                    const bPieces = parseInt(b.pieces || b.quantity || 0);
                    return bPieces - aPieces;
                });
                
                selectedItems = sortedItems.map((item, index) => {
                    const itemPieces = parseInt(item.pieces || item.quantity || 0);
                    let piecesToInspectFromItem = 0;
                    
                    if (remainingPiecesToInspect > 0 && itemPieces > 0) {
                        // Calculate proportional pieces, but ensure we don't exceed item's total pieces
                        const proportion = itemPieces / totalAvailablePieces;
                        let calculatedPieces = Math.ceil(totalPiecesToInspect * proportion);
                        
                        // For the last few items, take remaining pieces
                        if (index === sortedItems.length - 1) {
                            piecesToInspectFromItem = Math.min(remainingPiecesToInspect, itemPieces);
                        } else {
                            piecesToInspectFromItem = Math.min(calculatedPieces, itemPieces, remainingPiecesToInspect);
                        }
                        
                        remainingPiecesToInspect -= piecesToInspectFromItem;
                    }
                    
                    return {
                        ...item,
                        selected_for_inspection: piecesToInspectFromItem > 0,
                        inspection_pieces: piecesToInspectFromItem,
                        inspection_reason: piecesToInspectFromItem > 0 ? 
                            `AQL Based - ${piecesToInspectFromItem} of ${itemPieces} pieces (total sample: ${totalPiecesToInspect})` :
                            `Not selected - no pieces needed from this item`
                    };
                });
            }
        }
        
    } else {
        // Default: select all items with all pieces
        selectedItems = allItems.map(item => ({
            ...item,
            selected_for_inspection: true,
            inspection_pieces: parseInt(item.pieces || item.quantity || 0),
            inspection_reason: 'Default - All pieces in all items'
        }));
    }
    
    // Store selected items
    trimsInspectionState.selectedItems = selectedItems;
    
    // Log the results for debugging
    const totalSelectedPieces = selectedItems.reduce((sum, item) => sum + (item.inspection_pieces || 0), 0);
    const selectedItemsCount = selectedItems.filter(item => item.selected_for_inspection).length;
    console.log(`Selected ${selectedItemsCount} items for inspection with ${totalSelectedPieces} total pieces:`, 
                selectedItems.filter(item => item.selected_for_inspection));
    
    return selectedItems;
}

// Update selected items summary display
function updateSelectedItemsSummary() {
    if (!trimsInspectionState.selectedItems) {
        trimsInspectionState.selectedItems = selectItemsForInspection();
    }
    
    const selectedItems = trimsInspectionState.selectedItems;
    const totalItems = Object.keys(trimsInspectionState.itemsData || {}).length;
    
    // Calculate total pieces to inspect and total available pieces
    const totalPiecesToInspect = selectedItems.reduce((sum, item) => sum + (item.inspection_pieces || 0), 0);
    const selectedItemsCount = selectedItems.filter(item => item.selected_for_inspection).length;
    
    // Get total available pieces from all items (not just selected ones)
    const allItems = Object.values(trimsInspectionState.itemsData || {});
    const totalAvailablePieces = allItems.reduce((sum, item) => sum + parseInt(item.pieces || item.quantity || 0), 0);
    
    // Update sampling text - show pieces instead of items for AQL based
    const samplingText = document.getElementById('sampling-text');
    if (samplingText) {
        const inspectionType = document.getElementById('inspection-type')?.value || 'AQL Based';
        if (inspectionType === 'AQL Based' && trimsInspectionState.aqlConfiguration && trimsInspectionState.aqlConfiguration.sample_size > 0) {
            // For AQL Based, show the API response sample_size as pieces to inspect
            const apiSampleSize = trimsInspectionState.aqlConfiguration.sample_size;
            samplingText.textContent = `${apiSampleSize} pieces out of ${totalAvailablePieces} total pieces`;
        } else if (inspectionType === '100% Inspection') {
            samplingText.textContent = `${totalAvailablePieces} pieces out of ${totalAvailablePieces} total pieces (100% Inspection)`;
        } else if (inspectionType === 'AQL Based') {
            // AQL Based but no configuration yet
            samplingText.textContent = `${totalAvailablePieces} pieces available - AQL configuration needed`;
        } else {
            samplingText.textContent = `${selectedItemsCount} items out of ${totalItems} total items (${totalPiecesToInspect} pieces)`;
        }
    }
    
    // Update selected item count - show pieces for AQL
    const selectedItemCount = document.getElementById('selected-item-count');
    if (selectedItemCount) {
        const inspectionType = document.getElementById('inspection-type')?.value || 'AQL Based';
        if (inspectionType === 'AQL Based' && trimsInspectionState.aqlConfiguration && trimsInspectionState.aqlConfiguration.sample_size > 0) {
            // Show API sample_size for AQL Based
            const apiSampleSize = trimsInspectionState.aqlConfiguration.sample_size;
            selectedItemCount.textContent = apiSampleSize.toString();
        } else if (inspectionType === '100% Inspection') {
            selectedItemCount.textContent = totalAvailablePieces.toString();
        } else if (inspectionType === 'AQL Based') {
            // AQL Based but no configuration yet
            selectedItemCount.textContent = totalItems.toString() + ' items';
        } else {
            selectedItemCount.textContent = selectedItemsCount.toString();
        }
    }
    
    // Update selected item details - show which items and how many pieces from each
    const selectedItemDetails = document.getElementById('selected-item-details');
    if (selectedItemDetails) {
        const activeItems = selectedItems.filter(item => item.selected_for_inspection && (item.inspection_pieces || 0) > 0);
        if (activeItems.length > 0) {
            const itemsText = activeItems.map(item => 
                `${item.item_number} (${item.inspection_pieces || 0} pieces)`
            ).join(', ');
            selectedItemDetails.textContent = itemsText;
        } else {
            selectedItemDetails.textContent = 'No items selected';
        }
    }
    
    console.log(`Updated selected items summary: ${selectedItemsCount} items, ${totalPiecesToInspect} pieces out of ${totalAvailablePieces} total pieces`);
}

// Update defect count when input changes
function updateDefectCount(input) {
    if (trimsInspectionState.isCalculating) return;
    
    const itemNumber = input.dataset.item;
    const defectCode = input.dataset.defect;
    const category = input.dataset.category;
    const count = parseInt(input.value) || 0;
    
    // Create defect key - ensure consistent naming
    const defectKey = `${category.toLowerCase().replace(/\s+/g, '_')}_${defectCode}`;
    
    // Initialize item data if needed
    if (!trimsInspectionState.defectsData[itemNumber]) {
        trimsInspectionState.defectsData[itemNumber] = {};
    }
    
    // Store all valid counts including zero (important for trims count-based system)
    if (isNaN(count) || count < 0) {
        delete trimsInspectionState.defectsData[itemNumber][defectKey];
    } else {
        // Store all non-negative counts (including zero)
        trimsInspectionState.defectsData[itemNumber][defectKey] = count;
    }
    
    // Clean up empty item objects
    if (Object.keys(trimsInspectionState.defectsData[itemNumber]).length === 0) {
        delete trimsInspectionState.defectsData[itemNumber];
    }
    
    trimsInspectionState.isDirty = true;
    
    // Update the individual total display immediately
    updateIndividualDefectTotal(itemNumber, defectCode, count);
    
    // Recalculate all totals
    debounce(calculateTotals, 100)();
    
    // Check if submit button should be enabled after defect update
    debounce(checkTrimsSubmitButtonStatus, 200)();
    
    console.log(`Updated defect ${defectKey} for item ${itemNumber}: ${count}`);
}

// Update individual defect total display
function updateIndividualDefectTotal(itemNumber, defectCode, count) {
    const elementId = `total-${itemNumber}-${defectCode}`;
    updateElement(elementId, count || 0);
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
        
        // Debug: Log current defects data
        console.log('Calculating totals from defects data:', trimsInspectionState.defectsData);
        
        // Calculate for each item
        for (const itemNumber in trimsInspectionState.defectsData) {
            const itemDefects = trimsInspectionState.defectsData[itemNumber];
            
            let itemCritical = 0;
            let itemMajor = 0;
            let itemMinor = 0;
            
            // Calculate item totals with better category detection
            for (const defectKey in itemDefects) {
                const count = parseInt(itemDefects[defectKey]) || 0;
                if (count > 0) {
                    // Determine severity from defect key prefix
                    let severity = 'Minor'; // Default
                    
                    if (defectKey.startsWith('critical_')) {
                        severity = 'Critical';
                    } else if (defectKey.startsWith('major_')) {
                        severity = 'Major';
                    } else if (defectKey.startsWith('minor_')) {
                        severity = 'Minor';
                    } else {
                        // Fallback: extract defect code and determine severity
                        const parts = defectKey.split('_');
                        const defectCode = parts[parts.length - 1];
                        severity = getDefectSeverity(defectCode);
                    }
                    
                    // Add to appropriate category
                    if (severity === 'Critical') {
                        itemCritical += count;
                    } else if (severity === 'Major') {
                        itemMajor += count;
                    } else {
                        itemMinor += count;
                    }
                    
                    console.log(`Item ${itemNumber}: ${defectKey} = ${count} (${severity})`);
                }
            }
            
            // Update item summary displays - use original itemNumber as HTML uses it directly
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
            
            console.log(`Item ${itemNumber} totals: Critical=${itemCritical}, Major=${itemMajor}, Minor=${itemMinor}`);
        }
        
        // Update final displays
        updateElement('total-critical-defects', totalCriticalDefects);
        updateElement('total-major-defects', totalMajorDefects);
        updateElement('total-minor-defects', totalMinorDefects);
        updateElement('total-items-inspected', totalItems);
        
        // Update final decision
        updateFinalDecision(totalCriticalDefects, totalMajorDefects, totalMinorDefects);
        
        console.log(`Final totals: Critical=${totalCriticalDefects}, Major=${totalMajorDefects}, Minor=${totalMinorDefects}`);
        
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
    // Use more robust element finding
    let statusElement = document.getElementById(`item-status-${itemNumber}`);
    
    // If getElementById fails, try other methods
    if (!statusElement) {
        try {
            const escapedId = CSS.escape(`item-status-${itemNumber}`);
            statusElement = document.querySelector(`#${escapedId}`);
        } catch (error) {
            // Try attribute selector as fallback
            statusElement = document.querySelector(`[id="item-status-${itemNumber}"]`);
        }
    }
    
    if (!statusElement) {
        console.warn(`Could not find status element for item: ${itemNumber}`);
        return;
    }
    
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
            
            // Update the global inspection data to reflect new hold status and reason
            inspectionData.inspection_status = 'Hold';
            inspectionData.hold_reason = reason.trim();
            inspectionData.hold_by = frappe.session.user;
            inspectionData.hold_timestamp = new Date().toISOString();
            
            // Update UI immediately to reflect hold status
            updateUIForHoldStatus();
            
            // Update page header status immediately
            const statusElement = document.querySelector('.meta');
            if (statusElement) {
                statusElement.innerHTML = statusElement.innerHTML.replace(/Status: [^|]*/, 'Status: Hold');
            }
            
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
            
            // Update the global inspection data to reflect resumed status
            inspectionData.inspection_status = 'In Progress';
            inspectionData.hold_reason = '';
            inspectionData.hold_by = '';
            inspectionData.hold_timestamp = '';
            
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
    console.log('=== CHECKING TRIMS INSPECTION COMPLETENESS ===');
    
    // Check if mandatory physical testing results are completed
    let mandatoryChecklistCompleted = true;
    let mandatoryFailures = 0;
    let mandatoryItems = [];
    
    if (Array.isArray(trimsInspectionState.checklistData)) {
        console.log('Checklist data:', trimsInspectionState.checklistData);
        for (const item of trimsInspectionState.checklistData) {
            if (item.is_mandatory) {
                mandatoryItems.push(item.test_parameter);
                const status = item.results?.status;
                console.log(`Mandatory item "${item.test_parameter}": status = "${status}"`);
                if (!status || status === '') {
                    mandatoryChecklistCompleted = false;
                    console.log(`❌ Mandatory item "${item.test_parameter}" is incomplete`);
                    break;
                }
                if (status === 'Fail') {
                    mandatoryFailures++;
                }
            }
        }
    }
    
    console.log(`Mandatory items found: ${mandatoryItems.length}`, mandatoryItems);
    console.log(`Mandatory checklist completed: ${mandatoryChecklistCompleted}`);
    
    // If there are mandatory items but they're not completed, block submission
    if (mandatoryItems.length > 0 && !mandatoryChecklistCompleted) {
        const reason = 'Mandatory physical testing results are not completed';
        console.log(`❌ RESULT: Not ready - ${reason}`);
        return { ready: false, reason };
    }
    
    // Check if there are any defects or checklist data entered
    const hasDefects = Object.keys(trimsInspectionState.defectsData || {}).length > 0;
    const hasChecklistData = Array.isArray(trimsInspectionState.checklistData) && 
                            trimsInspectionState.checklistData.some(item => item.results?.status);
    
    console.log('Defects data:', trimsInspectionState.defectsData);
    console.log(`Has defects: ${hasDefects}`);
    console.log(`Has checklist data: ${hasChecklistData}`);
    
    // Enhanced defects check - look for actual meaningful defect data
    let hasValidDefectData = false;
    if (trimsInspectionState.defectsData && typeof trimsInspectionState.defectsData === 'object') {
        for (const itemNumber in trimsInspectionState.defectsData) {
            const itemDefects = trimsInspectionState.defectsData[itemNumber];
            if (itemDefects && typeof itemDefects === 'object') {
                for (const defectKey in itemDefects) {
                    const count = itemDefects[defectKey];
                    if (count !== null && count !== undefined && count !== '' && !isNaN(count)) {
                        hasValidDefectData = true;
                        console.log(`Found valid defect data: ${itemNumber}.${defectKey} = ${count}`);
                        break;
                    }
                }
                if (hasValidDefectData) break;
            }
        }
    }
    
    console.log(`Has valid defect data: ${hasValidDefectData}`);
    
    // Accept if we have either valid defects OR valid checklist data OR both
    const hasAnyData = hasValidDefectData || hasChecklistData;
    console.log(`Has any inspection data: ${hasAnyData}`);
    
    if (!hasAnyData) {
        const reason = 'No inspection data has been recorded';
        console.log(`❌ RESULT: Not ready - ${reason}`);
        return { ready: false, reason };
    }
    
    console.log('✅ RESULT: Ready for submission');
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
function sanitizeElementId(itemNumber) {
    // Replace spaces and special characters with underscores for valid CSS IDs
    return itemNumber.replace(/[^a-zA-Z0-9-_]/g, '_');
}

function updateElement(id, value) {
    // First try getElementById (most common case)
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
        console.log(`Updated element ${id} with value: ${value}`);
        return;
    }
    
    // If getElementById fails, try with CSS.escape for special characters
    try {
        const escapedId = CSS.escape(id);
        const altElement = document.querySelector(`#${escapedId}`);
        if (altElement) {
            altElement.textContent = value;
            console.log(`Updated alternative element for ${id} with value: ${value}`);
            return;
        }
    } catch (error) {
        console.warn(`CSS.escape failed for ID '${id}':`, error);
    }
    
    // Final fallback: try attribute selector (this is safer for problematic IDs)
    try {
        const attrElement = document.querySelector(`[id="${id}"]`);
        if (attrElement) {
            attrElement.textContent = value;
            console.log(`Updated element via attribute selector for ${id} with value: ${value}`);
            return;
        }
    } catch (error) {
        console.warn(`Attribute selector failed for ID '${id}':`, error);
    }
    
    console.warn(`Element with ID '${id}' not found after all attempts. Value: ${value}`);
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
        } else if (currentStatus === 'Accepted' || currentStatus === 'Rejected' || currentStatus === 'Conditional Accept') {
            // Check if current user is Quality Inspector and if inspection should be read-only
            if (inspectionData.is_readonly) {
                updateUIForReadOnlyStatus();
                showMessage(`This inspection is read-only. Only Quality Managers can modify inspections with status '${currentStatus}'`, 'info');
            }
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
            // Create hold message with reason
            let holdMessage = '⏸️ This inspection is on hold - Click Resume to continue working';
            if (inspectionData.hold_reason) {
                holdMessage += `<br><strong>Reason:</strong> ${inspectionData.hold_reason}`;
            }
            if (inspectionData.hold_by) {
                holdMessage += `<br><strong>Hold by:</strong> ${inspectionData.hold_by}`;
            }
            holdNotice.innerHTML = holdMessage;
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
    let resumeBtn = document.getElementById('resume-trims-inspection-btn');
    if (!resumeBtn) {
        resumeBtn = document.createElement('button');
        resumeBtn.id = 'resume-trims-inspection-btn';
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
    const resumeBtn = document.getElementById('resume-trims-inspection-btn');
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

// Update UI for read-only status (Quality Inspectors cannot edit Accepted/Rejected/Conditional Accept)
function updateUIForReadOnlyStatus() {
    // Disable all editing inputs but keep values visible
    const inputs = document.querySelectorAll('input:not([readonly]), select, textarea');
    inputs.forEach(input => {
        input.disabled = true;
        input.style.opacity = '0.8'; // Make it visually apparent it's disabled
    });
    
    // Hide action buttons that modify the inspection
    const editingButtons = document.querySelectorAll('button[onclick*="save"], button[onclick*="submit"], button[onclick*="hold"]');
    editingButtons.forEach(btn => {
        btn.style.display = 'none';
    });
    
    // Add read-only notice
    const pageHeader = document.querySelector('.page-header');
    if (pageHeader) {
        let readOnlyNotice = pageHeader.querySelector('.readonly-notice');
        if (!readOnlyNotice) {
            readOnlyNotice = document.createElement('div');
            readOnlyNotice.className = 'readonly-notice';
            readOnlyNotice.style.cssText = `
                background: #e3f2fd; 
                color: #0d47a1; 
                padding: 10px; 
                margin-top: 10px; 
                border-radius: 6px; 
                border: 1px solid #90caf9;
                text-align: center;
                font-weight: 500;
            `;
            readOnlyNotice.innerHTML = '🔒 This inspection is read-only. Only Quality Managers can make modifications.';
            pageHeader.appendChild(readOnlyNotice);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTrimsData();
});