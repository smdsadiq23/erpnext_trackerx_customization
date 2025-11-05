import React from 'react';
import TableHeader from './TableHeader';
import StyleRow from './StyleRow';
import LoadingSpinner from '../UI/LoadingSpinner';
import { generateColumns } from '../../utils/columnGenerator';

const DynamicTable = ({ data, operations, loading, error, screenSize }) => {
  const columns = generateColumns(operations);

  if (loading && (!data || data.length === 0)) {
    return <LoadingSpinner />;
  }

  if (error && (!data || data.length === 0)) {
    return (
      <div className="error-state">
        <div className="error-icon">⚠️</div>
        <div className="error-message">{error}</div>
        <div className="error-suggestion">Please check your connection and try again</div>
      </div>
    );
  }

  return (
    <div className="dynamic-table">
      <TableHeader columns={columns} />
      <div className="table-body">
        {data && data.length > 0 ? (
          data.map((styleGroup, index) => (
            <StyleRow
              key={styleGroup.id || index}
              styleData={styleGroup}
              operations={operations}
              columns={columns}
              screenSize={screenSize}
            />
          ))
        ) : (
          <div className="no-data-state">
            <div className="no-data-icon">📭</div>
            <div className="no-data-message">No production data available</div>
          </div>
        )}
      </div>

      {loading && data && data.length > 0 && (
        <div className="updating-indicator">
          <span>🔄 Updating data...</span>
        </div>
      )}
    </div>
  );
};

export default DynamicTable;