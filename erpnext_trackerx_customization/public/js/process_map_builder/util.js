// Dynamic color generation for components
function generateComponentColor(componentName) {
  if (!componentName) return "#999999";

  // Create a hash from component name for consistent colors
  let hash = 0;
  for (let i = 0; i < componentName.length; i++) {
    hash = componentName.charCodeAt(i) + ((hash << 5) - hash);
  }

  // Generate HSL color with good saturation and lightness for visibility
  const hue = Math.abs(hash) % 360;
  const saturation = 65 + (Math.abs(hash) % 20); // 65-85% for good vibrancy
  const lightness = 45 + (Math.abs(hash) % 15);  // 45-60% for good contrast

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Export function to get component color
export const getComponentColor = (componentName) => {
  return generateComponentColor(componentName);
};

// Legacy support - keep COMPONENT_COLORS for backward compatibility but make it dynamic
export const COMPONENT_COLORS = new Proxy({}, {
  get: function(target, prop) {
    return generateComponentColor(prop);
  }
});

// Color blending utility - works with both hex and HSL colors
export function blendColors(colors) {
  if (!colors.length) return "#999999";
  if (colors.length === 1) return colors[0];

  // Convert all colors to RGB for blending
  const rgbColors = colors.map(color => {
    if (color.startsWith('hsl')) {
      // Parse HSL: hsl(240, 70%, 50%)
      const hslMatch = color.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
      if (hslMatch) {
        const [, h, s, l] = hslMatch.map(Number);
        return hslToRgb(h, s, l);
      }
    } else if (color.startsWith('#')) {
      // Parse hex color
      const bigint = parseInt(color.slice(1), 16);
      return [
        (bigint >> 16) & 255,
        (bigint >> 8) & 255,
        bigint & 255
      ];
    }
    return [150, 150, 150]; // fallback gray
  });

  // Average the RGB values
  const avg = rgbColors
    .reduce((acc, val) => [
      acc[0] + val[0],
      acc[1] + val[1],
      acc[2] + val[2]
    ], [0, 0, 0])
    .map(c => Math.round(c / colors.length));

  return `#${((1 << 24) + (avg[0] << 16) + (avg[1] << 8) + avg[2])
    .toString(16)
    .slice(1)}`;
}

// Helper function to convert HSL to RGB
function hslToRgb(h, s, l) {
  h /= 360;
  s /= 100;
  l /= 100;

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;

  const r = Math.round(hueToRgb(p, q, h + 1/3) * 255);
  const g = Math.round(hueToRgb(p, q, h) * 255);
  const b = Math.round(hueToRgb(p, q, h - 1/3) * 255);

  return [r, g, b];
}

function hueToRgb(p, q, t) {
  if (t < 0) t += 1;
  if (t > 1) t -= 1;
  if (t < 1/6) return p + (q - p) * 6 * t;
  if (t < 1/2) return q;
  if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
  return p;
}
