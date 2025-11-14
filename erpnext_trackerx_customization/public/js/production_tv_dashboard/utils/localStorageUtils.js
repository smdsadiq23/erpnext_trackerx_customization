export const saveToLocalStorage = (key, data) => {
  try {
    // Validate input
    if (!key || typeof key !== 'string') {
      throw new Error('Invalid key provided');
    }

    if (data === undefined) {
      console.warn(`Attempting to save undefined value for key: ${key}`);
      return { success: false, error: 'Undefined value' };
    }

    const serializedData = JSON.stringify(data);
    const fullKey = `production_tv_dashboard_${key}`;

    // Check localStorage availability and quota
    if (typeof Storage === 'undefined') {
      throw new Error('localStorage is not supported');
    }

    localStorage.setItem(fullKey, serializedData);

    // Verify the save was successful
    const verification = localStorage.getItem(fullKey);
    if (verification !== serializedData) {
      throw new Error('Data verification failed after save');
    }

    // Save timestamp for tracking
    localStorage.setItem(`${fullKey}_timestamp`, Date.now().toString());

    return { success: true, timestamp: Date.now() };
  } catch (error) {
    console.error(`Error saving to localStorage [${key}]:`, error);

    // Handle quota exceeded error
    if (error.name === 'QuotaExceededError') {
      console.warn('localStorage quota exceeded, attempting cleanup...');
      cleanupOldEntries();
      // Retry once after cleanup
      try {
        localStorage.setItem(`production_tv_dashboard_${key}`, JSON.stringify(data));
        return { success: true, timestamp: Date.now(), retried: true };
      } catch (retryError) {
        return { success: false, error: 'Storage quota exceeded', originalError: error };
      }
    }

    return { success: false, error: error.message, originalError: error };
  }
};

export const getFromLocalStorage = (key) => {
  try {
    // Validate input
    if (!key || typeof key !== 'string') {
      console.warn('Invalid key provided to getFromLocalStorage');
      return null;
    }

    const fullKey = `production_tv_dashboard_${key}`;
    const serializedData = localStorage.getItem(fullKey);

    if (serializedData === null) {
      return null;
    }

    // Check if localStorage is corrupted
    if (serializedData === '') {
      console.warn(`Empty value found for key: ${key}, removing corrupted entry`);
      localStorage.removeItem(fullKey);
      return null;
    }

    const parsedData = JSON.parse(serializedData);

    // Get and return metadata if available
    const timestampKey = `${fullKey}_timestamp`;
    const timestamp = localStorage.getItem(timestampKey);

    return {
      data: parsedData,
      timestamp: timestamp ? parseInt(timestamp) : null,
      key: key
    };
  } catch (error) {
    console.error(`Error loading from localStorage [${key}]:`, error);

    // If JSON parsing failed, remove the corrupted entry
    if (error instanceof SyntaxError) {
      console.warn(`Corrupted JSON data for key: ${key}, removing entry`);
      try {
        localStorage.removeItem(`production_tv_dashboard_${key}`);
        localStorage.removeItem(`production_tv_dashboard_${key}_timestamp`);
      } catch (cleanupError) {
        console.error('Error during cleanup:', cleanupError);
      }
    }

    return null;
  }
};

// Helper function to cleanup old localStorage entries
const cleanupOldEntries = () => {
  try {
    const keys = Object.keys(localStorage);
    const dashboardKeys = keys.filter(key => key.startsWith('production_tv_dashboard_'));
    const now = Date.now();
    const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days in milliseconds

    dashboardKeys.forEach(key => {
      if (key.endsWith('_timestamp')) {
        const timestamp = parseInt(localStorage.getItem(key));
        if (now - timestamp > maxAge) {
          const dataKey = key.replace('_timestamp', '');
          localStorage.removeItem(dataKey);
          localStorage.removeItem(key);
          console.log(`Cleaned up old localStorage entry: ${dataKey}`);
        }
      }
    });
  } catch (error) {
    console.error('Error during localStorage cleanup:', error);
  }
};

export const removeFromLocalStorage = (key) => {
  try {
    localStorage.removeItem(`production_tv_dashboard_${key}`);
  } catch (error) {
    console.error('Error removing from localStorage:', error);
  }
};

export const clearAllDashboardData = () => {
  try {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('production_tv_dashboard_')) {
        localStorage.removeItem(key);
      }
    });
  } catch (error) {
    console.error('Error clearing dashboard data:', error);
  }
};