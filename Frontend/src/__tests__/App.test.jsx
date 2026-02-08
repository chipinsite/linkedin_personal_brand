import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from '../App';

function mockJson(data) {
  return Promise.resolve({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => data,
    text: async () => JSON.stringify(data),
  });
}

function createApiState(overrides = {}) {
  const baseDraft = {
    id: '11111111-1111-1111-1111-111111111111',
    pillar_theme: 'Adtech fundamentals',
    sub_theme: 'Programmatic buying',
    format: 'TEXT',
    tone: 'EDUCATIONAL',
    content_body: 'Draft body',
    status: 'PENDING',
  };

  return {
    drafts: overrides.drafts ?? [],
    posts: [],
    comments: [],
    sources: [],
    learning: { format_weights_json: '{}', tone_weights_json: '{}' },
    report: {
      report_date: '2026-02-08',
      posts_published: 0,
      total_impressions: 0,
      total_reactions: 0,
      total_comments: 0,
      total_shares: 0,
      avg_engagement_rate: 0,
      auto_replies_sent: 0,
      escalations: 0,
    },
    adminConfig: {
      timezone: 'Africa/Johannesburg',
      posting_window_start: '08:00',
      posting_window_end: '17:00',
      posting_enabled: true,
      comment_replies_enabled: true,
      max_auto_replies: 5,
      escalation_follower_threshold: 10000,
      linkedin_api_mode: 'manual',
      kill_switch: false,
    },
    alignment: { enforced: { engagement_bait: 'blocked' } },
    auditLogs: [],
    engagementStatus: { monitored_total: 0, active_total: 0, due_total: 0 },
    baseDraft,
  };
}

function setupMockApi(overrides = {}) {
  const state = createApiState(overrides);
  const calls = [];

  global.fetch = vi.fn(async (url, options = {}) => {
    const parsed = new URL(url);
    const method = (options.method || 'GET').toUpperCase();
    const path = parsed.pathname;
    calls.push({ method, path, body: options.body || null });

    if (method === 'GET' && path === '/health') return mockJson({ status: 'ok' });
    if (method === 'GET' && path === '/health/deep') {
      return mockJson({ status: 'ok', checks: { database: { ok: true }, redis: { ok: true } } });
    }
    if (method === 'GET' && path === '/health/readiness') return mockJson({ ready: true });
    if (method === 'GET' && path === '/drafts') return mockJson(state.drafts);
    if (method === 'POST' && path === '/drafts/generate') {
      const newDraft = {
        ...state.baseDraft,
        id: `generated-${state.drafts.length + 1}`,
      };
      state.drafts = [newDraft, ...state.drafts];
      return mockJson(newDraft);
    }
    if (method === 'POST' && path.endsWith('/reject')) {
      const draftId = path.split('/')[2];
      state.drafts = state.drafts.map((draft) =>
        draft.id === draftId ? { ...draft, status: 'REJECTED' } : draft,
      );
      return mockJson(state.drafts.find((draft) => draft.id === draftId) || state.baseDraft);
    }
    if (method === 'GET' && path === '/posts') return mockJson(state.posts);
    if (method === 'GET' && path === '/comments') return mockJson(state.comments);
    if (method === 'GET' && path === '/sources') return mockJson(state.sources);
    if (method === 'GET' && path === '/learning/weights') return mockJson(state.learning);
    if (method === 'GET' && path === '/reports/daily') return mockJson(state.report);
    if (method === 'GET' && path === '/admin/config') return mockJson(state.adminConfig);
    if (method === 'GET' && path === '/admin/algorithm-alignment') return mockJson(state.alignment);
    if (method === 'GET' && path === '/admin/audit-logs') return mockJson(state.auditLogs);
    if (method === 'GET' && path === '/engagement/status') return mockJson(state.engagementStatus);

    return mockJson({});
  });

  return { calls, state };
}

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders dashboard and loads initial data', async () => {
    setupMockApi();
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Execution Console' })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Data refreshed')).toBeInTheDocument();
      expect(screen.getByText('Health: ok')).toBeInTheDocument();
      expect(screen.getByText('Readiness: true')).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalled();
  });

  it('calls generate draft endpoint when Generate is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Pending: 0')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/drafts/generate')).toBe(true);
      expect(screen.getByText('Draft generated')).toBeInTheDocument();
      expect(screen.getByText('Pending: 1')).toBeInTheDocument();
    });
  });

  it('calls reject endpoint when Reject is clicked for a pending draft', async () => {
    const pendingDraft = {
      id: '22222222-2222-2222-2222-222222222222',
      pillar_theme: 'AI in advertising',
      sub_theme: 'Generative creative',
      format: 'TEXT',
      tone: 'OPINIONATED',
      content_body: 'Pending draft',
      status: 'PENDING',
    };
    const { calls } = setupMockApi({ drafts: [pendingDraft] });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Pending: 1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Reject' }));

    await waitFor(() => {
      expect(
        calls.some(
          (call) => call.method === 'POST' && call.path === `/drafts/${pendingDraft.id}/reject`,
        ),
      ).toBe(true);
      expect(screen.getByText('Draft rejected')).toBeInTheDocument();
      expect(screen.getByText('Pending: 0')).toBeInTheDocument();
    });
  });
});
