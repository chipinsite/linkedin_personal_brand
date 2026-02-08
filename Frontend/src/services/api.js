const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

// Token storage keys
const ACCESS_TOKEN_KEY = 'auth.accessToken';
const REFRESH_TOKEN_KEY = 'auth.refreshToken';
const USER_KEY = 'auth.user';

// Token management
function getAccessToken() {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

function getRefreshToken() {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function setTokens(accessToken, refreshToken) {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  } catch {
    // ignore storage failures
  }
}

function clearTokens() {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    // ignore storage failures
  }
}

function getStoredUser() {
  try {
    const userJson = localStorage.getItem(USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
  } catch {
    return null;
  }
}

function setStoredUser(user) {
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    // ignore storage failures
  }
}

// Track if we're currently refreshing to avoid multiple refresh attempts
let isRefreshing = false;
let refreshPromise = null;

// Callback for when auth state changes (logout on 401)
let onAuthError = null;

export function setOnAuthError(callback) {
  onAuthError = callback;
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    clearTokens();
    throw new Error('Token refresh failed');
  }

  const data = await response.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

async function request(path, options = {}, skipAuth = false) {
  const headers = { ...(options.headers || {}) };

  if (options.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Add authentication header
  if (!skipAuth) {
    const accessToken = getAccessToken();
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    } else if (API_KEY) {
      headers['x-api-key'] = API_KEY;
    }
  }

  let response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  // Handle token expiration
  if (response.status === 401 && !skipAuth && getRefreshToken()) {
    // Try to refresh the token
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = refreshAccessToken()
        .then((newToken) => {
          isRefreshing = false;
          return newToken;
        })
        .catch((err) => {
          isRefreshing = false;
          if (onAuthError) {
            onAuthError();
          }
          throw err;
        });
    }

    try {
      const newToken = await refreshPromise;
      // Retry the original request with new token
      headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      });
    } catch {
      // Refresh failed, clear tokens and notify
      clearTokens();
      if (onAuthError) {
        onAuthError();
      }
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!response.ok) {
    const body = await response.text();

    // If still 401 after refresh attempt, clear auth and notify
    if (response.status === 401) {
      clearTokens();
      if (onAuthError) {
        onAuthError();
      }
    }

    throw new Error(`API ${response.status} ${response.statusText}: ${body}`);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export const api = {
  // Auth endpoints
  login: async (emailOrUsername, password) => {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email_or_username: emailOrUsername, password }),
    }, true);
    setTokens(data.access_token, data.refresh_token);
    // Fetch and store user info
    const user = await request('/auth/me');
    setStoredUser(user);
    return { tokens: data, user };
  },

  logout: async () => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        await request('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // Ignore logout errors, clear tokens anyway
      }
    }
    clearTokens();
  },

  logoutAll: async () => {
    try {
      await request('/auth/logout-all', { method: 'POST' });
    } catch {
      // Ignore errors
    }
    clearTokens();
  },

  register: (email, username, password, fullName = null) =>
    request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password, full_name: fullName }),
    }, true),

  getCurrentUser: () => request('/auth/me'),

  changePassword: (currentPassword, newPassword) =>
    request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    }),

  // Check if user is authenticated (has valid tokens)
  isAuthenticated: () => {
    return !!getAccessToken();
  },

  getStoredUser,

  // Clear auth state (for when auth error callback is triggered)
  clearAuth: clearTokens,

  // Health endpoints (no auth required)
  health: () => request('/health', {}, true),
  deepHealth: () => request('/health/deep', {}, true),
  readiness: () => request('/health/readiness', {}, true),

  // Protected endpoints
  drafts: () => request('/drafts'),
  createDraft: (payload) => request('/drafts', { method: 'POST', body: JSON.stringify(payload) }),
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
  createComment: (payload) => request('/comments', { method: 'POST', body: JSON.stringify(payload) }),
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
  exportState: () => request('/admin/export-state'),
  killSwitchOn: () => request('/admin/kill-switch/on', { method: 'POST' }),
  killSwitchOff: () => request('/admin/kill-switch/off', { method: 'POST' }),
  postingOn: () => request('/admin/posting/on', { method: 'POST' }),
  postingOff: () => request('/admin/posting/off', { method: 'POST' }),
};
