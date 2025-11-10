import { useState, useEffect, useCallback } from 'react';

export const useProductionData = () => {
  const [data, setData] = useState([]);
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = useCallback(async (limit = 20) => {
    try {
      setLoading(true);
      setError(null);

      // Call the real API - company will be auto-detected by backend
      const response = await frappe.call({
        method: 'erpnext_trackerx_customization.api.production_dashboard.get_production_dashboard_data',
        args: {
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
    updateStyleProgress
  };
};