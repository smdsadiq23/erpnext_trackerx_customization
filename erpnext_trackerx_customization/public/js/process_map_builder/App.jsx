import React, { useEffect, useState } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { Modal, Button } from "react-bootstrap";
import FlowCanvas from "./Components/FlowCanvas";
import { normalizeNodes, normalizeEdges } from "./nodeNormalizer";

export function App() {
  const [operationProcesses, setOperationProcesses] = useState([]);
  const [processMaps, setProcessMaps] = useState([]);
  const [styleGroups, setStyleGroups] = useState([]);
  const [styleGroupComponents, setStyleGroupComponents] = useState([]);
  const [operationGroups, setOperationGroups] = useState([]);

  // Modal + Process Map state
  const [showStyleGroupModal, setShowStyleGroupModal] = useState(true);

  const [selectedStyleGroup, setSelectedStyleGroup] = useState(null);
  const [processMapNo, setProcessMapNo] = useState("");
  const [description, setDescription] = useState("");
  const [processMapName, setProcessMapName] = useState("");

  // Component selection state
  const [availableComponents, setAvailableComponents] = useState([]);
  const [selectedComponents, setSelectedComponents] = useState([]);

  // Pre-loaded map data (when URL has id)
  const [loadedNodes, setLoadedNodes] = useState([]);
  const [loadedEdges, setLoadedEdges] = useState([]);
  const [isEditMode, setIsEditMode] = useState(false);

  const BASE_URL = `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ""
    }`;

  // Detect URL params for style group context
  const urlParams = new URLSearchParams(window.location.search);
  const styleGroupParam = urlParams.get('style_group');
  const mapNameParam = urlParams.get('map_name');
  const mapNumberParam = urlParams.get('map_number');


  // Detect URL param for direct process map ID
  const pathParts = window.location.pathname.split("/");
  const processMapId =
    pathParts[pathParts.length - 1] !== "process-map-builder"
      ? pathParts[pathParts.length - 1]
      : null;

  // Fetch docType helper
  const fetchDocType = async (doctypeName) => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/resource/${doctypeName}?fields=["*"]&limit_page_length=0`,
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        }
      );
      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error(`Error fetching ${doctypeName}:`, error);
      return [];
    }
  };

  const fetchStyleGroupDetails = async (styleGroupName) => {
    if (!styleGroupName) return null;
    try {
      // Get CSRF token
      const csrfToken = window.frappe?.csrf_token ||
                       document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

      const response = await fetch(
        `${BASE_URL}/api/method/erpnext_trackerx_customization.api.process_map.get_style_group_data`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": csrfToken
          },
          credentials: "include",
          body: JSON.stringify({ style_group_name: styleGroupName })
        }
      );
      const result = await response.json();
      return result.message?.data || null;
    } catch (error) {
      console.error("Error fetching Style Group details:", error);
      return null;
    }
  };

  const fetchProcessMaps = async () => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/resource/Process Map?fields=["*"]&limit_page_length=0`,
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        }
      );
      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error("Error fetching Process Maps:", error);
      return [];
    }
  };

  useEffect(() => {
    const loadStyleGroups = async () => {
      const styleGroupList = await fetchDocType("Style Group");
      setStyleGroups(styleGroupList);
    };
    loadStyleGroups();
  }, []);


  const fetchDocTypeItem = async (doctypeName, filters = []) => {
    try {
      const url = new URL(`${BASE_URL}/api/resource/${doctypeName}`);
      url.searchParams.append("fields", JSON.stringify(["*"]));
      url.searchParams.append("limit_page_length", "0");

      if (filters.length > 0) {
        url.searchParams.append("filters", JSON.stringify(filters));
      }

      const response = await fetch(url, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });

      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error(`Error fetching ${doctypeName}:`, error);
      return [];
    }
  };


  // Handle URL parameters and existing map loading
  useEffect(() => {
    const handleUrlParams = async () => {
      // Case 1: Direct process map ID in URL path
      if (processMapId) {
        try {
          const res = await fetch(
            `${BASE_URL}/api/resource/Process Map/${processMapId}?fields=["*"]`,
            {
              method: "GET",
              headers: { "Content-Type": "application/json" },
              credentials: "include",
            }
          );

          const result = await res.json();
          const mapData = result.data;

          setProcessMapName(mapData.map_name);
          setProcessMapNo(mapData.process_map_number);
          setDescription(mapData.description);
          setSelectedStyleGroup(mapData.style_group);

          // ✅ Normalize nodes & edges here
          setLoadedNodes(normalizeNodes(JSON.parse(mapData.nodes || "[]")));
          setLoadedEdges(normalizeEdges(JSON.parse(mapData.edges || "[]")));

          // Style Group components
          if (mapData.style_group) {
            const details = await fetchStyleGroupDetails(mapData.style_group);
            const components = details?.components || [];
            setAvailableComponents(components);

            const sgComps = components.map((comp) => comp.component_name);
            setSelectedComponents(sgComps);
            setStyleGroupComponents(sgComps);
          }

          // Fetch other references in parallel
          const [operationData, pmData, operationGroupData] =
            await Promise.all([
              fetchDocType("Operation"),
              fetchProcessMaps(),
              fetchDocType("Operation Group"),
            ]);

          let operationDataProcessed = operationData?.map((row) => ({
            ...row,
            process_name: row.name,
          })) || [];
          setOperationProcesses(operationDataProcessed);
          setProcessMaps(pmData || []);
          setOperationGroups(operationGroupData || []);

          setShowStyleGroupModal(false);
          setIsEditMode(true);
        } catch (err) {
          console.error("❌ Failed to load process map:", err);
        }
      }
      // Case 2: Style Group context from URL parameters
      else if (styleGroupParam) {
        setSelectedStyleGroup(styleGroupParam);

        if (mapNameParam) {
          setProcessMapName(mapNameParam);
        }
        if (mapNumberParam) {
          setProcessMapNo(mapNumberParam);
        }

        // Load Style Group components
        try {
          const details = await fetchStyleGroupDetails(styleGroupParam);
          const components = details?.components || [];
          setAvailableComponents(components);

          // Auto-select all components when loading from URL (but keep modal open)
          const sgComps = components.map((comp) => comp.component_name);
          setSelectedComponents(sgComps);

          // Fetch other references in parallel
          const [operationData, pmData, operationGroupData] =
            await Promise.all([
              fetchDocType("Operation"),
              fetchProcessMaps(),
              fetchDocType("Operation Group"),
            ]);

          let operationDataProcessed = operationData?.map((row) => ({
            ...row,
            process_name: row.name,
          })) || [];
          setOperationProcesses(operationDataProcessed);
          setProcessMaps(pmData || []);
          setOperationGroups(operationGroupData || []);

          // Keep modal open to allow component selection and process map naming
          setShowStyleGroupModal(true);
        } catch (err) {
          console.error("❌ Failed to load style group data:", err);
        }
      }
    };

    handleUrlParams();
  }, [processMapId, styleGroupParam, mapNameParam, mapNumberParam]);

  // Handle Style Group selection change
  const handleStyleGroupChange = async (styleGroupName) => {
    setSelectedStyleGroup(styleGroupName);

    if (styleGroupName) {
      // Fetch components for the selected style group
      const details = await fetchStyleGroupDetails(styleGroupName);
      const components = details?.components || [];
      setAvailableComponents(components);

      // Auto-select all components by default
      const componentNames = components.map((comp) => comp.component_name);
      setSelectedComponents(componentNames);
    } else {
      setAvailableComponents([]);
      setSelectedComponents([]);
    }
  };

  // Handle component selection toggle
  const handleComponentToggle = (componentName) => {
    setSelectedComponents(prev => {
      if (prev.includes(componentName)) {
        return prev.filter(name => name !== componentName);
      } else {
        return [...prev, componentName];
      }
    });
  };

  // Handle select all / deselect all
  const handleSelectAllComponents = () => {
    const allComponentNames = availableComponents.map(comp => comp.component_name);
    setSelectedComponents(allComponentNames);
  };

  const handleDeselectAllComponents = () => {
    setSelectedComponents([]);
  };

  const handleConfirmStyleGroup = async () => {
    if (!selectedStyleGroup || selectedComponents.length === 0) return;

    // Use only selected components
    setStyleGroupComponents(selectedComponents);

    const [operationData, pmData, operationGroupData] =
      await Promise.all([
        fetchDocType("Operation"),
        fetchProcessMaps(),
        fetchDocType("Operation Group"),
      ]);

    let operationDataProcessed = operationData?.map((row) => ({
      ...row,
      process_name: row.name,
    })) || [];
    setOperationProcesses(operationDataProcessed);
    setProcessMaps(pmData || []);
    setOperationGroups(operationGroupData || []);

    setShowStyleGroupModal(false);
  };

   const handleCloseModal = () => {
    setShowStyleGroupModal(false);
    window.history.pushState({}, "", "/app/home");
    window.location.href = "/app/process-map";
  };

  return (
    <>
      {/* Case 1 → Only show modal if no mapId */}
      {/* {!processMapId && (
        <Modal show={showItemModal} backdrop="static" keyboard={false}>
          <Modal.Header>
            <Modal.Title>Enter Process Map Details</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <label className="form-label fw-semibold">FG Item</label>
            <select
              className="form-select mb-3"
              value={selectedItem || ""}
              onChange={(e) => setSelectedItem(e.target.value)}
            >
              <option value="">-- Select Item --</option>
              {items.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.item_name || item.name}
                </option>
              ))}
            </select>

            <label className="form-label fw-semibold">Process Map Name</label>
            <input
              type="text"
              className="form-control mb-3"
              value={processMapName}
              onChange={(e) => setProcessMapName(e.target.value)}
            />

            <label className="form-label fw-semibold">Process Map Number</label>
            <input
              type="text"
              className="form-control mb-3"
              value={processMapNo}
              onChange={(e) => setProcessMapNo(e.target.value)}
            />

            <label className="form-label fw-semibold">Description</label>
            <textarea
              className="form-control"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="primary"
              onClick={handleConfirmItem}
              disabled={!selectedItem || !processMapName}
            >
              Confirm
            </Button>
          </Modal.Footer>
        </Modal>
      )} */}

      {!processMapId && (
        <Modal show={showStyleGroupModal} backdrop="static" keyboard={false}>
           <Modal.Header>
            <Modal.Title>Enter Process Map Details</Modal.Title>
             <button
          onClick={handleCloseModal}
          className="btn btn-light close-btn"
             >
               ×
            </button>


          </Modal.Header>
          <Modal.Body>
            {/* Style Group */}
            <div className="mb-3">
              <label className="form-label fw-semibold">Style Group</label>
              <div>
                <select
                 className="form-select"
                  style={{
                    display: "block",
                    width: "100%",
                    padding: ".375rem 2.25rem .375rem .75rem",
                    MozPaddingStart: "calc(0.75rem - 3px)",
                    lineHeight: 1,
                    backgroundColor: "#F3F3F3",
                    border: "1px solid #ced4da",
                    borderRadius: ".25rem",
                    MozAppearance: "none"
                  }}

                  value={selectedStyleGroup || ""}
                  onChange={(e) => handleStyleGroupChange(e.target.value)}
                  disabled={!!styleGroupParam}
                >
                  <option value="">-- Select Style Group --</option>
                  {styleGroups.map((sg) => (
                    <option key={sg.name} value={sg.name}>
                      {sg.name}
                    </option>
                  ))}
                </select>
              </div>

            </div>

            {/* Component Selection Group */}
            {availableComponents.length > 0 && (
              <div className="mb-3">
                <label className="form-label fw-semibold">Select Components</label>
                <div className="mb-2">
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary me-2"
                    onClick={handleSelectAllComponents}
                  >
                    Select All
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={handleDeselectAllComponents}
                  >
                    Deselect All
                  </button>
                </div>
                <div style={{
                  maxHeight: "150px",
                  overflowY: "auto",
                  border: "1px solid #ced4da",
                  borderRadius: ".25rem",
                  padding: "8px"
                }}>
                  {availableComponents.map((component) => (
                    <div key={component.component_name} className="form-check">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id={`component-${component.component_name}`}
                        checked={selectedComponents.includes(component.component_name)}
                        onChange={() => handleComponentToggle(component.component_name)}
                      />
                      <label
                        className="form-check-label"
                        htmlFor={`component-${component.component_name}`}
                      >
                        <strong>{component.component_name}</strong>
                        {component.description && (
                          <small className="text-muted d-block">
                            {component.description}
                          </small>
                        )}
                      </label>
                    </div>
                  ))}
                </div>
                <small className="text-muted">
                  Selected: {selectedComponents.length} of {availableComponents.length} components
                </small>
              </div>
            )}

            {/* Process Map Name Group */}
            <div className="mb-3">
              <label className="form-label fw-semibold">Process Map Name</label>
              <input
                type="text"
                className="form-control"
                value={processMapName}
                onChange={(e) => setProcessMapName(e.target.value)}
              />
            </div>

            {/* Process Map Number Group */}
            <div className="mb-3">
              <label className="form-label fw-semibold">Process Map Number</label>
              <input
                type="text"
                className="form-control"
                value={processMapNo}
                onChange={(e) => setProcessMapNo(e.target.value)}
              />
            </div>

            {/* Description Group */}
            <div className="mb-3">
              <label className="form-label fw-semibold">Description</label>
              <textarea
                className="form-control"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3} // Optional: Add rows for better textarea sizing
              />
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="primary"
              onClick={handleConfirmStyleGroup}
              disabled={!selectedStyleGroup || !processMapName || selectedComponents.length === 0}
            >
              Confirm
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* Canvas */}
      {!showStyleGroupModal && styleGroupComponents.length > 0 && (
        <ReactFlowProvider>
          <FlowCanvas
            operationProcesses={operationProcesses}
            processMaps={processMaps}
            operationGroups={operationGroups}
            defaultComponents={styleGroupComponents}
            processMapNumber={processMapNo}
            selectedStyleGroup={selectedStyleGroup}
            description={description}
            processMapName={processMapName}
            initialNodes={loadedNodes}
            initialEdges={loadedEdges}
            isEditMode={isEditMode}
            setIsEditMode={setIsEditMode}
          />
        </ReactFlowProvider>
      )}
    </>
  );
}
