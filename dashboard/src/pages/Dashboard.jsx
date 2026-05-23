/**
 * Dashboard.jsx
 * Main page - composes all components, owns layout and state routing
 * Swap activePage to navigate between views without a router dependency
 */

import { useState } from 'react';
import { useClaims } from '../hooks/useClaims';
import Sidebar            from '../components/Sidebar';
import KpiCards           from '../components/KpiCards';
import ClaimsTable        from '../components/ClaimsTable';
import AgentChatPanel     from '../components/AgentChatPanel';
import AgentSessionPanel  from '../components/AgentSessionPanel';

export default function Dashboard() {
  const { claims, loading, error, connected, lastRefresh, stats, refresh } = useClaims();
  const [activePage, setActivePage] = useState('agent');
  const [agentSteps, setAgentSteps] = useState([]);
  const [sessionId]  = useState(() => Math.random().toString(36).slice(2, 10));

  const refreshLabel = lastRefresh
    ? 'Refreshed ' + lastRefresh.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '--';

  return (
    <div style={styles.shell}>
      <Sidebar activePage={activePage} onNavigate={setActivePage} totalClaims={stats.total} />

      <div style={styles.main}>
        <header style={styles.header}>
          <div>
            <div style={styles.headerTitle}>
              {activePage === 'agent' ? 'AI Claims Review Assistant' : 'Claims Overview'}
            </div>
            <div style={styles.headerSub}>
              {activePage === 'agent'
                ? 'Ask questions about claims, get insights, and review results.'
                : 'Live data from MarkLogic roxy-content database'}
            </div>
          </div>
          <div style={styles.headerRight}>
            {error
              ? <span style={styles.pillErr}>⚠ Disconnected</span>
              : connected
                ? <span style={styles.pillOk}>● Connected</span>
                : <span style={styles.pillWait}>○ Connecting...</span>
            }
            <span style={styles.refreshTime}>{refreshLabel}</span>
            <button onClick={refresh} style={styles.refreshBtn}>↺ Refresh</button>
          </div>
        </header>

        <div style={styles.content}>
          {activePage === 'agent' ? (
            <div style={styles.agentLayout}>
              <div style={styles.agentMain}>
                <AgentChatPanel claims={claims} onStepsUpdate={setAgentSteps} />
              </div>
              <AgentSessionPanel steps={agentSteps} sessionId={sessionId} />
            </div>
          ) : (
            <div style={styles.overviewLayout}>
              {error && (
                <div style={styles.errorBox}>
                  Cannot connect to MarkLogic at localhost:8040. Run: <code>python serve_dashboard.py</code>
                </div>
              )}
              <KpiCards stats={stats} loading={loading} />
              <ClaimsTable claims={claims} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  shell:         { display: 'flex', height: '100vh', overflow: 'hidden', fontFamily: 'system-ui, -apple-system, sans-serif', background: '#f9fafb' },
  main:          { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  header:        { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderBottom: '0.5px solid #e5e7eb', background: '#fff', flexShrink: 0 },
  headerTitle:   { fontSize: 16, fontWeight: 500, color: '#111' },
  headerSub:     { fontSize: 11, color: '#9ca3af', marginTop: 2 },
  headerRight:   { display: 'flex', alignItems: 'center', gap: 14 },
  pillOk:        { fontSize: 11, color: '#15803d', background: '#f0fdf4', padding: '3px 10px', borderRadius: 20 },
  pillErr:       { fontSize: 11, color: '#dc2626', background: '#fef2f2', padding: '3px 10px', borderRadius: 20 },
  pillWait:      { fontSize: 11, color: '#d97706', background: '#fffbeb', padding: '3px 10px', borderRadius: 20 },
  refreshTime:   { fontSize: 10, color: '#9ca3af' },
  refreshBtn:    { fontSize: 10, padding: '5px 12px', borderRadius: 6, border: '0.5px solid #d1d5db', background: '#fff', cursor: 'pointer', color: '#6b7280' },
  content:       { flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' },
  agentLayout:   { display: 'flex', height: '100%', overflow: 'hidden' },
  agentMain:     { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  overviewLayout: { padding: 20, overflowY: 'auto', flex: 1 },
  errorBox:      { background: '#fef2f2', border: '0.5px solid #fca5a5', borderRadius: 8, padding: '12px 16px', fontSize: 12, color: '#dc2626', marginBottom: 16 },
};
