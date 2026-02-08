import { useEffect, useMemo, useState } from 'react';
import Panel from './components/Panel';
import { api } from './services/api';

const METRIC_DEFAULTS = { impressions: 1000, reactions: 40, comments_count: 8, shares: 3 };
const DRAFT_DEFAULTS = {
  pillar_theme: 'Adtech fundamentals',
  sub_theme: 'Programmatic buying',
  format: 'TEXT',
  tone: 'EDUCATIONAL',
  content_body: 'A practical observation on Adtech execution and what teams can do differently this week.',
  image_url: '',
  carousel_document_url: '',
};

function countWords(text) {
  return (text || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

function extractHashtags(text) {
  return (text || '').match(/#[\p{L}\p{N}_-]+/gu) || [];
}

function hasExternalLink(text) {
  return /(https?:\/\/|www\.)/i.test(text || '');
}

function includesTopicHint(text, draft) {
  const body = String(text || '').toLowerCase();
  const pillar = String(draft?.pillar_theme || '').toLowerCase().trim();
  const subTheme = String(draft?.sub_theme || '').toLowerCase().trim();
  if (!pillar && !subTheme) {
    return true;
  }
  return Boolean((pillar && body.includes(pillar)) || (subTheme && body.includes(subTheme)));
}

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

export default function App() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [health, setHealth] = useState(null);
  const [deepHealth, setDeepHealth] = useState(null);
  const [readiness, setReadiness] = useState(null);

  const [drafts, setDrafts] = useState([]);
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState([]);
  const [sources, setSources] = useState([]);
  const [learning, setLearning] = useState(null);
  const [report, setReport] = useState(null);
  const [adminConfig, setAdminConfig] = useState(null);
  const [alignment, setAlignment] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [engagementStatus, setEngagementStatus] = useState(null);

  const [rejectReason, setRejectReason] = useState('Not aligned with strategy');
  const [publishUrl, setPublishUrl] = useState('https://linkedin.com/feed/update/urn:li:activity:');
  const [publishFilter, setPublishFilter] = useState('all');
  const [feedInput, setFeedInput] = useState('https://digiday.com/feed/,https://www.adexchanger.com/feed/');

  const [manualDraft, setManualDraft] = useState(DRAFT_DEFAULTS);
  const [metricsTargetPostId, setMetricsTargetPostId] = useState('');
  const [metricsInput, setMetricsInput] = useState(METRIC_DEFAULTS);
  const [commentInput, setCommentInput] = useState({
    published_post_id: '',
    commenter_name: 'Test User',
    comment_text: 'Great point. I would like to know how this applies to retail media.',
    commenter_follower_count: 500,
    commenter_profile_url: '',
  });

  async function withAction(label, fn) {
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await fn();
      setMessage(label);
      await refreshAll();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  async function refreshAll() {
    const [
      healthRes,
      deepHealthRes,
      readinessRes,
      draftsRes,
      postsRes,
      commentsRes,
      sourcesRes,
      learningRes,
      reportRes,
      adminRes,
      alignmentRes,
      auditsRes,
      engagementRes,
    ] = await Promise.all([
      api.health(),
      api.deepHealth(),
      api.readiness(),
      api.drafts(),
      api.posts(),
      api.comments(),
      api.sources(),
      api.learningWeights(),
      api.dailyReport(),
      api.adminConfig(),
      api.algorithmAlignment(),
      api.auditLogs(),
      api.engagementStatus(),
    ]);

    setHealth(healthRes);
    setDeepHealth(deepHealthRes);
    setReadiness(readinessRes);
    setDrafts(draftsRes);
    setPosts(postsRes);
    setComments(commentsRes);
    setSources(sourcesRes);
    setLearning(learningRes);
    setReport(reportRes);
    setAdminConfig(adminRes);
    setAlignment(alignmentRes);
    setAuditLogs(auditsRes.slice(0, 12));
    setEngagementStatus(engagementRes);

    const firstPostId = postsRes[0]?.id || '';
    if (firstPostId) {
      if (!metricsTargetPostId) {
        setMetricsTargetPostId(firstPostId);
      }
      if (!commentInput.published_post_id) {
        setCommentInput((prev) => ({ ...prev, published_post_id: firstPostId }));
      }
    }
  }

  useEffect(() => {
    withAction('Data refreshed', refreshAll);
  }, []);

  async function bootstrapDemoData() {
    const demoDraft = await api.createDraft({
      ...DRAFT_DEFAULTS,
      content_body: `${DRAFT_DEFAULTS.content_body} [demo ${Date.now()}]`,
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
      ...commentInput,
      published_post_id: targetPost.id,
      commenter_profile_url: commentInput.commenter_profile_url || null,
    });
    await api.ingestSources(feedInput.split(',').map((s) => s.trim()).filter(Boolean));
    await api.sendDailyReport();
  }

  const pendingDrafts = useMemo(() => drafts.filter((d) => d.status === 'PENDING'), [drafts]);
  const escalatedComments = useMemo(() => comments.filter((comment) => comment.escalated), [comments]);
  const latestDraftForPublishing = useMemo(() => {
    if (pendingDrafts.length > 0) {
      return pendingDrafts[0];
    }
    return drafts[0] || null;
  }, [drafts, pendingDrafts]);
  const publishChecklist = useMemo(() => {
    const content = latestDraftForPublishing?.content_body || '';
    const hashtags = extractHashtags(content);
    const words = countWords(content);
    const hasLink = hasExternalLink(content);
    const topicalMatch = includesTopicHint(content, latestDraftForPublishing);
    const violations = [];

    if (hashtags.length > 3) {
      violations.push(`Hashtag count high (${hashtags.length}). Keep to 1-3.`);
    }
    if (hasLink) {
      violations.push('External link detected in body. Prefer native post text.');
    }
    if (words > 300) {
      violations.push(`Word count above 300 (${words}).`);
    }
    if (!topicalMatch) {
      violations.push('Topic mismatch risk. Body may not match selected pillar or sub-theme.');
    }

    return {
      ready: violations.length === 0 && Boolean(content),
      hashtags,
      words,
      hasLink,
      topicalMatch,
      violations,
    };
  }, [latestDraftForPublishing]);
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

  async function copyDraftBodyForManualPublish() {
    const content = latestDraftForPublishing?.content_body || '';
    if (!content) {
      throw new Error('No draft content available to copy');
    }
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(content);
      return;
    }
    throw new Error('Clipboard API unavailable in this browser');
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <p className="eyebrow">LinkedIn Brand Operations</p>
        <h1>Execution Console</h1>
        <p>
          Single interface for content, publishing, engagement, learning, and platform-alignment controls.
        </p>
        <div className="hero-meta">
          <span>Health: {health?.status || '-'}</span>
          <span>Readiness: {String(readiness?.ready ?? '-')}</span>
          <span>Deep: {deepHealth?.status || '-'}</span>
        </div>
      </header>

      {message ? <div className="banner success">{message}</div> : null}
      {error ? <div className="banner error">{error}</div> : null}

      <main className="grid">
        <Panel
          title="Playground"
          action={
            <button disabled={loading} onClick={() => withAction('Demo bootstrap complete', bootstrapDemoData)}>
              Bootstrap demo
            </button>
          }
        >
          <p>One click flow to create draft, approve, confirm publish, update metrics, add comment, ingest sources, and send report.</p>
          <div className="row-actions">
            <button disabled={loading} onClick={() => withAction('Data refreshed', refreshAll)}>Refresh now</button>
          </div>
        </Panel>

        <Panel
          title="Manual Publish Assistant"
          action={
            <button
              disabled={loading || !latestDraftForPublishing?.content_body}
              onClick={() => withAction('Draft body copied for manual publish', copyDraftBodyForManualPublish)}
            >
              Copy draft body
            </button>
          }
        >
          <p>Draft in focus: {latestDraftForPublishing?.id ? String(latestDraftForPublishing.id).slice(0, 8) : 'none'}</p>
          <ul className="metrics">
            <li>Words: {publishChecklist.words}</li>
            <li>Hashtags: {publishChecklist.hashtags.length}</li>
            <li>External link in body: {publishChecklist.hasLink ? 'yes' : 'no'}</li>
            <li>Topic consistency hint: {publishChecklist.topicalMatch ? 'aligned' : 'review'}</li>
          </ul>
          {publishChecklist.ready ? (
            <div className="banner success">Checklist passed. Ready for manual LinkedIn publishing.</div>
          ) : (
            <div className="banner error">
              {publishChecklist.violations.length ? publishChecklist.violations.join(' ') : 'No draft content available.'}
            </div>
          )}
          <p>Golden hour rule: reply to meaningful comments in the first 60-90 minutes after publish confirmation.</p>
        </Panel>

        <Panel
          title="Drafts"
          action={<button disabled={loading} onClick={() => withAction('Draft generated', () => api.generateDraft())}>Generate</button>}
        >
          <p>Pending: {pendingDrafts.length}</p>
          <div className="list">
            {pendingDrafts.slice(0, 5).map((draft) => (
              <div className="list-row" key={draft.id}>
                <div>
                  <strong>{draft.pillar_theme}</strong>
                  <p>{draft.sub_theme}</p>
                </div>
                <div className="row-actions">
                  <button disabled={loading} onClick={() => withAction('Draft approved', () => api.approveDraft(draft.id))}>Approve</button>
                  <button
                    disabled={loading}
                    onClick={() => withAction('Draft rejected', () => api.rejectDraft(draft.id, rejectReason))}
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
          <label>
            Reject reason
            <input value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} />
          </label>
          <div className="form-grid">
            <label>
              Pillar theme
              <input
                value={manualDraft.pillar_theme}
                onChange={(e) => setManualDraft((prev) => ({ ...prev, pillar_theme: e.target.value }))}
              />
            </label>
            <label>
              Sub theme
              <input
                value={manualDraft.sub_theme}
                onChange={(e) => setManualDraft((prev) => ({ ...prev, sub_theme: e.target.value }))}
              />
            </label>
            <label>
              Format
              <select
                value={manualDraft.format}
                onChange={(e) => setManualDraft((prev) => ({ ...prev, format: e.target.value }))}
              >
                <option value="TEXT">TEXT</option>
                <option value="IMAGE">IMAGE</option>
                <option value="CAROUSEL">CAROUSEL</option>
              </select>
            </label>
            <label>
              Tone
              <select
                value={manualDraft.tone}
                onChange={(e) => setManualDraft((prev) => ({ ...prev, tone: e.target.value }))}
              >
                <option value="EDUCATIONAL">EDUCATIONAL</option>
                <option value="OPINIONATED">OPINIONATED</option>
                <option value="DIRECT">DIRECT</option>
                <option value="EXPLORATORY">EXPLORATORY</option>
              </select>
            </label>
            <label className="span-2">
              Content body
              <textarea
                rows={3}
                value={manualDraft.content_body}
                onChange={(e) => setManualDraft((prev) => ({ ...prev, content_body: e.target.value }))}
              />
            </label>
            <div className="row-actions span-2">
              <button
                disabled={loading}
                onClick={() =>
                  withAction('Manual draft created', () =>
                    api.createDraft({
                      ...manualDraft,
                      image_url: manualDraft.image_url || null,
                      carousel_document_url: manualDraft.carousel_document_url || null,
                    }),
                  )
                }
              >
                Create Draft
              </button>
            </div>
          </div>
        </Panel>

        <Panel
          title="Publishing"
          action={<button disabled={loading} onClick={() => withAction('Due posts processed', () => api.publishDue())}>Run Due</button>}
        >
          <p>Posts tracked: {publishQueueSummary.total}</p>
          <ul className="metrics">
            <li>Due now: {publishQueueSummary.dueNow}</li>
            <li>Unpublished: {publishQueueSummary.unpublished}</li>
            <li>Published: {publishQueueSummary.published}</li>
          </ul>
          <label>
            LinkedIn post URL
            <input value={publishUrl} onChange={(e) => setPublishUrl(e.target.value)} />
          </label>
          <label>
            Queue filter
            <select value={publishFilter} onChange={(e) => setPublishFilter(e.target.value)}>
              <option value="all">All</option>
              <option value="due_now">Due now</option>
              <option value="unpublished">Unpublished</option>
              <option value="published">Published</option>
            </select>
          </label>
          <div className="list">
            {filteredPosts.slice(0, 5).map((post) => (
              <div className="list-row" key={post.id}>
                <div>
                  <strong>{post.id.slice(0, 8)}</strong>
                  <p>Published: {post.published_at ? 'yes' : 'no'}{isDueNow(post) ? ' • due now' : ''}</p>
                </div>
                <button
                  disabled={loading}
                  onClick={() => withAction('Manual publish confirmed', () => api.confirmPublish(post.id, publishUrl + Date.now()))}
                >
                  Confirm publish
                </button>
              </div>
            ))}
          </div>
          <div className="form-grid">
            <label>
              Metrics post id
              <select
                value={metricsTargetPostId}
                onChange={(e) => setMetricsTargetPostId(e.target.value)}
              >
                <option value="">Select post</option>
                {posts.map((post) => (
                  <option key={post.id} value={post.id}>{post.id}</option>
                ))}
              </select>
            </label>
            <label>
              Impressions
              <input
                type="number"
                value={metricsInput.impressions}
                onChange={(e) => setMetricsInput((prev) => ({ ...prev, impressions: Number(e.target.value || 0) }))}
              />
            </label>
            <label>
              Reactions
              <input
                type="number"
                value={metricsInput.reactions}
                onChange={(e) => setMetricsInput((prev) => ({ ...prev, reactions: Number(e.target.value || 0) }))}
              />
            </label>
            <label>
              Comments
              <input
                type="number"
                value={metricsInput.comments_count}
                onChange={(e) => setMetricsInput((prev) => ({ ...prev, comments_count: Number(e.target.value || 0) }))}
              />
            </label>
            <label>
              Shares
              <input
                type="number"
                value={metricsInput.shares}
                onChange={(e) => setMetricsInput((prev) => ({ ...prev, shares: Number(e.target.value || 0) }))}
              />
            </label>
            <div className="row-actions span-2">
              <button
                disabled={loading || !metricsTargetPostId}
                onClick={() => withAction('Post metrics updated', () => api.updateMetrics(metricsTargetPostId, metricsInput))}
              >
                Update metrics
              </button>
            </div>
          </div>
        </Panel>

        <Panel
          title="Engagement"
          action={<button disabled={loading} onClick={() => withAction('Engagement poll complete', () => api.pollEngagement())}>Poll</button>}
        >
          <p>Comments stored: {comments.length}</p>
          <p>Due for poll: {engagementStatus?.due_total ?? '-'}</p>
          <p>Active monitoring: {engagementStatus?.active_total ?? '-'}</p>
          <div className="form-grid">
            <label>
              Comment post id
              <select
                value={commentInput.published_post_id}
                onChange={(e) => setCommentInput((prev) => ({ ...prev, published_post_id: e.target.value }))}
              >
                <option value="">Select post</option>
                {posts.map((post) => (
                  <option key={post.id} value={post.id}>{post.id}</option>
                ))}
              </select>
            </label>
            <label>
              Commenter name
              <input
                value={commentInput.commenter_name}
                onChange={(e) => setCommentInput((prev) => ({ ...prev, commenter_name: e.target.value }))}
              />
            </label>
            <label>
              Follower count
              <input
                type="number"
                value={commentInput.commenter_follower_count}
                onChange={(e) =>
                  setCommentInput((prev) => ({ ...prev, commenter_follower_count: Number(e.target.value || 0) }))
                }
              />
            </label>
            <label className="span-2">
              Comment text
              <textarea
                rows={2}
                value={commentInput.comment_text}
                onChange={(e) => setCommentInput((prev) => ({ ...prev, comment_text: e.target.value }))}
              />
            </label>
            <div className="row-actions span-2">
              <button
                disabled={loading || !commentInput.published_post_id}
                onClick={() =>
                  withAction('Comment added', () =>
                    api.createComment({
                      ...commentInput,
                      commenter_profile_url: commentInput.commenter_profile_url || null,
                    }),
                  )
                }
              >
                Add Comment
              </button>
            </div>
          </div>
        </Panel>

        <Panel title="Escalations">
          <p>Escalated comments: {escalatedComments.length}</p>
          <div className="list">
            {escalatedComments.slice(0, 5).map((comment) => (
              <div className="list-row" key={comment.id}>
                <div>
                  <strong>{comment.commenter_name}</strong>
                  <p>{comment.high_value_reason || 'REVIEW'}</p>
                </div>
                <span>{comment.comment_text}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title="Sources"
          action={
            <button
              disabled={loading}
              onClick={() =>
                withAction('Sources ingested', () => api.ingestSources(feedInput.split(',').map((s) => s.trim()).filter(Boolean)))
              }
            >
              Ingest
            </button>
          }
        >
          <p>Sources: {sources.length}</p>
          <label>
            Feed URLs (comma separated)
            <textarea value={feedInput} onChange={(e) => setFeedInput(e.target.value)} rows={3} />
          </label>
        </Panel>

        <Panel
          title="Learning"
          action={<button disabled={loading} onClick={() => withAction('Learning recomputed', () => api.recomputeLearning())}>Recompute</button>}
        >
          <div className="code-block">{learning ? learning.format_weights_json : '{}'}</div>
          <div className="code-block">{learning ? learning.tone_weights_json : '{}'}</div>
        </Panel>

        <Panel
          title="Reports"
          action={<button disabled={loading} onClick={() => withAction('Daily report sent', () => api.sendDailyReport())}>Send</button>}
        >
          {report ? (
            <ul className="metrics">
              <li>Published: {report.posts_published}</li>
              <li>Impressions: {report.total_impressions}</li>
              <li>Reactions: {report.total_reactions}</li>
              <li>Comments: {report.total_comments}</li>
              <li>Shares: {report.total_shares}</li>
            </ul>
          ) : null}
        </Panel>

        <Panel title="Controls">
          <div className="row-actions">
            <button disabled={loading} onClick={() => withAction('Kill switch enabled', () => api.killSwitchOn())}>Kill ON</button>
            <button disabled={loading} onClick={() => withAction('Kill switch disabled', () => api.killSwitchOff())}>Kill OFF</button>
            <button disabled={loading} onClick={() => withAction('Posting enabled', () => api.postingOn())}>Posting ON</button>
            <button disabled={loading} onClick={() => withAction('Posting disabled', () => api.postingOff())}>Posting OFF</button>
          </div>
          <div className="code-block">{JSON.stringify(adminConfig || {}, null, 2)}</div>
        </Panel>

        <Panel title="Algorithm Alignment">
          <div className="code-block">{JSON.stringify(alignment || {}, null, 2)}</div>
        </Panel>

        <Panel title="Audit Trail">
          <div className="list compact">
            {auditLogs.map((row) => (
              <div className="list-row" key={row.id}>
                <div>
                  <strong>{row.action}</strong>
                  <p>{row.actor} • {row.resource_type}</p>
                </div>
                <span>{new Date(row.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </Panel>
      </main>
    </div>
  );
}
