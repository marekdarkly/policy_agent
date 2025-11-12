import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
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
  duration?: number;
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
  const [showEvalReasoning, setShowEvalReasoning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContentRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAgent]);

  const pollForEvaluation = async (requestId: string) => {
    // Poll for evaluation results up to 20 times (max 10 seconds)
    const maxAttempts = 20;
    let attempts = 0;

    console.log(`🔍 Starting evaluation polling for request_id: ${requestId}`);

    const poll = async () => {
      if (attempts >= maxAttempts) {
        console.log('⚠️  Evaluation polling timed out after 10 seconds');
        return;
      }

      attempts++;
      console.log(`📊 Polling attempt ${attempts}/${maxAttempts} for evaluation...`);

      try {
        const response = await fetch(`http://localhost:8000/api/evaluation/${requestId}`);
        const data = await response.json();

        console.log(`📋 Polling response:`, data);

        if (data.ready && data.evaluation) {
          console.log(`✅ Evaluation ready!`, data.evaluation);
          
          // Update metrics with evaluation results
          setLastMetrics((prev) => {
            if (!prev) {
              console.warn('⚠️  No previous metrics to update');
              return prev;
            }
            
            const updated = {
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
            
            console.log('📊 Updated metrics:', updated);
            return updated;
          });
          
          console.log('✅ Evaluation results received and metrics updated!');
        } else {
          // Not ready yet, try again
          console.log(`⏳ Evaluation not ready yet (attempt ${attempts}/${maxAttempts})`);
          setTimeout(poll, 500); // Poll every 500ms
        }
      } catch (error) {
        console.error('❌ Error polling for evaluation:', error);
        if (attempts < maxAttempts) {
          setTimeout(poll, 500);
        }
      }
    };

    // Start polling after a short delay (evaluation needs time to start)
    setTimeout(poll, 1000);
  };

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

    // Start progressive agent status updates
    setCurrentAgent('🔍 Analyzing your question...');
    
    // Set up estimated timing for status updates (will update with actual timing when response arrives)
    const triageTimer = setTimeout(() => setCurrentAgent('📋 Looking up your policy...'), 2000);
    const brandTimer = setTimeout(() => setCurrentAgent('✨ Writing up my thoughts...'), 10000);

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

      // Clear the estimated timers
      clearTimeout(triageTimer);
      clearTimeout(brandTimer);

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      // Now use actual agent flow to show final status updates
      if (data.agentFlow.length > 1) {
        const specialist = data.agentFlow.find(a => a.agent.includes('specialist'));
        if (specialist) {
          setCurrentAgent(`${specialist.icon} Finalizing with ${specialist.name}...`);
          await new Promise((resolve) => setTimeout(resolve, 400));
        }
      }

      // Show brand voice status if present
      const brandVoice = data.agentFlow.find((a) => a.agent === 'brand_voice');
      if (brandVoice) {
        setCurrentAgent('✨ Polishing the response...');
        await new Promise((resolve) => setTimeout(resolve, 300));
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

      // Start polling for evaluation results (async, non-blocking)
      pollForEvaluation(data.requestId);

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
    <>
      {/* Background Images */}
      <div className="homepage-background">
        <img
          src="/health/backgrounds/health-homepage-background-left.svg"
          alt=""
          className="bg-left"
        />
        <img
          src="/health/backgrounds/health-homepage-background-right.svg"
          alt=""
          className="bg-right"
        />
      </div>

      {/* Main Page Content */}
      <div className="homepage-wrapper">
        {/* Navigation Header */}
        <nav className="health-nav">
          <img
            src="/health/toggleHealth_logo_horizontal.svg"
            alt="ToggleHealth"
            className="nav-logo"
          />
          <div className="nav-links">
            <a href="#services">Services</a>
            <a href="#about">About</a>
            <a href="#contact">Contact</a>
          </div>
        </nav>

        {/* Hero Section */}
        <header className="hero-section">
          <img
            src="/health/backgrounds/health-hero-background-pills.svg"
            alt=""
            className="hero-bg-pills"
          />
          <img
            src="/health/backgrounds/health-hero-background-heart.svg"
            alt=""
            className="hero-bg-heart"
          />
          
          <div className="hero-content">
            <h1 className="hero-title">Your health, simplified with ToggleHealth</h1>
            <p className="hero-subtitle">Trusted by over 100,000 patients nationwide</p>
            <div className="hero-buttons">
              <button className="btn-primary">Get Started</button>
              <button className="btn-secondary">Learn More</button>
            </div>
          </div>
        </header>

        {/* Services Section */}
        <section className="services-section">
          <h2 className="services-title">OUR HEALTH SERVICES</h2>
          <div className="services-grid">
            <div className="service-item">
              <div className="service-icon">
                <img src="/health/icons/prescriptions.svg" alt="Prescriptions" />
              </div>
              <p>Prescriptions</p>
            </div>
            <div className="service-item">
              <div className="service-icon">
                <img src="/health/icons/telemedicine.svg" alt="Telemedicine" />
              </div>
              <p>Telemedicine</p>
            </div>
            <div className="service-item">
              <div className="service-icon">
                <img src="/health/icons/pharmacy.svg" alt="Pharmacy" />
              </div>
              <p>Pharmacy</p>
            </div>
            <div className="service-item">
              <div className="service-icon">
                <img src="/health/icons/wellness.svg" alt="Wellness" />
              </div>
              <p>Wellness</p>
            </div>
            <div className="service-item">
              <div className="service-icon">
                <img src="/health/icons/insurance.svg" alt="Insurance" />
              </div>
              <p>Insurance</p>
            </div>
          </div>
        </section>

        {/* Content Cards Section */}
        <section className="content-cards">
          <div className="card-row">
            <div className="card card-telemedicine">
              <span className="card-label">TELEMEDICINE</span>
              <h3>Virtual care at your fingertips</h3>
              <p>Connect with healthcare providers from the comfort of your home, anytime, anywhere.</p>
            </div>
            <div className="card card-wellness">
              <div className="card-text">
                <span className="card-label-gray">WELLNESS PROGRAMS</span>
                <h3 className="card-title-green">Preventive care & wellness</h3>
                <p className="card-description">Join our wellness programs designed to keep you healthy and active.</p>
              </div>
              <img
                src="/health/backgrounds/health-homepage-health-card-background.svg"
                alt=""
                className="card-image"
              />
            </div>
          </div>

          <div className="card-row">
            <div className="card card-offer">
              <span className="card-label-gray">SPECIAL OFFER</span>
              <h3 className="card-title-green">New patient discount</h3>
              <p className="card-description">Get 50% off your first consultation and prescription refill. Limited time offer.</p>
            </div>
            <div className="card card-offer-image">
              <img
                src="/health/backgrounds/health-homepage-specialoffer-background.svg"
                alt="Special Offer"
                className="offer-image"
              />
            </div>
          </div>
        </section>
      </div>

      {/* Floating Chat Widget */}
      <div className="app-container">
      {/* Header */}
      <header className="chat-header">
        <div className="header-content">
          <div className="header-text">
            <h2 className="chat-title">Coverage Concierge</h2>
            <p className="header-subtitle">
              Powered by <span className="provider-badge">Amazon Bedrock</span>
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
              <div key={message.id} className="message-row message-row-user">
                <div className="message message-user">
                  {message.content}
                </div>
              </div>
            );
          } else if (message.role === 'assistant') {
            return (
              <div key={message.id} className="message-row">
                <img src="/assets/ToggleAvatar.png" alt="" className="message-avatar" />
                <div className="message message-assistant markdown-content">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              </div>
            );
          } else if (message.role === 'system' && message.content === 'loading') {
            return (
              <div key={message.id} className="message-row">
                <img src="/assets/ToggleAvatar.png" alt="" className="message-avatar" />
                <div className="message message-assistant">
                  <div className="loading-dots">
                    <div className="dot"></div>
                    <div className="dot"></div>
                    <div className="dot"></div>
                  </div>
                </div>
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
                {/* Overall Metrics */}
                <div className="metrics-section">
                  <h4 className="metrics-section-title">Overall</h4>
                  <div className="metric-row">
                    <span className="metric-label">Query Type:</span>
                    <span className="metric-value">{lastMetrics.query_type}</span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">Confidence:</span>
                    <span className={`metric-value ${lastMetrics.confidence >= 0.7 ? 'metric-good' : 'metric-warning'}`}>
                      {(lastMetrics.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Per-Agent Metrics */}
                <div className="metrics-section">
                  <h4 className="metrics-section-title">Per-Agent Performance</h4>
                  {lastAgentFlow.map((agent, idx) => (
                    <div key={idx} className="agent-metric-card">
                      <div className="agent-metric-header">
                        <span className="agent-icon">{agent.icon}</span>
                        <span className="agent-name">{agent.name}</span>
                      </div>
                      <div className="agent-metric-details">
                        {agent.confidence !== undefined && (
                          <div className="agent-metric-item">
                            <span>Confidence:</span>
                            <span className={agent.confidence >= 0.7 ? 'metric-good' : 'metric-warning'}>
                              {(agent.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {agent.rag_docs !== undefined && (
                          <div className="agent-metric-item">
                            <span>RAG Documents:</span>
                            <span>{agent.rag_docs}</span>
                          </div>
                        )}
                        {agent.duration && (
                          <div className="agent-metric-item">
                            <span>Duration:</span>
                            <span>{agent.duration}ms</span>
                          </div>
                        )}
                        {agent.tokens && (
                          <div className="agent-metric-item">
                            <span>Tokens:</span>
                            <span>{agent.tokens.input}/{agent.tokens.output}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Judge Evaluation */}
                {(lastMetrics.accuracy_score !== undefined || lastMetrics.coherence_score !== undefined) && (
                  <div className="metrics-section">
                    <h4 className="metrics-section-title">Judge Evaluation</h4>
                    {lastMetrics.accuracy_score !== undefined && (
                      <div className="metric-row">
                        <span className="metric-label">Accuracy:</span>
                        <span className={`metric-value ${lastMetrics.accuracy_score >= 0.8 ? 'metric-good' : 'metric-bad'}`}>
                          {(lastMetrics.accuracy_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {lastMetrics.coherence_score !== undefined && (
                      <div className="metric-row">
                        <span className="metric-label">Coherence:</span>
                        <span className={`metric-value ${lastMetrics.coherence_score >= 0.7 ? 'metric-good' : 'metric-bad'}`}>
                          {(lastMetrics.coherence_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    
                    {/* Judge Reasoning Dropdown */}
                    {(lastMetrics.accuracy_reasoning || lastMetrics.coherence_reasoning) && (
                      <>
                        <button
                          className="metrics-subsection-toggle"
                          onClick={() => setShowEvalReasoning(!showEvalReasoning)}
                        >
                          {showEvalReasoning ? '▼' : '▶'} Judge Reasoning
                        </button>
                        {showEvalReasoning && (
                          <div className="eval-reasoning-content">
                            {lastMetrics.accuracy_reasoning && (
                              <div className="eval-reasoning-item">
                                <h5>Accuracy Reasoning</h5>
                                <p>{lastMetrics.accuracy_reasoning}</p>
                                {lastMetrics.accuracy_issues && lastMetrics.accuracy_issues.length > 0 && (
                                  <div className="eval-issues">
                                    <strong>Issues Found:</strong>
                                    <ul>
                                      {lastMetrics.accuracy_issues.map((issue: string, idx: number) => (
                                        <li key={idx}>{issue}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                            {lastMetrics.coherence_reasoning && (
                              <div className="eval-reasoning-item">
                                <h5>Coherence Reasoning</h5>
                                <p>{lastMetrics.coherence_reasoning}</p>
                                {lastMetrics.coherence_issues && lastMetrics.coherence_issues.length > 0 && (
                                  <div className="eval-issues">
                                    <strong>Issues Found:</strong>
                                    <ul>
                                      {lastMetrics.coherence_issues.map((issue: string, idx: number) => (
                                        <li key={idx}>{issue}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                            {lastMetrics.judge_model_name && (
                              <div className="judge-info">
                                <small>Judge Model: {lastMetrics.judge_model_name} | Tokens: {lastMetrics.judge_input_tokens}/{lastMetrics.judge_output_tokens}</small>
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
    </>
  );
}

export default App;

