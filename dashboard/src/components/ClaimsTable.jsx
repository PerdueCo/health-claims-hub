/**
 * ClaimsTable.jsx
 * Filterable claims table with status badges and financial columns
 * Receives claims array as prop - no direct API dependency
 */

import { useState } from 'react';

const fmt$ = n => '$' + Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 0 });
const fmtDate = s => s ? new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '--';

const STATUS_STYLE = {
  PAID:    { background: '#f0fdf4', color: '#15803d' },
  DENIED:  { background: '#fef2f2', color: '#dc2626' },
  PENDING: { background: '#fffbeb', color: '#d97706' },
};

const RISK_COLOR = score => score >= 80 ? '#dc2626' : score >= 60 ? '#d97706' : '#15803d';

const FILTERS = ['ALL', 'PAID', 'DENIED', 'PENDING'];

export default function ClaimsTable({ claims }) {
  const [filter, setFilter]   = useState('ALL');
  const [page, setPage]       = useState(1);
  const PAGE_SIZE = 10;

  const filtered = filter === 'ALL' ? claims : claims.filter(c => c.status === filter);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleFilter = (f) => { setFilter(f); setPage(1); };

  return (
    <div style={styles.wrap}>
      <div style={styles.toolbar}>
        <div style={styles.filterGroup}>
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => handleFilter(f)}
              style={{ ...styles.filterBtn, ...(filter === f ? styles.filterActive : {}) }}
            >
              {f === 'ALL' ? 'All' : f.charAt(0) + f.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
        <span style={styles.count}>{filtered.length} claims</span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.thead}>
              {['Claim ID', 'Provider', 'Member', 'Service Date', 'Status', 'Billed', 'Paid', 'Risk'].map(h => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr><td colSpan={8} style={styles.empty}>No claims match this filter.</td></tr>
            ) : visible.map(c => (
              <tr key={c.claimId} style={styles.tr}>
                <td style={styles.tdId}>{c.claimId || '--'}</td>
                <td style={styles.td}>{c.provider || '--'}</td>
                <td style={{ ...styles.td, color: '#9ca3af', fontFamily: 'monospace', fontSize: 11 }}>{c.memberId || '--'}</td>
                <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: 11 }}>{fmtDate(c.serviceDate)}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, ...STATUS_STYLE[c.status] }}>{c.status}</span>
                </td>
                <td style={{ ...styles.td, fontFamily: 'monospace' }}>{fmt$(c.amountBilled)}</td>
                <td style={{ ...styles.td, fontFamily: 'monospace', color: c.status === 'PAID' ? '#15803d' : '#9ca3af' }}>
                  {c.status === 'PAID' ? fmt$(c.amountPaid) : '—'}
                </td>
                <td style={{ ...styles.td, fontFamily: 'monospace', fontWeight: 500, color: RISK_COLOR(c.riskScore) }}>
                  {c.riskScore ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div style={styles.pagination}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={styles.pageBtn}>←</button>
          <span style={styles.pageInfo}>Page {page} of {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={styles.pageBtn}>→</button>
        </div>
      )}
    </div>
  );
}

const styles = {
  wrap:        { background: '#fff', border: '0.5px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' },
  toolbar:     { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '0.5px solid #e5e7eb' },
  filterGroup: { display: 'flex', gap: 6 },
  filterBtn:   { background: 'transparent', border: '0.5px solid #d1d5db', borderRadius: 6, padding: '4px 12px', fontSize: 11, color: '#6b7280', cursor: 'pointer' },
  filterActive: { background: '#eff6ff', borderColor: '#93c5fd', color: '#1d4ed8', fontWeight: 500 },
  count:       { fontSize: 11, color: '#9ca3af' },
  table:       { width: '100%', borderCollapse: 'collapse', fontSize: 12 },
  thead:       { borderBottom: '0.5px solid #e5e7eb' },
  th:          { padding: '8px 12px', textAlign: 'left', fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.08em', fontWeight: 500, whiteSpace: 'nowrap' },
  tr:          { borderBottom: '0.5px solid #f3f4f6', cursor: 'default' },
  td:          { padding: '10px 12px', color: '#374151', fontSize: 12 },
  tdId:        { padding: '10px 12px', color: '#1d4ed8', fontFamily: 'monospace', fontSize: 11, fontWeight: 500 },
  badge:       { display: 'inline-block', fontSize: 10, padding: '2px 8px', borderRadius: 20, fontWeight: 500 },
  empty:       { padding: 20, textAlign: 'center', color: '#9ca3af', fontSize: 12 },
  pagination:  { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, padding: '10px 14px', borderTop: '0.5px solid #e5e7eb' },
  pageBtn:     { background: 'transparent', border: '0.5px solid #d1d5db', borderRadius: 6, padding: '4px 10px', fontSize: 12, cursor: 'pointer', color: '#374151' },
  pageInfo:    { fontSize: 11, color: '#9ca3af' },
};
