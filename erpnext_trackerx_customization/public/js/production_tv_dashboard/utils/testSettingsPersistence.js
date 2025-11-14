/**
 * Test utility for settings persistence
 * This helps verify that user settings are properly saved and restored
 */

import { saveToLocalStorage, getFromLocalStorage, clearAllDashboardData } from './localStorageUtils';

// Test data for operations
const mockDynamicOperations = [
  { id: 1, name: 'Cutting', operation: 'cutting', enabled: true, sequence: 1 },
  { id: 2, name: 'Sewing', operation: 'sewing', enabled: true, sequence: 2 },
  { id: 3, name: 'Finishing', operation: 'finishing', enabled: true, sequence: 3 },
  { id: 4, name: 'Ironing', operation: 'ironing', enabled: true, sequence: 4 },
  { id: 5, name: 'Packing', operation: 'packing', enabled: true, sequence: 5 }
];

const mockUserOperations = [
  { id: 1, name: 'Cutting', operation: 'cutting', enabled: false, sequence: 1, isVisible: false },
  { id: 2, name: 'Sewing', operation: 'sewing', enabled: true, sequence: 2, isVisible: true },
  { id: 3, name: 'Finishing', operation: 'finishing', enabled: false, sequence: 3, isVisible: false },
  { id: 4, name: 'Ironing', operation: 'ironing', enabled: true, sequence: 4, isVisible: true },
  { id: 5, name: 'Packing', operation: 'packing', enabled: true, sequence: 5, isVisible: true },
  { id: 6, name: 'Custom QC', operation: 'custom_qc', enabled: true, sequence: 6, isVisible: true, isCustom: true }
];

/**
 * Test the settings persistence functionality
 * @returns {Object} Test results
 */
export const testSettingsPersistence = () => {
  console.log('🧪 Testing Settings Persistence...\n');

  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };

  const addTest = (name, passed, details = '') => {
    results.tests.push({ name, passed, details });
    if (passed) {
      results.passed++;
      console.log(`✅ ${name}`);
    } else {
      results.failed++;
      console.log(`❌ ${name} - ${details}`);
    }
  };

  try {
    // Clear existing data first
    clearAllDashboardData();

    // Test 1: Save and retrieve operations
    const operationsSaveResult = saveToLocalStorage('operations', mockUserOperations);
    addTest(
      'Save operations configuration',
      operationsSaveResult.success,
      operationsSaveResult.error || ''
    );

    const operationsRetrieved = getFromLocalStorage('operations');
    addTest(
      'Retrieve operations configuration',
      operationsRetrieved !== null && operationsRetrieved.data.length === mockUserOperations.length,
      operationsRetrieved ? `Retrieved ${operationsRetrieved.data.length} operations` : 'No operations retrieved'
    );

    // Test 2: Save and retrieve screen size
    const screenSizeSaveResult = saveToLocalStorage('screenSize', '43inch');
    addTest(
      'Save screen size setting',
      screenSizeSaveResult.success,
      screenSizeSaveResult.error || ''
    );

    const screenSizeRetrieved = getFromLocalStorage('screenSize');
    addTest(
      'Retrieve screen size setting',
      screenSizeRetrieved !== null && screenSizeRetrieved.data === '43inch',
      screenSizeRetrieved ? `Retrieved: ${screenSizeRetrieved.data}` : 'No screen size retrieved'
    );

    // Test 3: Test smart merge functionality simulation
    // First save user preferences
    saveToLocalStorage('operations', mockUserOperations);

    // Simulate what happens during refresh with new dynamic operations
    const savedOpsResult = getFromLocalStorage('operations');
    const savedOps = savedOpsResult?.data;

    if (savedOps) {
      // Create smart merge result
      const savedOpsMap = new Map();
      savedOps.forEach(op => {
        savedOpsMap.set(op.name || op.operation, op);
      });

      const mergedOps = [];
      const addedOperations = new Set();

      // Process dynamic operations with user preferences
      mockDynamicOperations.forEach(dynamicOp => {
        const opKey = dynamicOp.name || dynamicOp.operation;
        const savedOp = savedOpsMap.get(opKey);

        if (savedOp) {
          mergedOps.push({
            ...dynamicOp,
            ...savedOp,
            name: dynamicOp.name || dynamicOp.operation,
            operation: dynamicOp.operation || dynamicOp.name,
          });
        } else {
          mergedOps.push({
            ...dynamicOp,
            enabled: true,
            sequence: mergedOps.length + 1,
            id: dynamicOp.id || Date.now() + Math.random()
          });
        }
        addedOperations.add(opKey);
      });

      // Add custom operations
      savedOps.forEach(savedOp => {
        const opKey = savedOp.name || savedOp.operation;
        if (!addedOperations.has(opKey)) {
          mergedOps.push({
            ...savedOp,
            isCustom: true
          });
        }
      });

      // Check if user preferences were preserved
      const cuttingOp = mergedOps.find(op => op.operation === 'cutting');
      const customQcOp = mergedOps.find(op => op.operation === 'custom_qc');

      addTest(
        'Smart merge preserves user preferences',
        cuttingOp && cuttingOp.enabled === false && cuttingOp.isVisible === false,
        cuttingOp ? `Cutting enabled: ${cuttingOp.enabled}, visible: ${cuttingOp.isVisible}` : 'Cutting operation not found'
      );

      addTest(
        'Smart merge preserves custom operations',
        customQcOp && customQcOp.isCustom === true,
        customQcOp ? 'Custom QC operation preserved' : 'Custom QC operation lost'
      );
    }

    // Test 4: Test error handling
    const invalidSaveResult = saveToLocalStorage('', mockUserOperations);
    addTest(
      'Error handling for invalid key',
      !invalidSaveResult.success && invalidSaveResult.error === 'Invalid key provided',
      invalidSaveResult.error || 'Unexpected result'
    );

    // Test 5: Test timestamp functionality
    const timestampSaveResult = saveToLocalStorage('test_timestamp', { test: 'data' });
    if (timestampSaveResult.success) {
      const timestampRetrieved = getFromLocalStorage('test_timestamp');
      addTest(
        'Timestamp functionality',
        timestampRetrieved !== null && timestampRetrieved.timestamp !== null,
        timestampRetrieved ? `Timestamp: ${new Date(timestampRetrieved.timestamp).toISOString()}` : 'No timestamp'
      );
    }

    // Test 6: Simulate browser refresh scenario
    console.log('\n🔄 Simulating browser refresh scenario...');

    // Save current settings
    saveToLocalStorage('operations', mockUserOperations);
    saveToLocalStorage('screenSize', '65inch');

    // Simulate what happens on page load
    const refreshOperations = getFromLocalStorage('operations')?.data;
    const refreshScreenSize = getFromLocalStorage('screenSize')?.data;

    addTest(
      'Browser refresh - operations persist',
      refreshOperations !== null && refreshOperations.length === mockUserOperations.length,
      refreshOperations ? `${refreshOperations.length} operations loaded` : 'No operations found'
    );

    addTest(
      'Browser refresh - screen size persists',
      refreshScreenSize === '65inch',
      refreshScreenSize ? `Screen size: ${refreshScreenSize}` : 'No screen size found'
    );

  } catch (error) {
    addTest('General test execution', false, error.message);
  }

  // Summary
  console.log(`\n📊 Test Summary:`);
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`📈 Success Rate: ${((results.passed / (results.passed + results.failed)) * 100).toFixed(1)}%`);

  if (results.failed === 0) {
    console.log('\n🎉 All tests passed! Settings persistence is working correctly.');
  } else {
    console.log('\n⚠️  Some tests failed. Check the details above.');
  }

  return results;
};

/**
 * Run a quick integration test
 */
export const runQuickTest = () => {
  console.log('🚀 Running quick settings persistence test...\n');
  return testSettingsPersistence();
};

/**
 * Test data corruption handling
 */
export const testCorruptionHandling = () => {
  console.log('🛡️  Testing corruption handling...\n');

  try {
    // Deliberately create corrupted data
    localStorage.setItem('production_tv_dashboard_corrupted_test', 'invalid{json');

    const result = getFromLocalStorage('corrupted_test');
    const passed = result === null;

    console.log(passed ? '✅ Corruption handling works correctly' : '❌ Corruption handling failed');

    return passed;
  } catch (error) {
    console.log(`❌ Corruption test failed: ${error.message}`);
    return false;
  }
};

// Export for console testing
if (typeof window !== 'undefined') {
  window.testSettingsPersistence = testSettingsPersistence;
  window.runQuickTest = runQuickTest;
  window.testCorruptionHandling = testCorruptionHandling;
}