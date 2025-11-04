import React, { useState } from 'react';

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

  const screenSizes = ['24inch', '32inch', '43inch', '55inch', '65inch', '70inch'];

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