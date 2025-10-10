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
  const [items, setItems] = useState([]);
  const [fgComponents, setFgComponents] = useState([]);
  const [operationGroups, setOperationGroups] = useState([]);

  // Modal + Process Map state
  const [showItemModal, setShowItemModal] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [processMapNo, setProcessMapNo] = useState("");
  const [description, setDescription] = useState("");
  const [processMapName, setProcessMapName] = useState("");

  // Pre-loaded map data (when URL has id)
  const [loadedNodes, setLoadedNodes] = useState([]);
  const [loadedEdges, setLoadedEdges] = useState([]);
  const [isEditMode, setIsEditMode] = useState(false);

  const BASE_URL = `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ""
    }`;

  // Detect URL param
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

  const fetchItemDetails = async (itemName) => {
    if (!itemName) return null;
    try {
      const response = await fetch(
        `${BASE_URL}/api/resource/Item/${itemName}`,
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        }
      );
      const result = await response.json();
      return result.data;
    } catch (error) {
      console.error("Error fetching Item details:", error);
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
    const loadItems = async () => {
      const itemList = await fetchDocTypeItem("Item", [
        ["custom_select_master", "=", "Finished Goods"],
      ]);
      setItems(itemList);
    };
    loadItems();
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


  // Case 2 → URL has processMapId → fetch directly
  useEffect(() => {
    const loadExistingMap = async () => {
      if (!processMapId) return;

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
        setSelectedItem(mapData.select_fg);

        // ✅ Normalize nodes & edges here
        setLoadedNodes(normalizeNodes(JSON.parse(mapData.nodes || "[]")));
        setLoadedEdges(normalizeEdges(JSON.parse(mapData.edges || "[]")));

        // FG components
        if (mapData.select_fg) {
          const details = await fetchItemDetails(mapData.select_fg);
          const fgComps =
            details?.custom_fg_components?.map((row) => row.component_name) ||
            [];
          setFgComponents(fgComps);
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

        setShowItemModal(false); // 🚀 Skip modal if URL provided
        setIsEditMode(true)
      } catch (err) {
        console.error("❌ Failed to load process map:", err);
      }
    };

    loadExistingMap();
  }, [processMapId]);

  const handleConfirmItem = async () => {
    if (!selectedItem) return;

    const details = await fetchItemDetails(selectedItem);
    const fgComps =
      details?.custom_fg_components?.map((row) => row.component_name) || [];
    setFgComponents(fgComps);

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

    setShowItemModal(false);
  };

   const handleCloseModal = () => {
    setShowItemModal(false);
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
              disabled={!selectedItem || !processMapName || !processMapNo}
            >
              Confirm
            </Button>
          </Modal.Footer>
        </Modal>
      )} */}

      {!processMapId && (
        <Modal show={showItemModal} backdrop="static" keyboard={false}>
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
            {/* FG Item Group */}
            <div className="mb-3">
              <label className="form-label fw-semibold">FG Item</label>
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
                 
                  value={selectedItem || ""}
                  onChange={(e) => setSelectedItem(e.target.value)}
                >
                  <option value="">-- Select Item --</option>
                  {items.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.item_code || item_code}
                    </option>
                  ))}
                </select>
              </div>

            </div>

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
              onClick={handleConfirmItem}
              disabled={!selectedItem || !processMapName || !processMapNo}
            >
              Confirm
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* Canvas */}
      {!showItemModal && fgComponents.length > 0 && (
        <ReactFlowProvider>
          <FlowCanvas
            operationProcesses={operationProcesses}
            processMaps={processMaps}
            operationGroups={operationGroups}
            defaultComponents={fgComponents}
            processMapNumber={processMapNo}
            selectedItem={selectedItem}
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
