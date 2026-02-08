import { C } from '../../constants/theme';

export default function LoadingSpinner({ label = 'Loading...', size = 'medium', inline = false }) {
  const sizes = {
    small: { spinner: 14, border: 2, gap: 6 },
    medium: { spinner: 16, border: 2, gap: 10 },
    large: { spinner: 24, border: 3, gap: 12 },
  };

  const s = sizes[size] || sizes.medium;

  if (inline) {
    return (
      <span
        role="status"
        aria-busy="true"
        aria-label={label}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span
          aria-hidden="true"
          style={{
            display: 'inline-block',
            width: `${s.spinner}px`,
            height: `${s.spinner}px`,
            border: `${s.border}px solid ${C.border}`,
            borderTop: `${s.border}px solid currentColor`,
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </span>
    );
  }

  return (
    <div
      role="status"
      aria-busy="true"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: `${s.gap}px`,
        padding: '24px',
        color: C.textMuted,
        fontSize: '13px',
      }}
    >
      <div
        aria-hidden="true"
        style={{
          width: `${s.spinner}px`,
          height: `${s.spinner}px`,
          border: `${s.border}px solid ${C.border}`,
          borderTop: `${s.border}px solid ${C.accent}`,
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {label}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
