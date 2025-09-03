import React from "react";
import { Handle, Position } from "@xyflow/react";

 const ProcessGroupNode = ({ data }) => {
  return (
    <div style={{ padding: '10px' }}>
      <strong>{data.label}</strong>
      <ul style={{ paddingLeft: '16px', marginTop: '8px', marginBottom: 0 }}>
        {Array.isArray(data.addData) &&
          data.addData.map((item, idx) => (
            <li key={idx} style={{ fontSize: '13px', lineHeight: '1.4' }}>
              {item}
            </li>
          ))}
      </ul>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};


export default ProcessGroupNode