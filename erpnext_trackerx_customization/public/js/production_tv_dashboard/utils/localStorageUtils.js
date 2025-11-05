export const saveToLocalStorage = (key, data) => {
  try {
    const serializedData = JSON.stringify(data);
    localStorage.setItem(`production_tv_dashboard_${key}`, serializedData);
  } catch (error) {
    console.error('Error saving to localStorage:', error);
  }
};

export const getFromLocalStorage = (key) => {
  try {
    const serializedData = localStorage.getItem(`production_tv_dashboard_${key}`);
    if (serializedData === null) {
      return null;
    }
    return JSON.parse(serializedData);
  } catch (error) {
    console.error('Error loading from localStorage:', error);
    return null;
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