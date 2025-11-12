import { useState, useEffect, useRef } from 'react';
import { PulseLoader } from 'react-spinners';
import './App.css';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface AgentStep {
  agent: string;
  name: string;
  status: string;
  confidence?: number;
  rag_docs?: number;
  icon: string;
}

interface ChatResponse {
  response: string;
  requestId: string;
  agentFlow: AgentStep[];
  metrics?: {
    query_type: string;
    confidence: number;
    agent_count: number;
    rag_enabled: boolean;
  };
  error?: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: 'Hello! I\'m your ToggleHealth assistant. How can I help you today?',
    },
  ]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [lastMetrics, setLastMetrics] = useState<ChatResponse['metrics'] | null>(null);
  const [lastAgentFlow, setLastAgentFlow] = useState<AgentStep[]>([]);
  const [showMetrics, setShowMetrics] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContentRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAgent]);

  const sendMessage = async () => {
    if (!userInput.trim()) return;

    const currentInput = userInput;
    setUserInput('');
    setIsLoading(true);
    setCurrentAgent(null);
    setShowMetrics(false);

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: currentInput,
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'system',
      content: 'loading',
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);

    // Simulate agent progression
    setTimeout(() => setCurrentAgent('🔍 Analyzing your question...'), 500);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userInput: currentInput,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      // Simulate specialist agent
      if (data.agentFlow.length > 1) {
        const specialist = data.agentFlow[1];
        setCurrentAgent(`${specialist.icon} Reaching out to ${specialist.name}...`);
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }

      // Simulate brand voice
      if (data.agentFlow.some((a) => a.agent === 'brand_voice')) {
        setCurrentAgent('✨ Putting an answer together...');
        await new Promise((resolve) => setTimeout(resolve, 800));
      }

      // Clear agent status
      setCurrentAgent(null);

      // Add assistant message
      const assistantMessage: Message = {
        id: data.requestId,
        role: 'assistant',
        content: data.response,
      };

      setMessages((prev) => prev.filter((m) => m.content !== 'loading').concat(assistantMessage));
      
      // Store metrics and agent flow
      setLastMetrics(data.metrics || null);
      setLastAgentFlow(data.agentFlow);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'I\'m sorry, an error occurred. Please try again.',
      };
      setMessages((prev) => prev.filter((m) => m.content !== 'loading').concat(errorMessage));
    } finally {
      setIsLoading(false);
      setCurrentAgent(null);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="chat-header">
        <div className="header-content">
          <div className="logo-container">
            <img
              src="/health/toggleHealth_logo_horizontal.svg"
              alt="ToggleHealth"
              className="logo"
            />
          </div>
          <div className="header-text">
            <p className="header-subtitle">
              Multi-Agent AI powered by <span className="provider-badge">Amazon Bedrock</span>
            </p>
          </div>
        </div>
        <div className="header-actions">
          <button className="feedback-btn feedback-good" title="Good service">
            😊
          </button>
          <button className="feedback-btn feedback-bad" title="Bad service">
            ☹️
          </button>
        </div>
      </header>

      {/* Chat Content */}
      <div className="chat-content" ref={chatContentRef}>
        {messages.map((message) => {
          if (message.role === 'user') {
            return (
              <div key={message.id} className="message message-user">
                {message.content}
              </div>
            );
          } else if (message.role === 'assistant') {
            return (
              <div key={message.id} className="message message-assistant">
                {message.content}
              </div>
            );
          } else if (message.role === 'system' && message.content === 'loading') {
            return (
              <div key={message.id} className="message message-assistant">
                <PulseLoader size={8} color="#4A90E2" />
              </div>
            );
          }
          return null;
        })}

        {/* Agent Status */}
        {currentAgent && (
          <div className="agent-status">
            {currentAgent}
          </div>
        )}

        {/* Metrics Panel */}
        {lastMetrics && (
          <div className="metrics-panel">
            <button
              className="metrics-toggle"
              onClick={() => setShowMetrics(!showMetrics)}
            >
              {showMetrics ? '▼' : '▶'} Response Metrics
            </button>
            {showMetrics && (
              <div className="metrics-content">
                <div className="metric-row">
                  <span className="metric-label">Query Type:</span>
                  <span className="metric-value">{lastMetrics.query_type}</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Confidence:</span>
                  <span className="metric-value">
                    {(lastMetrics.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Agents Used:</span>
                  <span className="metric-value">{lastMetrics.agent_count}</span>
                </div>
                {lastMetrics.rag_enabled && (
                  <div className="metric-row">
                    <span className="metric-label">RAG Enabled:</span>
                    <span className="metric-value">✅ Yes</span>
                  </div>
                )}
                
                {/* Agent Flow */}
                <div className="agent-flow">
                  <p className="agent-flow-title">Agent Flow:</p>
                  <div className="agent-badges">
                    {lastAgentFlow.map((agent, idx) => (
                      <div key={idx} className="agent-badge">
                        <span className="agent-icon">{agent.icon}</span>
                        <span className="agent-name">{agent.name}</span>
                        {agent.rag_docs !== undefined && (
                          <span className="agent-docs">({agent.rag_docs} docs)</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-footer">
        <input
          type="text"
          className="chat-input"
          placeholder="Type your message..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button
          className="send-button"
          onClick={sendMessage}
          disabled={isLoading || !userInput.trim()}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m22 2-7 20-4-9-9-4Z" />
            <path d="M22 2 11 13" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default App;

