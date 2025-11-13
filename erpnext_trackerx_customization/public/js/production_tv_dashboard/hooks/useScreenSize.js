import { useState, useEffect } from 'react';
import { saveToLocalStorage, getFromLocalStorage } from '../utils/localStorageUtils';

export const useScreenSize = () => {
  const [screenSize, setScreenSize] = useState('55inch'); // Default to 55 inch
  const [fontSize, setFontSize] = useState(2.2);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const screenSizeMapping = {
    '24inch': { fontSize: 1.4, progressHeight: 18, iconSize: 20 },
    '32inch': { fontSize: 1.6, progressHeight: 20, iconSize: 24 },
    '43inch': { fontSize: 1.8, progressHeight: 22, iconSize: 28 },
    '55inch': { fontSize: 2.2, progressHeight: 26, iconSize: 32 },
    '65inch': { fontSize: 2.6, progressHeight: 30, iconSize: 36 },
    '70inch': { fontSize: 3.0, progressHeight: 34, iconSize: 40 }
  };

  useEffect(() => {
    // Load saved screen size preference
    const savedScreenSizeResult = getFromLocalStorage('screenSize');
    const savedScreenSize = savedScreenSizeResult?.data;
    if (savedScreenSize && screenSizeMapping[savedScreenSize]) {
      setScreenSize(savedScreenSize);
      setFontSize(screenSizeMapping[savedScreenSize].fontSize);
    }

    // Detect fullscreen changes
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const changeScreenSize = (newSize) => {
    if (screenSizeMapping[newSize]) {
      setScreenSize(newSize);
      setFontSize(screenSizeMapping[newSize].fontSize);
      const saveResult = saveToLocalStorage('screenSize', newSize);

      if (!saveResult.success) {
        console.error('Failed to save screen size setting:', saveResult.error);
        window.dispatchEvent(new CustomEvent('screenSizeSaveFailed', { detail: saveResult }));
      } else {
        window.dispatchEvent(new CustomEvent('screenSizeSaved', { detail: saveResult }));
      }
    }
  };

  const getScreenSettings = () => {
    return screenSizeMapping[screenSize] || screenSizeMapping['55inch'];
  };

  return {
    screenSize,
    fontSize,
    isFullscreen,
    changeScreenSize,
    getScreenSettings,
    availableSizes: Object.keys(screenSizeMapping)
  };
};