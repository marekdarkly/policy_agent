import { useState, useEffect, useRef } from 'react';
import './Terminal.css';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  name: string;
}

function stripEmojis(text: string): string {
  return text
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/gu, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

export default function Terminal() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let retryTimeout: ReturnType<typeof setTimeout>;
    let cancelled = false;

    function connect() {
      if (cancelled) return;

      const eventSource = new EventSource('/api/logs/stream');
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const logEntry: LogEntry = JSON.parse(event.data);
          if (logEntry.level === 'HEARTBEAT') return;
          logEntry.message = stripEmojis(logEntry.message);
          setLogs((prevLogs) => [...prevLogs, logEntry]);
        } catch (error) {
          console.error('Failed to parse log entry:', error);
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        eventSource.close();
        if (!cancelled) {
          retryTimeout = setTimeout(connect, 2000);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(retryTimeout);
      eventSourceRef.current?.close();
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

  const clearLogs = () => {
    setLogs([]);
  };

  if (isCollapsed) {
    return (
      <div className="terminal-collapsed">
        <button className="terminal-expand-btn" onClick={() => setIsCollapsed(false)}>
          <span className="terminal-icon">&gt;_</span>
          <span>Terminal</span>
          {isConnected && <span className="status-indicator connected"></span>}
        </button>
      </div>
    );
  }

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <div className="terminal-title">
          <span className="terminal-icon">&gt;_</span>
          <span>Agent Pipeline</span>
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
        </div>
        <div className="terminal-actions">
          <button className="terminal-btn" onClick={clearLogs} title="Clear logs">
            Clear
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
            {!isConnected && <p className="terminal-error">Not connected to server</p>}
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className={`terminal-line ${getLogClass(log.level)}`}>
              <span className="log-icon">›</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
