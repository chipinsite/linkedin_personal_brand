import { useEffect, useMemo, useState } from 'react';
import { api } from '../../services/api';
import { C, Icons, formatDate } from '../../constants/theme';
import Button from '../ui/Button';
import StatusBadge from '../ui/StatusBadge';

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
  return (text || '').trim().split(/\s+/).filter(Boolean).length;
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

export default function ContentView() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [drafts, setDrafts] = useState([]);
  const [selectedDraftId, setSelectedDraftId] = useState('');
  const [rejectReason, setRejectReason] = useState('Not aligned with strategy');
  const [manualDraft, setManualDraft] = useState(DRAFT_DEFAULTS);

  async function refreshDrafts() {
    const draftRes = await api.drafts();
    setDrafts(draftRes);
    if (!selectedDraftId && draftRes[0]?.id) {
      setSelectedDraftId(draftRes[0].id);
    }
  }

  async function withAction(label, fn) {
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await fn();
      setMessage(label);
      await refreshDrafts();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    withAction('Data refreshed', refreshDrafts);
  }, []);

  const pendingDrafts = useMemo(() => drafts.filter((d) => d.status === 'PENDING'), [drafts]);
  const selectedDraft = useMemo(() => drafts.find((d) => d.id === selectedDraftId) || pendingDrafts[0] || drafts[0] || null, [drafts, pendingDrafts, selectedDraftId]);

  const publishChecklist = useMemo(() => {
    const content = selectedDraft?.content_body || '';
    const hashtags = extractHashtags(content);
    const words = countWords(content);
    const hasLink = hasExternalLink(content);
    const topicalMatch = includesTopicHint(content, selectedDraft);
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

    return { words, hashtags, hasLink, topicalMatch, violations, ready: violations.length === 0 && Boolean(content) };
  }, [selectedDraft]);

  async function copyDraftBodyForManualPublish() {
    const content = selectedDraft?.content_body || '';
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
          Content Pipeline
        </h2>
        <Button disabled={loading} variant="primary" onClick={() => withAction('Draft generated', () => api.generateDraft())}>Generate</Button>
      </div>

      {message ? <div style={{ background: C.successMuted, color: C.success, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{message}</div> : null}
      {error ? <div style={{ background: C.dangerMuted, color: C.danger, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>{error}</div> : null}

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px', display: 'grid', gap: '8px' }}>
        <div style={{ fontSize: '12px', color: C.textMuted }}>Pending: {pendingDrafts.length}</div>
        {pendingDrafts.slice(0, 5).map((draft) => (
          <div key={draft.id} style={{ border: `1px solid ${C.border}`, borderRadius: '6px', padding: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ color: C.text, fontSize: '13px' }}>{draft.pillar_theme}</strong>
              <p style={{ color: C.textMuted, fontSize: '12px', margin: 0 }}>{draft.sub_theme}</p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button disabled={loading} size="sm" variant="primary" onClick={() => withAction('Draft approved', () => api.approveDraft(draft.id))}>Approve</Button>
              <Button disabled={loading} size="sm" variant="danger" onClick={() => withAction('Draft rejected', () => api.rejectDraft(draft.id, rejectReason))}>Reject</Button>
            </div>
          </div>
        ))}
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Reject reason
          <input value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '20px', minHeight: '400px' }}>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', overflow: 'hidden' }}>
          <div style={{ padding: '14px 16px', borderBottom: `1px solid ${C.border}` }}>
            <span style={{ fontSize: '12px', color: C.textMuted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Drafts ({drafts.length})
            </span>
          </div>
          {drafts.map((draft) => (
            <button
              key={draft.id}
              onClick={() => setSelectedDraftId(draft.id)}
              style={{
                width: '100%',
                border: 'none',
                textAlign: 'left',
                padding: '14px 16px',
                borderBottom: `1px solid ${C.border}`,
                cursor: 'pointer',
                background: selectedDraft?.id === draft.id ? C.surfaceHover : 'transparent',
                color: C.text,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', color: C.textDim }}>{formatDate(draft.created_at)}</span>
                <StatusBadge status={draft.status} />
              </div>
              <p style={{ fontSize: '12px', color: C.textMuted, margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                {draft.pillar_theme}
              </p>
              <p style={{ fontSize: '13px', color: C.text, margin: 0, lineHeight: 1.4 }}>
                {(draft.content_body || '').slice(0, 80)}
              </p>
            </button>
          ))}
        </div>

        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '16px 20px', borderBottom: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '11px', color: C.textDim, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Draft in focus: {selectedDraft?.id ? String(selectedDraft.id).slice(0, 8) : 'none'}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              {selectedDraft?.format ? <StatusBadge status={selectedDraft.format} /> : null}
              {selectedDraft?.tone ? <StatusBadge status={selectedDraft.tone} /> : null}
            </div>
          </div>

          <div style={{ padding: '12px 20px', borderBottom: `1px solid ${C.border}`, background: 'rgba(200,147,90,0.03)' }}>
            <div style={{ display: 'grid', gap: '6px', fontSize: '12px', color: C.textMuted }}>
              <span>Words: {publishChecklist.words}</span>
              <span>Hashtags: {publishChecklist.hashtags.length}</span>
              <span>External link in body: {publishChecklist.hasLink ? 'yes' : 'no'}</span>
              <span>Topic consistency hint: {publishChecklist.topicalMatch ? 'aligned' : 'review'}</span>
            </div>
            {publishChecklist.ready ? (
              <div style={{ marginTop: '8px', color: C.success, fontSize: '12px' }}>Checklist passed. Ready for manual LinkedIn publishing.</div>
            ) : (
              <div style={{ marginTop: '8px', color: C.warning, fontSize: '12px' }}>
                {publishChecklist.violations.length ? publishChecklist.violations.join(' ') : 'No draft content available.'}
              </div>
            )}
          </div>

          <div style={{ padding: '24px 20px', flex: 1, overflowY: 'auto' }}>
            <p style={{ fontSize: '14px', color: C.text, lineHeight: 1.8, whiteSpace: 'pre-wrap', margin: 0 }}>
              {selectedDraft?.content_body || 'Select a draft to review'}
            </p>
          </div>

          <div style={{ padding: '16px 20px', borderTop: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ color: C.textMuted, fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              {Icons.clock}
              Golden hour rule: reply to meaningful comments in the first 60-90 minutes after publish confirmation.
            </div>
            <Button disabled={loading || !selectedDraft?.content_body} variant="ghost" size="sm" onClick={() => withAction('Draft body copied for manual publish', copyDraftBodyForManualPublish)}>
              {Icons.copy}
              Copy draft body
            </Button>
          </div>
        </div>
      </div>

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px', display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '8px' }}>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Pillar theme
          <input value={manualDraft.pillar_theme} onChange={(e) => setManualDraft((prev) => ({ ...prev, pillar_theme: e.target.value }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Sub theme
          <input value={manualDraft.sub_theme} onChange={(e) => setManualDraft((prev) => ({ ...prev, sub_theme: e.target.value }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Format
          <select value={manualDraft.format} onChange={(e) => setManualDraft((prev) => ({ ...prev, format: e.target.value }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }}>
            <option value="TEXT">TEXT</option>
            <option value="IMAGE">IMAGE</option>
            <option value="CAROUSEL">CAROUSEL</option>
          </select>
        </label>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px' }}>
          Tone
          <select value={manualDraft.tone} onChange={(e) => setManualDraft((prev) => ({ ...prev, tone: e.target.value }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }}>
            <option value="EDUCATIONAL">EDUCATIONAL</option>
            <option value="OPINIONATED">OPINIONATED</option>
            <option value="DIRECT">DIRECT</option>
            <option value="EXPLORATORY">EXPLORATORY</option>
          </select>
        </label>
        <label style={{ fontSize: '12px', color: C.textMuted, display: 'grid', gap: '4px', gridColumn: '1 / span 2' }}>
          Content body
          <textarea rows={3} value={manualDraft.content_body} onChange={(e) => setManualDraft((prev) => ({ ...prev, content_body: e.target.value }))} style={{ background: C.bg, border: `1px solid ${C.border}`, color: C.text, borderRadius: '6px', padding: '8px' }} />
        </label>
        <div style={{ gridColumn: '1 / span 2' }}>
          <Button disabled={loading} onClick={() => withAction('Manual draft created', () => api.createDraft({ ...manualDraft, image_url: manualDraft.image_url || null, carousel_document_url: manualDraft.carousel_document_url || null }))}>Create Draft</Button>
        </div>
      </div>
    </div>
  );
}
