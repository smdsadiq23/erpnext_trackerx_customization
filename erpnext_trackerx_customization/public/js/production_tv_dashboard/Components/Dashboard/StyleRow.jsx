import React from 'react';
import OperationCell from './OperationCell';

const StyleRow = ({ styleData, operations, columns, screenSize }) => {
  return (
    <div className="style-row">
      {/* Fixed columns */}
      <div className="fixed-columns">
        <div className="style-info-cell">
          <div className="style-id">{styleData.id}</div>
          <div className="style-name">{styleData.styleName}</div>
          <div className="style-description">{styleData.description}</div>
        </div>

        <div className="color-cell">
          <div className="color-value">{styleData.color}</div>
        </div>

        <div className="delivery-cell">
          <div className="delivery-date">{styleData.deliveryDate}</div>
        </div>
      </div>

      {/* Dynamic operation columns */}
      <div className="operation-columns">
        {columns.map(column => {
          const operation = operations.find(op => op.code === column.key);
          const progress = styleData.progress[column.key] || {
            percentage: 0,
            completed: 0,
            status: 'pending'
          };

          return (
            <OperationCell
              key={column.key}
              operation={operation}
              progress={progress}
              totalQuantity={styleData.totalQuantity}
              columnWidth={column.columnWidth}
              screenSize={screenSize}
            />
          );
        })}
      </div>
    </div>
  );
};

export default StyleRow;