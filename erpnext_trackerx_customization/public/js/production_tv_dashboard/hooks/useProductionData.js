import { useState, useEffect, useCallback } from 'react';

export const useProductionData = () => {
  const [data, setData] = useState([]);
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = useCallback(async (company = null, limit = 20) => {
    try {
      setLoading(true);
      setError(null);

      // Call the real API
      const response = await frappe.call({
        method: 'erpnext_trackerx_customization.api.production_dashboard.get_production_dashboard_data',
        args: {
          company: company,
          limit: limit
        }
      });

      if (response.message && response.message.success) {
        const apiData = response.message;
        setData(apiData.data || []);
        setOperations(apiData.operations_config || []);
        setLastUpdated(new Date());
      } else {
        throw new Error(response.message?.error?.message || 'API returned no data');
      }
    } catch (err) {
      setError('Failed to fetch production data: ' + (err.message || err));
      console.error('Data fetch error:', err);
      // Fallback to empty data on error
      setData([]);
      setOperations([]);
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
    operations,
    loading,
    error,
    lastUpdated,
    refresh: fetchData,
    updateStyleProgress,
    simulateRealTimeUpdates
  };
};