import React from 'react';

const LoadingSpinner = ({ message = 'Loading production data...' }) => {
  return (
    <div className="loading-spinner-container">
      <div className="loading-spinner">
        <div className="spinner-ring"></div>
        <div className="spinner-ring"></div>
        <div className="spinner-ring"></div>
      </div>
      <div className="loading-message">{message}</div>
    </div>
  );
};

export default LoadingSpinner;