import React, { useEffect, useState } from "react";

export function App() {
  const [items, setItems] = useState([]);
  const [tree, setTree] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [warehouseTypes, setWarehouseTypes] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState({ show: false, node: null });

  // 🔹 Modal state
  const [showModal, setShowModal] = useState(false);
  const [selectedParent, setSelectedParent] = useState(null);
  const [form, setForm] = useState({ warehouse_name: "", warehouse_type: "" });

  // 🔹 Fetch Warehouses (reusable)
  async function fetchWarehouses() {
    setLoading(true);
    try {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Warehouse",
          // fields: [
          //   "name",
          //   "warehouse_name",
          //   "parent_warehouse",
          //   "is_group",
          //   "disabled",
          //   "warehouse_type",
          // ],
          fields: ["*"],
          filters: [["disabled", "!=", 1]],
          limit_page_length: 1000,
        },
      });

      const list = res.message || [];
      setItems(list);

      // build tree
      const map = {};
      list.forEach((it) => (map[it.name] = { ...it, children: [] }));
      const roots = [];
      list.forEach((it) => {
        if (it.parent_warehouse && map[it.parent_warehouse]) {
          map[it.parent_warehouse].children.push(map[it.name]);
        } else {
          roots.push(map[it.name]);
        }
      });

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

  // 🔹 On mount → fetch data
  useEffect(() => {
    fetchWarehouses();
  }, []);

  // 🔹 Fetch Warehouse Types
  useEffect(() => {
    async function fetchWarehouseTypes() {
      try {
        const res = await frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Warehouse Type",
            fields: ["name"],
            limit_page_length: 1000,
          },
        });
        setWarehouseTypes(res.message || []);
      } catch (err) {
        console.error("❌ Error fetching Warehouse Types:", err);
      }
    }
    fetchWarehouseTypes();
  }, []);

  function toggleExpand(name) {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  }

  // 🔹 Open Add Child modal
  function handleAddChild(node) {
    setSelectedParent(node);
    setForm({ warehouse_name: "", warehouse_type: "", capacity: "", capacity_unit: "" });
    setIsEditing(false);
    setShowModal(true);
  }

  // 🔹 Open Edit modal
  function handleEdit(node) {
    setSelectedParent(node);
    setForm({
      warehouse_name: node.warehouse_name || "",
      warehouse_type: node.warehouse_type || "",
      capacity: node.capacity || "",
      capacity_unit: node.capacity_unit || "",
    });
    setIsEditing(true);
    setShowModal(true);
  }

  // 🔹 Submit (Add + Edit)
  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.warehouse_name) {
      frappe.msgprint("Warehouse Name is required");
      return;
    }

    try {
      if (isEditing) {
        await frappe.call({
          method: "frappe.client.set_value",
          args: {
            doctype: "Warehouse",
            name: selectedParent.name, // ✅ always use name
            fieldname: {
              warehouse_name: form.warehouse_name,
              warehouse_type: form.warehouse_type || "Stores",
              capacity: Number(form.capacity) || 0,
              capacity_unit: form.capacity_unit || "",
            },
          },
        });
        frappe.msgprint(`✅ Updated Warehouse: ${form.warehouse_name}`);
      } else {

        const res = await frappe.call({
          method: "frappe.client.insert",
          args: {
            doc: {
              doctype: "Warehouse",
              warehouse_name: form.warehouse_name,
              warehouse_type: form.warehouse_type || "Stores",
              parent_warehouse: selectedParent?.name,
              is_group: 0,
              capacity: Number(form.capacity) || 0,
              capacity_unit: form.capacity_unit || "",
            },
          },
        });
        frappe.msgprint(`✅ Created Warehouse: ${res.message.warehouse_name}`);

        // 🔹 ensure parent becomes group
        if (selectedParent && selectedParent.is_group === 0) {
          await frappe.call({
            method: "frappe.client.set_value",
            args: {
              doctype: "Warehouse",
              name: selectedParent.name,
              fieldname: { is_group: 1 },
            },
          });
        }

      }

      setShowModal(false);
      setIsEditing(false);
      await fetchWarehouses(); // refresh tree
    } catch (err) {
      console.error("❌ Save error:", err);
      frappe.msgprint("Error saving warehouse. Check console.");
    }
  }

  // 🔹 Handle delete
  async function handleDelete(node) {
    if (!node?.name) {
      frappe.msgprint("❌ Invalid warehouse selected for deletion");
      return;
    }

    try {
      await frappe.call({
        method: "frappe.client.delete",
        args: {
          doctype: "Warehouse",
          name: node.name, // ✅ always use name
        },
      });

      frappe.msgprint(`🗑 Deleted Warehouse: ${node.warehouse_name}`);
      setDeleteConfirm({ show: false, node: null });

      await fetchWarehouses();
    } catch (err) {
      console.error("❌ Delete error:", err);
      frappe.msgprint(err.message || "Error deleting warehouse. Check console.");
    }
  }

  // 🔹 Render node recursively
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
      position: "relative",
    };

    const nameContainerStyle = {
      display: "flex",
      alignItems: "center",
      flex: 1,
      paddingLeft: level * 16,
    };

    const caretStyle = {
      width: 30,
      height: 30,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      marginRight: 8,
      cursor: hasChildren ? "pointer" : "default",
      fontSize: 24,
      color: "#444",
      border: "none",
      background: "transparent"
    };

    const actionBtnStyle = {
      marginLeft: 8,
      fontSize: 12,
      padding: "2px 6px",
      cursor: "pointer",
      border: "1px solid #ccc",
      borderRadius: 4,
      background: "#f8f8f8",
    };

    return (
      <div key={node.name}>
        <div style={rowStyle}>
          <div style={nameContainerStyle}>
            {hasChildren ? (
              <button onClick={() => toggleExpand(node.name)} style={caretStyle}>
                {isExpanded ? "▾" : "▸"}
              </button>
            ) : (
              <span style={{ display: "inline-block", width: 18, marginRight: 8 }} />
            )}
            <div>
              <strong>{node.warehouse_name || node.name}</strong>
              <div style={{ fontSize: 12, color: "#888" }}>{node.name}</div>
              {(node.capacity || node.capacity_unit) && (
                <div style={{ fontSize: 12, color: "#555" }}>
                  Capacity: {node.capacity || "0"} {node.capacity_unit || ""}
                </div>
              )}
            </div>

          </div>
          <button style={actionBtnStyle} onClick={() => handleAddChild(node)}>
            ➕ Add Child
          </button>
          <button style={actionBtnStyle} onClick={() => handleEdit(node)}>
            ✏️ Edit
          </button>
          <button
            style={{ ...actionBtnStyle, color: node?.children?.length > 0 ? "grey" : "red", borderColor: node?.children?.length > 0 ? "grey" : "red" }}
            disabled={node.children && node.children.length > 0}
            onClick={() => setDeleteConfirm({ show: true, node })}
          >
            🗑 Delete
          </button>
        </div>

        {hasChildren && isExpanded && (
          <div>{node.children.map((c) => renderNode(c, level + 1))}</div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: 12 }}>
      <div
        style={{
          border: "1px solid #e6e6e6",
          borderRadius: 6,
          overflow: "auto",
          maxHeight: "60vh",
        }}
      >
        {loading ? (
          <div style={{ padding: 20 }}>Loading…</div>
        ) : error ? (
          <div style={{ padding: 20, color: "red" }}>Error loading warehouses</div>
        ) : tree.length === 0 ? (
          <div style={{ padding: 20 }}>No warehouses found.</div>
        ) : (
          tree.map((root) => renderNode(root))
        )}
      </div>

      {/* 🔹 Add/Edit Modal */}
      {showModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              background: "#fff",
              padding: 20,
              borderRadius: 8,
              width: 400,
              boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
            }}
          >
            <h3>
              {isEditing
                ? `Edit Warehouse ${selectedParent?.warehouse_name}`
                : `Add Child to ${selectedParent?.warehouse_name}`}
            </h3>
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: 10 }}>
                <label>Warehouse Name *</label>
                <input
                  type="text"
                  value={form.warehouse_name}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, warehouse_name: e.target.value }))
                  }
                  style={{ width: "100%", padding: 6, marginTop: 4 }}
                />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Warehouse Type</label>
                <select
                  value={form.warehouse_type}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, warehouse_type: e.target.value }))
                  }
                  style={{ width: "100%", padding: 6, marginTop: 4 }}
                >
                  <option value="">-- Select Type --</option>
                  {warehouseTypes.map((wt) => (
                    <option key={wt.name} value={wt.name}>
                      {wt.name}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Capacity</label>
                <input
                  type="number"
                  value={form.capacity}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, capacity: e.target.value }))
                  }
                  style={{ width: "100%", padding: 6, marginTop: 4 }}
                />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Capacity Unit</label>
                <input
                  type="text"
                  value={form.capacity_unit}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, capacity_unit: e.target.value }))
                  }
                  style={{ width: "100%", padding: 6, marginTop: 4 }}
                />
              </div>

              <div style={{ textAlign: "right" }}>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  style={{ marginRight: 8 }}
                >
                  Cancel
                </button>
                <button type="submit" style={{ background: "#1677ff", color: "#fff" }}>
                  {isEditing ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 🔹 Delete Confirmation Modal */}
      {deleteConfirm.show && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              background: "#fff",
              padding: 20,
              borderRadius: 8,
              width: 300,
              textAlign: "center",
              boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
            }}
          >
            <p>
              Are you sure you want to delete{" "}
              <strong>{deleteConfirm.node?.warehouse_name}</strong>?
            </p>
            <div style={{ marginTop: 20 }}>
              <button
                onClick={() => setDeleteConfirm({ show: false, node: null })}
                style={{ marginRight: 8 }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm.node)}
                style={{ background: "red", color: "#fff" }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
