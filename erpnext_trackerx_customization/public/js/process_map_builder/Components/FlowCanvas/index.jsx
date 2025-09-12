import React, { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  useReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  Background
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Modal, Button, Form } from 'react-bootstrap';

import ProcessGroupNode from '../ProcessGroupNode';
import OperationProcessNode from '../OperationProcessNode';
import { blendColors, COMPONENT_COLORS } from '../../util';
import Sidebar from '../Sidebar';

let id = 0;
const getId = () => `node_${id++}`;

const nodeTypes = {
  process_group: ProcessGroupNode,
  operationProcess: OperationProcessNode,
};

const FlowCanvas = ({ operationProcesses, processGroups, streams, processMaps, defaultComponents, processMapNumber, selectedItem, description, processMapName }) => {
  const { screenToFlowPosition } = useReactFlow();
  // const defaultComponents = ['Front', 'Back', 'Sleeve'];
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [edgeComponents, setEdgeComponents] = useState({});
  const [newEdgeParams, setNewEdgeParams] = useState(null);
  const [selectedComponents, setSelectedComponents] = useState([]);
  const [showNodeModal, setShowNodeModal] = useState(false);
  const [showEdgeModal, setShowEdgeModal] = useState(false);
  const [targetNode, setTargetNode] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);
  const [csrfToken, setCsrfToken] = useState('');



  useEffect(() => {
    // Try frappe.csrf_token first
    if (window.frappe && window.frappe.csrf_token) {
      setCsrfToken(window.frappe.csrf_token);
    } else {
      // Fallback: Extract from meta tag
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) {
        setCsrfToken(metaTag.getAttribute('content'));
      } else {
        console.warn('CSRF token not found in meta tag or frappe object');
      }
    }
  }, []);

  const getAvailableComponentsFromSource = (sourceNodeId) => {
    const outgoingEdges = edges.filter(e => e.source === sourceNodeId);
    const alreadyUsed = outgoingEdges.flatMap(e => edgeComponents[e.id] || []);
    const incomingEdges = edges.filter(e => e.target === sourceNodeId);
    const inherited = incomingEdges.length === 0
      ? defaultComponents
      : incomingEdges.flatMap(e => edgeComponents[e.id] || []);
    return inherited.filter(c => !alreadyUsed.includes(c));
  };

  const onConnect = useCallback((params) => {
    const availableComponents = getAvailableComponentsFromSource(params.source);

    if (availableComponents.length === 1) {
      // Automatically create edge with the single component
      const component = availableComponents[0];
      const componentColor = COMPONENT_COLORS[component] || '#999999';
      const newEdge = {
        ...params,
        id: `${params.source}-${params.target}`,
        label: component,
        style: { stroke: componentColor, strokeWidth: 2 },
      };
      setEdges((eds) => addEdge(newEdge, eds));
      setEdgeComponents((prev) => ({
        ...prev,
        [newEdge.id]: [component],
      }));
    } else if (availableComponents.length > 1) {
      // Show modal for multiple components
      setNewEdgeParams(params);
      setSelectedComponents([]); // Reset selected components
      setShowEdgeModal(true);
    }
    // If no components are available, do nothing (edge creation is blocked)
  }, [edges, edgeComponents, setEdges, setEdgeComponents]);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const payload = JSON.parse(event.dataTransfer.getData('application/reactflow'));
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });

      const findParent = (pos) => {
        let parent = null;
        for (const node of nodes) {
          const width = node.data.width || 350;
          const height = node.data.height || 250;
          const within =
            pos.x >= node.position.x &&
            pos.x <= node.position.x + width &&
            pos.y >= node.position.y &&
            pos.y <= node.position.y + height;
          if (within) parent = node;
        }
        return parent;
      };

      const outerParent = findParent(position);
      const isStream = outerParent?.type === 'group';
      const isProcessGroup = outerParent?.type === 'process_group';

      const newNodeId = getId();
      const newNode = {
        id: newNodeId,
        data: {
          label: payload.label,
          width: 320,
          height: 200,
          addData: payload?.addData,
          quantity: '',
          onValueChange: (val) => {
            setNodes((nds) =>
              nds.map((node) =>
                node.id === newNodeId
                  ? { ...node, data: { ...node.data, quantity: val } }
                  : node
              )
            );
          }
        },
        position:
          outerParent && (isStream || isProcessGroup)
            ? {
              x: 20,
              y:
                nodes
                  .filter((n) => n.parentId === outerParent.id)
                  .reduce((acc, n) => acc + 80, 20),
            }
            : position,
        ...(outerParent ? { parentId: outerParent.id, extent: 'parent' } : {}),
        ...(payload.type === 'stream'
          ? { type: 'group', style: { border: '2px dashed #0d6efd', backgroundColor: '#e7f1ff' } }
          : payload.type === 'process_group'
            ? { type: 'process_group', style: { border: '2px dashed orange', backgroundColor: '#fff6e5' } }
            : { type: 'operationProcess' }),
      };

      setNodes((nds) => nds.concat(newNode));

      if (outerParent) {
        const childCount = nodes.filter((n) => n.parentId === outerParent.id).length + 1;
        const newHeight = Math.max(250, childCount * 90);
        setNodes((nds) =>
          nds.map((n) =>
            n.id === outerParent.id
              ? {
                ...n,
                data: { ...n.data, height: newHeight },
              }
              : n
          )
        );
      }
    },
    [nodes, screenToFlowPosition, setNodes]
  );

  const onDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  };

  const onNodeContextMenu = (event, node) => {
    event.preventDefault();
    setTargetNode(node);
    setShowNodeModal(true);
  };

  const onEdgeContextMenu = useCallback((event, edge) => {
    event.preventDefault();
    setSelectedEdgeId(edge.id);
    setShowEdgeModal(true);
  }, []);

  const handleDeleteNode = () => {
    if (!targetNode) return;
    const getAllChildren = (parentId) => {
      const children = nodes.filter((n) => n.parentId === parentId);
      let all = [...children];
      for (let c of children) {
        all = [...all, ...getAllChildren(c.id)];
      }
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
    if (selectedEdgeId) {
      setEdges((eds) => eds.filter((e) => e.id !== selectedEdgeId));
    }
    setShowEdgeModal(false);
  };

  const handleConfirmEdge = () => {
    if (newEdgeParams && selectedComponents.length > 0) {
      const componentColors = selectedComponents.map(
        (comp) => COMPONENT_COLORS[comp] || '#999999'
      );
      const edgeColor =
        componentColors.length === 1
          ? componentColors[0]
          : blendColors(componentColors);
      const newEdge = {
        ...newEdgeParams,
        id: `${newEdgeParams.source}-${newEdgeParams.target}`,
        label: selectedComponents.join(', '),
        style: { stroke: edgeColor, strokeWidth: 2 },
      };
      setEdges((eds) => addEdge(newEdge, eds));
      setEdgeComponents((prev) => ({
        ...prev,
        [newEdge.id]: selectedComponents,
      }));
    }
    setShowEdgeModal(false);
    setSelectedComponents([]);
    setNewEdgeParams(null);
  };

  // const API_TOKEN = 'f15ebc3b84401d2:9cddcb70db531d1';
  const BASE_URL = `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ''}`;;

  const handleSaveMap = async () => {
    // const map_name = prompt("Enter a name for this Process Map:");
    // if (!map_name) return alert("Map name is required to save.");

    if (!processMapName || !processMapNumber || !selectedItem) {
      return alert("Process Map Name, Number, and FG Item are required.");
    }

    const nodePayload = nodes.map((node) => ({
      id: node.id,
      type: node.type,
      label: node.data?.label || '',
      position: node.position,
      data: {
        process_group: node.data?.process_group || null,
        stream: node.data?.stream || null,
        quantity: node.data?.quantity || null
      }
    }));

    const edgePayload = edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label || null,
      components: edgeComponents[edge.id] || [],
      style: edge.style
    }));
    console.log("payload", nodePayload, edgePayload);

    const payload = {
      map_name: processMapName,
      nodes: JSON.stringify(nodePayload),
      edges: JSON.stringify(edgePayload),
      description,
      process_map_number: processMapNumber, // from textbox
      select_fg: selectedItem,
    };

    try {
      const response = await fetch(`${BASE_URL}/api/method/erpnext_trackerx_customization.api.process_map.save_process_map`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-Frappe-CSRF-Token': csrfToken,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        console.log("✅ Map saved:", data);
        alert(`✅ Process map saved successfully! Doc: ${data.message.docname}`);
      } else {
        console.error("❌ Failed to save map:", data);
        alert(`❌ Failed to save map: ${data.message}`);
      }
    } catch (error) {
      console.error("❌ API error:", error);
      alert("❌ Error saving map. See console for details.");
    }
  };

  const handleLoadMap = async (mapName) => {
    try {
      const res = await fetch(`${BASE_URL}/api/resource/Process Map/${mapName}?fields=["*"]`, {
        method: 'GET',
        headers: {
          // Authorization: `token ${API_TOKEN}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      const result = await res.json();
      const mapData = result.data;

      const parsedNodes = JSON.parse(mapData.nodes || '[]').map((node) => ({
        ...node,
        data: {
          ...node.data,
          label: node.label || node.data?.label || '',
        },
        type: node.type || 'default',
        position: node.position || { x: 0, y: 0 },
        style:
          node.type === 'group'
            ? {
              border: '2px dashed #0d6efd',
              backgroundColor: '#e7f1ff',
            }
            : node.type === 'process_group'
              ? {
                border: '2px dashed orange',
                backgroundColor: '#fff6e5',
              }
              : undefined,
      }));

      const parsedEdges = JSON.parse(mapData.edges || '[]').map((edge) => ({
        ...edge,
        data: {
          ...(edge.data || {}),
          components: edge.data?.components || [],
          style: {
            ...(edge.style || {}),
            stroke: edge.style?.stroke || '#999',
            strokeWidth: edge.style?.strokeWidth || 2,
          },
        },
      }));

      setNodes(parsedNodes);
      setEdges(parsedEdges);

      alert(`✅ Loaded process map: ${mapData.map_name}`);
    } catch (err) {
      console.error("❌ Error loading map:", err);
      alert("❌ Failed to load map.");
    }
  };

  return (
    <div className="container-fluid" style={{ height: '100vh' }}>
      <div className="row h-100">

        <Sidebar
          operationProcesses={operationProcesses}
          processGroups={processGroups}
          streams={streams}
          processMaps={processMaps}
          handleSaveMap={handleSaveMap}
          handleLoadMap={handleLoadMap}
        />
        <div className="col-9 p-0">
          <ReactFlow
            nodeTypes={nodeTypes}
            nodes={nodes.map((n) =>
              ['group'].includes(n.type)
                ? {
                  ...n,
                  style: {
                    ...n.style,
                    width: n.data.width,
                    height: n.data.height,
                    padding: 10,
                  },
                }
                : n
            )}
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

      {/* <Modal show={showNodeModal} onHide={() => setShowNodeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Delete Node</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Delete <strong>{targetNode?.data.label}</strong> and its children?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowNodeModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDeleteNode}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal> */}

      <Modal show={showEdgeModal} onHide={() => setShowEdgeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Select Components</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group controlId="formComponents">
            <Form.Label>Select components flowing in this connection:</Form.Label>
            <Form.Control
              as="select"
              multiple
              value={selectedComponents}
              onChange={(e) =>
                setSelectedComponents(Array.from(e.target.selectedOptions, (opt) => opt.value))
              }
            >
              {(newEdgeParams
                ? getAvailableComponentsFromSource(newEdgeParams.source)
                : defaultComponents
              ).map((component) => (
                <option key={component} value={component}>
                  {component}
                </option>
              ))}
            </Form.Control>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEdgeModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleConfirmEdge}>
            Confirm
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default FlowCanvas