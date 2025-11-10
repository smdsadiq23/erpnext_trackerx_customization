import React, { useState, useEffect, useRef } from 'react';
import DashboardHeader from './Components/Dashboard/DashboardHeader';
import DynamicTable from './Components/Dashboard/DynamicTable';
import ConfigPanel from './Components/Configuration/ConfigPanel';
import { useOperationsConfig } from './hooks/useOperationsConfig';
import { useProductionData } from './hooks/useProductionData';
import { useScreenSize } from './hooks/useScreenSize';

export const App = ({ pageInstance }) => {
  const [showConfig, setShowConfig] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date());
  const [appError, setAppError] = useState(null);

  const autoRefreshInterval = useRef(null);

  console.log('App: Rendering with pageInstance:', pageInstance);

  // Initialize hooks with error handling
  let operations, updateOperations, addOperation, removeOperation;
  let data, loading, error, refresh;
  let screenSize, fontSize, changeScreenSize, getScreenSettings;

  try {
    console.log('App: Initializing hooks...');

    // First get production data which includes dynamic operations
    const productionData = useProductionData();
    data = productionData.data;
    loading = productionData.loading;
    error = productionData.error;
    refresh = productionData.refresh;

    // Then pass dynamic operations to operations config
    const operationsConfig = useOperationsConfig(productionData.operations);
    operations = operationsConfig.operations;
    updateOperations = operationsConfig.updateOperations;
    addOperation = operationsConfig.addOperation;
    removeOperation = operationsConfig.removeOperation;

    const screenSizeConfig = useScreenSize();
    screenSize = screenSizeConfig.screenSize;
    fontSize = screenSizeConfig.fontSize;
    changeScreenSize = screenSizeConfig.changeScreenSize;
    getScreenSettings = screenSizeConfig.getScreenSettings;

    console.log('App: Hooks initialized successfully');
    console.log('App: Operations:', operations?.length || 0);
    console.log('App: Data:', data?.length || 0);
    console.log('App: Screen size:', screenSize);
  } catch (err) {
    console.error('App: Error initializing hooks:', err);
    setAppError(err.message);
  }

  // Setup auto-refresh
  useEffect(() => {
    try {
      console.log('App: Setting up auto-refresh...');
      if (refresh) {
        autoRefreshInterval.current = setInterval(() => {
          console.log('App: Auto-refresh triggered');
          refresh();
          setLastUpdateTime(new Date());
        }, 30000); // Refresh every 30 seconds
      }

      return () => {
        if (autoRefreshInterval.current) {
          console.log('App: Cleaning up auto-refresh interval');
          clearInterval(autoRefreshInterval.current);
        }
      };
    } catch (err) {
      console.error('App: Error setting up auto-refresh:', err);
    }
  }, [refresh]);


  // Expose toggle function to page instance
  useEffect(() => {
    try {
      if (pageInstance) {
        console.log('App: Setting up page instance communication');
        pageInstance.react_instance = {
          toggleConfig: () => {
            console.log('App: Config toggle called from page instance');
            setShowConfig(prev => !prev);
          }
        };
      }
    } catch (err) {
      console.error('App: Error setting up page instance communication:', err);
    }
  }, [pageInstance, showConfig]);

  const handleManualRefresh = () => {
    try {
      console.log('App: Manual refresh triggered');
      if (refresh) {
        refresh();
        setLastUpdateTime(new Date());
      }
    } catch (err) {
      console.error('App: Error during manual refresh:', err);
    }
  };

  const handleConfigToggle = () => {
    console.log('App: Config toggle from header, current state:', showConfig);
    setShowConfig(prev => !prev);
  };

  if (appError) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#721c24', background: '#f8d7da', border: '1px solid #f5c6cb', borderRadius: '8px', margin: '20px' }}>
        <h3>Application Error</h3>
        <p>{appError}</p>
        <button onClick={() => window.location.reload()} style={{ padding: '8px 16px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Reload Page
        </button>
      </div>
    );
  }

  const screenSettings = getScreenSettings ? getScreenSettings() : { progressHeight: 24, iconSize: 24 };

  console.log('App: Rendering dashboard with showConfig:', showConfig);

  return (
    <div
      className={`production-dashboard dashboard-${screenSize || '55inch'}`}
      style={{
        '--font-size': `${fontSize || 2.2}rem`,
        '--progress-height': `${screenSettings.progressHeight}px`,
        '--icon-size': `${screenSettings.iconSize}px`
      }}
    >
      <DashboardHeader
        lastUpdated={lastUpdateTime}
        onRefresh={handleManualRefresh}
        onConfigToggle={handleConfigToggle}
        isLoading={loading}
      />

      {showConfig && (
        <ConfigPanel
          operations={operations || []}
          onOperationsUpdate={updateOperations}
          onAddOperation={addOperation}
          onRemoveOperation={removeOperation}
          onClose={() => setShowConfig(false)}
          screenSize={screenSize || '55inch'}
          onScreenSizeChange={changeScreenSize}
        />
      )}

      <DynamicTable
        data={data || []}
        operations={operations || []}
        loading={loading}
        error={error}
        screenSize={screenSize || '55inch'}
      />

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={handleManualRefresh} className="retry-btn">
            Retry
          </button>
        </div>
      )}
    </div>
  );
};