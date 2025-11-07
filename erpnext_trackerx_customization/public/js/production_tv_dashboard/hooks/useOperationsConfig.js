import { useState, useEffect } from 'react';
import { getDefaultOperations } from '../constants/defaultOperations';
import { saveToLocalStorage, getFromLocalStorage } from '../utils/localStorageUtils';

export const useOperationsConfig = (dynamicOperations = []) => {
  const [operations, setOperations] = useState([]);

  useEffect(() => {
    // If dynamic operations are available, use them as the source of truth
    if (dynamicOperations && dynamicOperations.length > 0) {
      setOperations(dynamicOperations);
      // Optionally save to localStorage for offline mode
      saveToLocalStorage('dynamic_operations', dynamicOperations);
    } else {
      // Fallback: Load from localStorage or use defaults
      const savedDynamicOperations = getFromLocalStorage('dynamic_operations');
      const savedOperations = getFromLocalStorage('operations');
      setOperations(savedDynamicOperations || savedOperations || getDefaultOperations());
    }
  }, [dynamicOperations]);

  const updateOperations = (newOperations) => {
    setOperations(newOperations);
    saveToLocalStorage('operations', newOperations);
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