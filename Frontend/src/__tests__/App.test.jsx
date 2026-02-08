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
    posts: overrides.posts ?? [],
    comments: overrides.comments ?? [],
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
    if (method === 'POST' && path === '/drafts') {
      const payload = JSON.parse(options.body || '{}');
      const created = {
        id: `manual-${state.drafts.length + 1}`,
        status: 'PENDING',
        ...state.baseDraft,
        ...payload,
      };
      state.drafts = [created, ...state.drafts];
      return mockJson(created);
    }
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
    if (method === 'POST' && path.endsWith('/approve')) {
      const draftId = path.split('/')[2];
      state.drafts = state.drafts.map((draft) =>
        draft.id === draftId ? { ...draft, status: 'APPROVED' } : draft,
      );
      return mockJson(state.drafts.find((draft) => draft.id === draftId) || state.baseDraft);
    }
    if (method === 'GET' && path === '/posts') return mockJson(state.posts);
    if (method === 'POST' && path === '/posts/publish-due') return mockJson({ processed: 0 });
    if (method === 'POST' && path.endsWith('/confirm-manual-publish')) {
      const postId = path.split('/')[2];
      state.posts = state.posts.map((post) =>
        post.id === postId ? { ...post, published_at: '2026-02-08T12:00:00Z' } : post,
      );
      return mockJson(state.posts.find((post) => post.id === postId) || {});
    }
    if (method === 'POST' && path.endsWith('/metrics')) {
      const postId = path.split('/')[2];
      const payload = JSON.parse(options.body || '{}');
      state.posts = state.posts.map((post) => (post.id === postId ? { ...post, ...payload } : post));
      return mockJson(state.posts.find((post) => post.id === postId) || {});
    }
    if (method === 'GET' && path === '/comments') return mockJson(state.comments);
    if (method === 'POST' && path === '/comments') {
      const payload = JSON.parse(options.body || '{}');
      const created = {
        id: `comment-${state.comments.length + 1}`,
        ...payload,
        commented_at: '2026-02-08T12:00:00Z',
        is_high_value: false,
        high_value_reason: null,
        escalated: false,
        auto_reply_sent: false,
        auto_reply_text: null,
      };
      state.comments = [created, ...state.comments];
      return mockJson(created);
    }
    if (method === 'GET' && path === '/sources') return mockJson(state.sources);
    if (method === 'POST' && path === '/sources/ingest') {
      state.sources = [
        {
          id: `source-${state.sources.length + 1}`,
          source_name: 'Digiday',
          source_url: 'https://digiday.com/example',
          title: 'Sample source',
          summary: 'Summary',
        },
        ...state.sources,
      ];
      return mockJson({ created: 1, feeds_count: 1 });
    }
    if (method === 'GET' && path === '/learning/weights') return mockJson(state.learning);
    if (method === 'POST' && path === '/learning/recompute') return mockJson(state.learning);
    if (method === 'GET' && path === '/reports/daily') return mockJson(state.report);
    if (method === 'POST' && path === '/reports/daily/send') {
      return mockJson({ sent: true, date: '2026-02-08' });
    }
    if (method === 'GET' && path === '/admin/config') return mockJson(state.adminConfig);
    if (method === 'POST' && path === '/admin/kill-switch/on') {
      state.adminConfig = { ...state.adminConfig, kill_switch: true };
      return mockJson({ kill_switch: true });
    }
    if (method === 'POST' && path === '/admin/kill-switch/off') {
      state.adminConfig = { ...state.adminConfig, kill_switch: false };
      return mockJson({ kill_switch: false });
    }
    if (method === 'POST' && path === '/admin/posting/on') {
      state.adminConfig = { ...state.adminConfig, posting_enabled: true };
      return mockJson({ posting_enabled: true });
    }
    if (method === 'POST' && path === '/admin/posting/off') {
      state.adminConfig = { ...state.adminConfig, posting_enabled: false };
      return mockJson({ posting_enabled: false });
    }
    if (method === 'GET' && path === '/admin/algorithm-alignment') return mockJson(state.alignment);
    if (method === 'GET' && path === '/admin/audit-logs') return mockJson(state.auditLogs);
    if (method === 'GET' && path === '/engagement/status') return mockJson(state.engagementStatus);
    if (method === 'POST' && path === '/engagement/poll') return mockJson({ processed_posts: 0, stored_comments: 0 });

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

  it('calls approve endpoint when Approve is clicked for a pending draft', async () => {
    const pendingDraft = {
      id: '33333333-3333-3333-3333-333333333333',
      pillar_theme: 'Agentic AI in Adtech',
      sub_theme: 'AI bidding agents',
      format: 'TEXT',
      tone: 'EDUCATIONAL',
      content_body: 'Pending approve draft',
      status: 'PENDING',
    };
    const { calls } = setupMockApi({ drafts: [pendingDraft] });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Pending: 1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

    await waitFor(() => {
      expect(
        calls.some(
          (call) => call.method === 'POST' && call.path === `/drafts/${pendingDraft.id}/approve`,
        ),
      ).toBe(true);
      expect(screen.getByText('Draft approved')).toBeInTheDocument();
      expect(screen.getByText('Pending: 0')).toBeInTheDocument();
    });
  });

  it('calls confirm publish endpoint when Confirm publish is clicked', async () => {
    const post = {
      id: '44444444-4444-4444-4444-444444444444',
      draft_id: '33333333-3333-3333-3333-333333333333',
      scheduled_time: '2026-02-08T08:00:00Z',
      published_at: null,
    };
    const { calls } = setupMockApi({ posts: [post] });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Posts tracked: 1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Confirm publish' }));

    await waitFor(() => {
      expect(
        calls.some(
          (call) =>
            call.method === 'POST' &&
            call.path === `/posts/${post.id}/confirm-manual-publish`,
        ),
      ).toBe(true);
      expect(screen.getByText('Manual publish confirmed')).toBeInTheDocument();
    });
  });

  it('calls source ingest endpoint when Ingest is clicked', async () => {
    const { calls } = setupMockApi({ sources: [] });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Sources: 0')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Ingest' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/sources/ingest')).toBe(true);
      expect(screen.getByText('Sources ingested')).toBeInTheDocument();
      expect(screen.getByText('Sources: 1')).toBeInTheDocument();
    });
  });

  it('calls daily report send endpoint when Send is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Send' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/reports/daily/send')).toBe(true);
      expect(screen.getByText('Daily report sent')).toBeInTheDocument();
    });
  });

  it('calls create draft endpoint when Create Draft is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Pending: 0')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Create Draft' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/drafts')).toBe(true);
      expect(screen.getByText('Manual draft created')).toBeInTheDocument();
      expect(screen.getByText('Pending: 1')).toBeInTheDocument();
    });
  });

  it('calls update metrics endpoint when Update metrics is clicked', async () => {
    const post = {
      id: '55555555-5555-5555-5555-555555555555',
      draft_id: '33333333-3333-3333-3333-333333333333',
      scheduled_time: '2026-02-08T08:00:00Z',
      published_at: null,
    };
    const { calls } = setupMockApi({ posts: [post] });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Posts tracked: 1')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Metrics post id'), { target: { value: post.id } });
    fireEvent.click(screen.getByRole('button', { name: 'Update metrics' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === `/posts/${post.id}/metrics`)).toBe(true);
      expect(screen.getByText('Post metrics updated')).toBeInTheDocument();
    });
  });

  it('calls create comment endpoint when Add Comment is clicked', async () => {
    const post = {
      id: '66666666-6666-6666-6666-666666666666',
      draft_id: '33333333-3333-3333-3333-333333333333',
      scheduled_time: '2026-02-08T08:00:00Z',
      published_at: null,
    };
    const { calls } = setupMockApi({ posts: [post] });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Posts tracked: 1')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Comment post id'), { target: { value: post.id } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Comment' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/comments')).toBe(true);
      expect(screen.getByText('Comment added')).toBeInTheDocument();
    });
  });

  it('calls publish-due endpoint when Run Due is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Run Due' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/posts/publish-due')).toBe(true);
      expect(screen.getByText('Due posts processed')).toBeInTheDocument();
    });
  });

  it('calls engagement poll endpoint when Poll is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Poll' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/engagement/poll')).toBe(true);
      expect(screen.getByText('Engagement poll complete')).toBeInTheDocument();
    });
  });

  it('calls learning recompute endpoint when Recompute is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Recompute' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/learning/recompute')).toBe(true);
      expect(screen.getByText('Learning recomputed')).toBeInTheDocument();
    });
  });

  it('calls kill switch on endpoint when Kill ON is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Kill ON' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/kill-switch/on')).toBe(true);
      expect(screen.getByText('Kill switch enabled')).toBeInTheDocument();
    });
  });

  it('calls kill switch off endpoint when Kill OFF is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Kill OFF' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/kill-switch/off')).toBe(true);
      expect(screen.getByText('Kill switch disabled')).toBeInTheDocument();
    });
  });

  it('calls posting on endpoint when Posting ON is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Posting ON' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/posting/on')).toBe(true);
      expect(screen.getByText('Posting enabled')).toBeInTheDocument();
    });
  });

  it('calls posting off endpoint when Posting OFF is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Posting OFF' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/posting/off')).toBe(true);
      expect(screen.getByText('Posting disabled')).toBeInTheDocument();
    });
  });
});
