import React from 'react';

const DashboardHeader = ({ lastUpdated, onRefresh, onConfigToggle, isLoading }) => {
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: true,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const currentTime = new Date();

  return (
    <div className="dashboard-header">
      <div className="header-left">
        <div className="dashboard-title">
          <span className="title-icon">📊</span>
          <h1>Production Dashboard</h1>
          <span className="subtitle">Real-time Shopfloor Tracking</span>
        </div>
      </div>

      <div className="header-center">
        <div className="last-updated">
          <span className="update-label">Last Updated:</span>
          <span className="update-time">
            {lastUpdated ? formatTime(lastUpdated) : '--:--:--'}
          </span>
          {isLoading && <span className="loading-indicator">🔄</span>}
        </div>
      </div>

      <div className="header-right">
        <div className="current-time">
          <div className="time-display">
            {formatTime(currentTime)}
          </div>
          <div className="date-display">
            {formatDate(currentTime)}
          </div>
        </div>

        <div className="header-actions">
          <button
            className="action-btn refresh-btn"
            onClick={onRefresh}
            disabled={isLoading}
            title="Refresh Data"
          >
            🔄
          </button>
          <button
            className="action-btn config-btn"
            onClick={onConfigToggle}
            title="Configuration"
          >
            ⚙️
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardHeader;