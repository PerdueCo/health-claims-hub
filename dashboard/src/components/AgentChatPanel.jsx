/**
 * AgentChatPanel.jsx
 * AI chat interface - sends questions, shows AI responses with inline claims tables
 * Consumes agentService - swap to real LangGraph by updating agentService.js only
 */

import { useState, useRef, useEffect } from 'react';
import agentService from '../services/agentService';

const fmt$ = n => '$' + Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 0 });

const SUGGESTIONS = [
  { label: 'Explain Risk Factors',    prompt: 'Explain the risk factors for high-value pending claims', sub: 'Why are these flagged?' },
  { label: 'Show Denied Claims',      prompt: 'Show me high-value denied claims',                       sub: 'List denied claims > $5k' },
  { label: 'Summarize by Provider',   prompt: 'Summarize claims by provider with totals',               sub: 'Top providers by volume' },
  { label: 'Export Results',          prompt: 'How do I export these results as a CSV?',                sub: 'Download as CSV' },
];

const STATUS_STYLE = {
  PAID:    { background: '#f0fdf4', color: '#15803d' },
  DENIED:  { background: '#fef2f2', color: '#dc2626' },
  PENDING: { background: '#fffbeb', color: '#d97706' },
};

export default function AgentChatPanel({ claims, onStepsUpdate }) {
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState('');
  const [thinking, setThinking]   = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  const send = async (text) => {
    const q = (text || input).trim();
    if (!q) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setThinking(true);
    try {
      const res = await agentService.ask(q, claims);
      setMessages(prev => [...prev, { role: 'ai', content: res.answer, claims: res.claims || [], steps: res.steps || [] }]);
      if (onStepsUpdate && res.steps) onStepsUpdate(res.steps);
    } catch {
      setMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I could not connect to the agent. Make sure serve_dashboard.py is running.', claims: [] }]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <div style={styles.panel}>
      <div style={styles.chat}>
        {messages.length === 0 && (
          <div style={styles.empty}>
            <div style={styles.emptyIcon}>◈</div>
            <div style={styles.emptyTitle}>AI Claims Review Assistant</div>
            <div style={styles.emptySub}>Ask a question about your claims data</div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === 'user' ? (
              <div style={styles.userRow}>
                <div style={styles.userMsg}>{msg.content}</div>
              </div>
            ) : (
              <div style={styles.aiRow}>
                <div style={styles.aiAvatar}>◈</div>
                <div style={styles.aiCard}>
                  <div style={styles.aiText}>{msg.content}</div>
                  {msg.claims && msg.claims.length > 0 && (
                    <div style={styles.miniTable}>
                      <div style={styles.miniHead}>
                        <span>Claim ID</span><span>Provider</span><span>Amount</span><span>Status</span>
                      </div>
                      {msg.claims.slice(0, 8).map(c => (
                        <div key={c.claimId} style={styles.miniRow}>
                          <span style={{ color: '#1d4ed8', fontFamily: 'monospace', fontSize: 11 }}>{c.claimId}</span>
                          <span style={{ fontSize: 11, color: '#6b7280' }}>{c.provider}</span>
                          <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{fmt$(c.amountBilled)}</span>
                          <span style={{ ...styles.badge, ...STATUS_STYLE[c.status] }}>{c.status}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {thinking && (
          <div style={styles.aiRow}>
            <div style={styles.aiAvatar}>◈</div>
            <div style={styles.thinking}>
              <span style={styles.dot} /><span style={styles.dot} /><span style={styles.dot} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={styles.suggestions}>
        {SUGGESTIONS.map(s => (
          <button key={s.label} onClick={() => send(s.prompt)} style={styles.chip}>
            <div style={styles.chipTitle}>{s.label}</div>
            <div style={styles.chipSub}>{s.sub}</div>
          </button>
        ))}
      </div>

      <div style={styles.inputBar}>
        <input
          style={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask a question about your claims..."
          disabled={thinking}
        />
        <button onClick={() => send()} disabled={thinking || !input.trim()} style={styles.sendBtn}>
          ➤
        </button>
      </div>
    </div>
  );
}

const styles = {
  panel:      { display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' },
  chat:       { flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 },
  empty:      { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 40, color: '#9ca3af', textAlign: 'center' },
  emptyIcon:  { fontSize: 32, marginBottom: 12 },
  emptyTitle: { fontSize: 15, fontWeight: 500, color: '#374151', marginBottom: 4 },
  emptySub:   { fontSize: 12 },
  userRow:    { display: 'flex', justifyContent: 'flex-end' },
  userMsg:    { background: '#eff6ff', color: '#1e40af', padding: '8px 14px', borderRadius: '12px 12px 2px 12px', fontSize: 12, maxWidth: '80%', fontWeight: 500 },
  aiRow:      { display: 'flex', gap: 8, alignItems: 'flex-start' },
  aiAvatar:   { width: 28, height: 28, borderRadius: '50%', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1d4ed8', fontSize: 14, flexShrink: 0, marginTop: 2 },
  aiCard:     { background: '#fff', border: '0.5px solid #e5e7eb', borderRadius: 10, padding: 12, flex: 1, display: 'flex', flexDirection: 'column', gap: 10 },
  aiText:     { fontSize: 12, color: '#374151', lineHeight: 1.6 },
  miniTable:  { border: '0.5px solid #e5e7eb', borderRadius: 6, overflow: 'hidden', fontSize: 11 },
  miniHead:   { display: 'grid', gridTemplateColumns: '90px 1fr 80px 80px', gap: 8, padding: '6px 10px', background: '#f9fafb', color: '#9ca3af', fontSize: 10, textTransform: 'uppercase', letterSpacing: '.06em' },
  miniRow:    { display: 'grid', gridTemplateColumns: '90px 1fr 80px 80px', gap: 8, padding: '7px 10px', borderTop: '0.5px solid #f3f4f6', alignItems: 'center' },
  badge:      { display: 'inline-block', fontSize: 10, padding: '2px 6px', borderRadius: 20, fontWeight: 500 },
  thinking:   { display: 'flex', gap: 4, padding: '10px 14px', background: '#fff', border: '0.5px solid #e5e7eb', borderRadius: 10, alignItems: 'center' },
  dot:        { width: 6, height: 6, borderRadius: '50%', background: '#93c5fd', animation: 'pulse 1.4s ease-in-out infinite' },
  suggestions: { display: 'flex', gap: 6, padding: '8px 16px', flexWrap: 'wrap', borderTop: '0.5px solid #e5e7eb' },
  chip:       { background: '#f9fafb', border: '0.5px solid #e5e7eb', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', textAlign: 'left', transition: 'background .12s' },
  chipTitle:  { fontSize: 11, fontWeight: 500, color: '#374151' },
  chipSub:    { fontSize: 10, color: '#9ca3af', marginTop: 1 },
  inputBar:   { display: 'flex', gap: 8, padding: '10px 16px', borderTop: '0.5px solid #e5e7eb', background: '#fff', alignItems: 'center' },
  input:      { flex: 1, border: '0.5px solid #d1d5db', borderRadius: 8, padding: '7px 12px', fontSize: 12, background: '#f9fafb', color: '#111', outline: 'none' },
  sendBtn:    { width: 32, height: 32, borderRadius: 8, background: '#1d4ed8', border: 'none', cursor: 'pointer', color: '#fff', fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center' },
};
