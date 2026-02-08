import { C } from '../../constants/theme';

export default function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div
      role="status"
      aria-busy="true"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '24px',
        color: C.textMuted,
        fontSize: '13px',
      }}
    >
      <div
        aria-hidden="true"
        style={{
          width: '16px',
          height: '16px',
          border: `2px solid ${C.border}`,
          borderTop: `2px solid ${C.accent}`,
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {label}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
