import { C, Icons } from '../../constants/theme';

export default function Sidebar({ activeView, setActiveView, config, user, onLogout }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.dashboard },
    { id: 'content', label: 'Content', icon: Icons.content },
    { id: 'engagement', label: 'Engagement', icon: Icons.engage },
    { id: 'settings', label: 'Settings', icon: Icons.settings },
  ];

  const getUserInitials = () => {
    if (user?.full_name) {
      const names = user.full_name.split(' ');
      if (names.length >= 2) {
        return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
      }
      return names[0][0].toUpperCase();
    }
    return user?.username?.[0]?.toUpperCase() || 'U';
  };

  return (
    <nav
      aria-label="Main navigation"
      style={{
        width: '220px',
        minWidth: '220px',
        background: C.surface,
        borderRight: `1px solid ${C.border}`,
        display: 'flex',
        flexDirection: 'column',
        padding: '0',
      }}
    >
      <div style={{ padding: '24px 20px 20px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: `linear-gradient(135deg, ${C.accent}, ${C.accentBright})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              fontWeight: 700,
              color: C.bg,
              fontFamily: "'Instrument Serif', Georgia, serif",
            }}
          >
            S
          </div>
          <div>
            <span
              style={{
                fontSize: '14px',
                fontWeight: 600,
                color: C.text,
                display: 'block',
                lineHeight: 1.2,
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              Brand Engine
            </span>
            <span
              style={{
                fontSize: '10px',
                color: C.textDim,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              Personal Brand
            </span>
          </div>
        </div>
      </div>

      <div style={{ padding: '12px 8px', flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              aria-current={isActive ? 'page' : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                width: '100%',
                textAlign: 'left',
                background: isActive ? C.accentMuted : 'transparent',
                color: isActive ? C.accent : C.textMuted,
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                fontFamily: "'DM Sans', sans-serif",
                transition: 'all 0.15s ease',
                outline: 'none',
              }}
              onFocus={(e) => { e.target.style.boxShadow = `0 0 0 2px ${C.accent}`; }}
              onBlur={(e) => { e.target.style.boxShadow = 'none'; }}
            >
              <span style={{ opacity: isActive ? 1 : 0.7 }}>{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </div>

      {/* User Profile Section */}
      {user && (
        <div style={{ padding: '12px 8px', borderTop: `1px solid ${C.border}` }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              borderRadius: '6px',
              background: C.bg,
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: C.accentMuted,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: 600,
                color: C.accent,
                flexShrink: 0,
              }}
            >
              {getUserInitials()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: C.text,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {user.full_name || user.username}
              </div>
              <div
                style={{
                  fontSize: '10px',
                  color: C.textDim,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {user.email}
              </div>
            </div>
          </div>
          <button
            onClick={onLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              width: '100%',
              marginTop: '8px',
              padding: '8px',
              border: `1px solid ${C.border}`,
              borderRadius: '6px',
              cursor: 'pointer',
              background: 'transparent',
              color: C.textMuted,
              fontSize: '11px',
              fontWeight: 500,
              fontFamily: "'DM Sans', sans-serif",
              transition: 'all 0.15s ease',
              outline: 'none',
            }}
            onMouseEnter={(e) => {
              e.target.style.background = C.dangerMuted;
              e.target.style.color = C.danger;
              e.target.style.borderColor = C.danger;
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.color = C.textMuted;
              e.target.style.borderColor = C.border;
            }}
            onFocus={(e) => { e.target.style.boxShadow = `0 0 0 2px ${C.accent}`; }}
            onBlur={(e) => { e.target.style.boxShadow = 'none'; }}
          >
            Sign Out
          </button>
        </div>
      )}

      <div style={{ padding: '16px 20px', borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }} role="status" aria-label={config?.kill_switch ? 'System halted' : 'All systems active'}>
          <div
            aria-hidden="true"
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: config?.kill_switch ? C.danger : C.success,
            }}
          />
          <span style={{ fontSize: '11px', color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>
            {config?.kill_switch ? 'System halted' : 'All systems active'}
          </span>
        </div>
        <span style={{ fontSize: '10px', color: C.textDim, marginTop: '4px', display: 'block', fontFamily: "'DM Sans', sans-serif" }}>
          v5.0 · SAST
        </span>
      </div>
    </nav>
  );
}
