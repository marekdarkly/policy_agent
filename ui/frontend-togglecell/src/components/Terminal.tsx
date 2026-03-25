import { useState, useEffect, useRef } from 'react';
import './Terminal.css';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  name: string;
}

export default function Terminal() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const eventSource = new EventSource('/api/logs/stream');
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const logEntry: LogEntry = JSON.parse(event.data);
        if (logEntry.level === 'HEARTBEAT') return;
        setLogs((prevLogs) => [...prevLogs, logEntry]);
      } catch (error) {
        console.error('Failed to parse log entry:', error);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    if (!isCollapsed) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isCollapsed]);

  const getLogClass = (level: string): string => {
    const levelMap: Record<string, string> = {
      'INFO': 'log-info',
      'PRINT': 'log-print',
      'ERROR': 'log-error',
      'WARNING': 'log-warning',
      'DEBUG': 'log-debug',
    };
    return levelMap[level] || 'log-default';
  };

  const getLogIcon = (message: string): string => {
    if (message.includes('✅')) return '';
    if (message.includes('🔍')) return '';
    if (message.includes('📋')) return '';
    if (message.includes('🏥')) return '';
    if (message.includes('✨')) return '';
    if (message.includes('❌')) return '';
    if (message.includes('⚠️')) return '';
    if (message.includes('🔌')) return '';
    return '›';
  };

  const clearLogs = () => {
    setLogs([]);
  };

  if (isCollapsed) {
    return (
      <div className="terminal-collapsed">
        <button className="terminal-expand-btn" onClick={() => setIsCollapsed(false)}>
          <span className="terminal-icon">📟</span>
          <span>Show Terminal</span>
          {isConnected && <span className="status-indicator connected"></span>}
        </button>
      </div>
    );
  }

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <div className="terminal-title">
          <span className="terminal-icon">📟</span>
          <span>Backend Terminal</span>
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
        </div>
        <div className="terminal-actions">
          <button className="terminal-btn" onClick={clearLogs} title="Clear logs">
            🗑️
          </button>
          <button className="terminal-btn" onClick={() => setIsCollapsed(true)} title="Collapse">
            ◀
          </button>
        </div>
      </div>
      
      <div className="terminal-content">
        {logs.length === 0 ? (
          <div className="terminal-empty">
            <p>Waiting for logs...</p>
            {!isConnected && <p className="terminal-error">⚠️ Not connected to server</p>}
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className={`terminal-line ${getLogClass(log.level)}`}>
              <span className="log-icon">{getLogIcon(log.message)}</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
