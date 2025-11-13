import { useState, useEffect } from 'react';
import { getDefaultOperations } from '../constants/defaultOperations';
import { saveToLocalStorage, getFromLocalStorage } from '../utils/localStorageUtils';

// Smart merge function to preserve user preferences while incorporating new dynamic operations
const smartMergeOperations = (dynamicOps, savedOps) => {
  if (!savedOps || savedOps.length === 0) {
    return dynamicOps;
  }

  // Create a map of saved operations by operation name for quick lookup
  const savedOpsMap = new Map();
  savedOps.forEach(op => {
    savedOpsMap.set(op.name || op.operation, op);
  });

  // Merge operations: use saved preferences where available, add new dynamic operations
  const mergedOps = [];
  const addedOperations = new Set();

  // First, add saved operations that still exist in dynamic operations
  dynamicOps.forEach(dynamicOp => {
    const opKey = dynamicOp.name || dynamicOp.operation;
    const savedOp = savedOpsMap.get(opKey);

    if (savedOp) {
      // Preserve user preferences but update with latest dynamic data
      mergedOps.push({
        ...dynamicOp,
        ...savedOp,
        // Keep dynamic operation's core data but preserve user settings
        name: dynamicOp.name || dynamicOp.operation,
        operation: dynamicOp.operation || dynamicOp.name,
      });
    } else {
      // New dynamic operation, add with default enabled state
      mergedOps.push({
        ...dynamicOp,
        enabled: true,
        sequence: mergedOps.length + 1,
        id: dynamicOp.id || Date.now() + Math.random()
      });
    }
    addedOperations.add(opKey);
  });

  // Add any saved operations that don't exist in dynamic operations (custom user additions)
  savedOps.forEach(savedOp => {
    const opKey = savedOp.name || savedOp.operation;
    if (!addedOperations.has(opKey)) {
      mergedOps.push({
        ...savedOp,
        isCustom: true // Mark as custom user addition
      });
    }
  });

  return mergedOps;
};

export const useOperationsConfig = (dynamicOperations = []) => {
  const [operations, setOperations] = useState([]);

  useEffect(() => {
    // Load user preferences first
    const savedOperationsResult = getFromLocalStorage('operations');
    const savedDynamicOperationsResult = getFromLocalStorage('dynamic_operations');

    // Extract data from enhanced localStorage response
    const savedOperations = savedOperationsResult?.data;
    const savedDynamicOperations = savedDynamicOperationsResult?.data;

    if (dynamicOperations && dynamicOperations.length > 0) {
      // Smart merge: preserve user preferences while incorporating new dynamic operations
      const mergedOperations = smartMergeOperations(dynamicOperations, savedOperations);
      setOperations(mergedOperations);
      // Save dynamic operations for offline mode
      const saveResult = saveToLocalStorage('dynamic_operations', dynamicOperations);
      if (!saveResult.success) {
        console.warn('Failed to save dynamic operations:', saveResult.error);
      }
    } else {
      // Fallback: Load from localStorage or use defaults
      setOperations(savedDynamicOperations || savedOperations || getDefaultOperations());
    }
  }, [dynamicOperations]);

  const updateOperations = (newOperations) => {
    setOperations(newOperations);
    const saveResult = saveToLocalStorage('operations', newOperations);
    if (!saveResult.success) {
      console.error('Failed to save operations configuration:', saveResult.error);
      // You could emit an event here for UI feedback
      window.dispatchEvent(new CustomEvent('operationsSaveFailed', { detail: saveResult }));
    } else {
      // Emit success event for UI feedback
      window.dispatchEvent(new CustomEvent('operationsSaved', { detail: saveResult }));
    }
    return saveResult;
  };

  const addOperation = (operation) => {
    const newOp = {
      ...operation,
      id: Date.now(),
      sequence: operations.length + 1
    };
    const newOps = [...operations, newOp];
    updateOperations(newOps);
  };

  const removeOperation = (operationId) => {
    const newOps = operations.filter(op => op.id !== operationId);
    updateOperations(newOps);
  };

  const updateOperation = (operationId, updates) => {
    const newOps = operations.map(op =>
      op.id === operationId ? { ...op, ...updates } : op
    );
    updateOperations(newOps);
  };

  const reorderOperations = (startIndex, endIndex) => {
    const result = Array.from(operations);
    const [removed] = result.splice(startIndex, 1);
    result.splice(endIndex, 0, removed);

    // Update sequences
    const reordered = result.map((op, index) => ({
      ...op,
      sequence: index + 1
    }));

    updateOperations(reordered);
  };

  const resetToDefaults = () => {
    updateOperations(getDefaultOperations());
  };

  return {
    operations,
    updateOperations,
    addOperation,
    removeOperation,
    updateOperation,
    reorderOperations,
    resetToDefaults
  };
};