import { useState, useEffect } from 'react';
import { getDefaultOperations } from '../constants/defaultOperations';
import { saveToLocalStorage, getFromLocalStorage } from '../utils/localStorageUtils';

export const useOperationsConfig = () => {
  const [operations, setOperations] = useState([]);

  useEffect(() => {
    // Load from localStorage or use defaults
    const savedOperations = getFromLocalStorage('operations');
    setOperations(savedOperations || getDefaultOperations());
  }, []);

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