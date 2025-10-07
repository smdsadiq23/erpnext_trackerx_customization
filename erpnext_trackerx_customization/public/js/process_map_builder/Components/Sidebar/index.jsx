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
        <h5>Processes</h5>

        {/* Operation Group Filter */}
        <select
          style={{
            backgroundColor: "white",
            borderRight: "0",
          }}
          className="form-select mb-3"
          value={selectedOperationGroup}
          onChange={(e) => setSelectedOperationGroup(e.target.value)}
        >
          <option value="">-- All Operation Groups --</option>
          {(operationGroups || []).map((group) => (
            <option key={group.name} value={group.name}>
              {group.group_name}
            </option>
          ))}
        </select>

        {/* Process Search Input */}
        <input
          style={{
            backgroundColor: "white",
            borderRight: "0",
          }}
          type="text"
          className="form-control mb-3"
          placeholder="Search process"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        {/* Processes List */}
        {filteredProcesses.length > 0 ? (
          filteredProcesses.map((op) => (
            <div
              key={op.name}
              className="border rounded p-2 mb-2 bg-white text-center shadow-sm"
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
              style={{ cursor: "grab" }}
            >
              {op.process_name}
            </div>
          ))
        ) : (
          <p className="text-muted text-center">No processes found</p>
        )}
      </div>

      <hr />

      <button onClick={handleSaveMap} className="btn btn-success w-100 mt-4">
        Save Process Map
      </button>

      <hr />
      <h5>Saved Maps</h5>

      {/* Saved Maps Search Input */}
      <input
        style={{
          backgroundColor: "white",
          borderRight: "0",
          marginBottom: "10px",
        }}
        type="text"
        className="form-control"
        placeholder="Search saved map"
        value={mapSearchTerm}
        onChange={(e) => setMapSearchTerm(e.target.value)}
      />

      {/* Saved Maps List */}
      {filteredMaps.length > 0 ? (
        filteredMaps.map((map) => (
          <div
            key={map.name}
            className="border rounded p-2 mb-2 bg-secondary text-white text-center shadow-sm"
            style={{ cursor: "pointer" }}
            onClick={() => handleLoadMap(map.name)}
          >
            {map.map_name}
          </div>
        ))
      ) : (
        <p className="text-muted">No maps found</p>
      )}
    </div>
  );
};

export default Sidebar;
