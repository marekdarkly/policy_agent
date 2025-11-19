// This file will be overwritten at runtime in production
// It provides development defaults for the runtime environment variables
window.REACT_APP_API_URL = window.REACT_APP_API_URL || "http://localhost:8000";
window.REACT_APP_WS_URL = window.REACT_APP_WS_URL || "ws://localhost:8000/ws";
console.log("env-config.js loaded - API:", window.REACT_APP_API_URL, "WS:", window.REACT_APP_WS_URL); 