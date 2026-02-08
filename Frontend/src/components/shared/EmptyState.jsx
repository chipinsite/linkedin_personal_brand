import { C } from '../../constants/theme';

export default function EmptyState({ title, message }) {
  return (
    <div
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: '8px',
        padding: '32px 24px',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '14px', color: C.text, fontWeight: 600, marginBottom: '8px' }}>
        {title}
      </div>
      <div style={{ fontSize: '13px', color: C.textMuted, lineHeight: 1.5 }}>
        {message}
      </div>
    </div>
  );
}
