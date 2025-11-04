import React from 'react';
import DynamicProgressBar from '../UI/DynamicProgressBar';

const OperationCell = ({ operation, progress, totalQuantity, columnWidth, screenSize }) => {
  const { completed = 0, percentage = 0, status = 'pending' } = progress;

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#10B981';
      case 'on-track': return '#3B82F6';
      case 'warning': return '#F59E0B';
      case 'behind': return '#EF4444';
      default: return '#6B7280';
    }
  };

  return (
    <div
      className={`operation-cell ${status}`}
      style={{ width: `${columnWidth}%` }}
    >
      <div className="quantity-display">
        <div className="completed-count">
          <span className="number">{completed.toLocaleString()}</span>
        </div>
        <div className="percentage-display">
          <span
            className="percentage"
            style={{ color: getStatusColor(status) }}
          >
            {percentage}%
          </span>
        </div>
      </div>

      <DynamicProgressBar
        value={percentage}
        color={operation?.color || '#6B7280'}
        animated={true}
        status={status}
      />

      {percentage === 100 && (
        <div className="completion-badge">
          ✅ Complete
        </div>
      )}
    </div>
  );
};

export default OperationCell;