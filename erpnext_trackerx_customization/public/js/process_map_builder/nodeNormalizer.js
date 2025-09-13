// src/utils/nodeNormalizer.js
export const normalizeNodes = (nodes = []) =>
  nodes.map((node) => ({
    ...node,
    type: node.type || "default",
    position: node.position || { x: 0, y: 0 },
    data: {
      ...node.data,
      label: node.label || node.data?.label || "",
    },
    style:
      node.type === "group"
        ? {
            border: "2px dashed #0d6efd",
            backgroundColor: "#e7f1ff",
          }
        : node.type === "process_group"
        ? {
            border: "2px dashed orange",
            backgroundColor: "#fff6e5",
          }
        : node.style || undefined,
  }));

export const normalizeEdges = (edges = []) =>
  edges.map((edge) => ({
    ...edge,
    data: {
      ...(edge.data || {}),
      components: edge.data?.components || [],
    },
    style: {
      ...(edge.style || {}),
      stroke: edge.style?.stroke || "#999",
      strokeWidth: edge.style?.strokeWidth || 2,
    },
  }));
