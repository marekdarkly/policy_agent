import { useState, useEffect, useRef, useMemo } from 'react';
import './Terminal.css';

// ============================================================================
// Types
// ============================================================================

type NodeKind = 'triage' | 'policy' | 'provider' | 'scheduler' | 'brand';
type NodeState = 'running' | 'complete' | 'blocked' | 'healed';

interface RAGState {
  active: boolean;
  count: number;
  scores: number[];
}

interface FallbackInfo {
  state: 'pending' | 'running' | 'complete';
  variation?: string;
  model?: string;
  durationMs?: number;
  inputTokens?: number;
  outputTokens?: number;
  costCents?: number;
}

interface GuardrailInfo {
  policyType?: string;
  filterType?: string;
  fallback?: FallbackInfo;
}

interface AgentNode {
  id: number;
  kind: NodeKind;
  label: string;
  state: NodeState;
  model?: string;
  startedAt: number;
  inputTokens?: number;
  outputTokens?: number;
  costCents?: number;
  durationMs?: number;
  rag?: RAGState;
  guardrail?: GuardrailInfo;
}

interface RunSession {
  id: number;
  query?: string;
  startedAt: number;
  nodes: AgentNode[];
  totalDurationMs?: number;
  agentCount?: number;
  responseChars?: number;
  accuracy?: string;
  coherence?: string;
  finished: boolean;
}

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  name: string;
}

// ============================================================================
// Helpers
// ============================================================================

function stripEmojis(text: string): string {
  return text
    .replace(
      /[\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}\u{FE00}-\u{FE0F}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/gu,
      ''
    )
    .replace(/[─━│┃┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬]/g, '')
    .replace(/={4,}/g, '')
    .replace(/-{4,}/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

function shortenModel(id?: string): string {
  if (!id) return '';
  // us.anthropic.claude-haiku-4-5-20251001-v1:0  →  claude-haiku-4-5
  // meta.llama4-maverick-...                      →  llama4-maverick
  const m = id.match(
    /(claude-[a-z0-9-]+?(?:-\d-\d)?|llama[\d.\-a-z]*?(?:-[a-z]+)?|nova-[a-z]+|gpt-[\d.\-a-z]+|mistral-[a-z0-9-]+)/i
  );
  let name = m ? m[1] : id.split(/[.:/]/).pop() || id;
  name = name.replace(/-\d{8}.*$/, '').replace(/-v\d+(:\d+)?$/i, '');
  return name;
}

function fmtMs(ms?: number): string {
  if (ms == null) return '';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function fmtTokens(input?: number, output?: number): string {
  const i = input ?? 0;
  const o = output ?? 0;
  const total = i + o;
  if (total >= 1000) return `${(total / 1000).toFixed(1)}k tok`;
  return `${total} tok`;
}

function fmtCost(cents?: number): string {
  if (cents == null) return '';
  if (cents < 1) return `${cents.toFixed(2)}¢`;
  if (cents < 100) return `${cents.toFixed(1)}¢`;
  return `$${(cents / 100).toFixed(2)}`;
}

const KIND_LABEL: Record<NodeKind, string> = {
  triage: 'Triage',
  policy: 'Policy Specialist',
  provider: 'Provider Specialist',
  scheduler: 'Scheduler',
  brand: 'Brand Voice',
};

// ============================================================================
// Parser → updates RunSession[]
// ============================================================================

const PAT = {
  agentStart: {
    triage: /^TRIAGE AGENT:/i,
    policy: /^POLICY SPECIALIST:/i,
    provider: /^PROVIDER SPECIALIST:/i,
    scheduler: /^SCHEDULER AGENT:/i,
    brand: /^BRAND VOICE AGENT:/i,
  } as Record<NodeKind, RegExp>,
  modelPicked:
    /^(Triage|Policy|Provider|Scheduler|Brand Voice) Agent pulled from LaunchDarkly\s*[-–—]?\s*using\s+(\S+)/i,
  ragRetrievingTopic: /^Retrieving (policy|provider) documents via RAG/i,
  ragRetrievingKB: /^Retrieving from Bedrock KB/i,
  ragGotDocs: /^Retrieved\s+(\d+)\s+documents\s+\(top score:\s+([\d.]+)\)/i,
  ragFinalPolicy: /^Retrieved\s+(\d+)\s+policy documents from Bedrock KB$/i,
  ragFinalProvider: /^Using\s+(\d+)\s+provider documents from Bedrock KB$/i,
  ragDoc: /^Doc\s+(\d+):\s+Score\s+([\d.]+)/i,
  agentCost:
    /^(Triage|Policy|Provider|Scheduler|Brand)\s+agent\s+cost:\s+([\d.]+)¢?\s*\(\$([\d.]+)\)\s*\[in=(\d+),\s*out=(\d+),\s*model=([^\]]+)\]/i,
  agentDuration: /^(Triage|Policy|Provider|Scheduler|Brand)?\s*agent\s+duration:\s+(\d+)\s*ms/i,
  blocked: /^Response blocked due to policy violation/i,
  policyTypeLine: /^Policy Type:\s+(.+)$/i,
  filterTypeLine: /^Filter Type:\s+(.+)$/i,
  selfHealing: /^SELF-HEALING:\s*Guardrail intervention detected/i,
  fallbackVariation: /^LaunchDarkly returned variation:\s+'([^']+)'/i,
  fallbackGenerating: /^Generating response with fallback variation/i,
  selfHealingSuccess: /^Self-healing succeeded/i,
  fallbackDuration: /^Fallback duration:\s+(\d+)ms/i,
  chatRequest: /^\[([^\]]{6,})\]\s+Chat request:\s+(.+?)(\.\.\.)?$/,
  responseGenerated:
    /^\[([^\]]+)\]\s+Response generated:\s+(\d+)\s+chars,\s+(\d+)\s+agents,\s+(\d+)\s*ms/,
  accuracyLine: /^\[([^\]]+)\]?\s*Accuracy:\s+(.+)$/i,
  coherenceLine: /^\[([^\]]+)\]?\s*Coherence:\s+(.+)$/i,
};

let nodeIdCounter = 0;
let runIdCounter = 0;

function emptyRun(): RunSession {
  return {
    id: ++runIdCounter,
    startedAt: Date.now(),
    nodes: [],
    finished: false,
  };
}

// Returns the active (last unfinished) run, creating one if needed
function getOrCreateActiveRun(runs: RunSession[]): {
  runs: RunSession[];
  active: RunSession;
} {
  if (runs.length > 0 && !runs[runs.length - 1].finished) {
    return { runs, active: runs[runs.length - 1] };
  }
  const r = emptyRun();
  return { runs: [...runs, r], active: r };
}

function lastNodeOf(run: RunSession, kind?: NodeKind): AgentNode | undefined {
  for (let i = run.nodes.length - 1; i >= 0; i--) {
    if (!kind || run.nodes[i].kind === kind) return run.nodes[i];
  }
  return undefined;
}

function applyLog(runs: RunSession[], raw: string): RunSession[] {
  const msg = stripEmojis(raw);
  if (!msg) return runs;

  // ---- Run boundaries ----
  let m = msg.match(PAT.chatRequest);
  if (m) {
    // Always start a fresh run
    const fresh = emptyRun();
    fresh.query = m[2];
    return [...runs, fresh];
  }

  m = msg.match(PAT.responseGenerated);
  if (m) {
    const next = [...runs];
    if (next.length > 0) {
      const r = { ...next[next.length - 1] };
      r.responseChars = parseInt(m[2], 10);
      r.agentCount = parseInt(m[3], 10);
      r.totalDurationMs = parseInt(m[4], 10);
      r.finished = true;
      r.nodes = r.nodes.map((n) =>
        n.state === 'running'
          ? { ...n, state: 'complete' as NodeState, durationMs: n.durationMs ?? Date.now() - n.startedAt }
          : n
      );
      next[next.length - 1] = r;
    }
    return next;
  }

  m = msg.match(PAT.accuracyLine);
  if (m && runs.length > 0) {
    const next = [...runs];
    const r = { ...next[next.length - 1] };
    r.accuracy = m[2].trim();
    next[next.length - 1] = r;
    return next;
  }
  m = msg.match(PAT.coherenceLine);
  if (m && runs.length > 0) {
    const next = [...runs];
    const r = { ...next[next.length - 1] };
    r.coherence = m[2].trim();
    next[next.length - 1] = r;
    return next;
  }

  // ---- Agent start (creates a node) ----
  for (const kind of Object.keys(PAT.agentStart) as NodeKind[]) {
    if (PAT.agentStart[kind].test(msg)) {
      const { runs: r1, active } = getOrCreateActiveRun(runs);
      // Defensive: any still-running nodes from prior steps get marked complete
      // so the shimmer never gets stuck if a cost line is missed.
      const closedNodes = active.nodes.map((n) =>
        n.state === 'running'
          ? { ...n, state: 'complete' as NodeState, durationMs: n.durationMs ?? Date.now() - n.startedAt }
          : n
      );
      const node: AgentNode = {
        id: ++nodeIdCounter,
        kind,
        label: KIND_LABEL[kind],
        state: 'running',
        startedAt: Date.now(),
      };
      if (kind === 'policy' || kind === 'provider') {
        node.rag = { active: false, count: 0, scores: [] };
      }
      const updated = { ...active, nodes: [...closedNodes, node] };
      const next = [...r1];
      next[next.length - 1] = updated;
      return next;
    }
  }

  // ---- Model picked ----
  m = msg.match(PAT.modelPicked);
  if (m && runs.length > 0) {
    const role = m[1].toLowerCase();
    const model = shortenModel(m[2]);
    const kindMap: Record<string, NodeKind> = {
      triage: 'triage',
      policy: 'policy',
      provider: 'provider',
      scheduler: 'scheduler',
      'brand voice': 'brand',
    };
    const kind = kindMap[role];
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, kind);
    if (node && !node.model) {
      node.model = model;
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  // ---- RAG events ----
  if (PAT.ragRetrievingTopic.test(msg) || PAT.ragRetrievingKB.test(msg)) {
    if (runs.length === 0) return runs;
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run);
    if (node && (node.kind === 'policy' || node.kind === 'provider') && node.rag) {
      node.rag = { ...node.rag, active: true };
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  m = msg.match(PAT.ragGotDocs);
  if (m && runs.length > 0) {
    const count = parseInt(m[1], 10);
    const top = parseFloat(m[2]);
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run);
    if (node && node.rag) {
      node.rag = { active: false, count, scores: [top] };
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  m = msg.match(PAT.ragDoc);
  if (m && runs.length > 0) {
    const score = parseFloat(m[2]);
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run);
    if (node && node.rag) {
      node.rag = {
        ...node.rag,
        scores: [...node.rag.scores, score],
      };
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  m = msg.match(PAT.ragFinalPolicy) || msg.match(PAT.ragFinalProvider);
  if (m && runs.length > 0) {
    const count = parseInt(m[1], 10);
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run);
    if (node && node.rag) {
      node.rag = { ...node.rag, active: false, count };
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  // ---- Cost / completion ----
  m = msg.match(PAT.agentCost);
  if (m && runs.length > 0) {
    const role = m[1].toLowerCase();
    const cents = parseFloat(m[2]);
    const inTok = parseInt(m[4], 10);
    const outTok = parseInt(m[5], 10);
    const model = shortenModel(m[6]);
    const kindMap: Record<string, NodeKind> = {
      triage: 'triage',
      policy: 'policy',
      provider: 'provider',
      scheduler: 'scheduler',
      brand: 'brand',
    };
    const kind = kindMap[role];
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, kind);
    if (node) {
      node.inputTokens = inTok;
      node.outputTokens = outTok;
      node.costCents = cents;
      if (!node.model) node.model = model;

      // Brand cost when fallback active → assign to fallback
      if (kind === 'brand' && node.guardrail?.fallback) {
        node.guardrail.fallback.inputTokens = inTok;
        node.guardrail.fallback.outputTokens = outTok;
        node.guardrail.fallback.costCents = cents;
        if (!node.guardrail.fallback.model) {
          node.guardrail.fallback.model = model;
        }
        if (node.guardrail.fallback.state !== 'complete') {
          node.guardrail.fallback.state = 'complete';
        }
        node.state = 'healed';
      } else {
        node.state = 'complete';
        node.durationMs = Date.now() - node.startedAt;
      }
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  m = msg.match(PAT.agentDuration);
  if (m && runs.length > 0) {
    const ms = parseInt(m[2], 10);
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run);
    if (node) {
      node.durationMs = ms;
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  // ---- Guardrail block ----
  if (PAT.blocked.test(msg) && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node) {
      node.state = 'blocked';
      node.guardrail = { ...(node.guardrail || {}) };
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  m = msg.match(PAT.policyTypeLine);
  if (m && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node && node.guardrail) {
      node.guardrail.policyType = m[1].trim();
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }
  m = msg.match(PAT.filterTypeLine);
  if (m && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node && node.guardrail) {
      node.guardrail.filterType = m[1].trim();
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  // ---- Self-healing fallback ----
  if (PAT.selfHealing.test(msg) && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node) {
      node.guardrail = node.guardrail || {};
      node.guardrail.fallback = { state: 'pending' };
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  m = msg.match(PAT.fallbackVariation);
  if (m && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node?.guardrail?.fallback) {
      node.guardrail.fallback.variation = m[1];
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  if (PAT.fallbackGenerating.test(msg) && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node?.guardrail?.fallback) {
      node.guardrail.fallback.state = 'running';
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  m = msg.match(PAT.fallbackDuration);
  if (m && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node?.guardrail?.fallback) {
      node.guardrail.fallback.durationMs = parseInt(m[1], 10);
      node.guardrail.fallback.state = 'complete';
      node.state = 'healed';
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  if (PAT.selfHealingSuccess.test(msg) && runs.length > 0) {
    const next = [...runs];
    const run = { ...next[next.length - 1] };
    const node = lastNodeOf(run, 'brand');
    if (node?.guardrail?.fallback) {
      node.guardrail.fallback.state = 'complete';
      node.state = 'healed';
      run.nodes = [...run.nodes];
      next[next.length - 1] = run;
    }
    return next;
  }

  return runs;
}

// ============================================================================
// Component
// ============================================================================

export default function Terminal() {
  const [runs, setRuns] = useState<RunSession[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const eventSource = new EventSource('/api/logs/stream');
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => setIsConnected(true);
    eventSource.onmessage = (event) => {
      try {
        const entry: LogEntry = JSON.parse(event.data);
        if (entry.level === 'HEARTBEAT') return;
        setRuns((prev) => applyLog(prev, entry.message));
      } catch (err) {
        console.error('Failed to parse log entry:', err);
      }
    };
    eventSource.onerror = () => setIsConnected(false);

    return () => eventSource.close();
  }, []);

  useEffect(() => {
    if (!isCollapsed) {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [runs, isCollapsed]);

  const clearRuns = () => setRuns([]);

  const visibleRuns = useMemo(
    () => runs.slice(-10),
    [runs]
  );

  if (isCollapsed) {
    return (
      <div className="terminal-collapsed">
        <button
          className="terminal-expand-btn"
          onClick={() => setIsCollapsed(false)}
        >
          <span className="terminal-icon">&gt;_</span>
          <span>Pipeline</span>
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
          <span>Pipeline</span>
          <span
            className={`status-indicator ${
              isConnected ? 'connected' : 'disconnected'
            }`}
          ></span>
        </div>
        <div className="terminal-actions">
          <button
            className="terminal-btn"
            onClick={clearRuns}
            title="Clear"
          >
            Clear
          </button>
          <button
            className="terminal-btn"
            onClick={() => setIsCollapsed(true)}
            title="Collapse"
          >
            ◀
          </button>
        </div>
      </div>

      <div className="terminal-content" ref={scrollRef}>
        {visibleRuns.length === 0 ? (
          <div className="terminal-empty">
            <div className="empty-glyph">◍</div>
            <div className="empty-text">awaiting query</div>
            {!isConnected && (
              <div className="empty-error">disconnected from server</div>
            )}
          </div>
        ) : (
          visibleRuns.map((run) => <RunCard key={run.id} run={run} />)
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Subcomponents
// ============================================================================

function RunCard({ run }: { run: RunSession }) {
  const totalCostCents = run.nodes.reduce(
    (acc, n) => acc + (n.costCents ?? 0) + (n.guardrail?.fallback?.costCents ?? 0),
    0
  );
  const totalTokens = run.nodes.reduce(
    (acc, n) =>
      acc +
      (n.inputTokens ?? 0) +
      (n.outputTokens ?? 0) +
      (n.guardrail?.fallback?.inputTokens ?? 0) +
      (n.guardrail?.fallback?.outputTokens ?? 0),
    0
  );

  return (
    <div className={`run-card ${run.finished ? 'finished' : 'live'}`}>
      <div className="run-header">
        <div className="run-marker"></div>
        <div className="run-query">
          {run.query ? truncate(run.query, 80) : 'incoming…'}
        </div>
      </div>

      <div className="run-rail">
        {run.nodes.map((node, i) => (
          <NodeCard
            key={node.id}
            node={node}
            isLast={i === run.nodes.length - 1}
          />
        ))}
      </div>

      {run.finished && (
        <div className="run-footer">
          <span className="run-stat">
            <span className="run-stat-label">total</span>
            <span className="run-stat-value">{fmtMs(run.totalDurationMs)}</span>
          </span>
          <span className="run-divider">·</span>
          <span className="run-stat">
            <span className="run-stat-value">
              {totalTokens >= 1000
                ? `${(totalTokens / 1000).toFixed(1)}k`
                : totalTokens}{' '}
              tok
            </span>
          </span>
          <span className="run-divider">·</span>
          <span className="run-stat">
            <span className="run-stat-value">{fmtCost(totalCostCents)}</span>
          </span>
          {(run.accuracy || run.coherence) && (
            <>
              <span className="run-divider">·</span>
              {run.accuracy && (
                <span className="run-eval">acc {run.accuracy}</span>
              )}
              {run.coherence && (
                <span className="run-eval">coh {run.coherence}</span>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function NodeCard({ node, isLast }: { node: AgentNode; isLast: boolean }) {
  return (
    <div className={`node-card state-${node.state} kind-${node.kind}`}>
      <div className="node-row">
        <NodeStatusGlyph state={node.state} />
        <div className="node-main">
          <div className="node-title-row">
            <span className="node-title">{node.label}</span>
            <NodeStateBadge state={node.state} />
          </div>
          {node.model && (
            <div className="node-model">
              <span className="node-model-mark">▸</span>
              {node.model}
            </div>
          )}

          {node.rag && (node.rag.active || node.rag.count > 0) && (
            <RAGStrip rag={node.rag} />
          )}

          {node.state === 'complete' && (
            <NodeStats
              tokens={fmtTokens(node.inputTokens, node.outputTokens)}
              cost={fmtCost(node.costCents)}
              dur={fmtMs(node.durationMs)}
            />
          )}

          {node.state === 'running' && !node.rag && <RunningShimmer />}
          {node.state === 'running' && node.rag && !node.rag.active && node.rag.count > 0 && (
            <RunningShimmer />
          )}
        </div>
      </div>

      {node.guardrail && <GuardrailStrip g={node.guardrail} />}

      {!isLast && <div className="node-connector" />}
    </div>
  );
}

function NodeStatusGlyph({ state }: { state: NodeState }) {
  if (state === 'running') {
    return (
      <div className="node-glyph running">
        <span className="pulse-dot" />
      </div>
    );
  }
  if (state === 'complete') {
    return (
      <div className="node-glyph complete">
        <span>✓</span>
      </div>
    );
  }
  if (state === 'blocked') {
    return (
      <div className="node-glyph blocked">
        <span>!</span>
      </div>
    );
  }
  if (state === 'healed') {
    return (
      <div className="node-glyph healed">
        <span>✓</span>
      </div>
    );
  }
  return (
    <div className="node-glyph">
      <span>·</span>
    </div>
  );
}

function NodeStateBadge({ state }: { state: NodeState }) {
  const text =
    state === 'running'
      ? 'running'
      : state === 'complete'
      ? 'done'
      : state === 'blocked'
      ? 'blocked'
      : state === 'healed'
      ? 'healed'
      : '';
  return <span className={`state-badge ${state}`}>{text}</span>;
}

function NodeStats({
  tokens,
  cost,
  dur,
}: {
  tokens: string;
  cost: string;
  dur: string;
}) {
  return (
    <div className="node-stats">
      <span className="stat">{tokens}</span>
      {cost && (
        <>
          <span className="stat-sep">·</span>
          <span className="stat">{cost}</span>
        </>
      )}
      {dur && (
        <>
          <span className="stat-sep">·</span>
          <span className="stat">{dur}</span>
        </>
      )}
    </div>
  );
}

function RunningShimmer() {
  return (
    <div className="shimmer-row">
      <div className="shimmer-bar" />
    </div>
  );
}

function RAGStrip({ rag }: { rag: RAGState }) {
  if (rag.active && rag.count === 0) {
    return (
      <div className="rag-strip active">
        <div className="rag-label">RAG</div>
        <div className="rag-shimmer">
          <span className="rag-pulse" />
          <span className="rag-pulse" />
          <span className="rag-pulse" />
          <span className="rag-pulse" />
          <span className="rag-pulse" />
        </div>
      </div>
    );
  }
  if (rag.count > 0) {
    const shown = Math.min(rag.count, 12);
    return (
      <div className="rag-strip done">
        <div className="rag-label">RAG</div>
        <div className="rag-chips">
          {Array.from({ length: shown }).map((_, i) => {
            const score = rag.scores[i];
            const intensity = score != null ? Math.max(0.35, Math.min(1, score)) : 0.7;
            return (
              <span
                key={i}
                className="rag-chip"
                style={{
                  opacity: intensity,
                  animationDelay: `${i * 35}ms`,
                }}
                title={score != null ? `score ${score.toFixed(3)}` : undefined}
              />
            );
          })}
        </div>
        <div className="rag-count">{rag.count}</div>
      </div>
    );
  }
  return null;
}

function GuardrailStrip({ g }: { g: GuardrailInfo }) {
  return (
    <div className="guardrail-block">
      <div className="guardrail-divider" />
      <div className="guardrail-block-row">
        <div className="guardrail-icon">⊘</div>
        <div className="guardrail-content">
          <div className="guardrail-title">guardrail intervened</div>
          <div className="guardrail-meta">
            {g.policyType && <span className="gr-tag">{g.policyType}</span>}
            {g.filterType && <span className="gr-tag mono">{g.filterType}</span>}
          </div>
        </div>
      </div>

      {g.fallback && (
        <>
          <div className="fallback-arrow">
            <span>↓</span>
            <span className="fallback-arrow-label">fallback</span>
          </div>
          <div className={`fallback-card state-${g.fallback.state}`}>
            <div className="fallback-row">
              <div className="fallback-icon">
                {g.fallback.state === 'complete' ? '✓' : '↺'}
              </div>
              <div className="fallback-main">
                <div className="fallback-title">
                  Safe Fallback
                  {g.fallback.variation && (
                    <span className="fallback-variation">
                      {g.fallback.variation}
                    </span>
                  )}
                </div>
                {g.fallback.model && (
                  <div className="node-model">
                    <span className="node-model-mark">▸</span>
                    {g.fallback.model}
                  </div>
                )}
                {g.fallback.state === 'running' && <RunningShimmer />}
                {g.fallback.state === 'complete' && (
                  <NodeStats
                    tokens={fmtTokens(
                      g.fallback.inputTokens,
                      g.fallback.outputTokens
                    )}
                    cost={fmtCost(g.fallback.costCents)}
                    dur={fmtMs(g.fallback.durationMs)}
                  />
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return s.slice(0, n - 1) + '…';
}
