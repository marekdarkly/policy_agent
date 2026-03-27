import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./ChatWidget.css";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  requestId?: string;
}

interface AgentStep {
  agent: string;
  name: string;
  status: string;
  confidence?: number;
  rag_docs?: number;
  icon: string;
  duration?: number;
  ttft_ms?: number;
  tokens?: {
    input: number;
    output: number;
  };
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
    total_duration_ms?: number;
    accuracy_score?: number;
    accuracy_reasoning?: string;
    accuracy_issues?: string[];
    coherence_score?: number;
    coherence_reasoning?: string;
    coherence_issues?: string[];
    judge_model_name?: string;
    judge_input_tokens?: number;
    judge_output_tokens?: number;
  };
  error?: string;
}

interface ChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

const DOMAIN = "togglecell";

const ChatWidget = ({ isOpen, onClose, initialQuery }: ChatWidgetProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "0",
      role: "assistant",
      content:
        "Hi Alex! I'm your ToggleCell support assistant. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [lastMetrics, setLastMetrics] = useState<ChatResponse["metrics"] | null>(null);
  const [lastAgentFlow, setLastAgentFlow] = useState<AgentStep[]>([]);
  const [lastRequestId, setLastRequestId] = useState<string | null>(null);
  const [feedbackGiven, setFeedbackGiven] = useState<"positive" | "negative" | null>(null);
  const [showMetrics, setShowMetrics] = useState(false);
  const [showEvalReasoning, setShowEvalReasoning] = useState(false);
  const [guardrailEnabled, setGuardrailEnabled] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasProcessedInitial = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAgent]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && initialQuery && !hasProcessedInitial.current) {
      hasProcessedInitial.current = true;
      sendMessage(initialQuery);
    }
  }, [isOpen, initialQuery]);

  const pollForEvaluation = async (requestId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      if (attempts >= maxAttempts) return;
      attempts++;

      try {
        const response = await fetch(`/api/evaluation/${requestId}`);
        const data = await response.json();

        if (data.ready && data.evaluation) {
          setLastMetrics((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              accuracy_score: data.evaluation.accuracy?.score,
              accuracy_reasoning: data.evaluation.accuracy?.reason,
              accuracy_issues: data.evaluation.accuracy?.issues,
              coherence_score: data.evaluation.coherence?.score,
              coherence_reasoning: data.evaluation.coherence?.reason,
              coherence_issues: data.evaluation.coherence?.issues,
              judge_model_name: data.evaluation.judge_model_name,
              judge_input_tokens: data.evaluation.judge_input_tokens,
              judge_output_tokens: data.evaluation.judge_output_tokens,
            };
          });
        } else {
          setTimeout(poll, 500);
        }
      } catch {
        if (attempts < maxAttempts) {
          setTimeout(poll, 500);
        }
      }
    };

    setTimeout(poll, 1000);
  };

  const sendFeedback = async (isPositive: boolean) => {
    if (!lastRequestId) return;

    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requestId: lastRequestId,
          feedback: isPositive ? "positive" : "negative",
        }),
      });

      if (!response.ok) {
        throw new Error(`Feedback request failed with status ${response.status}`);
      }

      setFeedbackGiven(isPositive ? "positive" : "negative");
    } catch (error) {
      console.error("Error sending feedback:", error);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const currentInput = text.trim();
    setInput("");
    setIsLoading(true);
    setCurrentAgent(null);
    setShowMetrics(false);
    setFeedbackGiven(null);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: currentInput,
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "system",
      content: "loading",
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);

    setCurrentAgent("🔍 Analyzing your question...");
    const triageTimer = setTimeout(
      () => setCurrentAgent("📋 Looking up your policy..."),
      2000
    );
    const brandTimer = setTimeout(
      () => setCurrentAgent("✨ Writing up my thoughts..."),
      10000
    );

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userInput: currentInput,
          domain: DOMAIN,
          userName: "Alex Morgan",
          location: "London, UK",
          policyId: "TC-5G-UNLIM-2026",
          coverageType: "TC-5G-UNLIM-2026",
          guardrailEnabled,
        }),
      });

      clearTimeout(triageTimer);
      clearTimeout(brandTimer);

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      if (data.agentFlow.length > 1) {
        const specialist = data.agentFlow.find((a) =>
          a.agent.includes("specialist")
        );
        if (specialist) {
          setCurrentAgent(`${specialist.icon} Finalizing with ${specialist.name}...`);
          await new Promise((resolve) => setTimeout(resolve, 400));
        }
      }

      const brandVoice = data.agentFlow.find((a) => a.agent === "brand_voice");
      if (brandVoice) {
        setCurrentAgent("✨ Polishing the response...");
        await new Promise((resolve) => setTimeout(resolve, 300));
      }

      setCurrentAgent(null);

      const assistantMessage: Message = {
        id: data.requestId,
        role: "assistant",
        content: data.response,
        requestId: data.requestId,
      };

      setMessages((prev) =>
        prev.filter((m) => m.content !== "loading").concat(assistantMessage)
      );

      setLastMetrics(data.metrics || null);
      setLastAgentFlow(data.agentFlow);
      setLastRequestId(data.requestId);

      pollForEvaluation(data.requestId);
    } catch (error) {
      console.error("Chat error:", error);
      clearTimeout(triageTimer);
      clearTimeout(brandTimer);

      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "I'm sorry, an error occurred. Please try again.",
      };
      setMessages((prev) =>
        prev.filter((m) => m.content !== "loading").concat(errorMessage)
      );
    } finally {
      setIsLoading(false);
      setCurrentAgent(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="cw-container">
      {/* Header */}
      <div className="cw-header">
        <div className="cw-header-content">
          <div className="cw-header-text">
            <h2 className="cw-title">ToggleCell Support</h2>
            <p className="cw-subtitle">
              Powered by <span className="cw-provider-badge">Amazon Bedrock</span>
            </p>
          </div>
        </div>
        <div className="cw-header-actions">
          <button
            className={`cw-guardrail-toggle ${guardrailEnabled ? "enabled" : "disabled"}`}
            title={guardrailEnabled ? "Guardrail Enabled (click to disable)" : "Guardrail Disabled (click to enable)"}
            onClick={() => setGuardrailEnabled(!guardrailEnabled)}
            disabled={isLoading}
          >
            🛡️ {guardrailEnabled ? "ON" : "OFF"}
          </button>
          <button
            className={`cw-feedback-btn ${feedbackGiven === "positive" ? "active" : ""}`}
            title="Good response"
            onClick={() => sendFeedback(true)}
            disabled={!lastRequestId || isLoading}
          >
            😊
          </button>
          <button
            className={`cw-feedback-btn ${feedbackGiven === "negative" ? "active" : ""}`}
            title="Bad response"
            onClick={() => sendFeedback(false)}
            disabled={!lastRequestId || isLoading}
          >
            ☹️
          </button>
          <button className="cw-close-btn" onClick={onClose} title="Close chat">
            ✕
          </button>
        </div>
      </div>

      {/* Chat Content */}
      <div className="cw-content">
        {messages.map((message) => {
          if (message.role === "user") {
            return (
              <div key={message.id} className="cw-msg-row cw-msg-row-user">
                <div className="cw-msg cw-msg-user">{message.content}</div>
              </div>
            );
          }

          if (message.role === "assistant") {
            return (
              <div key={message.id} className="cw-msg-row">
                <div className="cw-msg-avatar">🤖</div>
                <div className="cw-msg cw-msg-assistant cw-markdown">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              </div>
            );
          }

          if (message.role === "system" && message.content === "loading") {
            return (
              <div key={message.id} className="cw-msg-row">
                <div className="cw-msg-avatar">🤖</div>
                <div className="cw-msg cw-msg-assistant">
                  <div className="cw-loading-dots">
                    <div className="cw-dot"></div>
                    <div className="cw-dot"></div>
                    <div className="cw-dot"></div>
                  </div>
                </div>
              </div>
            );
          }

          return null;
        })}

        {/* Agent Status */}
        {currentAgent && <div className="cw-agent-status">{currentAgent}</div>}

        {/* Metrics Panel */}
        {lastMetrics && (
          <div className="cw-metrics-panel">
            <button
              className="cw-metrics-toggle"
              onClick={() => setShowMetrics(!showMetrics)}
            >
              {showMetrics ? "▼" : "▶"} Response Metrics
            </button>
            {showMetrics && (
              <div className="cw-metrics-content">
                {/* Overall Metrics */}
                <div className="cw-metrics-section">
                  <h4 className="cw-metrics-section-title">Overall</h4>
                  <div className="cw-metric-row">
                    <span className="cw-metric-label">Query Type:</span>
                    <span className="cw-metric-value">{lastMetrics.query_type}</span>
                  </div>
                  <div className="cw-metric-row">
                    <span className="cw-metric-label">Confidence:</span>
                    <span
                      className={`cw-metric-value ${
                        lastMetrics.confidence >= 0.7
                          ? "cw-metric-good"
                          : "cw-metric-warning"
                      }`}
                    >
                      {(lastMetrics.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  {lastMetrics.total_duration_ms !== undefined && (
                    <div className="cw-metric-row">
                      <span className="cw-metric-label">Total Duration:</span>
                      <span className="cw-metric-value">
                        {lastMetrics.total_duration_ms}ms
                      </span>
                    </div>
                  )}
                </div>

                {/* Per-Agent Performance */}
                <div className="cw-metrics-section">
                  <h4 className="cw-metrics-section-title">Per-Agent Performance</h4>
                  {lastAgentFlow.map((agent, idx) => (
                    <div key={idx} className="cw-agent-metric-card">
                      <div className="cw-agent-metric-header">
                        <span className="cw-agent-icon">{agent.icon}</span>
                        <span className="cw-agent-name">{agent.name}</span>
                      </div>
                      <div className="cw-agent-metric-details">
                        {agent.confidence !== undefined && (
                          <div className="cw-agent-metric-item">
                            <span>Confidence:</span>
                            <span
                              className={
                                agent.confidence >= 0.7
                                  ? "cw-metric-good"
                                  : "cw-metric-warning"
                              }
                            >
                              {(agent.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {agent.rag_docs !== undefined && (
                          <div className="cw-agent-metric-item">
                            <span>RAG Documents:</span>
                            <span>{agent.rag_docs}</span>
                          </div>
                        )}
                        {agent.duration && (
                          <div className="cw-agent-metric-item">
                            <span>Duration:</span>
                            <span>{agent.duration}ms</span>
                          </div>
                        )}
                        {agent.ttft_ms && (
                          <div className="cw-agent-metric-item">
                            <span>Time to First Token:</span>
                            <span>{agent.ttft_ms}ms</span>
                          </div>
                        )}
                        {agent.tokens && (
                          <div className="cw-agent-metric-item">
                            <span>Tokens:</span>
                            <span>
                              {agent.tokens.input}/{agent.tokens.output}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Judge Evaluation */}
                {(lastMetrics.accuracy_score !== undefined ||
                  lastMetrics.coherence_score !== undefined) && (
                  <div className="cw-metrics-section">
                    <h4 className="cw-metrics-section-title">Judge Evaluation</h4>
                    {lastMetrics.accuracy_score !== undefined && (
                      <div className="cw-metric-row">
                        <span className="cw-metric-label">Accuracy:</span>
                        <span
                          className={`cw-metric-value ${
                            lastMetrics.accuracy_score >= 0.8
                              ? "cw-metric-good"
                              : "cw-metric-bad"
                          }`}
                        >
                          {(lastMetrics.accuracy_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {lastMetrics.coherence_score !== undefined && (
                      <div className="cw-metric-row">
                        <span className="cw-metric-label">Coherence:</span>
                        <span
                          className={`cw-metric-value ${
                            lastMetrics.coherence_score >= 0.7
                              ? "cw-metric-good"
                              : "cw-metric-bad"
                          }`}
                        >
                          {(lastMetrics.coherence_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}

                    {/* Judge Reasoning Dropdown */}
                    {(lastMetrics.accuracy_reasoning ||
                      lastMetrics.coherence_reasoning) && (
                      <>
                        <button
                          className="cw-eval-toggle"
                          onClick={() => setShowEvalReasoning(!showEvalReasoning)}
                        >
                          {showEvalReasoning ? "▼" : "▶"} Judge Reasoning
                        </button>
                        {showEvalReasoning && (
                          <div className="cw-eval-reasoning-content">
                            {lastMetrics.accuracy_reasoning && (
                              <div className="cw-eval-reasoning-item">
                                <h5>Accuracy Reasoning</h5>
                                <p>{lastMetrics.accuracy_reasoning}</p>
                                {lastMetrics.accuracy_issues &&
                                  lastMetrics.accuracy_issues.length > 0 && (
                                    <div className="cw-eval-issues">
                                      <strong>Issues Found:</strong>
                                      <ul>
                                        {lastMetrics.accuracy_issues.map(
                                          (issue: string, idx: number) => (
                                            <li key={idx}>{issue}</li>
                                          )
                                        )}
                                      </ul>
                                    </div>
                                  )}
                              </div>
                            )}
                            {lastMetrics.coherence_reasoning && (
                              <div className="cw-eval-reasoning-item">
                                <h5>Coherence Reasoning</h5>
                                <p>{lastMetrics.coherence_reasoning}</p>
                                {lastMetrics.coherence_issues &&
                                  lastMetrics.coherence_issues.length > 0 && (
                                    <div className="cw-eval-issues">
                                      <strong>Issues Found:</strong>
                                      <ul>
                                        {lastMetrics.coherence_issues.map(
                                          (issue: string, idx: number) => (
                                            <li key={idx}>{issue}</li>
                                          )
                                        )}
                                      </ul>
                                    </div>
                                  )}
                              </div>
                            )}
                            {lastMetrics.judge_model_name && (
                              <div className="cw-judge-info">
                                <small>
                                  Judge Model: {lastMetrics.judge_model_name} | Tokens:{" "}
                                  {lastMetrics.judge_input_tokens}/
                                  {lastMetrics.judge_output_tokens}
                                </small>
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form className="cw-footer" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className="cw-input"
          placeholder="Type your question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="cw-send-btn"
          disabled={isLoading || !input.trim()}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
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
      </form>
    </div>
  );
};

export default ChatWidget;
