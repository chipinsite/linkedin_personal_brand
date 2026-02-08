import { C } from '../../constants/theme';

export default function Button({ children, variant = 'default', size = 'md', onClick, style: extraStyle, disabled, type = 'button', ...rest }) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontFamily: "'DM Sans', sans-serif",
    fontWeight: 500,
    letterSpacing: '0.01em',
    borderRadius: '6px',
    transition: 'all 0.15s ease',
    opacity: disabled ? 0.5 : 1,
    fontSize: size === 'sm' ? '12px' : '13px',
    padding: size === 'sm' ? '6px 12px' : '8px 16px',
  };

  const variants = {
    default: { background: C.surfaceHover, color: C.text, border: `1px solid ${C.border}` },
    primary: { background: C.accent, color: '#0C0E12', fontWeight: 600 },
    danger: { background: C.dangerMuted, color: C.danger, border: '1px solid rgba(248,113,113,0.2)' },
    success: { background: C.successMuted, color: C.success, border: '1px solid rgba(74,222,128,0.2)' },
    ghost: { background: 'transparent', color: C.textMuted },
  };

  return (
    <button type={type} onClick={onClick} disabled={disabled} style={{ ...base, ...variants[variant], ...extraStyle }} {...rest}>
      {children}
    </button>
  );
}
