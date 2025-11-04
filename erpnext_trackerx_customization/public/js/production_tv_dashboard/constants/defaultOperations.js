export const DEFAULT_OPERATIONS = [
  {
    id: 1,
    code: 'knitting',
    name: 'Knitting',
    icon: '🧶',
    color: '#3B82F6',
    sequence: 1,
    isVisible: true,
    columnWidth: 15
  },
  {
    id: 2,
    code: 'primary',
    name: 'Primary',
    icon: '🔧',
    color: '#8B5CF6',
    sequence: 2,
    isVisible: true,
    columnWidth: 15
  },
  {
    id: 3,
    code: 'washing',
    name: 'Washing',
    icon: '🧼',
    color: '#06B6D4',
    sequence: 3,
    isVisible: true,
    columnWidth: 15
  },
  {
    id: 4,
    code: 'cutting',
    name: 'Cutting',
    icon: '✂️',
    color: '#F97316',
    sequence: 4,
    isVisible: true,
    columnWidth: 15
  },
  {
    id: 5,
    code: 'linking',
    name: 'Linking',
    icon: '🔗',
    color: '#EC4899',
    sequence: 5,
    isVisible: true,
    columnWidth: 15
  },
  {
    id: 6,
    code: 'checking',
    name: 'Checking',
    icon: '✅',
    color: '#10B981',
    sequence: 6,
    isVisible: true,
    columnWidth: 15
  },
  {
    id: 7,
    code: 'packing',
    name: 'Packing',
    icon: '📦',
    color: '#F59E0B',
    sequence: 7,
    isVisible: true,
    columnWidth: 10
  }
];

export const getDefaultOperations = () => {
  return DEFAULT_OPERATIONS.map(op => ({ ...op }));
};