const STYLE_NAMES = [
  'Premium Cotton Crew Neck',
  'Merino Wool V-Neck Sweater',
  'Classic Polo Shirt',
  'Hooded Sweatshirt',
  'Button-down Shirt',
  'Casual T-Shirt',
  'Knitted Cardigan',
  'Denim Jacket'
];

const COLORS = [
  'Navy Blue',
  'Charcoal Grey',
  'Burgundy',
  'Forest Green',
  'Black',
  'White',
  'Royal Blue',
  'Maroon'
];

const generateRandomDate = () => {
  const start = new Date();
  const end = new Date(start.getTime() + (30 * 24 * 60 * 60 * 1000)); // 30 days from now
  const randomTime = start.getTime() + Math.random() * (end.getTime() - start.getTime());
  return new Date(randomTime).toLocaleDateString();
};

const generateRandomProgress = () => {
  const operations = ['knitting', 'primary', 'washing', 'cutting', 'linking', 'checking', 'packing'];
  const progress = {};

  operations.forEach((op, index) => {
    // Simulate realistic production flow - later operations have lower completion
    const baseCompletion = Math.max(0, 100 - (index * 8) + (Math.random() * 15));
    const percentage = Math.min(100, Math.floor(baseCompletion));
    progress[op] = {
      percentage,
      completed: 0, // Will be calculated based on total quantity
      status: percentage >= 100 ? 'completed' : percentage >= 80 ? 'on-track' : percentage >= 60 ? 'warning' : 'behind'
    };
  });

  return progress;
};

export const MOCK_PRODUCTION_DATA = Array.from({ length: 8 }, (_, index) => {
  const totalQuantity = Math.floor(Math.random() * 500) + 500;
  const progress = generateRandomProgress();

  // Calculate completed quantities based on percentages
  Object.keys(progress).forEach(op => {
    progress[op].completed = Math.floor((progress[op].percentage / 100) * totalQuantity);
  });

  return {
    id: `ST-2024-${(index + 1).toString().padStart(3, '0')}`,
    styleName: STYLE_NAMES[index % STYLE_NAMES.length],
    description: `Style Group ${index + 1}`,
    color: COLORS[index % COLORS.length],
    deliveryDate: generateRandomDate(),
    totalQuantity,
    progress
  };
});

export const generateMockData = (count = 8) => {
  return MOCK_PRODUCTION_DATA.slice(0, count);
};