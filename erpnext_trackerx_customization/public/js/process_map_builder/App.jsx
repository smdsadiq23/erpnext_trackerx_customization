import React, { useEffect, useState } from 'react';
import {
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import { styles } from "./styles";
import FlowCanvas from './Components/FlowCanvas';


export function App() {
  const [operationProcesses, setOperationProcesses] = useState([]);
  const [processGroups, setProcessGroups] = useState([]);
  const [streams, setStreams] = useState([]);
  const [processMaps, setProcessMaps] = useState([]);

  // const API_TOKEN = 'f15ebc3b84401d2:9cddcb70db531d1';
  const BASE_URL = `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ''}`;;

  const fetchDocType = async (doctypeName) => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/resource/${doctypeName}?fields=["*"]`,
        {
          method: 'GET',
          headers: {
            // Authorization: `token ${API_TOKEN}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        }
      );
      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error(`Error fetching ${doctypeName}:`, error);
      return [];
    }
  };

  const fetchProcessMaps = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/resource/Process Map?fields=["*"]`, {
        method: 'GET',
        headers: {
          // Authorization: `token ${API_TOKEN}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error("Error fetching Process Maps:", error);
      return [];
    }
  };

  useEffect(() => {
    const fetchAll = async () => {
      const [opData, pgData, streamData, pmData] = await Promise.all([
        fetchDocType('Operation Process'),
        fetchDocType('Process Group'),
        fetchDocType('Stream'),
        fetchProcessMaps(),
      ]);
      setOperationProcesses(opData);
      setProcessGroups(pgData);
      setStreams(streamData);
      setProcessMaps(pmData);
    };
    fetchAll();
  }, []);

  return (<>
    {/* <div style={styles.titleBold}>React flow</div> */}
    <ReactFlowProvider>
      <FlowCanvas
        operationProcesses={operationProcesses}
        processGroups={processGroups}
        streams={streams}
        processMaps={processMaps}
      />
    </ReactFlowProvider>
  </>

  );
}