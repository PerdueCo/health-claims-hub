/**
 * Sidebar.jsx
 * Left navigation panel - framework-independent structure
 * Pass activePage and onNavigate as props for easy migration to other frameworks
 */

const NAV = [
  { section: 'Overview', items: [
    { id: 'dashboard',   icon: '⊞', label: 'Dashboard' }
  ]},
  { section: 'Claims', items: [
    { id: 'search',      icon: '⌕', label: 'Search Claims' },
    { id: 'browse',      icon: '☰', label: 'Browse Claims' },
    { id: 'analytics',   icon: '▦', label: 'Claim Analytics' },
    { id: 'providers',   icon: '⊕', label: 'Providers' }
  ]},
  { section: 'AI & Review', items: [
    { id: 'agent',       icon: '◈', label: 'AI Agent Chat', badge: null },
    { id: 'queue',       icon: '⊟', label: 'Review Queue',  badge: 12 },
    { id: 'human',       icon: '◎', label: 'Human Review',  badge: 5 }
  ]},
  { section: 'Data & System', items: [
    { id: 'sparql',      icon: '⬡', label: 'SPARQL Explorer' },
    { id: 'sources',     icon: '⇌', label: 'Data Sources' },
    { id: 'settings',    icon: '⚙', label: 'Settings' }
  ]}
];

export default function Sidebar({ activePage, onNavigate, totalClaims }) {
  return (
    <nav style={styles.nav}>
      <div style={styles.brand}>
        <div style={styles.brandIcon}>♥</div>
        <div>
          <div style={styles.brandName}>Health Claims Hub</div>
          <div style={styles.brandSub}>MECP Claims Review</div>
        </div>
      </div>

      {NAV.map(group => (
        <div key={group.section} style={styles.group}>
          <div style={styles.groupLabel}>{group.section}</div>
          {group.items.map(item => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              style={{
                ...styles.navItem,
                ...(activePage === item.id ? styles.navItemActive : {})
              }}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              <span style={styles.navLabel}>{item.label}</span>
              {item.badge && <span style={styles.badge}>{item.badge}</span>}
            </button>
          ))}
        </div>
      ))}

      <div style={styles.footer}>
        <div style={styles.footerText}>MECP v0.1.0</div>
        {totalClaims > 0 && (
          <div style={styles.footerLive}>
            <span style={styles.liveDot} />
            {totalClaims.toLocaleString()} claims loaded
          </div>
        )}
      </div>
    </nav>
  );
}

const styles = {
  nav:          { width: 200, minWidth: 200, background: '#fff', borderRight: '0.5px solid #e5e7eb', display: 'flex', flexDirection: 'column', overflow: 'auto', fontFamily: 'system-ui, sans-serif' },
  brand:        { display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderBottom: '0.5px solid #e5e7eb' },
  brandIcon:    { width: 28, height: 28, borderRadius: 6, background: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1d4ed8', fontSize: 16 },
  brandName:    { fontSize: 13, fontWeight: 500, color: '#111', lineHeight: 1.2 },
  brandSub:     { fontSize: 10, color: '#9ca3af' },
  group:        { padding: '8px 0' },
  groupLabel:   { fontSize: 10, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.07em', padding: '4px 16px 2px', fontWeight: 500 },
  navItem:      { display: 'flex', alignItems: 'center', gap: 8, padding: '7px 16px', width: '100%', border: 'none', background: 'transparent', cursor: 'pointer', fontSize: 12, color: '#6b7280', textAlign: 'left', transition: 'background .12s' },
  navItemActive: { background: '#eff6ff', color: '#1d4ed8', fontWeight: 500 },
  navIcon:      { fontSize: 14, width: 16, flexShrink: 0 },
  navLabel:     { flex: 1 },
  badge:        { marginLeft: 'auto', background: '#fee2e2', color: '#dc2626', fontSize: 10, padding: '1px 6px', borderRadius: 10, fontWeight: 500 },
  footer:       { marginTop: 'auto', padding: '10px 16px', borderTop: '0.5px solid #e5e7eb' },
  footerText:   { fontSize: 10, color: '#9ca3af' },
  footerLive:   { display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: '#6b7280', marginTop: 3 },
  liveDot:      { width: 6, height: 6, borderRadius: '50%', background: '#22c55e' }
};
