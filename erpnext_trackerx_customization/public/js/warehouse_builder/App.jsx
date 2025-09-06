import  React, { useEffect } from "react";

/**
 * Warehouse Builder (read-only tree)
 * Drop this into erpnext_trackerx_customization/public/js/warehouse_builder/App.jsx
 */
export function App() {
  const [items, setItems] = React.useState([]); // raw flat list
  const [tree, setTree] = React.useState([]); // nested tree
  const [expanded, setExpanded] = React.useState({}); // expanded state map by name
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  useEffect(() => {
    let mounted = true;

    async function fetchWarehouses() {
      setLoading(true);
      try {
        // Using frappe.client.get_list returns an array of objects which is easy to map
        const res = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Warehouse",
            fields: [
              "name",
              "warehouse_name",
              "parent_warehouse",
              "is_group",
              "disabled",
              "warehouse_type"
            ],
            filters: [
              // only active warehouses by default — change/remove as needed
              ["disabled", "!=", 1]
            ],
            limit_page_length: 1000, // adjust if you have >1000 warehouses
          },
        });

        console.log("🔍 raw get_list response:", res);
        const list = res.message || [];

        if (!mounted) return;
        setItems(list);

        // Build map and tree
        const map = {};
        list.forEach((it) => {
          map[it.name] = { ...it, children: [] };
        });

        const roots = [];
        list.forEach((it) => {
          const parent = it.parent_warehouse;
          if (parent && map[parent]) {
            map[parent].children.push(map[it.name]);
          } else {
            // if parent is missing or falsy -> top-level
            roots.push(map[it.name]);
          }
        });

        // Sort helper (by warehouse_name or fallback to name)
        const sortFn = (a, b) =>
          (a.warehouse_name || a.name).localeCompare(b.warehouse_name || b.name);

        const sortRecursive = (node) => {
          node.children.sort(sortFn);
          node.children.forEach(sortRecursive);
        };

        roots.sort(sortFn);
        roots.forEach(sortRecursive);

        setTree(roots);
      } catch (err) {
        console.error("❌ fetchWarehouses error:", err);
        setError(err);
      } finally {
        setLoading(false);
      }
    }

    fetchWarehouses();

    return () => {
      mounted = false;
    };
  }, []);

  function toggleExpand(name) {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  }

  function renderNode(node, level = 0) {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = !!expanded[node.name];

    const rowStyle = {
      display: "flex",
      alignItems: "center",
      padding: "8px 10px",
      background: level % 2 === 0 ? "#ffffff" : "#fbfbfb",
      borderBottom: "1px solid #eee",
      fontFamily: "Arial, sans-serif",
    };

    const nameContainerStyle = {
      display: "flex",
      alignItems: "center",
      flex: 1,
      paddingLeft: level * 16, // indent per level
      minWidth: 0,
    };

    const caretStyle = {
      width: 30,
      height: 30,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      marginRight: 8,
      cursor: hasChildren ? "pointer" : "default",
      userSelect: "none",
      borderRadius: 4,
      border: "none",
      background: "transparent",
      fontSize: 24, // 🔹 bigger caret
      lineHeight: 1,
      color: "#444",
    };

    const metaStyle = {
      width: 140,
      textAlign: "right",
      color: "#666",
      fontSize: 13,
      paddingLeft: 12,
    };

    return (
      <div key={node.name}>
        <div style={rowStyle}>
          <div style={nameContainerStyle}>
            {hasChildren ? (
              <button
                aria-label={isExpanded ? "Collapse" : "Expand"}
                onClick={() => toggleExpand(node.name)}
                style={caretStyle}
                title={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? "▾" : "▸"}
              </button>
            ) : (
              // placeholder for alignment
              <span style={{ display: "inline-block", width: 18, marginRight: 8 }} />
            )}

            <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              <strong style={{ fontSize: 14 }}>{node.warehouse_name || node.name}</strong>
              <div style={{ fontSize: 12, color: "#888" }}>{node.name}</div>
            </div>
          </div>

          <div style={metaStyle}>{node.warehouse_type || ""}</div>
        </div>

        {hasChildren && isExpanded && (
          <div>
            {node.children.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: 12 }}>
      {/* <h3 style={{ margin: 0, marginBottom: 6 }}>Warehouse Builder — Tree (read-only)</h3> */}


      <div
        style={{
          border: "1px solid #e6e6e6",
          borderRadius: 6,
          overflow: "auto",
          maxHeight: "60vh",
          boxShadow: "0 1px 0 rgba(0,0,0,0.02)",
        }}
      >
        {loading ? (
          <div style={{ padding: 20, color: "#555" }}>Loading warehouses…</div>
        ) : error ? (
          <div style={{ padding: 20, color: "crimson" }}>
            Error loading warehouses. Check console for details.
          </div>
        ) : tree.length === 0 ? (
          <div style={{ padding: 20, color: "#666" }}>No warehouses found.</div>
        ) : (
          tree.map((root) => renderNode(root, 0))
        )}
      </div>
    </div>
  );
}
