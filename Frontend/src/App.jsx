import { useEffect, useMemo, useState } from 'react';
import Panel from './components/Panel';
import { api } from './services/api';

const initialMetrics = { impressions: 1000, reactions: 40, comments_count: 8, shares: 3 };

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
  const [feedInput, setFeedInput] = useState('https://digiday.com/feed/,https://www.adexchanger.com/feed/');

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
  }

  useEffect(() => {
    withAction('Data refreshed', refreshAll);
  }, []);

  const pendingDrafts = useMemo(() => drafts.filter((d) => d.status === 'PENDING'), [drafts]);

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
        </Panel>

        <Panel
          title="Publishing"
          action={<button disabled={loading} onClick={() => withAction('Due posts processed', () => api.publishDue())}>Run Due</button>}
        >
          <p>Posts tracked: {posts.length}</p>
          <div className="list">
            {posts.slice(0, 5).map((post) => (
              <div className="list-row" key={post.id}>
                <div>
                  <strong>{post.id.slice(0, 8)}</strong>
                  <p>Published: {post.published_at ? 'yes' : 'no'}</p>
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
        </Panel>

        <Panel
          title="Engagement"
          action={<button disabled={loading} onClick={() => withAction('Engagement poll complete', () => api.pollEngagement())}>Poll</button>}
        >
          <p>Comments stored: {comments.length}</p>
          <p>Due for poll: {engagementStatus?.due_total ?? '-'}</p>
          <p>Active monitoring: {engagementStatus?.active_total ?? '-'}</p>
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
