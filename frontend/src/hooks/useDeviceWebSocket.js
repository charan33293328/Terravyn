import { useState, useEffect, useRef } from 'react';
import apiClient from '../api/client';

export const useDeviceWebSocket = (deviceId) => {
  const [sensorData, setSensorData] = useState(null);
  const [deviceStatus, setDeviceStatus] = useState('connecting');
  const wsRef = useRef(null);

  useEffect(() => {
    if (!deviceId) return;

    const fetchInitial = async () => {
      try {
        const res = await apiClient.get(`/device/latest?device_id=${deviceId}`);
        setSensorData(res.data);
      } catch (err) {
        console.log("No initial sensor data found");
      }
    };
    fetchInitial();

    const connect = () => {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const wsProtocol = baseUrl.startsWith('https') ? 'wss:' : 'ws:';
      const host = baseUrl.replace(/^https?:\/\//, '');
      const wsUrl = `${wsProtocol}//${host}/api/device/ws/${deviceId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setDeviceStatus('online');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'sensor_update') {
            setSensorData(message.data);
            setDeviceStatus('online'); // ensure status is online if getting data
          } else if (message.type === 'status_update') {
            setDeviceStatus(message.status);
          } else if (message.type === 'command') {
            // handle commands broadcasted back
            console.log('Received command broadcast:', message);
          }
        } catch (error) {
          console.error("Error parsing websocket message:", error);
        }
      };

      ws.onclose = () => {
        setDeviceStatus('offline');
        // Attempt to reconnect after 3 seconds
        setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        ws.close();
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [deviceId]);

  const sendCommand = (commandData) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(commandData));
    } else {
      console.error('WebSocket is not connected');
    }
  };

  return { sensorData, deviceStatus, sendCommand };
};
