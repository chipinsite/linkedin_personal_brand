const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (API_KEY) {
    headers['x-api-key'] = API_KEY;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status} ${response.statusText}: ${body}`);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export const api = {
  health: () => request('/health'),
  deepHealth: () => request('/health/deep'),
  readiness: () => request('/health/readiness'),

  drafts: () => request('/drafts'),
  generateDraft: () => request('/drafts/generate', { method: 'POST' }),
  approveDraft: (id) => request(`/drafts/${id}/approve`, { method: 'POST', body: JSON.stringify({}) }),
  rejectDraft: (id, reason) => request(`/drafts/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),

  posts: () => request('/posts'),
  publishDue: () => request('/posts/publish-due', { method: 'POST' }),
  confirmPublish: (id, linkedinPostUrl) =>
    request(`/posts/${id}/confirm-manual-publish`, {
      method: 'POST',
      body: JSON.stringify({ linkedin_post_url: linkedinPostUrl }),
    }),
  updateMetrics: (id, payload) => request(`/posts/${id}/metrics`, { method: 'POST', body: JSON.stringify(payload) }),

  comments: () => request('/comments'),
  pollEngagement: () => request('/engagement/poll', { method: 'POST' }),
  engagementStatus: () => request('/engagement/status'),

  sources: () => request('/sources'),
  ingestSources: (feedUrls) => request('/sources/ingest', { method: 'POST', body: JSON.stringify({ feed_urls: feedUrls }) }),

  learningWeights: () => request('/learning/weights'),
  recomputeLearning: () => request('/learning/recompute', { method: 'POST' }),

  dailyReport: () => request('/reports/daily'),
  sendDailyReport: () => request('/reports/daily/send', { method: 'POST' }),

  adminConfig: () => request('/admin/config'),
  algorithmAlignment: () => request('/admin/algorithm-alignment'),
  auditLogs: () => request('/admin/audit-logs'),
  killSwitchOn: () => request('/admin/kill-switch/on', { method: 'POST' }),
  killSwitchOff: () => request('/admin/kill-switch/off', { method: 'POST' }),
  postingOn: () => request('/admin/posting/on', { method: 'POST' }),
  postingOff: () => request('/admin/posting/off', { method: 'POST' }),
};
