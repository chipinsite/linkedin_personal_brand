import { C } from '../../constants/theme';

export default function MetricCard({ label, value, sub, trend, accent }) {
  return (
    <div
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: '8px',
        padding: '20px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        minWidth: 0,
      }}
    >
      <span
        style={{
          fontSize: '12px',
          color: C.textMuted,
          fontWeight: 500,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          fontFamily: "'DM Sans', sans-serif",
        }}
      >
        {label}
      </span>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
        <span
          style={{
            fontSize: '28px',
            fontWeight: 600,
            color: accent || C.text,
            fontFamily: "'Instrument Serif', Georgia, serif",
            lineHeight: 1,
          }}
        >
          {value}
        </span>
        {trend ? (
          <span
            style={{
              fontSize: '12px',
              color: trend > 0 ? C.success : C.danger,
              fontWeight: 500,
              fontFamily: "'DM Sans', sans-serif",
            }}
          >
            {trend > 0 ? '+' : ''}
            {trend}%
          </span>
        ) : null}
      </div>
      {sub ? (
        <span style={{ fontSize: '12px', color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>{sub}</span>
      ) : null}
    </div>
  );
}
