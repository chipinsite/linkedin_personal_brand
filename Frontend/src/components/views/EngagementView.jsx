import { useEffect, useMemo, useState } from 'react';
import { api } from '../../services/api';
import { C } from '../../constants/theme';
import Button from '../ui/Button';
import MetricCard from '../ui/MetricCard';
import StatusBadge from '../ui/StatusBadge';
import LoadingSpinner from '../shared/LoadingSpinner';
import ErrorMessage from '../shared/ErrorMessage';
import EmptyState from '../shared/EmptyState';

export default function EngagementView() {
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [fetchError, setFetchError] = useState('');

  const [comments, setComments] = useState([]);
  const [posts, setPosts] = useState([]);
  const [engagementStatus, setEngagementStatus] = useState(null);

  const [filter, setFilter] = useState('all');
  const [commentInput, setCommentInput] = useState({
    published_post_id: '',
    commenter_name: 'Test User',
    comment_text: 'Great point. I would like to know how this applies to retail media.',
    commenter_follower_count: 500,
    commenter_profile_url: '',
  });

  async function refreshData() {
    setFetchError('');
    try {
      const [commentsRes, postsRes, engagementStatusRes] = await Promise.all([
        api.comments(),
        api.posts(),
        api.engagementStatus(),
      ]);
      setComments(commentsRes);
      setPosts(postsRes);
      setEngagementStatus(engagementStatusRes);
      if (!commentInput.published_post_id && postsRes[0]?.id) {
        setCommentInput((prev) => ({ ...prev, published_post_id: postsRes[0].id }));
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
    })();
  }, []);

  const escalatedComments = useMemo(() => comments.filter((comment) => comment.escalated), [comments]);
  const filteredComments = useMemo(() => {
    if (filter === 'escalated') return comments.filter((comment) => comment.escalated);
    if (filter === 'replied') return comments.filter((comment) => comment.auto_reply_sent);
    return comments;
  }, [comments, filter]);

  if (initialLoading) {
    return <LoadingSpinner label="Loading engagement..." />;
  }

  if (fetchError && comments.length === 0) {
    return <ErrorMessage error={`Failed to load engagement: ${fetchError}`} onRetry={() => { setInitialLoading(true); refreshData().finally(() => setInitialLoading(false)); }} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
          Engagement
        </h2>
        <Button disabled={loading} onClick={() => withAction('Engagement poll complete', () => api.pollEngagement())}>Poll</Button>
      </div>

      {message ? <div style={{ background: C.successMuted, color: C.success, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{message}</div> : null}
      {error ? <div style={{ background: C.dangerMuted, color: C.danger, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{error}</div> : null}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <MetricCard label="Comments stored" value={comments.length} />
        <MetricCard label="Escalated" value={escalatedComments.length} accent={C.danger} />
        <MetricCard label="Due for poll" value={engagementStatus?.due_total ?? '-'} />
      </div>

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '4px', background: C.bg, border: `1px solid ${C.border}`, borderRadius: '6px', padding: '4px', width: 'fit-content' }}>
          {['all', 'escalated', 'replied'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '6px 14px',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                background: filter === f ? C.surfaceHover : 'transparent',
                color: filter === f ? C.text : C.textMuted,
                fontSize: '12px',
                fontWeight: 500,
                textTransform: 'capitalize',
              }}
            >
              {f}
            </button>
          ))}
        </div>

        <div style={{ display: 'grid', gap: '12px', marginTop: '12px' }}>
          <div style={{ fontSize: '12px', color: C.textMuted }}>Escalated comments: {escalatedComments.length}</div>
          {filteredComments.length === 0 ? (
            <EmptyState title="No comments" message="Comments will appear here once engagement polling detects them on published posts." />
          ) : null}
          {filteredComments.map((comment) => (
            <div key={comment.id} style={{ background: C.bg, border: `1px solid ${comment.escalated ? 'rgba(248,113,113,0.2)' : C.border}`, borderRadius: '8px', padding: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <div style={{ fontSize: '13px', color: C.text, fontWeight: 600 }}>{comment.commenter_name}</div>
                  <div style={{ fontSize: '12px', color: C.textDim }}>
                    {comment.commenter_follower_count?.toLocaleString()} followers
                    {comment.high_value_reason ? ` · ${comment.high_value_reason}` : ''}
                  </div>
                </div>
                {comment.escalated && !comment.auto_reply_sent ? <StatusBadge status="ESCALATED" /> : null}
                {comment.auto_reply_sent ? <StatusBadge status="PUBLISHED" /> : null}
              </div>
              <p style={{ fontSize: '13px', color: C.textMuted, margin: 0 }}>{comment.comment_text}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px', display: 'grid', gap: '8px' }}>
        <div style={{ fontSize: '13px', color: C.text, fontWeight: 600 }}>Add comment</div>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Comment post id
          <select
            aria-label="Comment post id"
            value={commentInput.published_post_id}
            onChange={(e) => setCommentInput((prev) => ({ ...prev, published_post_id: e.target.value }))}
            style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }}
          >
            <option value="">Select post</option>
            {posts.map((post) => (
              <option key={post.id} value={post.id}>{post.id}</option>
            ))}
          </select>
        </label>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Commenter name
          <input value={commentInput.commenter_name} onChange={(e) => setCommentInput((prev) => ({ ...prev, commenter_name: e.target.value }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Follower count
          <input type="number" value={commentInput.commenter_follower_count} onChange={(e) => setCommentInput((prev) => ({ ...prev, commenter_follower_count: Number(e.target.value || 0) }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Comment text
          <textarea rows={2} value={commentInput.comment_text} onChange={(e) => setCommentInput((prev) => ({ ...prev, comment_text: e.target.value }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
        <Button
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
        </Button>
      </div>
    </div>
  );
}
