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
    auditLogs: overrides.auditLogs ?? [],
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
      const hasPost = state.posts.some((post) => post.draft_id === draftId);
      if (!hasPost) {
        state.posts = [
          {
            id: `post-${state.posts.length + 1}`,
            draft_id: draftId,
            scheduled_time: '2026-02-08T08:00:00Z',
            published_at: null,
          },
          ...state.posts,
        ];
      }
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

function openView(name) {
  fireEvent.click(screen.getByRole('button', { name }));
}

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('renders dashboard and loads initial data', async () => {
    setupMockApi();
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Execution Console' })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Data refreshed')).toBeInTheDocument();
      expect(screen.getByText(/Health: ok/)).toBeInTheDocument();
      expect(screen.getByText(/Readiness: true/)).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalled();
  });

  it('calls generate draft endpoint when Generate is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    openView('Content');
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

    openView('Content');
    await waitFor(() => expect(screen.getByText('Pending: 1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Reject' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === `/drafts/${pendingDraft.id}/reject`)).toBe(true);
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

    openView('Content');
    await waitFor(() => expect(screen.getByText('Pending: 1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === `/drafts/${pendingDraft.id}/approve`)).toBe(true);
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

    await waitFor(() => expect(screen.getByText('Posts tracked')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Confirm publish' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === `/posts/${post.id}/confirm-manual-publish`)).toBe(true);
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

    openView('Content');
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

    await waitFor(() => expect(screen.getByText('Posts tracked')).toBeInTheDocument());

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

    openView('Engagement');
    await waitFor(() => expect(screen.getByText('Comments stored')).toBeInTheDocument());

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

    openView('Engagement');
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

    openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Recompute' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/learning/recompute')).toBe(true);
      expect(screen.getByText('Learning recomputed')).toBeInTheDocument();
    });
  });

  it('calls kill switch on endpoint when Kill ON is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Kill ON' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/kill-switch/on')).toBe(true);
      expect(screen.getByText('Kill switch enabled')).toBeInTheDocument();
    });
  });

  it('calls kill switch off endpoint when Kill OFF is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Kill OFF' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/kill-switch/off')).toBe(true);
      expect(screen.getByText('Kill switch disabled')).toBeInTheDocument();
    });
  });

  it('calls posting on endpoint when Posting ON is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Posting ON' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/posting/on')).toBe(true);
      expect(screen.getByText('Posting enabled')).toBeInTheDocument();
    });
  });

  it('calls posting off endpoint when Posting OFF is clicked', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Posting OFF' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/posting/off')).toBe(true);
      expect(screen.getByText('Posting disabled')).toBeInTheDocument();
    });
  });

  it('runs bootstrap demo flow and calls key workflow endpoints', async () => {
    const { calls } = setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Bootstrap demo' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/drafts')).toBe(true);
      expect(calls.some((call) => call.method === 'POST' && call.path.includes('/approve'))).toBe(true);
      expect(calls.some((call) => call.method === 'POST' && call.path.includes('/confirm-manual-publish'))).toBe(true);
      expect(calls.some((call) => call.method === 'POST' && call.path.includes('/metrics'))).toBe(true);
      expect(calls.some((call) => call.method === 'POST' && call.path === '/comments')).toBe(true);
      expect(calls.some((call) => call.method === 'POST' && call.path === '/sources/ingest')).toBe(true);
      expect(calls.some((call) => call.method === 'POST' && call.path === '/reports/daily/send')).toBe(true);
      expect(screen.getByText('Demo bootstrap complete')).toBeInTheDocument();
    });
  });

  it('shows manual publish checklist warnings when draft violates linkedin constraints', async () => {
    setupMockApi({
      drafts: [
        {
          id: '77777777-7777-7777-7777-777777777777',
          pillar_theme: 'Adtech fundamentals',
          sub_theme: 'Programmatic buying',
          format: 'TEXT',
          tone: 'EDUCATIONAL',
          content_body:
            'Generic content with link https://example.com #one #two #three #four and limited topic relation.',
          status: 'PENDING',
        },
      ],
    });
    render(<App />);

    openView('Content');
    await waitFor(() => expect(screen.getByText('Draft in focus: 77777777')).toBeInTheDocument());

    expect(screen.getByText(/Hashtag count high/)).toBeInTheDocument();
    expect(screen.getByText(/External link detected in body/)).toBeInTheDocument();
  });

  it('shows escalated comments with reason in escalation panel', async () => {
    setupMockApi({
      comments: [
        {
          id: 'cmt-1',
          published_post_id: 'post-1',
          commenter_name: 'Industry Leader',
          comment_text: 'Can we discuss a partnership here?',
          commented_at: '2026-02-08T12:00:00Z',
          is_high_value: true,
          high_value_reason: 'PARTNERSHIP_SIGNAL',
          escalated: true,
          auto_reply_sent: false,
          auto_reply_text: null,
        },
      ],
    });
    render(<App />);

    openView('Engagement');
    await waitFor(() => expect(screen.getByText('Escalated comments: 1')).toBeInTheDocument());
    expect(screen.getByText(/PARTNERSHIP_SIGNAL/)).toBeInTheDocument();
    expect(screen.getByText('Industry Leader')).toBeInTheDocument();
  });

  it('copies draft body for manual publish', async () => {
    const clipboardWrite = vi.fn(async () => {});
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: clipboardWrite },
    });

    const draft = {
      id: '88888888-8888-8888-8888-888888888888',
      pillar_theme: 'Adtech fundamentals',
      sub_theme: 'Programmatic buying',
      format: 'TEXT',
      tone: 'EDUCATIONAL',
      content_body: 'Copy me to LinkedIn manually.',
      status: 'PENDING',
    };
    setupMockApi({ drafts: [draft] });
    render(<App />);

    openView('Content');
    await waitFor(() => expect(screen.getByText('Draft in focus: 88888888')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /Copy draft body/ }));

    await waitFor(() => {
      expect(clipboardWrite).toHaveBeenCalledWith('Copy me to LinkedIn manually.');
      expect(screen.getByText('Draft body copied for manual publish')).toBeInTheDocument();
    });
  });

  it('shows publish queue summary counts', async () => {
    const now = Date.now();
    setupMockApi({
      posts: [
        {
          id: 'post-due',
          draft_id: 'draft-1',
          scheduled_time: new Date(now - 60_000).toISOString(),
          published_at: null,
        },
        {
          id: 'post-future',
          draft_id: 'draft-2',
          scheduled_time: new Date(now + 3600_000).toISOString(),
          published_at: null,
        },
        {
          id: 'post-published',
          draft_id: 'draft-3',
          scheduled_time: new Date(now - 7200_000).toISOString(),
          published_at: new Date(now - 1800_000).toISOString(),
        },
      ],
    });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Posts tracked: 3')).toBeInTheDocument());
    expect(screen.getByText('Due now: 1')).toBeInTheDocument();
    expect(screen.getByText('Unpublished: 2')).toBeInTheDocument();
    expect(screen.getByText('Published: 1')).toBeInTheDocument();
  });

  it('filters publish queue by selected state', async () => {
    const now = Date.now();
    setupMockApi({
      posts: [
        {
          id: 'due-aaaaaaaa',
          draft_id: 'draft-1',
          scheduled_time: new Date(now - 60_000).toISOString(),
          published_at: null,
        },
        {
          id: 'future-bbbbbbbb',
          draft_id: 'draft-2',
          scheduled_time: new Date(now + 7200_000).toISOString(),
          published_at: null,
        },
        {
          id: 'published-cccc',
          draft_id: 'draft-3',
          scheduled_time: new Date(now - 7200_000).toISOString(),
          published_at: new Date(now - 1200_000).toISOString(),
        },
      ],
    });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Posts tracked: 3')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Queue filter'), { target: { value: 'due_now' } });

    await waitFor(() => {
      expect(screen.getByText('due-aaaa')).toBeInTheDocument();
      expect(screen.queryByText('future-b')).not.toBeInTheDocument();
      expect(screen.queryByText('publishe')).not.toBeInTheDocument();
      expect(screen.getByText(/due now/)).toBeInTheDocument();
    });
  });

  it('restores active view from localStorage on reload', async () => {
    localStorage.setItem('app.activeView', 'engagement');
    setupMockApi();
    render(<App />);

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Engagement' })).toBeInTheDocument());
  });

  it('restores dashboard queue filter from localStorage on reload', async () => {
    const now = Date.now();
    localStorage.setItem('app.dashboard.publishFilter', 'due_now');
    setupMockApi({
      posts: [
        {
          id: 'due-11111111',
          draft_id: 'draft-1',
          scheduled_time: new Date(now - 60_000).toISOString(),
          published_at: null,
        },
        {
          id: 'future-22222',
          draft_id: 'draft-2',
          scheduled_time: new Date(now + 3600_000).toISOString(),
          published_at: null,
        },
      ],
    });
    render(<App />);

    await waitFor(() => expect(screen.getByText('Posts tracked: 2')).toBeInTheDocument());
    expect(screen.getByDisplayValue('Due now')).toBeInTheDocument();
    expect(screen.getByText('due-1111')).toBeInTheDocument();
    expect(screen.queryByText('future-2')).not.toBeInTheDocument();
  });

  it('resets persisted preferences from settings control', async () => {
    const now = Date.now();
    localStorage.setItem('app.activeView', 'settings');
    localStorage.setItem('app.dashboard.publishFilter', 'due_now');
    setupMockApi({
      posts: [
        {
          id: 'due-11111111',
          draft_id: 'draft-1',
          scheduled_time: new Date(now - 60_000).toISOString(),
          published_at: null,
        },
        {
          id: 'future-22222',
          draft_id: 'draft-2',
          scheduled_time: new Date(now + 3600_000).toISOString(),
          published_at: null,
        },
      ],
    });
    render(<App />);

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Settings' })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Reset UI Preferences' }));

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Execution Console' })).toBeInTheDocument());
    await waitFor(() => expect(screen.getByDisplayValue('All')).toBeInTheDocument());
    expect(localStorage.getItem('app.activeView')).toBe('dashboard');
    expect(localStorage.getItem('app.dashboard.publishFilter')).toBe('all');
  });

  it('shows algorithm alignment and recent audit entries in settings', async () => {
    setupMockApi({
      alignment: { enforced: { engagement_bait: 'blocked', external_links: 'blocked' } },
      auditLogs: [
        {
          id: 'audit-1',
          created_at: '2026-02-08T10:00:00Z',
          actor: 'api',
          action: 'draft.generate',
          resource_type: 'draft',
        },
      ],
    });
    render(<App />);

    openView('Settings');
    await waitFor(() => expect(screen.getByText('Algorithm Alignment')).toBeInTheDocument());
    expect(screen.getByText('Audit Trail')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByText('draft.generate').length).toBeGreaterThan(0);
      expect(screen.getByText(/engagement_bait/)).toBeInTheDocument();
    });
  });

  it('filters audit trail entries in settings by query', async () => {
    setupMockApi({
      auditLogs: [
        {
          id: 'audit-1',
          created_at: '2026-02-08T10:00:00Z',
          actor: 'api',
          action: 'draft.generate',
          resource_type: 'draft',
        },
        {
          id: 'audit-2',
          created_at: '2026-02-08T10:05:00Z',
          actor: 'worker',
          action: 'report.daily.send',
          resource_type: 'report',
        },
      ],
    });
    render(<App />);

    openView('Settings');
    await waitFor(() => expect(screen.getByText('Audit Trail')).toBeInTheDocument());
    expect(screen.getByText('draft.generate')).toBeInTheDocument();
    expect(screen.getByText('report.daily.send')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Audit filter'), { target: { value: 'worker' } });

    await waitFor(() => {
      expect(screen.queryByText('draft.generate')).not.toBeInTheDocument();
      expect(screen.getByText('report.daily.send')).toBeInTheDocument();
    });
  });
});
