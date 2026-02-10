import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from '../App';
import { AuthProvider } from '../contexts/AuthContext';

const ALERT_SNOOZE_KEY = 'app.dashboard.alertSnoozes';

// Mock user for authenticated tests
const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  username: 'testuser',
  full_name: 'Test User',
  is_active: true,
  is_superuser: false,
};

// Wrapper component that provides auth context
function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

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
      pipeline_mode: 'LEGACY',
      ...(overrides.adminConfig ?? {}),
    },
    alignment: overrides.alignment ?? { enforced: { engagement_bait: 'blocked' } },
    auditLogs: overrides.auditLogs ?? [],
    engagementStatus: { monitored_total: 0, active_total: 0, due_total: 0 },
    pipelineOverview: overrides.pipelineOverview ?? {
      total: 0, claimed: 0,
      status_counts: { backlog: 0, todo: 0, writing: 0, review: 0, ready_to_publish: 0, published: 0, amplified: 0, done: 0 },
    },
    pipelineItems: overrides.pipelineItems ?? [],
    pipelineHealth: overrides.pipelineHealth ?? {
      health_status: 'healthy', overview: { total: 0, claimed: 0, status_counts: {} },
      stale_claims: 0, errored_items: 0, stuck_items: 0, checked_at: '2026-02-10T12:00:00Z',
    },
    baseDraft,
  };
}

function setupMockApi(overrides = {}) {
  const state = createApiState(overrides);
  const calls = [];

  // Set up mock auth tokens in localStorage for authenticated state
  localStorage.setItem('auth.accessToken', 'mock-access-token');
  localStorage.setItem('auth.refreshToken', 'mock-refresh-token');

  global.fetch = vi.fn(async (url, options = {}) => {
    const parsed = new URL(url);
    const method = (options.method || 'GET').toUpperCase();
    const path = parsed.pathname;
    calls.push({ method, path, body: options.body || null });

    // Auth endpoints
    if (method === 'GET' && path === '/auth/me') return mockJson(mockUser);
    if (method === 'POST' && path === '/auth/refresh') {
      return mockJson({ access_token: 'new-mock-access-token', token_type: 'bearer' });
    }
    if (method === 'POST' && path === '/auth/logout') return mockJson({ message: 'Logged out' });

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
    if (method === 'POST' && path.startsWith('/admin/pipeline-mode/')) {
      const mode = path.split('/').pop().toUpperCase();
      state.adminConfig = { ...state.adminConfig, pipeline_mode: mode };
      return mockJson({ pipeline_mode: mode, previous_mode: 'LEGACY' });
    }
    if (method === 'GET' && path === '/admin/pipeline-status') {
      const mode = state.adminConfig.pipeline_mode || 'LEGACY';
      return mockJson({
        pipeline_mode: mode,
        kill_switch: state.adminConfig.kill_switch,
        posting_enabled: state.adminConfig.posting_enabled,
        legacy_active: mode === 'LEGACY' || mode === 'SHADOW',
        v6_active: mode === 'V6' || mode === 'SHADOW',
        shadow_mode: mode === 'SHADOW',
        v6_publishing_enabled: mode === 'V6',
        all_disabled: mode === 'DISABLED',
      });
    }
    if (method === 'GET' && path === '/admin/algorithm-alignment') return mockJson(state.alignment);
    if (method === 'GET' && path === '/admin/audit-logs') return mockJson(state.auditLogs);
    if (method === 'GET' && path === '/admin/export-state') {
      return mockJson({ generated_at: '2026-02-08T12:00:00Z', drafts: state.drafts, posts: state.posts });
    }
    if (method === 'GET' && path === '/engagement/status') return mockJson(state.engagementStatus);
    if (method === 'POST' && path === '/engagement/poll') return mockJson({ processed_posts: 0, stored_comments: 0 });

    // Pipeline endpoints
    if (method === 'GET' && path === '/pipeline/overview') return mockJson(state.pipelineOverview);
    if (method === 'GET' && path === '/pipeline/items') return mockJson(state.pipelineItems);
    if (method === 'GET' && path === '/pipeline/health') return mockJson(state.pipelineHealth);
    if (method === 'POST' && path.startsWith('/pipeline/run/')) {
      const agent = path.split('/').pop();
      return mockJson({ agent, stale_claims_recovered: 0, errored_items_reset: 0, health: state.pipelineHealth });
    }

    return mockJson({});
  });

  return { calls, state };
}

async function openView(name) {
  // Wait for auth to complete and dashboard to load before switching views
  await waitFor(() => expect(screen.getByRole('button', { name })).toBeInTheDocument());
  fireEvent.click(screen.getByRole('button', { name }));
}

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    delete window.__APP_ALERT_TICK_MS__;
  });

  it('renders dashboard and loads initial data', async () => {
    setupMockApi();
    render(<AppWithAuth />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Execution Console' })).toBeInTheDocument();
      expect(screen.getByText('Data refreshed')).toBeInTheDocument();
      expect(screen.getByText(/Health: ok/)).toBeInTheDocument();
      expect(screen.getByText(/Readiness: true/)).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalled();
  });

  it('shows operational alerts for critical dashboard conditions', async () => {
    const now = Date.now();
    setupMockApi({
      adminConfig: { kill_switch: true, posting_enabled: false },
      posts: [
        {
          id: 'post-due-1',
          draft_id: 'draft-1',
          scheduled_time: new Date(now - 60_000).toISOString(),
          published_at: null,
        },
      ],
      comments: [
        {
          id: 'esc-1',
          published_post_id: 'post-due-1',
          commenter_name: 'Operator',
          comment_text: 'Need manual review',
          commented_at: '2026-02-08T12:00:00Z',
          is_high_value: true,
          high_value_reason: 'TECHNICAL_QUESTION',
          escalated: true,
          auto_reply_sent: false,
          auto_reply_text: null,
        },
      ],
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Operational Alerts')).toBeInTheDocument());
    expect(screen.getByText('4 active')).toBeInTheDocument();
    expect(screen.getByText(/Kill switch is ON/)).toBeInTheDocument();
    expect(screen.getByText(/Posting is disabled/)).toBeInTheDocument();
    expect(screen.getByText(/post\(s\) are due now/)).toBeInTheDocument();
    expect(screen.getByText(/escalated comment\(s\) need manual follow-up/)).toBeInTheDocument();
  });

  it('shows clear operational alert state when there are no active issues', async () => {
    setupMockApi();
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Operational Alerts')).toBeInTheDocument());
    expect(screen.getByText('0 active')).toBeInTheDocument();
    expect(screen.getByText('No active operational alerts.')).toBeInTheDocument();
  });

  it('snoozes an operational alert for two hours', async () => {
    setupMockApi({
      adminConfig: { kill_switch: true, posting_enabled: true },
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Operational Alerts')).toBeInTheDocument());
    expect(screen.getByText('1 active')).toBeInTheDocument();
    expect(screen.getByText(/Kill switch is ON/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Snooze kill-switch' }));

    await waitFor(() => {
      expect(screen.getByText('0 active')).toBeInTheDocument();
      expect(screen.queryByText(/Kill switch is ON/)).not.toBeInTheDocument();
      expect(screen.getByText('No active operational alerts.')).toBeInTheDocument();
    });

    const snoozes = JSON.parse(localStorage.getItem(ALERT_SNOOZE_KEY) || '{}');
    expect(Number(snoozes['kill-switch'] || 0)).toBeGreaterThan(Date.now());
  });

  it('restores snoozed alert after expiration on refresh', async () => {
    const baseNow = 1_700_000_000_000;
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(baseNow);
    window.__APP_ALERT_TICK_MS__ = 20;
    localStorage.setItem(ALERT_SNOOZE_KEY, JSON.stringify({ 'kill-switch': baseNow + 2 * 60 * 60 * 1000 }));

    setupMockApi({
      adminConfig: { kill_switch: true, posting_enabled: true },
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Operational Alerts')).toBeInTheDocument());
    expect(screen.getByText('0 active')).toBeInTheDocument();
    expect(screen.queryByText(/Kill switch is ON/)).not.toBeInTheDocument();

    await act(async () => {
      nowSpy.mockReturnValue(baseNow + 2 * 60 * 60 * 1000 + 1);
      await new Promise((resolve) => setTimeout(resolve, 60));
    });

    await waitFor(() => {
      expect(screen.getByText('1 active')).toBeInTheDocument();
      expect(screen.getByText(/Kill switch is ON/)).toBeInTheDocument();
    });

    nowSpy.mockRestore();
  });

  it('shows snoozed countdown summary and clears snoozes', async () => {
    const baseNow = 1_700_000_000_000;
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(baseNow);
    localStorage.setItem(ALERT_SNOOZE_KEY, JSON.stringify({ 'kill-switch': baseNow + 30 * 60 * 1000 }));

    setupMockApi({
      adminConfig: { kill_switch: true, posting_enabled: true },
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Operational Alerts')).toBeInTheDocument());
    expect(screen.getByText('Snoozed alerts: 1')).toBeInTheDocument();
    expect(screen.getByText(/kill-switch: 30m left/)).toBeInTheDocument();
    expect(screen.getByText('0 active')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Clear Snoozes' }));

    await waitFor(() => {
      expect(screen.getByText('1 active')).toBeInTheDocument();
      expect(screen.getByText(/Kill switch is ON/)).toBeInTheDocument();
      expect(screen.queryByText(/Snoozed alerts: 1/)).not.toBeInTheDocument();
    });

    const snoozes = JSON.parse(localStorage.getItem(ALERT_SNOOZE_KEY) || '{}');
    expect(Object.keys(snoozes)).toHaveLength(0);
    nowSpy.mockRestore();
  });

  it('updates snoozed countdown text on interval tick', async () => {
    let now = 1_700_000_000_000;
    const nowSpy = vi.spyOn(Date, 'now').mockImplementation(() => now);
    window.__APP_ALERT_TICK_MS__ = 20;
    localStorage.setItem(ALERT_SNOOZE_KEY, JSON.stringify({ 'kill-switch': now + 2 * 60 * 1000 }));

    setupMockApi({
      adminConfig: { kill_switch: true, posting_enabled: true },
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText(/kill-switch: 2m left/)).toBeInTheDocument());

    await act(async () => {
      now += 60 * 1000;
      await new Promise((resolve) => setTimeout(resolve, 60));
    });

    await waitFor(() => expect(screen.getByText(/kill-switch: 1m left/)).toBeInTheDocument());

    delete window.__APP_ALERT_TICK_MS__;
    nowSpy.mockRestore();
  });

  it('calls export state endpoint from settings backup action', async () => {
    const createObjectURL = vi.fn(() => 'blob:backup');
    const revokeObjectURL = vi.fn();
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createObjectURL });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeObjectURL });

    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Export Backup' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'GET' && call.path === '/admin/export-state')).toBe(true);
      expect(createObjectURL).toHaveBeenCalled();
      expect(revokeObjectURL).toHaveBeenCalled();
      expect(screen.getByText('Backup exported')).toBeInTheDocument();
    });

    clickSpy.mockRestore();
  });

  it('calls generate draft endpoint when Generate is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Content');
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
    render(<AppWithAuth />);

    await openView('Content');
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
    render(<AppWithAuth />);

    await openView('Content');
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
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Posts tracked')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Confirm publish' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === `/posts/${post.id}/confirm-manual-publish`)).toBe(true);
      expect(screen.getByText('Manual publish confirmed')).toBeInTheDocument();
    });
  });

  it('calls source ingest endpoint when Ingest is clicked', async () => {
    const { calls } = setupMockApi({ sources: [] });
    render(<AppWithAuth />);

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
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/reports/daily/send')).toBe(true);
      expect(screen.getByText('Daily report sent')).toBeInTheDocument();
    });
  });

  it('calls create draft endpoint when Create Draft is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Content');
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
    render(<AppWithAuth />);

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
    render(<AppWithAuth />);

    await openView('Engagement');
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
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Run Due' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/posts/publish-due')).toBe(true);
      expect(screen.getByText('Due posts processed')).toBeInTheDocument();
    });
  });

  it('calls engagement poll endpoint when Poll is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Engagement');
    await waitFor(() => expect(screen.getByText('Comments stored')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Poll' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/engagement/poll')).toBe(true);
      expect(screen.getByText('Engagement poll complete')).toBeInTheDocument();
    });
  });

  it('calls learning recompute endpoint when Recompute is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Recompute' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/learning/recompute')).toBe(true);
      expect(screen.getByText('Learning recomputed')).toBeInTheDocument();
    });
  });

  it('calls kill switch on endpoint when Kill ON is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Kill ON' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/kill-switch/on')).toBe(true);
      expect(screen.getByText('Kill switch enabled')).toBeInTheDocument();
    });
  });

  it('calls kill switch off endpoint when Kill OFF is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Kill OFF' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/kill-switch/off')).toBe(true);
      expect(screen.getByText('Kill switch disabled')).toBeInTheDocument();
    });
  });

  it('calls posting on endpoint when Posting ON is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Posting ON' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/posting/on')).toBe(true);
      expect(screen.getByText('Posting enabled')).toBeInTheDocument();
    });
  });

  it('calls posting off endpoint when Posting OFF is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('System Controls')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Posting OFF' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/admin/posting/off')).toBe(true);
      expect(screen.getByText('Posting disabled')).toBeInTheDocument();
    });
  });

  it('runs bootstrap demo flow and calls key workflow endpoints', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

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
    render(<AppWithAuth />);

    await openView('Content');
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
    render(<AppWithAuth />);

    await openView('Engagement');
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
    render(<AppWithAuth />);

    await openView('Content');
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
    render(<AppWithAuth />);

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
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Posts tracked: 3')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('Queue filter'), { target: { value: 'due_now' } });

    await waitFor(() => {
      expect(screen.getByText('due-aaaa')).toBeInTheDocument();
      expect(screen.queryByText('future-b')).not.toBeInTheDocument();
      expect(screen.queryByText('publishe')).not.toBeInTheDocument();
      expect(screen.getAllByText(/due now/i).length).toBeGreaterThan(0);
    });
  });

  it('restores active view from localStorage on reload', async () => {
    localStorage.setItem('app.activeView', 'engagement');
    setupMockApi();
    render(<AppWithAuth />);

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
    render(<AppWithAuth />);

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
    render(<AppWithAuth />);

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
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('Algorithm Alignment')).toBeInTheDocument());
    expect(screen.getByText('Audit Trail')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByText('draft.generate').length).toBeGreaterThan(0);
      expect(screen.getByText(/engagement_bait/)).toBeInTheDocument();
    });
  });

  it('shows loading spinner on dashboard before data resolves', async () => {
    let resolveHealth;
    const pendingHealth = new Promise((resolve) => { resolveHealth = resolve; });
    const { calls } = setupMockApi();
    const originalFetch = global.fetch;
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      if (parsed.pathname === '/health') {
        await pendingHealth;
        return mockJson({ status: 'ok' });
      }
      return originalFetch(url, options);
    });
    render(<AppWithAuth />);

    // Wait for auth to complete (auth loading shows just "Loading...")
    // Then check for dashboard loading state
    await waitFor(() => expect(screen.getByText('Loading dashboard...')).toBeInTheDocument());

    await act(async () => { resolveHealth(); });

    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).not.toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Execution Console' })).toBeInTheDocument();
    });
  });

  it('shows error state on dashboard when all APIs fail', async () => {
    // Set up auth tokens so auth succeeds
    localStorage.setItem('auth.accessToken', 'mock-access-token');
    localStorage.setItem('auth.refreshToken', 'mock-refresh-token');

    global.fetch = vi.fn(async (url) => {
      const parsed = new URL(url);
      // Allow auth to succeed, fail everything else
      if (parsed.pathname === '/auth/me') return mockJson(mockUser);
      throw new Error('Network down');
    });
    render(<AppWithAuth />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard/)).toBeInTheDocument();
      expect(screen.getByText(/Network down/)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('shows empty state on dashboard when no posts exist', async () => {
    setupMockApi({ posts: [] });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    expect(screen.getByText('No posts yet')).toBeInTheDocument();
  });

  it('shows loading spinner on content view before data resolves', async () => {
    let resolveDrafts;
    const pendingDrafts = new Promise((resolve) => { resolveDrafts = resolve; });
    setupMockApi();
    const baseFetch = global.fetch;
    let draftsCallCount = 0;
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      if (parsed.pathname === '/drafts' && (options?.method || 'GET').toUpperCase() === 'GET') {
        draftsCallCount++;
        if (draftsCallCount > 1) {
          await pendingDrafts;
          return mockJson([]);
        }
      }
      return baseFetch(url, options);
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    await openView('Content');

    expect(screen.getByText('Loading content...')).toBeInTheDocument();

    await act(async () => { resolveDrafts(); });

    await waitFor(() => {
      expect(screen.queryByText('Loading content...')).not.toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Content Pipeline' })).toBeInTheDocument();
    });
  });

  it('shows error state on content view when API fails', async () => {
    setupMockApi();
    const baseFetch = global.fetch;
    let draftsGetCount = 0;
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      if (parsed.pathname === '/drafts' && (options?.method || 'GET').toUpperCase() === 'GET') {
        draftsGetCount++;
        if (draftsGetCount > 1) {
          throw new Error('Drafts unavailable');
        }
      }
      return baseFetch(url, options);
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    await openView('Content');

    await waitFor(() => {
      expect(screen.getByText(/Failed to load drafts/)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('shows empty state for pending drafts on content view', async () => {
    setupMockApi({ drafts: [] });
    render(<AppWithAuth />);

    await openView('Content');
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Content Pipeline' })).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('No pending drafts')).toBeInTheDocument());
  });

  it('shows loading spinner on engagement view before data resolves', async () => {
    let resolveComments;
    const pendingComments = new Promise((resolve) => { resolveComments = resolve; });
    setupMockApi();
    const baseFetch = global.fetch;
    let commentsCallCount = 0;
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      if (parsed.pathname === '/comments' && (options?.method || 'GET').toUpperCase() === 'GET') {
        commentsCallCount++;
        if (commentsCallCount > 1) {
          await pendingComments;
          return mockJson([]);
        }
      }
      return baseFetch(url, options);
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    await openView('Engagement');

    expect(screen.getByText('Loading engagement...')).toBeInTheDocument();

    await act(async () => { resolveComments(); });

    await waitFor(() => {
      expect(screen.queryByText('Loading engagement...')).not.toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Engagement' })).toBeInTheDocument();
    });
  });

  it('shows empty state for comments on engagement view', async () => {
    setupMockApi({ comments: [] });
    render(<AppWithAuth />);

    await openView('Engagement');
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Engagement' })).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('No comments')).toBeInTheDocument());
  });

  it('shows loading spinner on settings view before data resolves', async () => {
    let resolveConfig;
    const pendingConfig = new Promise((resolve) => { resolveConfig = resolve; });
    setupMockApi();
    const baseFetch = global.fetch;
    let configCallCount = 0;
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      if (parsed.pathname === '/admin/config') {
        configCallCount++;
        if (configCallCount > 1) {
          await pendingConfig;
          return mockJson({
            timezone: 'Africa/Johannesburg',
            posting_enabled: true,
            kill_switch: false,
          });
        }
      }
      return baseFetch(url, options);
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    await openView('Settings');

    expect(screen.getByText('Loading settings...')).toBeInTheDocument();

    await act(async () => { resolveConfig(); });

    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Settings' })).toBeInTheDocument();
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
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('Audit Trail')).toBeInTheDocument());
    expect(screen.getByText('draft.generate')).toBeInTheDocument();
    expect(screen.getByText('report.daily.send')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Audit filter'), { target: { value: 'worker' } });

    await waitFor(() => {
      expect(screen.queryByText('draft.generate')).not.toBeInTheDocument();
      expect(screen.getByText('report.daily.send')).toBeInTheDocument();
    });
  });

  // ── v4.8 Accessibility tests ──────────────────────────────

  it('renders skip-to-content link that becomes visible on focus', async () => {
    setupMockApi();
    render(<AppWithAuth />);
    await waitFor(() => expect(screen.getByText('Execution Console')).toBeInTheDocument());

    const skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toBeInTheDocument();
    expect(skipLink.getAttribute('href')).toBe('#main-content');
  });

  it('marks active sidebar nav item with aria-current', async () => {
    setupMockApi();
    render(<AppWithAuth />);
    await waitFor(() => expect(screen.getByText('Execution Console')).toBeInTheDocument());

    const dashboardBtn = screen.getByRole('button', { name: 'Dashboard' });
    expect(dashboardBtn.getAttribute('aria-current')).toBe('page');

    const contentBtn = screen.getByRole('button', { name: 'Content' });
    expect(contentBtn.getAttribute('aria-current')).toBeNull();
  });

  it('sidebar nav has aria-label', async () => {
    setupMockApi();
    render(<AppWithAuth />);
    await waitFor(() => expect(screen.getByText('Execution Console')).toBeInTheDocument());

    const nav = screen.getByRole('navigation', { name: 'Main navigation' });
    expect(nav).toBeInTheDocument();
  });

  it('main content area has aria-label reflecting active view', async () => {
    setupMockApi();
    render(<AppWithAuth />);
    await waitFor(() => expect(screen.getByText('Execution Console')).toBeInTheDocument());

    const main = screen.getByRole('main');
    expect(main.getAttribute('aria-label')).toBe('Dashboard view');
    expect(main.getAttribute('id')).toBe('main-content');
  });

  it('loading spinner has role=status and aria-busy', async () => {
    const { calls } = setupMockApi();
    const baseFetch = global.fetch;

    let draftsGetCount = 0;
    const pendingDrafts = new Promise(() => {});
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      const method = (options?.method || 'GET').toUpperCase();
      if (parsed.pathname === '/drafts' && method === 'GET') {
        draftsGetCount++;
        if (draftsGetCount > 1) {
          await pendingDrafts;
          return mockJson([]);
        }
      }
      return baseFetch(url, options);
    });

    render(<AppWithAuth />);
    await waitFor(() => expect(screen.getByText('Execution Console')).toBeInTheDocument());
    await openView('Content');

    await waitFor(() => {
      const statusElements = screen.getAllByRole('status');
      const spinner = statusElements.find((el) => el.getAttribute('aria-busy') === 'true');
      expect(spinner).toBeTruthy();
      expect(spinner.textContent).toContain('Loading');
    });
  });

  it('error message has role=alert', async () => {
    // Set up auth tokens so auth succeeds
    localStorage.setItem('auth.accessToken', 'mock-access-token');
    localStorage.setItem('auth.refreshToken', 'mock-refresh-token');

    global.fetch = vi.fn(async (url) => {
      const parsed = new URL(url);
      // Allow auth to succeed, fail everything else
      if (parsed.pathname === '/auth/me') return mockJson(mockUser);
      throw new Error('Network down');
    });
    render(<AppWithAuth />);

    await waitFor(() => {
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(alert.textContent).toContain('Network down');
    });
  });

  it('operational alert items have role=alert', async () => {
    setupMockApi({
      adminConfig: { kill_switch: true },
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Execution Console')).toBeInTheDocument());
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.length).toBeGreaterThan(0);
    });
  });

  // ── v6.3 Pipeline View tests ──────────────────────────────

  it('renders pipeline view with status overview cards and stage visualization', async () => {
    setupMockApi({
      pipelineOverview: {
        total: 10, claimed: 2,
        status_counts: { backlog: 3, todo: 2, writing: 1, review: 1, ready_to_publish: 0, published: 1, amplified: 0, done: 2 },
      },
      pipelineHealth: {
        health_status: 'healthy', overview: { total: 10 },
        stale_claims: 0, errored_items: 0, stuck_items: 0, checked_at: '2026-02-10T12:00:00Z',
      },
    });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    // Health status in subtitle
    expect(screen.getByText(/Health: healthy/)).toBeInTheDocument();
    expect(screen.getByText(/Total items: 10/)).toBeInTheDocument();

    // Overview cards
    expect(screen.getByText('Backlog')).toBeInTheDocument();
    expect(screen.getByText('In progress')).toBeInTheDocument();
    expect(screen.getByText('Ready / Published')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();

    // Pipeline stage visualization
    expect(screen.getByText('Pipeline Stages')).toBeInTheDocument();
  });

  it('shows health status banner when pipeline is degraded', async () => {
    setupMockApi({
      pipelineHealth: {
        health_status: 'degraded', overview: { total: 5 },
        stale_claims: 0, errored_items: 2, stuck_items: 1, checked_at: '2026-02-10T12:00:00Z',
      },
    });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    await waitFor(() => {
      expect(screen.getByText(/Pipeline degraded/)).toBeInTheDocument();
      expect(screen.getByText(/2 errored item/)).toBeInTheDocument();
      expect(screen.getByText(/1 stuck item/)).toBeInTheDocument();
    });
  });

  it('shows pipeline items list with status badges', async () => {
    setupMockApi({
      pipelineItems: [
        {
          id: 'pi-11111111-1111-1111-1111-111111111111',
          status: 'WRITING',
          pillar_theme: 'Adtech fundamentals',
          sub_theme: 'Programmatic buying',
          topic_keyword: 'real-time bidding',
          claimed_by: 'writer-001',
          quality_score: null,
          readability_score: null,
          fact_check_status: null,
          last_error: null,
          revision_count: 1,
          max_revisions: 3,
          updated_at: '2026-02-10T10:00:00Z',
          draft_id: null,
        },
      ],
    });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    await waitFor(() => {
      expect(screen.getByText('real-time bidding')).toBeInTheDocument();
      expect(screen.getByText(/Adtech fundamentals/)).toBeInTheDocument();
      expect(screen.getByText(/claimed by writer-001/)).toBeInTheDocument();
      expect(screen.getByText(/Revisions: 1\/3/)).toBeInTheDocument();
    });
  });

  it('shows error details on pipeline items with last_error', async () => {
    setupMockApi({
      pipelineItems: [
        {
          id: 'pi-22222222-2222-2222-2222-222222222222',
          status: 'WRITING',
          pillar_theme: 'AI in advertising',
          sub_theme: 'Generative creative',
          topic_keyword: 'ai-creative-gen',
          claimed_by: null,
          quality_score: null,
          readability_score: null,
          fact_check_status: null,
          last_error: 'Writer failed: LLM timeout after 30s',
          revision_count: 2,
          max_revisions: 3,
          updated_at: '2026-02-10T09:00:00Z',
          draft_id: null,
        },
      ],
    });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    await waitFor(() => {
      expect(screen.getByText(/Error: Writer failed: LLM timeout/)).toBeInTheDocument();
    });
  });

  it('calls run morgan agent endpoint when Run Morgan is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Run Morgan' }));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/pipeline/run/morgan')).toBe(true);
      expect(screen.getByText('Morgan PM complete')).toBeInTheDocument();
    });
  });

  it('calls agent trigger endpoint when agent control button is clicked', async () => {
    const { calls } = setupMockApi();
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Agent Controls')).toBeInTheDocument());

    // Click the Scout agent button (first in the agent controls grid)
    fireEvent.click(screen.getByText('Scout').closest('button'));

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST' && call.path === '/pipeline/run/scout')).toBe(true);
      expect(screen.getByText('Scout complete')).toBeInTheDocument();
    });
  });

  it('shows loading spinner on pipeline view before data resolves', async () => {
    let resolveOverview;
    const pendingOverview = new Promise((resolve) => { resolveOverview = resolve; });
    setupMockApi();
    const baseFetch = global.fetch;
    let overviewCallCount = 0;
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      if (parsed.pathname === '/pipeline/overview') {
        overviewCallCount++;
        if (overviewCallCount >= 1) {
          await pendingOverview;
          return mockJson({ total: 0, claimed: 0, status_counts: {} });
        }
      }
      return baseFetch(url, options);
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    await openView('Pipeline');

    expect(screen.getByText('Loading pipeline...')).toBeInTheDocument();

    await act(async () => { resolveOverview(); });

    await waitFor(() => {
      expect(screen.queryByText('Loading pipeline...')).not.toBeInTheDocument();
      expect(screen.getByText('Content Pipeline')).toBeInTheDocument();
    });
  });

  it('shows error state on pipeline view when API fails', async () => {
    setupMockApi();
    const baseFetch = global.fetch;
    let overviewCallCount = 0;
    global.fetch = vi.fn(async (url, options) => {
      const parsed = new URL(url);
      if (parsed.pathname === '/pipeline/overview') {
        overviewCallCount++;
        if (overviewCallCount >= 1) {
          throw new Error('Pipeline unavailable');
        }
      }
      return baseFetch(url, options);
    });
    render(<AppWithAuth />);

    await waitFor(() => expect(screen.getByText('Data refreshed')).toBeInTheDocument());
    await openView('Pipeline');

    await waitFor(() => {
      expect(screen.getByText(/Failed to load pipeline/)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('shows empty state on pipeline view when no items exist', async () => {
    setupMockApi({ pipelineItems: [] });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('No pipeline items')).toBeInTheDocument());
  });

  it('pipeline nav button has aria-current when active', async () => {
    setupMockApi();
    render(<AppWithAuth />);
    await waitFor(() => expect(screen.getByText('Execution Console')).toBeInTheDocument());

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    const pipelineBtn = screen.getByRole('button', { name: 'Pipeline' });
    expect(pipelineBtn.getAttribute('aria-current')).toBe('page');
  });

  // ── v6.4 Pipeline Mode / Shadow Mode tests ──────────────────

  it('settings view shows pipeline mode selector with current mode', async () => {
    setupMockApi({ adminConfig: { pipeline_mode: 'LEGACY' } });
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('Pipeline Mode')).toBeInTheDocument());

    // Should show mode buttons
    expect(screen.getByRole('button', { name: 'Legacy' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Shadow' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'V6' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Disabled' })).toBeInTheDocument();

    // Current mode indicator — text split across <strong> element so check container
    expect(screen.getByText('LEGACY')).toBeInTheDocument();
  });

  it('clicking shadow mode button calls pipeline-mode endpoint', async () => {
    const { calls } = setupMockApi({ adminConfig: { pipeline_mode: 'LEGACY' } });
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('Pipeline Mode')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Shadow' }));

    await waitFor(() => {
      expect(calls.some((c) => c.method === 'POST' && c.path === '/admin/pipeline-mode/shadow')).toBe(true);
      expect(screen.getByText('Pipeline mode set to shadow')).toBeInTheDocument();
    });
  });

  it('pipeline view shows mode banner when not in V6 mode', async () => {
    setupMockApi({ adminConfig: { pipeline_mode: 'LEGACY' } });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    await waitFor(() => {
      expect(screen.getByTestId('pipeline-mode-banner')).toBeInTheDocument();
      expect(screen.getByText(/Pipeline Mode: LEGACY/)).toBeInTheDocument();
      expect(screen.getByText(/V6 agents are not active/)).toBeInTheDocument();
    });
  });

  it('pipeline view shows shadow mode warning banner', async () => {
    setupMockApi({ adminConfig: { pipeline_mode: 'SHADOW' } });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    await waitFor(() => {
      expect(screen.getByTestId('pipeline-mode-banner')).toBeInTheDocument();
      expect(screen.getByText(/Pipeline Mode: SHADOW/)).toBeInTheDocument();
      expect(screen.getByText(/do NOT publish/)).toBeInTheDocument();
    });
  });

  it('pipeline view hides mode banner when in V6 mode', async () => {
    setupMockApi({ adminConfig: { pipeline_mode: 'V6' } });
    render(<AppWithAuth />);

    await openView('Pipeline');
    await waitFor(() => expect(screen.getByText('Content Pipeline')).toBeInTheDocument());

    // Banner should NOT be shown in V6 mode
    await waitFor(() => {
      expect(screen.queryByTestId('pipeline-mode-banner')).not.toBeInTheDocument();
    });
  });

  it('admin config response includes pipeline_mode', async () => {
    const { calls } = setupMockApi({ adminConfig: { pipeline_mode: 'SHADOW' } });
    render(<AppWithAuth />);

    await openView('Settings');
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument());

    // Verify admin config was requested
    await waitFor(() => {
      expect(calls.some((c) => c.method === 'GET' && c.path === '/admin/config')).toBe(true);
    });

    // Shadow mode specific text should appear
    await waitFor(() => {
      expect(screen.getByText(/V6 runs alongside legacy but does NOT publish/)).toBeInTheDocument();
    });
  });
});
