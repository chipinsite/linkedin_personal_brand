import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { C, pct } from '../../constants/theme';
import Button from '../ui/Button';
import ProgressBar from '../ui/ProgressBar';

function parseWeightJSON(raw, fallback) {
  if (!raw) return fallback;
  if (typeof raw === 'object') return raw;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export default function SettingsView({ onConfigChange }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [config, setConfig] = useState(null);
  const [learning, setLearning] = useState(null);

  async function refreshData() {
    const [configRes, learningRes] = await Promise.all([api.adminConfig(), api.learningWeights()]);
    setConfig(configRes);
    setLearning(learningRes);
    if (onConfigChange) {
      onConfigChange(configRes);
    }
  }

  async function withAction(label, fn) {
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await fn();
      setMessage(label);
      await refreshData();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    withAction('Data refreshed', refreshData);
  }, []);

  const formatWeights = parseWeightJSON(learning?.format_weights_json, {});
  const toneWeights = parseWeightJSON(learning?.tone_weights_json, {});

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <h2 style={{ fontSize: '20px', fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
        Settings
      </h2>

      {message ? <div style={{ background: C.successMuted, color: C.success, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{message}</div> : null}
      {error ? <div style={{ background: C.dangerMuted, color: C.danger, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{error}</div> : null}

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '20px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: C.text, display: 'block', marginBottom: '12px' }}>System Controls</span>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <Button disabled={loading} onClick={() => withAction('Kill switch enabled', () => api.killSwitchOn())}>Kill ON</Button>
          <Button disabled={loading} onClick={() => withAction('Kill switch disabled', () => api.killSwitchOff())}>Kill OFF</Button>
          <Button disabled={loading} onClick={() => withAction('Posting enabled', () => api.postingOn())}>Posting ON</Button>
          <Button disabled={loading} onClick={() => withAction('Posting disabled', () => api.postingOff())}>Posting OFF</Button>
          <Button disabled={loading} onClick={() => withAction('Learning recomputed', () => api.recomputeLearning())}>Recompute</Button>
        </div>
        <div style={{ marginTop: '12px', fontSize: '12px', color: C.textMuted }}>
          {config ? `Timezone: ${config.timezone} · Posting: ${String(config.posting_enabled)} · Kill switch: ${String(config.kill_switch)}` : 'Loading config...'}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '20px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: C.text, display: 'block', marginBottom: '16px' }}>Format Distribution</span>
          {Object.entries(formatWeights).map(([key, value]) => (
            <div key={key} style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: C.textMuted }}>{key}</span>
                <span style={{ fontSize: '12px', color: C.text }}>{pct(Number(value || 0))}</span>
              </div>
              <ProgressBar value={Number(value || 0) * 100} />
            </div>
          ))}
        </div>

        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '20px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: C.text, display: 'block', marginBottom: '16px' }}>Tone Distribution</span>
          {Object.entries(toneWeights).map(([key, value]) => (
            <div key={key} style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: C.textMuted }}>{key}</span>
                <span style={{ fontSize: '12px', color: C.text }}>{pct(Number(value || 0))}</span>
              </div>
              <ProgressBar value={Number(value || 0) * 100} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
