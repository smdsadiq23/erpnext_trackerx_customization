import React, { useState, useEffect } from 'react';
import '../../styles/config.css';

const ConfigPanel = ({
  operations,
  onOperationsUpdate,
  onAddOperation,
  onRemoveOperation,
  onClose,
  screenSize,
  onScreenSizeChange
}) => {
  const [activeTab, setActiveTab] = useState('operations');
  const [saveStatus, setSaveStatus] = useState({ type: '', message: '', visible: false });

  const screenSizes = ['24inch', '32inch', '43inch', '55inch', '65inch', '70inch'];

  // Listen for save events from localStorage operations
  useEffect(() => {
    const handleOperationsSaved = (event) => {
      setSaveStatus({
        type: 'success',
        message: 'Operations configuration saved successfully',
        visible: true
      });
      // Auto-hide after 3 seconds
      setTimeout(() => setSaveStatus(prev => ({ ...prev, visible: false })), 3000);
    };

    const handleOperationsSaveFailed = (event) => {
      setSaveStatus({
        type: 'error',
        message: `Failed to save: ${event.detail?.error || 'Unknown error'}`,
        visible: true
      });
      // Auto-hide after 5 seconds for errors
      setTimeout(() => setSaveStatus(prev => ({ ...prev, visible: false })), 5000);
    };

    const handleScreenSizeSaved = (event) => {
      setSaveStatus({
        type: 'success',
        message: 'Screen size setting saved successfully',
        visible: true
      });
      setTimeout(() => setSaveStatus(prev => ({ ...prev, visible: false })), 3000);
    };

    const handleScreenSizeSaveFailed = (event) => {
      setSaveStatus({
        type: 'error',
        message: `Failed to save screen size: ${event.detail?.error || 'Unknown error'}`,
        visible: true
      });
      setTimeout(() => setSaveStatus(prev => ({ ...prev, visible: false })), 5000);
    };

    // Add event listeners
    window.addEventListener('operationsSaved', handleOperationsSaved);
    window.addEventListener('operationsSaveFailed', handleOperationsSaveFailed);
    window.addEventListener('screenSizeSaved', handleScreenSizeSaved);
    window.addEventListener('screenSizeSaveFailed', handleScreenSizeSaveFailed);

    // Cleanup event listeners
    return () => {
      window.removeEventListener('operationsSaved', handleOperationsSaved);
      window.removeEventListener('operationsSaveFailed', handleOperationsSaveFailed);
      window.removeEventListener('screenSizeSaved', handleScreenSizeSaved);
      window.removeEventListener('screenSizeSaveFailed', handleScreenSizeSaveFailed);
    };
  }, []);

  const handleOperationToggle = (operationId) => {
    const updatedOperations = operations.map(op =>
      op.id === operationId ? { ...op, isVisible: !op.isVisible } : op
    );
    onOperationsUpdate(updatedOperations);
  };

  return (
    <div className="config-panel">
      <div className="config-overlay" onClick={onClose}></div>
      <div className="config-content">
        <div className="config-header">
          <h3>Dashboard Configuration</h3>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        {/* Save Status Indicator */}
        {saveStatus.visible && (
          <div className={`save-status ${saveStatus.type}`}>
            <span className="status-icon">
              {saveStatus.type === 'success' ? '✓' : '⚠'}
            </span>
            <span className="status-message">{saveStatus.message}</span>
          </div>
        )}

        <div className="config-tabs">
          <button
            className={activeTab === 'operations' ? 'active' : ''}
            onClick={() => setActiveTab('operations')}
          >
            Operations
          </button>
          <button
            className={activeTab === 'display' ? 'active' : ''}
            onClick={() => setActiveTab('display')}
          >
            Display Settings
          </button>
        </div>

        <div className="config-body">
          {activeTab === 'operations' && (
            <div className="operations-config">
              <h4>Configure Operations</h4>
              <div className="operations-list">
                {operations.map(operation => (
                  <div key={operation.id} className="operation-item">
                    <div className="operation-info">
                      <span className="operation-icon" style={{ color: operation.color }}>
                        {operation.icon}
                      </span>
                      <span className="operation-name">{operation.name}</span>
                    </div>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={operation.isVisible}
                        onChange={() => handleOperationToggle(operation.id)}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'display' && (
            <div className="display-config">
              <h4>Screen Size Optimization</h4>
              <div className="screen-size-selector">
                {screenSizes.map(size => (
                  <button
                    key={size}
                    className={`size-btn ${screenSize === size ? 'active' : ''}`}
                    onClick={() => onScreenSizeChange(size)}
                  >
                    {size.replace('inch', '"')}
                  </button>
                ))}
              </div>

              <div className="display-info">
                <p>Current setting: <strong>{screenSize.replace('inch', '"')}</strong></p>
                <p>Optimizes font size, spacing, and progress bar dimensions for your TV screen.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfigPanel;