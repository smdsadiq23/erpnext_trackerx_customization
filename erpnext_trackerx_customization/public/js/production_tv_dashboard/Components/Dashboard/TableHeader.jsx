import React from 'react';

const TableHeader = ({ columns }) => {
  return (
    <div className="table-header">
      {/* Fixed columns */}
      <div className="fixed-columns-header">
        <div className="header-cell style-header">
          <span>Style</span>
        </div>
        <div className="header-cell order-qty-header">
          <span>Order Qty</span>
        </div>
        <div className="header-cell delivery-header">
          <span>Delivery Date</span>
        </div>
      </div>

      {/* Dynamic operation columns */}
      <div className="operation-columns-header">
        {columns.map(column => (
          <div
            key={column.key}
            className="header-cell operation-header"
            style={{ width: `${column.columnWidth}%` }}
          >
            <div className="operation-header-content">
              <span className="operation-icon" style={{ color: column.color }}>
                {column.icon}
              </span>
              <span className="operation-name">{column.title}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TableHeader;