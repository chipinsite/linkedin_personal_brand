import { C } from '../../constants/theme';
import Button from '../ui/Button';

function formatSnoozeRemaining(ms) {
  const safeMs = Math.max(0, Number(ms || 0));
  const totalMinutes = Math.ceil(safeMs / 60_000);
  if (totalMinutes >= 60) {
    return `${Math.ceil(totalMinutes / 60)}h left`;
  }
  return `${totalMinutes}m left`;
}

function alertStyle(tone) {
  if (tone === 'critical') {
    return { bg: C.dangerMuted, color: C.danger };
  }
  if (tone === 'warning') {
    return { bg: C.warningMuted, color: C.warning };
  }
  return { bg: C.infoMuted, color: C.info };
}

export default function OperationalAlerts({
  visibleAlerts,
  snoozedAlerts,
  nowMs,
  onSnooze,
  onClearSnoozes,
}) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px', display: 'grid', gap: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', color: C.text, fontWeight: 600 }}>Operational Alerts</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: C.textMuted }}>{visibleAlerts.length} active</span>
          {snoozedAlerts.length > 0 ? (
            <Button size="sm" variant="default" onClick={onClearSnoozes}>Clear Snoozes</Button>
          ) : null}
        </div>
      </div>
      {snoozedAlerts.length > 0 ? (
        <div style={{ fontSize: '12px', color: C.textMuted }}>
          <strong style={{ color: C.text }}>Snoozed alerts: {snoozedAlerts.length}</strong>
          {' '}
          {snoozedAlerts.map((alert) => (
            <span key={alert.id} style={{ marginRight: '8px' }}>
              {alert.id}: {formatSnoozeRemaining(alert.snoozedUntil - nowMs)}
            </span>
          ))}
        </div>
      ) : null}
      {visibleAlerts.length === 0 ? (
        <div style={{ fontSize: '12px', color: C.textMuted }}>No active operational alerts.</div>
      ) : (
        visibleAlerts.map((alert) => {
          const style = alertStyle(alert.tone);
          return (
            <div key={alert.id} role="alert" style={{ background: style.bg, color: style.color, border: `1px solid ${C.border}`, borderRadius: '6px', padding: '10px', fontSize: '12px', display: 'flex', justifyContent: 'space-between', gap: '8px', alignItems: 'center' }}>
              <span>{alert.message}</span>
              <Button
                size="sm"
                variant="default"
                aria-label={`Snooze ${alert.id}`}
                onClick={() => onSnooze(alert.id)}
              >
                Snooze 2h
              </Button>
            </div>
          );
        })
      )}
    </div>
  );
}
