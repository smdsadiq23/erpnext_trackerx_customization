import React, { useEffect, useState } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { Modal, Button } from "react-bootstrap";
import FlowCanvas from "./Components/FlowCanvas";

export function App() {
  const [operationProcesses, setOperationProcesses] = useState([]);
  const [operation, setOperation] = useState([]);
  const [processGroups, setProcessGroups] = useState([]);
  const [streams, setStreams] = useState([]);
  const [processMaps, setProcessMaps] = useState([]);
  const [items, setItems] = useState([]);
  const [fgComponents, setFgComponents] = useState([]);

  // Modal state
  const [showItemModal, setShowItemModal] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [processMapNo, setProcessMapNo] = useState("");
  const [description, setDescription] = useState("");
  const [processMapName, setProcessMapName] = useState("");

  const BASE_URL = `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ""
    }`;

  // Generic fetcher for doctypes
  const fetchDocType = async (doctypeName) => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/resource/${doctypeName}?fields=["*"]`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
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

  // Fetch single Item details (with FG components)
  const fetchItemDetails = async (itemName) => {
    try {
      const response = await fetch(`${BASE_URL}/api/resource/Item/${itemName}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });
      const result = await response.json();
      return result.data; // full Item doc with FG components
    } catch (error) {
      console.error("Error fetching Item details:", error);
      return null;
    }
  };

  const fetchProcessMaps = async () => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/resource/Process Map?fields=["*"]`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
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

  // On mount → get all Items for dropdown
  useEffect(() => {
    const loadItems = async () => {
      const itemList = await fetchDocType("Item");
      setItems(itemList);
    };
    loadItems();
  }, []);

  // Confirm item selection → fetch FG components + process map data
  const handleConfirmItem = async () => {
    if (!selectedItem) return;

    const details = await fetchItemDetails(selectedItem);

    // ✅ Extract FG Components
    const fgComps = details?.custom_fg_components?.map((row) => row.component_name) || [];
    setFgComponents(fgComps);

    // Fetch other process map related data
    const [opData, pgData, streamData, operationData, pmData] = await Promise.all([
      fetchDocType("Operation Process"),
      fetchDocType("Process Group"),
      fetchDocType("Stream"),
      fetchDocType("Operation"),
      fetchProcessMaps(),
    ]);

    let operationDataProcessed = operationData?.map((row) => {
      return { process_name: row.name };
    });

    setOperationProcesses(operationDataProcessed);
    setProcessGroups(pgData);
    setStreams(streamData);
    setOperation(operationData);
    setProcessMaps(pmData);

    setShowItemModal(false); // close modal once everything is ready
  };

  return (
    <>
      {/* Item Selection Modal */}
      {/* <Modal show={showItemModal} backdrop="static" keyboard={false}>
        <Modal.Header>
          <Modal.Title>Select an Item</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <select
            className="form-select"
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
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="primary"
            onClick={handleConfirmItem}
            disabled={!selectedItem}
          >
            Confirm
          </Button>
        </Modal.Footer>
      </Modal> */}

      <Modal show={showItemModal} backdrop="static" keyboard={false}>
        <Modal.Header>
          <Modal.Title>Enter Process Map Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {/* Select FG Item */}
          <div>
            <div>
              <label className="form-label fw-semibold">FG Item</label>
            </div>
            <div>
              <select
                className="form-select form-select-lg mb-3 rounded border shadow-sm"
                value={selectedItem || ""}
                onChange={(e) => setSelectedItem(e.target.value)}
                style={{ backgroundColor: '#f8f9fa' }}
              >
                <option value="">-- Select Item --</option>
                {items.map((item) => (
                  <option key={item.name} value={item.name}>
                    {item.item_name || item.name}
                  </option>
                ))}
              </select>
            </div>


          </div>


          {/* Process Map Name */}
          <label className="form-label fw-semibold">Process Map Name</label>
          <input
            type="text"
            className="form-control mb-3 rounded border shadow-sm"
            value={processMapName}
            onChange={(e) => setProcessMapName(e.target.value)}
            placeholder="Enter Process Map Name"
          />

          {/* Process Map Number */}
          <label className="form-label fw-semibold">Process Map Number</label>
          <input
            type="text"
            className="form-control mb-3 rounded border shadow-sm"
            value={processMapNo}
            onChange={(e) => setProcessMapNo(e.target.value)}
            placeholder="Enter Process Map Number"
          />

          {/* Description */}
          <label className="form-label fw-semibold">Description</label>
          <textarea
            className="form-control rounded border shadow-sm"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description"
            rows={3}
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



      {/* Render FlowCanvas only after FG components are ready */}
      {!showItemModal && fgComponents.length > 0 && (
        <ReactFlowProvider>
          <FlowCanvas
            operationProcesses={operationProcesses}
            processGroups={processGroups}
            streams={streams}
            processMaps={processMaps}
            defaultComponents={fgComponents}
            processMapNumber={processMapNo}
            selectedItem={selectedItem}
            description={description}
            processMapName={processMapName}
          />
        </ReactFlowProvider>
      )}
    </>
  );
}
