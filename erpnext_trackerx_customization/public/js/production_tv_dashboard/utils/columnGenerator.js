export const generateColumns = (operations) => {
  if (!operations || !Array.isArray(operations)) {
    return [];
  }

  return operations
    .filter(operation => operation.isVisible !== false)
    .sort((a, b) => (a.sequence || 0) - (b.sequence || 0))
    .map((operation, index) => ({
      key: operation.code,
      title: operation.name,
      icon: operation.icon,
      color: operation.color,
      columnWidth: operation.columnWidth || 15,
      sequence: operation.sequence || index,
      isVisible: operation.isVisible !== false
    }));
};

export const generateTableHeader = (operations) => {
  const columns = generateColumns(operations);

  return [
    { key: 'style', title: 'Style', width: '20%', fixed: true },
    { key: 'color', title: 'Colour', width: '10%', fixed: true },
    { key: 'delivery', title: 'Delivery Date', width: '10%', fixed: true },
    ...columns.map(col => ({
      ...col,
      width: `${col.columnWidth}%`,
      fixed: false
    }))
  ];
};

export const calculateTotalWidth = (operations) => {
  const fixedWidth = 40; // 40% for fixed columns
  const operationWidth = operations.reduce((total, op) => total + (op.columnWidth || 15), 0);
  return fixedWidth + operationWidth;
};