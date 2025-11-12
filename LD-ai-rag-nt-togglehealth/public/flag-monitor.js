// Flag Monitor - Real-time flag change detection and page refresh
// This script connects to the backend WebSocket and refreshes the page when nt-toggle-rag-demo changes

class FlagMonitor {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // 2 seconds
        this.isConnected = false;
        this.currentFlagValue = null;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Flag Monitor...');
        this.connect();
        
        // Handle page visibility changes to reconnect when tab becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !this.isConnected) {
                console.log('📱 Page became visible, reconnecting...');
                this.connect();
            }
        });
        
        // Handle page unload to clean up WebSocket
        window.addEventListener('beforeunload', () => {
            if (this.ws) {
                this.ws.close();
            }
        });
    }
    
    connect() {
        try {
            // Get the current hostname and port
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = '8000'; // Backend port
            const wsUrl = `${protocol}//${host}:${port}/ws/flag-monitor`;
            
            console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // Start ping interval to keep connection alive
                this.startPingInterval();
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('❌ Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('🔌 WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                this.stopPingInterval();
                
                // Attempt to reconnect if not a normal closure
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`🔄 Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                    setTimeout(() => this.connect(), this.reconnectDelay);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('❌ Error creating WebSocket connection:', error);
        }
    }
    
    handleMessage(data) {
        console.log('📨 Received WebSocket message:', data);
        
        switch (data.type) {
            case 'initial_flag_value':
                this.currentFlagValue = data.current_value;
                console.log(`🎯 Initial flag value: ${this.currentFlagValue}`);
                break;
                
            case 'flag_change':
                if (data.flag_key === 'nt-toggle-rag-demo') {
                    console.log(`🔄 Flag changed from '${data.old_value}' to '${data.new_value}'`);
                    this.currentFlagValue = data.new_value;
                    
                    // Show notification to user
                    this.showNotification(data);
                    
                    // Refresh page after a short delay
                    setTimeout(() => {
                        console.log('🔄 Refreshing page due to flag change...');
                        window.location.reload();
                    }, 1500); // 1.5 second delay to show notification
                }
                break;
                
            case 'pong':
                // Keep-alive response, no action needed
                break;
                
            default:
                console.log('❓ Unknown message type:', data.type);
        }
    }
    
    showNotification(data) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 16px;">🔄</span>
                <div>
                    <div style="font-weight: 600; margin-bottom: 4px;">Industry Changed</div>
                    <div style="font-size: 12px; opacity: 0.9;">
                        ${data.old_value} → ${data.new_value}
                    </div>
                </div>
            </div>
        `;
        
        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        
        // Add to page
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    startPingInterval() {
        this.pingInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 30000); // Send ping every 30 seconds
    }
    
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    getCurrentFlagValue() {
        return this.currentFlagValue;
    }
    
    isConnected() {
        return this.isConnected;
    }
}

// Initialize the flag monitor when the script loads
let flagMonitor;

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        flagMonitor = new FlagMonitor();
    });
} else {
    flagMonitor = new FlagMonitor();
}

// Make it available globally for debugging
window.flagMonitor = flagMonitor;
