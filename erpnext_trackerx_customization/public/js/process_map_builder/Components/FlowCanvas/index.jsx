// FlowCanvas_Final.js
import React, { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  useReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  Background,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { Modal, Button, Form } from "react-bootstrap";

import ProcessGroupNode from "../ProcessGroupNode";
import OperationProcessNode from "../OperationProcessNode";
import { blendColors, COMPONENT_COLORS } from "../../util";
import Sidebar from "../Sidebar";

let idCounter = 0;
const getId = (prefix = "node") => {
  idCounter++;
  return `${prefix}_${Date.now()}_${idCounter}`;
};

const nodeTypes = {
  process_group: ProcessGroupNode,
  operationProcess: OperationProcessNode,
};

const FlowCanvas = ({
  operationProcesses,
  processMaps,
  operationGroups,
  defaultComponents,
  processMapNumber,
  selectedItem,
  description,
  processMapName,
  initialNodes = [],
  initialEdges = [],
  isEditMode,
  setIsEditMode,
}) => {
  const { screenToFlowPosition } = useReactFlow();

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [edgeComponents, setEdgeComponents] = useState({});
  const [newEdgeParams, setNewEdgeParams] = useState(null);
  const [selectedComponents, setSelectedComponents] = useState([]);
  const [showNodeModal, setShowNodeModal] = useState(false);
  const [showEdgeModal, setShowEdgeModal] = useState(false);
  const [targetNode, setTargetNode] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);
  const [csrfToken, setCsrfToken] = useState("");

  // Grab CSRF token
  useEffect(() => {
    if (window.frappe?.csrf_token) {
      setCsrfToken(window.frappe.csrf_token);
    } else {
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) setCsrfToken(metaTag.getAttribute("content"));
      else console.warn("CSRF token not found");
    }
  }, []);

  // --- IMPORTANT: initialize node data and edgeComponents when FlowCanvas mounts with initialNodes/initialEdges ---
  // 1) Ensure every node has initialComponents & usedComponents
  useEffect(() => {
    if (!initialNodes || initialNodes.length === 0) return;

    setNodes((current) =>
      current.map((n) => ({
        ...n,
        data: {
          // preserve existing data, but ensure these arrays exist
          ...(n.data || {}),
          initialComponents:
            (n.data && n.data.initialComponents && [...n.data.initialComponents]) ||
            (defaultComponents ? [...defaultComponents] : []),
          usedComponents: (n.data && n.data.usedComponents && [...n.data.usedComponents]) || [],
        },
      }))
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialNodes, defaultComponents, setNodes]);

  // 2) Rebuild edgeComponents from initialEdges so component-tracking works on direct URL loads
  useEffect(() => {
    if (!initialEdges || initialEdges.length === 0) return;

    const rebuilt = {};
    initialEdges.forEach((e) => {
      // edge may have components in e.data.components or e.components (depending on saved shape)
      rebuilt[e.id] = (e.data && e.data.components) || e.components || [];
    });
    setEdgeComponents(rebuilt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialEdges, setEdgeComponents]);

  // --- Utility to check available components ---
  const getAvailableComponentsFromSource = (sourceNodeId) => {
    if (!sourceNodeId) return [];

    const outgoingEdges = edges.filter((e) => e.source === sourceNodeId);
    const alreadyUsed = outgoingEdges.flatMap((e) => edgeComponents[e.id] || []);

    const incomingEdges = edges.filter((e) => e.target === sourceNodeId);
    let inherited;

    if (incomingEdges.length === 0) {
      inherited = defaultComponents || [];
    } else {
      inherited = incomingEdges.flatMap((e) => edgeComponents[e.id] || []);
    }

    if (!inherited || inherited.length === 0) {
      inherited = defaultComponents || [];
    }

    return inherited.filter((c) => !alreadyUsed.includes(c));
  };

  // --- Handle edge creation ---
  const onConnect = useCallback(
    (params) => {
      const availableComponents = getAvailableComponentsFromSource(params.source);

      if (availableComponents.length === 1) {
        // auto edge
        const component = availableComponents[0];
        const componentColor = COMPONENT_COLORS[component] || "#999999";
        const newEdge = {
          ...params,
          id: `${params.source}-${params.target}-${Date.now()}`,
          label: component,
          style: { stroke: componentColor, strokeWidth: 2 },
          data: { components: [component] },
        };
        setEdges((eds) => addEdge(newEdge, eds));
        setEdgeComponents((prev) => ({ ...prev, [newEdge.id]: [component] }));

        // mark component used on source node
        setNodes((nds) =>
          nds.map((n) =>
            n.id === params.source
              ? {
                ...n,
                data: {
                  ...n.data,
                  usedComponents: [...(n.data.usedComponents || []), component],
                  initialComponents: n.data?.initialComponents || defaultComponents || [],
                },
              }
              : n
          )
        );
      } else if (availableComponents.length > 1) {
        setNewEdgeParams(params);
        setSelectedComponents([]);
        setShowEdgeModal(true);
      }
      // if none available, we do nothing (no components to flow)
    },
    [edges, edgeComponents, setEdges, setEdgeComponents, setNodes, defaultComponents]
  );

  // --- Handle node drop ---
  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const payload = JSON.parse(event.dataTransfer.getData("application/reactflow"));
      console.log("payload", payload);
      
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });

      const newNodeId = getId("process");
      const newNode = {
        id: newNodeId,
        data: {
          label: payload.label,
          width: 320,
          height: 200,
          addData: payload?.addData,
          quantity: "",
          initialComponents: defaultComponents ? [...defaultComponents] : [],
          usedComponents: [],
          onValueChange: (val) => {
            setNodes((nds) =>
              nds.map((node) =>
                node.id === newNodeId ? { ...node, data: { ...node.data, quantity: val } } : node
              )
            );
          },
        },
        position,
        type: "operationProcess",
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes, defaultComponents]
  );

  const onDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  // --- Context menus ---
  const onNodeContextMenu = (event, node) => {
    event.preventDefault();
    setTargetNode(node);
    setShowNodeModal(true);
  };

  const onEdgeContextMenu = (event, edge) => {
    event.preventDefault();
    setSelectedEdgeId(edge.id);
    setSelectedComponents(edgeComponents[edge.id] || []);
    setShowEdgeModal(true);
  };

  // --- Node + Edge delete ---
  const handleDeleteNode = () => {
    if (!targetNode) return;
    const getAllChildren = (parentId) => {
      const children = nodes.filter((n) => n.parentId === parentId);
      let all = [...children];
      for (let c of children) all = [...all, ...getAllChildren(c.id)];
      return all;
    };
    const deleteIds = [targetNode.id, ...getAllChildren(targetNode.id).map((n) => n.id)];
    setNodes((nds) => nds.filter((n) => !deleteIds.includes(n.id)));
    setEdges((eds) =>
      eds.filter((e) => !deleteIds.includes(e.source) && !deleteIds.includes(e.target))
    );
    setShowNodeModal(false);
  };

  const handleDeleteEdge = () => {
    if (selectedEdgeId) setEdges((eds) => eds.filter((e) => e.id !== selectedEdgeId));
    setShowEdgeModal(false);
  };

  // --- Confirm edge ---
  const handleConfirmEdge = () => {
    if ((newEdgeParams || selectedEdgeId) && selectedComponents.length > 0) {
      const componentColors = selectedComponents.map((c) => COMPONENT_COLORS[c] || "#999999");
      const edgeColor = componentColors.length === 1 ? componentColors[0] : blendColors(componentColors);

      const edgeId = newEdgeParams ? `${newEdgeParams.source}-${newEdgeParams.target}-${Date.now()}` : selectedEdgeId;
      const edgeData = newEdgeParams || edges.find((e) => e.id === selectedEdgeId);

      const updatedEdge = {
        ...edgeData,
        id: edgeId,
        label: selectedComponents.join(", "),
        style: { stroke: edgeColor, strokeWidth: 2 },
        data: { components: selectedComponents },
      };

      setEdges((eds) => {
        if (newEdgeParams) return addEdge(updatedEdge, eds);
        return eds.map((e) => (e.id === selectedEdgeId ? updatedEdge : e));
      });

      setEdgeComponents((prev) => ({ ...prev, [edgeId]: selectedComponents }));

      // Track used components on source node (avoid duplicates)
      const sourceId = newEdgeParams ? newEdgeParams.source : edgeData.source;
      setNodes((nds) =>
        nds.map((n) =>
          n.id === sourceId
            ? {
              ...n,
              data: {
                ...n.data,
                usedComponents: [
                  ...(n.data.usedComponents || []),
                  ...selectedComponents.filter((c) => !(n.data.usedComponents || []).includes(c)),
                ],
              },
            }
            : n
        )
      );
    }

    setShowEdgeModal(false);
    setSelectedComponents([]);
    setNewEdgeParams(null);
    setSelectedEdgeId(null);
  };

  const BASE_URL = `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ""}`;

  // --- Save map ---
  const handleSaveMap = async () => {
    if (!processMapName || !processMapNumber || !selectedItem) {
      return alert("Process Map Name, Number, and FG Item are required.");
    }

    const nodePayload = nodes.map((node) => ({
      id: node.id,
      type: node.type,
      label: node.data?.label || "",
      position: node.position,
      data: {
        process_group: node.data?.process_group || null,
        stream: node.data?.stream || null,
        quantity: node.data?.quantity || null,
        initialComponents: node.data?.initialComponents || [],
        usedComponents: node.data?.usedComponents || [],
      },
    }));

    const edgePayload = edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label || null,
      components: edgeComponents[edge.id] || [],
      style: edge.style,
    }));

    const payload = {
      map_name: processMapName,
      nodes: JSON.stringify(nodePayload),
      edges: JSON.stringify(edgePayload),
      description,
      process_map_number: processMapNumber,
      select_fg: selectedItem,
    };

    try {
      const response = await fetch(`${BASE_URL}/api/method/erpnext_trackerx_customization.api.process_map.save_process_map`, {
        method: isEditMode ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Frappe-CSRF-Token": csrfToken,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (response.ok) alert(`✅ Process map saved successfully! Doc: ${data.message.docname}`);
      else alert(`❌ Failed to save map: ${data.message}`);
    } catch (error) {
      console.error("❌ API error:", error);
      alert("❌ Error saving map. See console for details.");
    }
  };

  // --- Load map (manual via sidebar) ---
  const handleLoadMap = async (mapName) => {
    try {
      const res = await fetch(`${BASE_URL}/api/resource/Process Map/${mapName}?fields=["*"]`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
      const result = await res.json();
      const mapData = result.data;

      const parsedNodes = JSON.parse(mapData.nodes || "[]").map((node) => ({
        ...node,
        data: {
          ...node.data,
          label: node.label || node.data?.label || "",
          initialComponents: node.data?.initialComponents || defaultComponents,
          usedComponents: node.data?.usedComponents || [],
        },
      }));

      const parsedEdges = JSON.parse(mapData.edges || "[]").map((edge) => ({
        ...edge,
        data: { components: edge.components || [] },
        style: {
          stroke: edge.style?.stroke || "#999",
          strokeWidth: edge.style?.strokeWidth || 2,
        },
      }));

      setNodes(parsedNodes);
      setEdges(parsedEdges);

      // Rebuild edgeComponents
      const rebuiltEdgeComponents = {};
      parsedEdges.forEach((e) => {
        rebuiltEdgeComponents[e.id] = e.data?.components || [];
      });
      setEdgeComponents(rebuiltEdgeComponents);

      setIsEditMode(true);
      alert(`✅ Loaded process map: ${mapData.map_name}`);
    } catch (err) {
      console.error("❌ Error loading map:", err);
      alert("❌ Failed to load map.");
    }
  };

  return (
    <div className="container-fluid" style={{ height: "100vh" }}>
      <div className="row h-100">
        <Sidebar
          operationProcesses={operationProcesses}
          processMaps={processMaps}
          operationGroups={operationGroups}
          handleSaveMap={handleSaveMap}
          handleLoadMap={handleLoadMap}
        />
        <div className="col-9 p-0">
          <ReactFlow
            nodeTypes={nodeTypes}
            nodes={nodes}
            edges={edges}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeContextMenu={onNodeContextMenu}
            onEdgeContextMenu={onEdgeContextMenu}
            fitView
          >
            <Background />
          </ReactFlow>
        </div>
      </div>

      {/* --- Edge Modal --- */}
      <Modal show={showEdgeModal} onHide={() => setShowEdgeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Select Components</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group controlId="formComponents">
            <Form.Label>Select components flowing in this connection:</Form.Label>
            <div>
              <Form.Control
                as="select"
                multiple
                value={selectedComponents}
                onChange={(e) => setSelectedComponents(Array.from(e.target.selectedOptions, (opt) => opt.value))}
              >
                {getAvailableComponentsFromSource(
                  newEdgeParams ? newEdgeParams.source : edges.find((e) => e.id === selectedEdgeId)?.source
                ).map((component) => (
                  <option key={component} value={component}>
                    {component}
                  </option>
                ))}
              </Form.Control>
            </div>

          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEdgeModal(false)}>Cancel</Button>
          <Button variant="primary" onClick={handleConfirmEdge}>Confirm</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default FlowCanvas;
