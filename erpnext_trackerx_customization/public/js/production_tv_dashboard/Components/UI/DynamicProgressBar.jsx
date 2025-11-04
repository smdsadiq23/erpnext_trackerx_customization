import React, { useEffect, useState } from 'react';

const DynamicProgressBar = ({ value, color, animated = true, status = 'pending' }) => {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => {
        setAnimatedValue(value);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setAnimatedValue(value);
    }
  }, [value, animated]);

  const getGradientColor = (baseColor) => {
    // Create a lighter version of the color for gradient
    const r = parseInt(baseColor.slice(1, 3), 16);
    const g = parseInt(baseColor.slice(3, 5), 16);
    const b = parseInt(baseColor.slice(5, 7), 16);

    const lighterR = Math.min(255, r + 40);
    const lighterG = Math.min(255, g + 40);
    const lighterB = Math.min(255, b + 40);

    return `#${lighterR.toString(16).padStart(2, '0')}${lighterG.toString(16).padStart(2, '0')}${lighterB.toString(16).padStart(2, '0')}`;
  };

  const progressStyle = {
    width: `${animatedValue}%`,
    background: `linear-gradient(90deg, ${color} 0%, ${getGradientColor(color)} 100%)`,
    transition: animated ? 'width 1s ease-in-out' : 'none'
  };

  return (
    <div className="dynamic-progress-bar">
      <div className="progress-track">
        <div
          className={`progress-fill ${animated ? 'animated' : ''} ${status}`}
          style={progressStyle}
        >
          {animatedValue > 20 && (
            <div className="progress-shine"></div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DynamicProgressBar;