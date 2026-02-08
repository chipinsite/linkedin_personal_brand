import { C, Icons } from '../../constants/theme';

export default function Sidebar({ activeView, setActiveView, config }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.dashboard },
    { id: 'content', label: 'Content', icon: Icons.content },
    { id: 'engagement', label: 'Engagement', icon: Icons.engage },
    { id: 'settings', label: 'Settings', icon: Icons.settings },
  ];

  return (
    <nav
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
              }}
            >
              <span style={{ opacity: isActive ? 1 : 0.7 }}>{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </div>

      <div style={{ padding: '16px 20px', borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
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
          v4.5 · SAST
        </span>
      </div>
    </nav>
  );
}
