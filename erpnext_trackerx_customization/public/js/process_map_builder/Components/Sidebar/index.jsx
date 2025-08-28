import React from "react";

const Sidebar = ({
  operationProcesses,
  processGroups,
  streams,
  processMaps,
  handleSaveMap,
  handleLoadMap,
}) => {
  return (
    <div className="col-3 border-end bg-light p-3 overflow-auto">
      <h5>Processes</h5>
      {operationProcesses.map((op) => (
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
              })
            )
          }
          style={{ cursor: "grab" }}
        >
          {op.process_name}
        </div>
      ))}

      <hr />
      <h5>Process Groups</h5>
      {processGroups.map((pg) => {
        const relatedProcesses = operationProcesses
          .filter((op) => op.process_group === pg.name)
          .map((op) => op.process_name);

        return (
          <div
            key={pg.name}
            className="border rounded p-2 mb-2 bg-warning text-dark text-center shadow-sm"
            draggable
            onDragStart={(e) =>
              e.dataTransfer.setData(
                "application/reactflow",
                JSON.stringify({
                  type: "process_group",
                  label: pg.group_name,
                  addData: relatedProcesses,
                })
              )
            }
            style={{ cursor: "grab" }}
          >
            {pg.group_name}
          </div>
        );
      })}

      <hr />
      <h5>Streams</h5>
      {streams.map((stream) => (
        <div
          key={stream.name}
          className="border rounded p-2 mb-2 bg-info text-white text-center shadow-sm"
          draggable
          onDragStart={(e) =>
            e.dataTransfer.setData(
              "application/reactflow",
              JSON.stringify({
                type: "stream",
                label: stream.stream_name,
              })
            )
          }
          style={{ cursor: "grab" }}
        >
          {stream.stream_name}
        </div>
      ))}

      <hr />
      <button onClick={handleSaveMap} className="btn btn-success w-100 mt-4">
        Save Process Map
      </button>

      <hr />
      <h5>Saved Maps</h5>
      {processMaps.length > 0 ? (
        processMaps.map((map) => (
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
        <p className="text-muted">No maps saved yet</p>
      )}
    </div>
  );
};

export default Sidebar;
