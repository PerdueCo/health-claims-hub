/**
 * KpiCards.jsx
 * Four summary metric cards: Total, Paid, Denied, Pending
 * Consumes stats object from useClaims() hook - no direct API calls
 */

const fmt = n => n?.toLocaleString() ?? '--';
const pct = (n, t) => t > 0 ? ((n / t) * 100).toFixed(1) + '%' : '0%';

const CARDS = [
  { key: 'total',   label: 'Total Claims',  color: '#1d4ed8', bg: '#eff6ff', sub: (s) => 'across all statuses' },
  { key: 'paid',    label: 'Paid',          color: '#15803d', bg: '#f0fdf4', sub: (s) => pct(s.paid, s.total) + ' of total' },
  { key: 'denied',  label: 'Denied',        color: '#dc2626', bg: '#fef2f2', sub: (s) => pct(s.denied, s.total) + ' of total' },
  { key: 'pending', label: 'Pending',       color: '#d97706', bg: '#fffbeb', sub: (s) => pct(s.pending, s.total) + ' of total' },
];

export default function KpiCards({ stats, loading }) {
  return (
    <div style={styles.grid}>
      {CARDS.map(card => (
        <div key={card.key} style={{ ...styles.card, borderTop: `3px solid ${card.color}` }}>
          <div style={styles.label}>{card.label}</div>
          {loading
            ? <div style={styles.skeleton} />
            : <div style={{ ...styles.value, color: card.color }}>{fmt(stats[card.key])}</div>
          }
          <div style={styles.sub}>{loading ? '...' : card.sub(stats)}</div>
          <div style={{ ...styles.bar, background: card.bg }}>
            <div style={{
              ...styles.barFill,
              background: card.color,
              width: loading ? '0%' : pct(stats[card.key], stats.total)
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}

const styles = {
  grid:     { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 },
  card:     { background: '#fff', border: '0.5px solid #e5e7eb', borderRadius: 10, padding: '16px 18px', position: 'relative', overflow: 'hidden' },
  label:    { fontSize: 11, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8, fontWeight: 500 },
  value:    { fontSize: 32, fontWeight: 500, lineHeight: 1, marginBottom: 6 },
  sub:      { fontSize: 11, color: '#9ca3af' },
  bar:      { position: 'absolute', bottom: 0, left: 0, right: 0, height: 3 },
  barFill:  { height: '100%', transition: 'width 1s ease' },
  skeleton: { height: 32, width: 80, background: '#f3f4f6', borderRadius: 4, marginBottom: 6 },
};
