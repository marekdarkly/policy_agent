import axios from 'axios';

// API base URL - with enhanced logging to debug Railway deployment issues
const getApiUrl = () => {
  // If running on Railway, use the correct public backend URL
  if (window.location.hostname.includes('railway.app')) {
    const backendUrl = 'https://ld-gr-backend-production.up.railway.app';
    console.log('Detected Railway deployment, using backend URL:', backendUrl);
    return backendUrl;
  }
  
  // Try runtime env first
  if (window.REACT_APP_API_URL) {
    console.log('Using runtime window.REACT_APP_API_URL:', window.REACT_APP_API_URL);
    
    // Add https:// protocol if not present
    if (!window.REACT_APP_API_URL.startsWith('http://') && !window.REACT_APP_API_URL.startsWith('https://')) {
      // Use HTTPS in production
      return window.location.protocol === 'https:' 
        ? 'https://' + window.REACT_APP_API_URL 
        : 'http://' + window.REACT_APP_API_URL;
    }
    return window.REACT_APP_API_URL;
  }
  
  // Try build time env next
  if (process.env.REACT_APP_API_URL) {
    console.log('Using build-time process.env.REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    
    // Add https:// protocol if not present
    if (!process.env.REACT_APP_API_URL.startsWith('http://') && !process.env.REACT_APP_API_URL.startsWith('https://')) {
      // Use HTTPS in production
      return window.location.protocol === 'https:' 
        ? 'https://' + process.env.REACT_APP_API_URL 
        : 'http://' + process.env.REACT_APP_API_URL;
    }
    return process.env.REACT_APP_API_URL;
  }
  
  // Fallback to localhost
  console.log('No environment variables found, using localhost fallback');
  return 'http://localhost:8000';
};

const API_URL = getApiUrl();
console.log('FINAL API URL:', API_URL);

// Configure axios
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Session management
export const getSessionId = async () => {
  // Check localStorage first
  let sessionId = localStorage.getItem('simulation_session_id');
  
  // If no session ID exists, create a new one
  if (!sessionId) {
    try {
      const response = await api.get('/session');
      sessionId = response.data.session_id;
      localStorage.setItem('simulation_session_id', sessionId);
      console.log('Created new session ID:', sessionId);
    } catch (error) {
      console.error('Error creating session:', error);
      // Fallback to a client-generated session ID
      sessionId = 'client-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
      localStorage.setItem('simulation_session_id', sessionId);
      console.log('Created fallback session ID:', sessionId);
    }
  } else {
    console.log('Using existing session ID:', sessionId);
  }
  
  return sessionId;
};

// Start simulation with configuration
export const startSimulation = async (config) => {
  try {
    // Get session ID
    const sessionId = await getSessionId();
    
    // Add session ID to config
    config.session_id = sessionId;
    
    // Use axios for all calls
    const response = await api.post('/simulation/start', config);
    return response.data;
  } catch (error) {
    console.error('Error starting simulation:', error);
    throw error;
  }
};

// Stop simulation
export const stopSimulation = async () => {
  try {
    // Get session ID
    const sessionId = await getSessionId();
    
    // Use axios for all calls
    const response = await api.post('/simulation/stop', { session_id: sessionId });
    return response.data;
  } catch (error) {
    console.error('Error stopping simulation:', error);
    throw error;
  }
};

// Get simulation status
export const getStatus = async () => {
  try {
    // Get session ID
    const sessionId = await getSessionId();
    
    // Use axios for all calls
    const response = await api.get(`/simulation/status?session_id=${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching status:', error);
    throw error;
  }
};

// Get simulation logs with pagination
export const getLogs = async (limit = 100, skip = 0) => {
  try {
    // Get session ID
    const sessionId = await getSessionId();
    
    // Use axios for all calls
    const response = await api.get(`/simulation/logs?session_id=${sessionId}&limit=${limit}&skip=${skip}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching logs:', error);
    throw error;
  }
};
