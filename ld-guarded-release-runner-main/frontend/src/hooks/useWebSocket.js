import { useState, useEffect, useCallback, useRef } from 'react';
import { getSessionId } from '../api/simulationApi';

// WebSocket URL - with enhanced logging to debug Railway deployment issues
const getWsUrl = async () => {
  // Get the session ID first
  const sessionId = await getSessionId();
  
  let baseUrl;
  
  // If running on Railway, use the correct public backend URL
  if (window.location.hostname.includes('railway.app')) {
    baseUrl = 'wss://ld-gr-backend-production.up.railway.app/ws';
    console.log('Detected Railway deployment, using backend WebSocket URL:', baseUrl);
  }
  // Try runtime env first
  else if (window.REACT_APP_WS_URL) {
    console.log('Using runtime window.REACT_APP_WS_URL:', window.REACT_APP_WS_URL);
    
    // Add appropriate protocol if not present
    if (!window.REACT_APP_WS_URL.startsWith('ws://') && !window.REACT_APP_WS_URL.startsWith('wss://')) {
      // Use WSS in production (if loaded over HTTPS)
      baseUrl = window.location.protocol === 'https:' 
        ? 'wss://' + window.REACT_APP_WS_URL 
        : 'ws://' + window.REACT_APP_WS_URL;
    } else {
      baseUrl = window.REACT_APP_WS_URL;
    }
  }
  // Try build time env next
  else if (process.env.REACT_APP_WS_URL) {
    console.log('Using build-time process.env.REACT_APP_WS_URL:', process.env.REACT_APP_WS_URL);
    
    // Add appropriate protocol if not present
    if (!process.env.REACT_APP_WS_URL.startsWith('ws://') && !process.env.REACT_APP_WS_URL.startsWith('wss://')) {
      // Use WSS in production (if loaded over HTTPS)
      baseUrl = window.location.protocol === 'https:' 
        ? 'wss://' + process.env.REACT_APP_WS_URL 
        : 'ws://' + process.env.REACT_APP_WS_URL;
    } else {
      baseUrl = process.env.REACT_APP_WS_URL;
    }
  }
  // Fallback to localhost
  else {
    console.log('No WebSocket environment variables found, using localhost fallback');
    // Use secure websocket if page is served over HTTPS
    baseUrl = window.location.protocol === 'https:' 
      ? 'wss://localhost:8000/ws' 
      : 'ws://localhost:8000/ws';
  }
  
  // Add session ID to URL
  const fullUrl = `${baseUrl}/${sessionId}`;
  console.log('FINAL WebSocket URL with session:', fullUrl);
  return fullUrl;
};

const useWebSocket = ({ onMessage }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  
  // Update ref when onMessage changes
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);
  
  // Initialize WebSocket connection - only once
  useEffect(() => {
    let ws = null;
    let pingInterval = null;
    let reconnectTimeout = null;
    
    const connect = async () => {
      // Clean up any existing connections
      if (ws) {
        ws.close();
      }
      
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }
      
      try {
        // Get the WebSocket URL with session ID
        const wsUrl = await getWsUrl();
        
        // Create new WebSocket connection
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setConnected(true);
          
          // Send ping every 30 seconds to keep connection alive
          pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ping' }));
            }
          }, 30000);
        };
        
        ws.onclose = (event) => {
          console.log(`WebSocket disconnected (code: ${event.code})`);
          setConnected(false);
          
          if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
          }
          
          // Only reconnect if this wasn't a normal closure
          if (event.code !== 1000) {
            console.log('Scheduling reconnect attempt...');
            // Try to reconnect after a delay
            reconnectTimeout = setTimeout(() => {
              connect();
            }, 3000);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            // Use the ref to always have the latest callback
            if (onMessageRef.current) {
              onMessageRef.current(data);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        setSocket(ws);
      } catch (error) {
        console.error('Error connecting to WebSocket:', error);
        // Try to reconnect after a delay
        reconnectTimeout = setTimeout(() => {
          connect();
        }, 3000);
      }
    };
    
    // Initial connection
    connect();
    
    // Clean up on unmount
    return () => {
      if (ws) {
        // Use 1000 (Normal Closure) to avoid reconnect attempts
        ws.close(1000, 'Component unmounted');
      }
      
      if (pingInterval) {
        clearInterval(pingInterval);
      }
      
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  // No dependencies - only run once on mount
  }, []); 
  
  // Send message through WebSocket
  const sendMessage = useCallback((data) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    }
  }, [socket]);
  
  return { connected, sendMessage };
};

export default useWebSocket;