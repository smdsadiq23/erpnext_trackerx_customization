import React from "react";
import { Handle, Position } from "@xyflow/react";

const OperationProcessNode = ({ data }) => {
  const handleChange = (e) => {
    const value = e.target.value;
    data.onValueChange && data.onValueChange(value);
  };

  return (
    <div
      style={{
        padding: "10px",
        border: "1px solid #999",
        borderRadius: "5px",
        background: "#fff",
      }}
    >
      <strong>{data.label}</strong>
      <input
        type="number"
        value={data.quantity || ""}
        onChange={handleChange}
        style={{
          width: "50px",
          marginLeft: "8px",
          fontSize: "12px",
          padding: "2px",
        }}
      />
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default OperationProcessNode;
