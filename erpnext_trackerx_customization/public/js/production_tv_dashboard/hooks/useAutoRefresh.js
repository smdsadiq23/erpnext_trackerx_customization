import { useEffect } from 'react';

export const useAutoRefresh = (refreshFn, interval = 30000) => {
  useEffect(() => {
    if (!refreshFn || typeof refreshFn !== 'function') {
      console.warn('useAutoRefresh: refreshFn is not a valid function');
      return;
    }

    console.log(`useAutoRefresh: Setting up auto-refresh with interval ${interval}ms`);

    const timer = setInterval(() => {
      console.log('useAutoRefresh: Triggering refresh');
      refreshFn();
    }, interval);

    return () => {
      console.log('useAutoRefresh: Cleaning up timer');
      clearInterval(timer);
    };
  }, [refreshFn, interval]);
};