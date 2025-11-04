import { useState, useEffect, useCallback } from 'react';
import { generateMockData } from '../constants/mockData';

export const useProductionData = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 800));

      // Generate mock data
      const mockData = generateMockData(8);

      setData(mockData);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch production data');
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateStyleProgress = useCallback((styleId, operationCode, newProgress) => {
    setData(prevData =>
      prevData.map(style => {
        if (style.id === styleId) {
          const updatedProgress = {
            ...style.progress,
            [operationCode]: {
              ...style.progress[operationCode],
              ...newProgress,
              completed: Math.floor((newProgress.percentage / 100) * style.totalQuantity)
            }
          };
          return { ...style, progress: updatedProgress };
        }
        return style;
      })
    );
  }, []);

  const simulateRealTimeUpdates = useCallback(() => {
    setData(prevData =>
      prevData.map(style => {
        const updatedProgress = { ...style.progress };

        // Randomly update some operations with small changes
        Object.keys(updatedProgress).forEach(op => {
          if (Math.random() < 0.3) { // 30% chance to update each operation
            const currentPercentage = updatedProgress[op].percentage;
            const change = (Math.random() - 0.5) * 2; // -1 to +1 change
            const newPercentage = Math.max(0, Math.min(100, currentPercentage + change));

            updatedProgress[op] = {
              ...updatedProgress[op],
              percentage: Math.floor(newPercentage),
              completed: Math.floor((newPercentage / 100) * style.totalQuantity)
            };
          }
        });

        return { ...style, progress: updatedProgress };
      })
    );
    setLastUpdated(new Date());
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    refresh: fetchData,
    updateStyleProgress,
    simulateRealTimeUpdates
  };
};