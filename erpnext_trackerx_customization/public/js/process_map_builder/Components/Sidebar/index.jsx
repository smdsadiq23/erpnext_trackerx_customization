import React, { useState } from "react";

const Sidebar = ({
  operationProcesses,
  processMaps,
  operationGroups,
  handleSaveMap,
  handleLoadMap,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [mapSearchTerm, setMapSearchTerm] = useState("");
  const [selectedOperationGroup, setSelectedOperationGroup] = useState(""); // new state for operation group filter

  // Filter processes by operation group and search term (case insensitive)
  const filteredProcesses = (operationProcesses || []).filter((op) => {
    // First filter by operation group if selected
    const groupFilter = selectedOperationGroup === "" || op.custom_operation_group === selectedOperationGroup;
    // Then filter by search term
    const searchFilter = op.process_name?.toLowerCase().includes(searchTerm.toLowerCase());
    return groupFilter && searchFilter;
  });

  // Get operation counts per group
  const getOperationCountForGroup = (groupName) => {
    if (!groupName) {
      return (operationProcesses || []).length;
    }
    return (operationProcesses || []).filter(op => op.custom_operation_group === groupName).length;
  };

  // Clear all filters
  const clearFilters = () => {
    setSelectedOperationGroup("");
    setSearchTerm("");
  };

  // Filter saved maps by search term (case insensitive)
  const filteredMaps = (processMaps || []).filter((map) =>
    map.map_name?.toLowerCase().includes(mapSearchTerm.toLowerCase())
  );

  return (
    <div className="col-3 border-end bg-light p-3 overflow-auto">
      <div
        style={{
          maxHeight: "300px",
          overflowY: "auto",
          padding: "6px",
        }}
      >
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="mb-0">Processes</h5>
          {(selectedOperationGroup || searchTerm) && (
            <button
              onClick={clearFilters}
              className="btn btn-sm btn-outline-secondary"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
              title="Clear all filters"
            >
              ✕ Clear
            </button>
          )}
        </div>

        {/* Operation Group Filter */}
        <div className="mb-3">
          <label className="form-label text-muted small fw-semibold mb-2">
            📂 Filter by Operation Group
          </label>
          <select
            style={{
              backgroundColor: "#f8f9fa",
              border: "2px solid #e9ecef",
              borderRadius: "8px",
              padding: "0.5rem 0.75rem",
              fontSize: "0.9rem",
              transition: "all 0.2s ease-in-out",
            }}
            className="form-select"
            value={selectedOperationGroup}
            onChange={(e) => setSelectedOperationGroup(e.target.value)}
            onFocus={(e) => {
              e.target.style.borderColor = "#0d6efd";
              e.target.style.backgroundColor = "white";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "#e9ecef";
              e.target.style.backgroundColor = "#f8f9fa";
            }}
          >
            <option value="">
              All Groups ({getOperationCountForGroup("")} operations)
            </option>
            {(operationGroups || []).map((group) => (
              <option key={group.name} value={group.name}>
                {group.group_name} ({getOperationCountForGroup(group.name)} operations)
              </option>
            ))}
          </select>
        </div>

        {/* Process Search Input */}
        <div className="mb-3">
          <label className="form-label text-muted small fw-semibold mb-2">
            🔍 Search Operations
          </label>
          <div className="position-relative">
            <input
              style={{
                backgroundColor: "#f8f9fa",
                border: "2px solid #e9ecef",
                borderRadius: "8px",
                padding: "0.5rem 2.5rem 0.5rem 0.75rem",
                fontSize: "0.9rem",
                transition: "all 0.2s ease-in-out",
              }}
              type="text"
              className="form-control"
              placeholder="Type to search operations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onFocus={(e) => {
                e.target.style.borderColor = "#0d6efd";
                e.target.style.backgroundColor = "white";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "#e9ecef";
                e.target.style.backgroundColor = "#f8f9fa";
              }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm("")}
                className="btn btn-sm position-absolute"
                style={{
                  right: "0.5rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  border: "none",
                  background: "none",
                  color: "#6c757d",
                  fontSize: "0.9rem",
                  padding: "0.25rem",
                }}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Results Counter */}
        <div className="mb-3">
          <small className="text-muted d-flex justify-content-between align-items-center">
            <span>
              Showing {filteredProcesses.length} operation{filteredProcesses.length !== 1 ? 's' : ''}
              {selectedOperationGroup && (
                <span className="badge bg-primary ms-2" style={{ fontSize: "0.7rem" }}>
                  {operationGroups.find(g => g.name === selectedOperationGroup)?.group_name}
                </span>
              )}
            </span>
            {searchTerm && (
              <span className="badge bg-info" style={{ fontSize: "0.7rem" }}>
                Searching: "{searchTerm}"
              </span>
            )}
          </small>
        </div>

        {/* Processes List */}
        {filteredProcesses.length > 0 ? (
          filteredProcesses.map((op) => (
            <div
              key={op.name}
              className="border rounded p-3 mb-2 bg-white text-center shadow-sm"
              draggable
              onDragStart={(e) =>
                e.dataTransfer.setData(
                  "application/reactflow",
                  JSON.stringify({
                    type: "process",
                    label: op.process_name,
                    item_code: op.item_code,
                    addData: op,
                  })
                )
              }
              style={{
                cursor: "grab",
                borderRadius: "8px",
                border: "2px solid #e9ecef",
                transition: "all 0.2s ease-in-out",
                backgroundImage: "linear-gradient(45deg, #f8f9fa 0%, #ffffff 100%)",
              }}
              onMouseEnter={(e) => {
                e.target.style.borderColor = "#0d6efd";
                e.target.style.transform = "translateY(-2px)";
                e.target.style.boxShadow = "0 4px 12px rgba(13, 110, 253, 0.15)";
              }}
              onMouseLeave={(e) => {
                e.target.style.borderColor = "#e9ecef";
                e.target.style.transform = "translateY(0)";
                e.target.style.boxShadow = "0 1px 3px rgba(0, 0, 0, 0.1)";
              }}
            >
              <div className="fw-semibold text-dark" style={{ fontSize: "0.9rem" }}>
                {op.process_name}
              </div>
              {op.custom_operation_group && (
                <div className="mt-1">
                  <small className="badge bg-light text-muted" style={{ fontSize: "0.7rem" }}>
                    {operationGroups.find(g => g.name === op.custom_operation_group)?.group_name || op.custom_operation_group}
                  </small>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-4">
            <div className="text-muted">
              <div style={{ fontSize: "2rem", opacity: 0.5 }}>🔍</div>
              <p className="mb-0 mt-2">No operations found</p>
              {(selectedOperationGroup || searchTerm) && (
                <small className="text-secondary">
                  Try adjusting your filters
                </small>
              )}
            </div>
          </div>
        )}
      </div>

      <hr />

      <button onClick={handleSaveMap} className="btn btn-success w-100 mt-4">
        Save Process Map
      </button>

      <hr className="my-4" />

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="mb-0">Saved Maps</h5>
        {mapSearchTerm && (
          <button
            onClick={() => setMapSearchTerm("")}
            className="btn btn-sm btn-outline-secondary"
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            title="Clear map search"
          >
            ✕ Clear
          </button>
        )}
      </div>

      {/* Saved Maps Search Input */}
      <div className="mb-3">
        <label className="form-label text-muted small fw-semibold mb-2">
          🗺️ Search Saved Maps
        </label>
        <div className="position-relative">
          <input
            style={{
              backgroundColor: "#f8f9fa",
              border: "2px solid #e9ecef",
              borderRadius: "8px",
              padding: "0.5rem 2.5rem 0.5rem 0.75rem",
              fontSize: "0.9rem",
              transition: "all 0.2s ease-in-out",
            }}
            type="text"
            className="form-control"
            placeholder="Type to search maps..."
            value={mapSearchTerm}
            onChange={(e) => setMapSearchTerm(e.target.value)}
            onFocus={(e) => {
              e.target.style.borderColor = "#0d6efd";
              e.target.style.backgroundColor = "white";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "#e9ecef";
              e.target.style.backgroundColor = "#f8f9fa";
            }}
          />
          {mapSearchTerm && (
            <button
              onClick={() => setMapSearchTerm("")}
              className="btn btn-sm position-absolute"
              style={{
                right: "0.5rem",
                top: "50%",
                transform: "translateY(-50%)",
                border: "none",
                background: "none",
                color: "#6c757d",
                fontSize: "0.9rem",
                padding: "0.25rem",
              }}
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Maps Counter */}
      <div className="mb-3">
        <small className="text-muted">
          Showing {filteredMaps.length} map{filteredMaps.length !== 1 ? 's' : ''}
          {mapSearchTerm && (
            <span className="badge bg-info ms-2" style={{ fontSize: "0.7rem" }}>
              Searching: "{mapSearchTerm}"
            </span>
          )}
        </small>
      </div>

      {/* Saved Maps List */}
      {filteredMaps.length > 0 ? (
        filteredMaps.map((map) => (
          <div
            key={map.name}
            className="border rounded p-3 mb-2 bg-white text-center shadow-sm"
            style={{
              cursor: "pointer",
              borderRadius: "8px",
              border: "2px solid #e9ecef",
              transition: "all 0.2s ease-in-out",
              backgroundImage: "linear-gradient(45deg, #e3f2fd 0%, #ffffff 100%)",
            }}
            onClick={() => handleLoadMap(map.name)}
            onMouseEnter={(e) => {
              e.target.style.borderColor = "#2196f3";
              e.target.style.transform = "translateY(-2px)";
              e.target.style.boxShadow = "0 4px 12px rgba(33, 150, 243, 0.15)";
            }}
            onMouseLeave={(e) => {
              e.target.style.borderColor = "#e9ecef";
              e.target.style.transform = "translateY(0)";
              e.target.style.boxShadow = "0 1px 3px rgba(0, 0, 0, 0.1)";
            }}
          >
            <div className="fw-semibold text-dark" style={{ fontSize: "0.9rem" }}>
              {map.map_name}
            </div>
            <small className="text-muted mt-1 d-block">
              📅 {new Date(map.modified).toLocaleDateString()}
            </small>
          </div>
        ))
      ) : (
        <div className="text-center py-4">
          <div className="text-muted">
            <div style={{ fontSize: "2rem", opacity: 0.5 }}>🗺️</div>
            <p className="mb-0 mt-2">No saved maps found</p>
            {mapSearchTerm && (
              <small className="text-secondary">
                Try adjusting your search
              </small>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
