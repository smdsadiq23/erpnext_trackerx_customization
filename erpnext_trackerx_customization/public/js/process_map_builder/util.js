// Component colors
export const COMPONENT_COLORS = {
  Front: "#ff4d4f",   // Red
  Back: "#40a9ff",    // Blue
  Sleeve: "#52c41a"   // Green
};

// Color blending utility
export function blendColors(colors) {
  if (!colors.length) return "#000000";

  const rgbColors = colors.map(hex => {
    const bigint = parseInt(hex.slice(1), 16);
    return [
      (bigint >> 16) & 255,
      (bigint >> 8) & 255,
      bigint & 255
    ];
  });

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
