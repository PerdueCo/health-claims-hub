/**
 * AgentSessionPanel.jsx
 * Right-side panel showing agent workflow steps, data sources, and related actions
 * Steps are passed as props from AgentChatPanel via parent state
 */

const DATA_SOURCES = [
  { name: 'MECP Claims API',   url: '/v1/resources/claims',                color: '#eff6ff', textColor: '#1d4ed8', icon: '⊕' },
  { name: 'SPARQL Endpoint',   url: 'localhost:7200/repositories/claims',   color: '#fffbeb', textColor: '#d97706', icon: '⬡' },
  { name: 'CORB Pipeline',     url: 'xcc://localhost:8041/roxy-content',    color: '#f0fdf4', textColor: '#15803d', icon: '⚙' },
];

const ACTIONS = [
  { label: 'Add to Review Queue',    icon: '⊟' },
  { label: 'Create Review Task',     icon: '⊕' },
  { label: 'Generate Summary Report', icon: '☰' },
];

const TABS = ['Summary', 'Steps', 'State', 'Feedback'];

export default function AgentSessionPanel({ steps, sessionId }) {
  const completed = steps.length > 0;

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>Agent Session</div>
          <div style={styles.sessionId}>Session ID: {sessionId || '—'}</div>
        </div>
        <button style={styles.newBtn}>New Session</button>
      </div>

      <div style={styles.tabs}>
        {TABS.map((t, i) => (
          <div key={t} style={{ ...styles.tab, ...(i === 0 ? styles.tabActive : {}) }}>{t}</div>
        ))}
      </div>

      <div style={styles.body}>
        {completed && (
          <div style={styles.statusCard}>
            <span style={styles.checkIcon}>✓</span>
            <div style={{ flex: 1 }}>
              <div style={styles.statusLabel}>Completed</div>
              <div style={styles.statusSub}>The agent has completed {steps.length} steps.</div>
            </div>
          </div>
        )}

        {!completed && (
          <div style={styles.idle}>
            <div style={styles.idleText}>No active session</div>
            <div style={styles.idleSub}>Ask a question to start the agent</div>
          </div>
        )}

        {steps.length > 0 && (
          <div>
            <div style={styles.sectionTitle}>Steps executed</div>
            {steps.map((step, i) => (
              <div key={i} style={styles.stepRow}>
                <div style={styles.stepCheck}>✓</div>
                <div style={styles.stepLabel}>{step.label}</div>
                <div style={styles.stepTime}>{step.time}</div>
              </div>
            ))}
          </div>
        )}

        <div>
          <div style={styles.sectionTitle}>Data sources</div>
          {DATA_SOURCES.map(ds => (
            <div key={ds.name} style={styles.dsCard}>
              <div style={{ ...styles.dsIcon, background: ds.color, color: ds.textColor }}>{ds.icon}</div>
              <div>
                <div style={styles.dsName}>{ds.name}</div>
                <div style={styles.dsUrl}>{ds.url}</div>
              </div>
            </div>
          ))}
        </div>

        <div>
          <div style={styles.sectionTitle}>Related actions</div>
          {ACTIONS.map(a => (
            <div key={a.label} style={styles.actionCard}>
              <span style={styles.actionIcon}>{a.icon}</span>
              <span style={styles.actionLabel}>{a.label}</span>
              <span style={styles.actionArrow}>›</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const styles = {
  panel:       { width: 280, minWidth: 280, background: '#fff', borderLeft: '0.5px solid #e5e7eb', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: 'system-ui, sans-serif' },
  header:      { padding: '12px 14px', borderBottom: '0.5px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  title:       { fontSize: 13, fontWeight: 500, color: '#111' },
  sessionId:   { fontSize: 10, color: '#9ca3af', fontFamily: 'monospace', marginTop: 1 },
  newBtn:      { fontSize: 11, padding: '4px 10px', borderRadius: 6, border: '0.5px solid #d1d5db', background: '#f9fafb', color: '#6b7280', cursor: 'pointer' },
  tabs:        { display: 'flex', borderBottom: '0.5px solid #e5e7eb' },
  tab:         { padding: '8px 14px', fontSize: 11, color: '#9ca3af', cursor: 'pointer', borderBottom: '2px solid transparent' },
  tabActive:   { color: '#1d4ed8', borderBottomColor: '#1d4ed8' },
  body:        { flex: 1, overflowY: 'auto', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 16 },
  statusCard:  { background: '#f0fdf4', border: '0.5px solid #bbf7d0', borderRadius: 8, padding: '10px 12px', display: 'flex', alignItems: 'flex-start', gap: 8 },
  checkIcon:   { color: '#15803d', fontSize: 16, marginTop: 1 },
  statusLabel: { fontSize: 12, fontWeight: 500, color: '#15803d' },
  statusSub:   { fontSize: 10, color: '#6b7280', marginTop: 2 },
  idle:        { background: '#f9fafb', borderRadius: 8, padding: '16px', textAlign: 'center' },
  idleText:    { fontSize: 12, color: '#6b7280', fontWeight: 500 },
  idleSub:     { fontSize: 11, color: '#9ca3af', marginTop: 2 },
  sectionTitle: { fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.07em', fontWeight: 500, marginBottom: 8 },
  stepRow:     { display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', borderBottom: '0.5px solid #f3f4f6' },
  stepCheck:   { width: 18, height: 18, borderRadius: '50%', background: '#f0fdf4', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: '#15803d', flexShrink: 0 },
  stepLabel:   { flex: 1, fontSize: 11, color: '#374151' },
  stepTime:    { fontSize: 10, color: '#9ca3af', fontFamily: 'monospace' },
  dsCard:      { border: '0.5px solid #e5e7eb', borderRadius: 8, padding: '8px 10px', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 },
  dsIcon:      { width: 28, height: 28, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 },
  dsName:      { fontSize: 11, fontWeight: 500, color: '#374151' },
  dsUrl:       { fontSize: 10, color: '#9ca3af', fontFamily: 'monospace', marginTop: 1 },
  actionCard:  { border: '0.5px solid #e5e7eb', borderRadius: 8, padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, cursor: 'pointer' },
  actionIcon:  { color: '#1d4ed8', fontSize: 14 },
  actionLabel: { flex: 1, fontSize: 12, color: '#374151' },
  actionArrow: { color: '#9ca3af', fontSize: 16 },
};
