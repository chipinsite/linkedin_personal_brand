import { C } from '../../constants/theme';
import Button from '../ui/Button';

export default function ErrorMessage({ error, onRetry }) {
  return (
    <div
      style={{
        background: C.dangerMuted,
        border: `1px solid ${C.border}`,
        borderRadius: '8px',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
      }}
    >
      <div style={{ fontSize: '13px', color: C.danger }}>
        {error || 'Something went wrong.'}
      </div>
      {onRetry ? (
        <Button size="sm" variant="danger" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
