import { useEffect, useMemo, useState } from 'react';
import { api } from '../../services/api';
import { C } from '../../constants/theme';
import Button from '../ui/Button';
import MetricCard from '../ui/MetricCard';
import OperationalAlerts from '../shared/OperationalAlerts';
import LoadingSpinner from '../shared/LoadingSpinner';
import ErrorMessage from '../shared/ErrorMessage';
import EmptyState from '../shared/EmptyState';

const METRIC_DEFAULTS = { impressions: 1000, reactions: 40, comments_count: 8, shares: 3 };
const ALERT_SNOOZE_KEY = 'app.dashboard.alertSnoozes';
const SNOOZE_MS = 2 * 60 * 60 * 1000;

function isDueNow(post) {
  if (!post || post.published_at || !post.scheduled_time) {
    return false;
  }
  const scheduledMs = Date.parse(post.scheduled_time);
  if (Number.isNaN(scheduledMs)) {
    return false;
  }
  return scheduledMs <= Date.now();
}

function getCountdownTickMs() {
  if (typeof window !== 'undefined') {
    const configured = Number(window.__APP_ALERT_TICK_MS__);
    if (Number.isFinite(configured) && configured > 0) {
      return configured;
    }
  }
  return 60_000;
}

export default function DashboardView() {
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [fetchError, setFetchError] = useState('');

  const [health, setHealth] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [adminConfig, setAdminConfig] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState([]);
  const [sources, setSources] = useState([]);
  const [report, setReport] = useState(null);

  const [publishUrl, setPublishUrl] = useState('https://linkedin.com/feed/update/urn:li:activity:');
  const [feedInput, setFeedInput] = useState('https://digiday.com/feed/,https://www.adexchanger.com/feed/');
  const [publishFilter, setPublishFilter] = useState(() => {
    try {
      return localStorage.getItem('app.dashboard.publishFilter') || 'all';
    } catch {
      return 'all';
    }
  });
  const [metricsTargetPostId, setMetricsTargetPostId] = useState('');
  const [metricsInput, setMetricsInput] = useState(METRIC_DEFAULTS);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const [alertSnoozes, setAlertSnoozes] = useState(() => {
    try {
      const raw = localStorage.getItem(ALERT_SNOOZE_KEY);
      const parsed = raw ? JSON.parse(raw) : {};
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch {
      return {};
    }
  });

  async function refreshData() {
    setFetchError('');
    try {
      const [healthRes, readinessRes, adminConfigRes, draftsRes, postsRes, commentsRes, sourcesRes, reportRes] = await Promise.all([
        api.health(),
        api.readiness(),
        api.adminConfig(),
        api.drafts(),
        api.posts(),
        api.comments(),
        api.sources(),
        api.dailyReport(),
      ]);

      setHealth(healthRes);
      setReadiness(readinessRes);
      setAdminConfig(adminConfigRes);
      setDrafts(draftsRes);
      setPosts(postsRes);
      setComments(commentsRes);
      setSources(sourcesRes);
      setReport(reportRes);

      if (!metricsTargetPostId && postsRes[0]?.id) {
        setMetricsTargetPostId(postsRes[0].id);
      }
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
      setMessage('Data refreshed');
    })();
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('app.dashboard.publishFilter', publishFilter);
    } catch {
      // ignore storage write failures in constrained environments
    }
  }, [publishFilter]);

  useEffect(() => {
    try {
      localStorage.setItem(ALERT_SNOOZE_KEY, JSON.stringify(alertSnoozes));
    } catch {
      // ignore storage write failures in constrained environments
    }
  }, [alertSnoozes]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setNowMs(Date.now());
    }, getCountdownTickMs());
    return () => clearInterval(intervalId);
  }, []);

  async function bootstrapDemoData() {
    const seedBody = `A practical observation on Adtech execution and what teams can do differently this week. [demo ${Date.now()}]`;
    const demoDraft = await api.createDraft({
      pillar_theme: 'Adtech fundamentals',
      sub_theme: 'Programmatic buying',
      format: 'TEXT',
      tone: 'EDUCATIONAL',
      content_body: seedBody,
      image_url: null,
      carousel_document_url: null,
    });

    await api.approveDraft(demoDraft.id);

    const refreshedPosts = await api.posts();
    const targetPost = refreshedPosts.find((post) => post.draft_id === demoDraft.id) || refreshedPosts[0];
    if (!targetPost) {
      throw new Error('No published post record created after draft approval');
    }

    await api.confirmPublish(targetPost.id, `${publishUrl}${Date.now()}`);
    await api.updateMetrics(targetPost.id, METRIC_DEFAULTS);
    await api.createComment({
      published_post_id: targetPost.id,
      commenter_name: 'Test User',
      comment_text: 'Great point. I would like to know how this applies to retail media.',
      commenter_follower_count: 500,
      commenter_profile_url: null,
    });
    await api.ingestSources(feedInput.split(',').map((s) => s.trim()).filter(Boolean));
    await api.sendDailyReport();
  }

  const publishQueueSummary = useMemo(() => {
    const dueNow = posts.filter((post) => isDueNow(post)).length;
    const unpublished = posts.filter((post) => !post.published_at).length;
    const published = posts.filter((post) => Boolean(post.published_at)).length;
    return {
      total: posts.length,
      dueNow,
      unpublished,
      published,
    };
  }, [posts]);

  const filteredPosts = useMemo(() => {
    if (publishFilter === 'unpublished') {
      return posts.filter((post) => !post.published_at);
    }
    if (publishFilter === 'published') {
      return posts.filter((post) => Boolean(post.published_at));
    }
    if (publishFilter === 'due_now') {
      return posts.filter((post) => isDueNow(post));
    }
    return posts;
  }, [posts, publishFilter]);

  const totalImpressions = posts.reduce((sum, post) => sum + Number(post.impressions || 0), 0);
  const escalatedCount = comments.filter((comment) => comment.escalated).length;
  const operationalAlerts = useMemo(() => {
    const alerts = [];
    if (adminConfig?.kill_switch) {
      alerts.push({ id: 'kill-switch', tone: 'critical', message: 'Kill switch is ON. Publishing workflows are halted.' });
    }
    if (adminConfig && !adminConfig.posting_enabled) {
      alerts.push({ id: 'posting-disabled', tone: 'warning', message: 'Posting is disabled. Scheduled posts will not be published.' });
    }
    if (publishQueueSummary.dueNow > 0) {
      alerts.push({
        id: 'due-posts',
        tone: 'warning',
        message: `${publishQueueSummary.dueNow} post(s) are due now and awaiting processing.`,
      });
    }
    if (escalatedCount > 0) {
      alerts.push({
        id: 'escalations',
        tone: 'info',
        message: `${escalatedCount} escalated comment(s) need manual follow-up.`,
      });
    }
    return alerts;
  }, [adminConfig, publishQueueSummary.dueNow, escalatedCount]);

  const visibleOperationalAlerts = (() => {
    const now = nowMs;
    return operationalAlerts.filter((alert) => {
      const until = Number(alertSnoozes[alert.id] || 0);
      return !until || until <= now;
    });
  })();

  const snoozedOperationalAlerts = (() => {
    const now = nowMs;
    return operationalAlerts
      .map((alert) => ({ ...alert, snoozedUntil: Number(alertSnoozes[alert.id] || 0) }))
      .filter((alert) => alert.snoozedUntil > now)
      .sort((a, b) => a.snoozedUntil - b.snoozedUntil);
  })();

  function snoozeAlert(alertId) {
    setAlertSnoozes((prev) => ({
      ...prev,
      [alertId]: Date.now() + SNOOZE_MS,
    }));
  }

  function clearSnoozes() {
    setAlertSnoozes({});
  }

  if (initialLoading) {
    return <LoadingSpinner label="Loading dashboard..." />;
  }

  if (fetchError && !health) {
    return <ErrorMessage error={`Failed to load dashboard: ${fetchError}`} onRetry={() => { setInitialLoading(true); refreshData().then(() => setInitialLoading(false)).catch(() => setInitialLoading(false)); }} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
            Execution Console
          </h1>
          <p style={{ fontSize: '13px', color: C.textMuted, marginTop: '4px', fontFamily: "'DM Sans', sans-serif" }}>
            Health: {health?.status || '-'} · Readiness: {String(readiness?.ready ?? '-')}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button disabled={loading} variant="default" onClick={() => withAction('Data refreshed', refreshData)}>Refresh now</Button>
          <Button disabled={loading} variant="primary" onClick={() => withAction('Demo bootstrap complete', bootstrapDemoData)}>Bootstrap demo</Button>
        </div>
      </div>

      {message ? <div style={{ background: C.successMuted, color: C.success, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{message}</div> : null}
      {error ? <div style={{ background: C.dangerMuted, color: C.danger, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{error}</div> : null}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '12px' }}>
        <MetricCard label="Posts tracked" value={publishQueueSummary.total} />
        <MetricCard label="Impressions" value={totalImpressions.toLocaleString()} />
        <MetricCard label="Escalated comments" value={escalatedCount} accent={C.danger} />
        <MetricCard label="Sources" value={sources.length} />
      </div>

      <OperationalAlerts
        visibleAlerts={visibleOperationalAlerts}
        snoozedAlerts={snoozedOperationalAlerts}
        nowMs={nowMs}
        onSnooze={snoozeAlert}
        onClearSnoozes={clearSnoozes}
      />

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: C.text, fontWeight: 600 }}>Publishing Queue</span>
          <Button disabled={loading} onClick={() => withAction('Due posts processed', () => api.publishDue())}>Run Due</Button>
        </div>
        <div style={{ display: 'flex', gap: '10px', fontSize: '12px', color: C.textMuted }}>
          <span>Posts tracked: {publishQueueSummary.total}</span>
          <span>Due now: {publishQueueSummary.dueNow}</span>
          <span>Unpublished: {publishQueueSummary.unpublished}</span>
          <span>Published: {publishQueueSummary.published}</span>
        </div>

        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          LinkedIn post URL
          <input style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} value={publishUrl} onChange={(e) => setPublishUrl(e.target.value)} />
        </label>

        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Queue filter
          <select
            aria-label="Queue filter"
            value={publishFilter}
            onChange={(e) => setPublishFilter(e.target.value)}
            style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }}
          >
            <option value="all">All</option>
            <option value="due_now">Due now</option>
            <option value="unpublished">Unpublished</option>
            <option value="published">Published</option>
          </select>
        </label>

        {posts.length === 0 ? (
          <EmptyState
            title="No posts yet"
            message="Generate and approve a draft to create your first post. Use 'Bootstrap demo' for a quick start."
          />
        ) : (
          <div style={{ display: 'grid', gap: '8px' }}>
            {filteredPosts.slice(0, 5).map((post) => (
              <div key={post.id} style={{ border: `1px solid ${C.border}`, borderRadius: '6px', padding: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '12px', color: C.textMuted }}>
                  <strong style={{ color: C.text }}>{post.id.slice(0, 8)}</strong>
                  <div>Published: {post.published_at ? 'yes' : 'no'}{isDueNow(post) ? ' \u00b7 due now' : ''}</div>
                </div>
                <Button disabled={loading} size="sm" onClick={() => withAction('Manual publish confirmed', () => api.confirmPublish(post.id, `${publishUrl}${Date.now()}`))}>Confirm publish</Button>
              </div>
            ))}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: '8px' }}>
          <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
            Metrics post id
            <select
              aria-label="Metrics post id"
              value={metricsTargetPostId}
              onChange={(e) => setMetricsTargetPostId(e.target.value)}
              style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }}
            >
              <option value="">Select post</option>
              {posts.map((post) => (
                <option key={post.id} value={post.id}>{post.id}</option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
            Impressions
            <input type="number" value={metricsInput.impressions} onChange={(e) => setMetricsInput((prev) => ({ ...prev, impressions: Number(e.target.value || 0) }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
          </label>
          <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
            Reactions
            <input type="number" value={metricsInput.reactions} onChange={(e) => setMetricsInput((prev) => ({ ...prev, reactions: Number(e.target.value || 0) }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
          </label>
          <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
            Comments
            <input type="number" value={metricsInput.comments_count} onChange={(e) => setMetricsInput((prev) => ({ ...prev, comments_count: Number(e.target.value || 0) }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
          </label>
          <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
            Shares
            <input type="number" value={metricsInput.shares} onChange={(e) => setMetricsInput((prev) => ({ ...prev, shares: Number(e.target.value || 0) }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
          </label>
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <Button disabled={loading || !metricsTargetPostId} onClick={() => withAction('Post metrics updated', () => api.updateMetrics(metricsTargetPostId, metricsInput))}>Update metrics</Button>
          <Button disabled={loading} onClick={() => withAction('Daily report sent', () => api.sendDailyReport())}>Send</Button>
        </div>

        {report ? (
          <div style={{ fontSize: '12px', color: C.textMuted }}>
            Published: {report.posts_published} · Impressions: {report.total_impressions} · Reactions: {report.total_reactions} · Comments: {report.total_comments} · Shares: {report.total_shares}
          </div>
        ) : null}
      </div>

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px', display: 'grid', gap: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: C.text, fontWeight: 600 }}>Sources</span>
          <Button disabled={loading} onClick={() => withAction('Sources ingested', () => api.ingestSources(feedInput.split(',').map((s) => s.trim()).filter(Boolean)))}>Ingest</Button>
        </div>
        <div style={{ fontSize: '12px', color: C.textMuted }}>Sources: {sources.length}</div>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Feed URLs (comma separated)
          <textarea rows={3} value={feedInput} onChange={(e) => setFeedInput(e.target.value)} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
      </div>

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px' }}>
        <span style={{ fontSize: '13px', color: C.text, fontWeight: 600 }}>Draft inventory</span>
        <div style={{ fontSize: '12px', color: C.textMuted, marginTop: '6px' }}>Pending: {drafts.filter((d) => d.status === 'PENDING').length}</div>
      </div>
    </div>
  );
}
