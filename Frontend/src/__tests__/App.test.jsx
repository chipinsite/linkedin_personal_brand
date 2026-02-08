import { render, screen, waitFor } from '@testing-library/react';
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

function routePayload(pathname) {
  if (pathname === '/health') return { status: 'ok' };
  if (pathname === '/health/deep') return { status: 'ok', checks: { database: { ok: true }, redis: { ok: true } } };
  if (pathname === '/health/readiness') return { ready: true };
  if (pathname === '/drafts') return [];
  if (pathname === '/posts') return [];
  if (pathname === '/comments') return [];
  if (pathname === '/sources') return [];
  if (pathname === '/learning/weights') return { format_weights_json: '{}', tone_weights_json: '{}' };
  if (pathname === '/reports/daily') {
    return {
      report_date: '2026-02-08',
      posts_published: 0,
      total_impressions: 0,
      total_reactions: 0,
      total_comments: 0,
      total_shares: 0,
      avg_engagement_rate: 0,
      auto_replies_sent: 0,
      escalations: 0,
    };
  }
  if (pathname === '/admin/config') {
    return {
      timezone: 'Africa/Johannesburg',
      posting_window_start: '08:00',
      posting_window_end: '17:00',
      posting_enabled: true,
      comment_replies_enabled: true,
      max_auto_replies: 5,
      escalation_follower_threshold: 10000,
      linkedin_api_mode: 'manual',
      kill_switch: false,
    };
  }
  if (pathname === '/admin/algorithm-alignment') return { enforced: { engagement_bait: 'blocked' } };
  if (pathname === '/admin/audit-logs') return [];
  if (pathname === '/engagement/status') return { monitored_total: 0, active_total: 0, due_total: 0 };
  return {};
}

describe('App', () => {
  beforeEach(() => {
    global.fetch = vi.fn((url) => {
      const parsed = new URL(url);
      return mockJson(routePayload(parsed.pathname));
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders dashboard and loads initial data', async () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Execution Console' })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Data refreshed')).toBeInTheDocument();
      expect(screen.getByText('Health: ok')).toBeInTheDocument();
      expect(screen.getByText('Readiness: true')).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalled();
  });
});
