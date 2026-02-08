import { C } from '../../constants/theme';

export default function StatusBadge({ status, size = 'sm' }) {
  const map = {
    PENDING: { bg: C.warningMuted, color: C.warning, label: 'Pending' },
    APPROVED: { bg: C.successMuted, color: C.success, label: 'Approved' },
    REJECTED: { bg: C.dangerMuted, color: C.danger, label: 'Rejected' },
    PUBLISHED: { bg: C.infoMuted, color: C.info, label: 'Published' },
    ESCALATED: { bg: C.dangerMuted, color: C.danger, label: 'Escalated' },
    TEXT: { bg: C.accentMuted, color: C.accent, label: 'Text' },
    IMAGE: { bg: C.infoMuted, color: C.info, label: 'Image' },
    CAROUSEL: { bg: C.successMuted, color: C.success, label: 'Carousel' },
    EDUCATIONAL: { bg: C.infoMuted, color: C.info, label: 'Educational' },
    OPINIONATED: { bg: C.warningMuted, color: C.warning, label: 'Opinionated' },
    DIRECT: { bg: C.accentMuted, color: C.accent, label: 'Direct' },
    EXPLORATORY: { bg: C.successMuted, color: C.success, label: 'Exploratory' },
  };

  const s = map[status] || { bg: C.border, color: C.textMuted, label: status || 'Unknown' };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: size === 'sm' ? '2px 8px' : '4px 12px',
        borderRadius: '4px',
        background: s.bg,
        color: s.color,
        fontSize: size === 'sm' ? '11px' : '12px',
        fontWeight: 500,
        letterSpacing: '0.02em',
        textTransform: 'uppercase',
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      {s.label}
    </span>
  );
}
