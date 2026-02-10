import { useEffect, useMemo, useState } from 'react';
import { api } from '../../services/api';
import { C, formatDate, formatTime, truncate } from '../../constants/theme';
import Button from '../ui/Button';
import MetricCard from '../ui/MetricCard';
import StatusBadge from '../ui/StatusBadge';
import LoadingSpinner from '../shared/LoadingSpinner';
import ErrorMessage from '../shared/ErrorMessage';
import EmptyState from '../shared/EmptyState';

const PIPELINE_STATUSES = [
  'BACKLOG', 'TODO', 'WRITING', 'REVIEW',
  'READY_TO_PUBLISH', 'PUBLISHED', 'AMPLIFIED', 'DONE',
];

const AGENTS = [
  { id: 'scout', label: 'Scout', description: 'Scan sources and seed backlog' },
  { id: 'writer', label: 'Writer', description: 'Generate drafts from TODO items' },
  { id: 'editor', label: 'Editor', description: 'Review drafts with quality gates' },
  { id: 'publisher', label: 'Publisher', description: 'Publish ready content' },
  { id: 'promoter', label: 'Promoter', description: 'Send engagement prompts' },
  { id: 'morgan', label: 'Morgan PM', description: 'Self-heal stale claims and errors' },
];

const STATUS_COLORS = {
  BACKLOG: C.textDim,
  TODO: C.warning,
  WRITING: C.accent,
  REVIEW: C.info,
  READY_TO_PUBLISH: C.accentBright,
  PUBLISHED: C.success,
  AMPLIFIED: C.info,
  DONE: C.textMuted,
};

export default function PipelineView() {
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [fetchError, setFetchError] = useState('');

  const [overview, setOverview] = useState(null);
  const [items, setItems] = useState([]);
  const [health, setHealth] = useState(null);
  const [pipelineMode, setPipelineMode] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');

  async function refreshData() {
    setFetchError('');
    try {
      const [overviewRes, itemsRes, healthRes, configRes] = await Promise.all([
        api.pipelineOverview(),
        api.pipelineItems(),
        api.pipelineHealth(),
        api.adminConfig(),
      ]);
      setOverview(overviewRes);
      setItems(itemsRes);
      setHealth(healthRes);
      setPipelineMode(configRes?.pipeline_mode || 'LEGACY');
    } catch (err) {
      setFetchError(String(err.message || err));
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
    (async () => {
      await refreshData();
      setInitialLoading(false);
    })();
  }, []);

  const filteredItems = useMemo(() => {
    if (statusFilter === 'all') return items;
    return items.filter((item) => item.status === statusFilter);
  }, [items, statusFilter]);

  const statusCounts = overview?.status_counts || {};

  if (initialLoading) {
    return <LoadingSpinner label="Loading pipeline..." />;
  }

  if (fetchError && !overview) {
    return (
      <ErrorMessage
        error={`Failed to load pipeline: ${fetchError}`}
        onRetry={() => {
          setInitialLoading(true);
          refreshData().finally(() => setInitialLoading(false));
        }}
      />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
            Content Pipeline
          </h2>
          <p style={{ fontSize: '13px', color: C.textMuted, marginTop: '4px', fontFamily: "'DM Sans', sans-serif" }}>
            Health: {health?.health_status || '-'} · Total items: {overview?.total ?? '-'} · Claimed: {overview?.claimed ?? '-'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button disabled={loading} variant="default" onClick={() => withAction('Pipeline refreshed', refreshData)}>Refresh</Button>
          <Button disabled={loading} variant="primary" onClick={() => withAction('Morgan PM complete', () => api.runAgent('morgan'))}>Run Morgan</Button>
        </div>
      </div>

      {/* Pipeline Mode Indicator */}
      {pipelineMode && pipelineMode !== 'V6' ? (
        <div
          data-testid="pipeline-mode-banner"
          style={{
            background: pipelineMode === 'SHADOW' ? (C.warningMuted || '#fef3c7') : pipelineMode === 'DISABLED' ? C.dangerMuted : C.surface,
            color: pipelineMode === 'SHADOW' ? (C.warning || '#f59e0b') : pipelineMode === 'DISABLED' ? C.danger : C.textMuted,
            border: `1px solid ${C.border}`,
            borderRadius: '8px',
            padding: '10px 16px',
            fontSize: '13px',
          }}
        >
          <strong>Pipeline Mode: {pipelineMode}</strong>
          {pipelineMode === 'LEGACY' && ' — V6 agents are not active. Switch to Shadow or V6 mode in Settings.'}
          {pipelineMode === 'SHADOW' && ' — V6 agents process content but do NOT publish (dry-run). Legacy workflow is primary.'}
          {pipelineMode === 'DISABLED' && ' — All pipeline tasks are stopped.'}
        </div>
      ) : null}

      {message ? <div style={{ background: C.successMuted, color: C.success, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{message}</div> : null}
      {error ? <div style={{ background: C.dangerMuted, color: C.danger, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{error}</div> : null}

      {/* Health Status Banner */}
      {health && health.health_status !== 'healthy' ? (
        <div
          role="alert"
          style={{
            background: health.health_status === 'unhealthy' ? C.dangerMuted : C.warningMuted,
            color: health.health_status === 'unhealthy' ? C.danger : C.warning,
            border: `1px solid ${C.border}`,
            borderRadius: '8px',
            padding: '12px 16px',
            fontSize: '13px',
          }}
        >
          Pipeline {health.health_status}: {health.stale_claims} stale claim(s), {health.errored_items} errored item(s), {health.stuck_items} stuck item(s)
        </div>
      ) : null}

      {/* Status Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '12px' }}>
        <MetricCard label="Backlog" value={statusCounts.backlog ?? 0} accent={STATUS_COLORS.BACKLOG} />
        <MetricCard label="In progress" value={(statusCounts.todo ?? 0) + (statusCounts.writing ?? 0) + (statusCounts.review ?? 0)} accent={C.accent} />
        <MetricCard label="Ready / Published" value={(statusCounts.ready_to_publish ?? 0) + (statusCounts.published ?? 0)} accent={C.success} />
        <MetricCard label="Done" value={statusCounts.done ?? 0} />
      </div>

      {/* Pipeline Stage Visualization */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px' }}>
        <div style={{ fontSize: '13px', color: C.text, fontWeight: 600, marginBottom: '12px' }}>Pipeline Stages</div>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'stretch' }}>
          {PIPELINE_STATUSES.map((status) => {
            const count = statusCounts[status.toLowerCase()] ?? 0;
            const isActive = statusFilter === status;
            return (
              <button
                key={status}
                onClick={() => setStatusFilter(isActive ? 'all' : status)}
                style={{
                  flex: 1,
                  padding: '10px 6px',
                  border: isActive ? `2px solid ${STATUS_COLORS[status] || C.accent}` : `1px solid ${C.border}`,
                  borderRadius: '6px',
                  cursor: 'pointer',
                  background: isActive ? 'rgba(200,147,90,0.08)' : C.bg,
                  color: C.text,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '18px', fontWeight: 600, color: STATUS_COLORS[status] || C.text, fontFamily: "'Instrument Serif', Georgia, serif" }}>
                  {count}
                </span>
                <span style={{ fontSize: '9px', color: C.textDim, textTransform: 'uppercase', letterSpacing: '0.04em', textAlign: 'center' }}>
                  {status.replace(/_/g, ' ')}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Agent Controls */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px' }}>
        <div style={{ fontSize: '13px', color: C.text, fontWeight: 600, marginBottom: '12px' }}>Agent Controls</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '8px' }}>
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              disabled={loading}
              onClick={() => withAction(`${agent.label} complete`, () => api.runAgent(agent.id))}
              style={{
                padding: '12px',
                border: `1px solid ${C.border}`,
                borderRadius: '6px',
                cursor: loading ? 'not-allowed' : 'pointer',
                background: C.bg,
                color: C.text,
                textAlign: 'left',
                opacity: loading ? 0.5 : 1,
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>{agent.label}</div>
              <div style={{ fontSize: '11px', color: C.textMuted }}>{agent.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Pipeline Items List */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <span style={{ fontSize: '13px', color: C.text, fontWeight: 600 }}>
            Pipeline Items {statusFilter !== 'all' ? `(${statusFilter.replace(/_/g, ' ')})` : ''}
          </span>
          <div style={{ display: 'flex', gap: '4px' }}>
            <select
              aria-label="Pipeline status filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '6px 8px', fontSize: '12px' }}
            >
              <option value="all">All statuses</option>
              {PIPELINE_STATUSES.map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
        </div>

        {filteredItems.length === 0 ? (
          <EmptyState
            title="No pipeline items"
            message="Run the Scout agent to seed the pipeline backlog from research sources."
          />
        ) : (
          <div style={{ display: 'grid', gap: '8px' }}>
            {filteredItems.slice(0, 20).map((item) => (
              <div
                key={item.id}
                style={{
                  border: `1px solid ${item.last_error ? 'rgba(248,113,113,0.2)' : C.border}`,
                  borderRadius: '6px',
                  padding: '12px',
                  background: C.bg,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: C.text }}>
                      {item.topic_keyword || item.pillar_theme || item.id.slice(0, 8)}
                    </div>
                    <div style={{ fontSize: '11px', color: C.textDim, marginTop: '2px' }}>
                      {item.pillar_theme ? `${item.pillar_theme}` : ''}
                      {item.sub_theme ? ` · ${item.sub_theme}` : ''}
                      {item.claimed_by ? ` · claimed by ${item.claimed_by}` : ''}
                    </div>
                  </div>
                  <StatusBadge status={item.status} />
                </div>

                {item.quality_score != null ? (
                  <div style={{ fontSize: '11px', color: C.textMuted, marginBottom: '4px' }}>
                    Quality: {item.quality_score.toFixed(1)} · Readability: {item.readability_score?.toFixed(1) || '-'} · Fact check: {item.fact_check_status || '-'}
                  </div>
                ) : null}

                {item.last_error ? (
                  <div style={{ fontSize: '11px', color: C.danger, marginBottom: '4px' }}>
                    Error: {truncate(item.last_error, 100)}
                  </div>
                ) : null}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                  <div style={{ fontSize: '10px', color: C.textDim }}>
                    Revisions: {item.revision_count}/{item.max_revisions} · {formatDate(item.updated_at)} {formatTime(item.updated_at)}
                  </div>
                  {item.draft_id ? (
                    <span style={{ fontSize: '10px', color: C.textDim }}>Draft: {item.draft_id.slice(0, 8)}</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
