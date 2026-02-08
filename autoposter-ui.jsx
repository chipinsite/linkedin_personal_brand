import { useState, useEffect, useCallback } from "react";

// ─── MOCK DATA ───────────────────────────────────────────────────────────────
const MOCK_DRAFTS = [
  {
    id: "d1",
    pillar_theme: "Adtech Fundamentals",
    sub_theme: "Supply Path Optimisation",
    format: "TEXT",
    tone: "EDUCATIONAL",
    status: "PENDING",
    created_at: "2026-02-08T04:00:00Z",
    content_body:
      "Supply path optimisation is no longer a nice to have. It is a commercial imperative.\n\nOver the past 18 months, I have watched agencies across Sub-Saharan Africa begin to take SPO seriously. The shift is driven by three things: rising CPMs, growing scrutiny on working media ratios, and the simple reality that buyers now have better tools to see where their money goes.\n\nThe challenge is that SPO is not a one-time exercise. It requires ongoing evaluation of intermediaries, constant validation of bid paths, and a willingness to cut partners who add cost without adding value.\n\nFor those of us in the sell side, the implication is clear: transparency is not optional. If you cannot articulate the value you add in the supply chain, you will be optimised out of it.\n\nWhat is your experience with SPO adoption in your market?",
    guardrail_check_passed: true,
    guardrail_violations: [],
  },
  {
    id: "d2",
    pillar_theme: "Agentic AI in Adtech",
    sub_theme: "Autonomous Campaign Management",
    format: "IMAGE",
    tone: "OPINIONATED",
    status: "APPROVED",
    created_at: "2026-02-07T04:00:00Z",
    scheduled_time: "2026-02-08T11:23:00Z",
    content_body:
      "The idea that an AI agent can manage a campaign end to end is closer than most people think. But the real question is not whether AI can do it. The question is whether we are ready to let it.\n\nI have seen three patterns emerge in autonomous campaign management pilots: agents that optimise bids outperform manual teams by 15 to 30 percent, agents that manage creative rotation reduce fatigue faster, and agents that handle budget pacing eliminate the end of month scramble.\n\nThe gap is trust. Most advertisers are not comfortable handing over budget authority to a system they cannot fully explain. And that is a reasonable concern.\n\nThe path forward is not full autonomy overnight. It is graduated delegation with clear guardrails.",
    guardrail_check_passed: true,
    guardrail_violations: [],
  },
];

const MOCK_POSTS = [
  {
    id: "p1",
    draft_id: "d0",
    linkedin_post_url: "https://linkedin.com/posts/sphiwe-123",
    published_at: "2026-02-07T09:45:00Z",
    content_body:
      "Retail media is reshaping the advertising landscape in ways most agencies have not yet fully grasped...",
    format: "TEXT",
    tone: "EDUCATIONAL",
    impressions: 4820,
    reactions: 127,
    comments_count: 23,
    shares: 8,
    engagement_rate: 3.28,
  },
  {
    id: "p2",
    draft_id: "d_old",
    linkedin_post_url: "https://linkedin.com/posts/sphiwe-122",
    published_at: "2026-02-06T14:12:00Z",
    content_body:
      "Three lessons from building AI-powered creative optimisation agents in emerging markets...",
    format: "CAROUSEL",
    tone: "DIRECT",
    impressions: 6340,
    reactions: 198,
    comments_count: 41,
    shares: 19,
    engagement_rate: 4.07,
  },
  {
    id: "p3",
    draft_id: "d_old2",
    linkedin_post_url: "https://linkedin.com/posts/sphiwe-121",
    published_at: "2026-02-05T10:30:00Z",
    content_body:
      "Is programmatic buying in Africa finally at an inflection point? The evidence suggests yes...",
    format: "TEXT",
    tone: "EXPLORATORY",
    impressions: 3210,
    reactions: 89,
    comments_count: 15,
    shares: 5,
    engagement_rate: 3.4,
  },
];

const MOCK_COMMENTS = [
  {
    id: "c1",
    published_post_id: "p1",
    commenter_name: "Thabo Mokoena",
    commenter_follower_count: 12400,
    comment_text:
      "This resonates deeply. We have been piloting retail media networks with two major FMCG clients and the attribution challenge is real. Would love to discuss collaboration opportunities.",
    is_high_value: true,
    high_value_reason: "PARTNERSHIP_SIGNAL",
    escalated: true,
    auto_reply_sent: false,
  },
  {
    id: "c2",
    published_post_id: "p1",
    commenter_name: "Lisa van der Berg",
    commenter_follower_count: 3200,
    comment_text:
      "Great post. What measurement framework would you recommend for retail media?",
    is_high_value: true,
    high_value_reason: "TECHNICAL_QUESTION",
    escalated: true,
    auto_reply_sent: false,
  },
  {
    id: "c3",
    published_post_id: "p1",
    commenter_name: "David Okafor",
    commenter_follower_count: 850,
    comment_text:
      "Spot on analysis. The SPO piece is what most people miss in this conversation.",
    is_high_value: false,
    high_value_reason: null,
    escalated: false,
    auto_reply_sent: true,
    auto_reply_text: "Thank you, David. You raise a good point about SPO. It is increasingly becoming the connective tissue between retail media and programmatic efficiency.",
  },
];

const MOCK_WEIGHTS = {
  format: { TEXT: 0.48, IMAGE: 0.32, CAROUSEL: 0.2 },
  tone: { EDUCATIONAL: 0.38, OPINIONATED: 0.27, DIRECT: 0.2, EXPLORATORY: 0.15 },
};

const MOCK_CONFIG = {
  posting_enabled: true,
  comment_replies_enabled: true,
  kill_switch: false,
  timezone: "Africa/Johannesburg",
  posting_window_start: "08:00",
  posting_window_end: "17:00",
  max_auto_replies: 5,
};

// ─── ICONS (inline SVGs) ────────────────────────────────────────────────────
const Icons = {
  dashboard: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  content: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  ),
  publish: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" />
    </svg>
  ),
  engage: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  ),
  analytics: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 20V10" /><path d="M12 20V4" /><path d="M6 20v-6" />
    </svg>
  ),
  settings: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.32 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  ),
  alert: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  check: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  copy: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
    </svg>
  ),
  clock: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  chevron: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  ),
  fire: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z" />
    </svg>
  ),
};

// ─── UTILITIES ───────────────────────────────────────────────────────────────
const formatDate = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-ZA", { day: "numeric", month: "short", year: "numeric" });
};
const formatTime = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-ZA", { hour: "2-digit", minute: "2-digit" });
};
const truncate = (str, len = 120) => (str?.length > len ? str.slice(0, len) + "..." : str || "");
const pct = (n) => `${Math.round(n * 100)}%`;

// ─── STYLE CONSTANTS ─────────────────────────────────────────────────────────
const C = {
  bg: "#0C0E12",
  surface: "#14161C",
  surfaceHover: "#1A1D25",
  border: "#23272F",
  borderLight: "#2C3140",
  text: "#E8E9EC",
  textMuted: "#8B8F9A",
  textDim: "#5A5F6E",
  accent: "#C8935A",
  accentMuted: "rgba(200,147,90,0.15)",
  accentBright: "#E0A96A",
  success: "#4ADE80",
  successMuted: "rgba(74,222,128,0.12)",
  warning: "#FBBF24",
  warningMuted: "rgba(251,191,36,0.12)",
  danger: "#F87171",
  dangerMuted: "rgba(248,113,113,0.12)",
  info: "#60A5FA",
  infoMuted: "rgba(96,165,250,0.12)",
};

// ─── COMPONENTS ──────────────────────────────────────────────────────────────

function StatusBadge({ status, size = "sm" }) {
  const map = {
    PENDING: { bg: C.warningMuted, color: C.warning, label: "Pending" },
    APPROVED: { bg: C.successMuted, color: C.success, label: "Approved" },
    REJECTED: { bg: C.dangerMuted, color: C.danger, label: "Rejected" },
    PUBLISHED: { bg: C.infoMuted, color: C.info, label: "Published" },
    ESCALATED: { bg: C.dangerMuted, color: C.danger, label: "Escalated" },
    TEXT: { bg: C.accentMuted, color: C.accent, label: "Text" },
    IMAGE: { bg: C.infoMuted, color: C.info, label: "Image" },
    CAROUSEL: { bg: C.successMuted, color: C.success, label: "Carousel" },
    EDUCATIONAL: { bg: C.infoMuted, color: C.info, label: "Educational" },
    OPINIONATED: { bg: C.warningMuted, color: C.warning, label: "Opinionated" },
    DIRECT: { bg: C.accentMuted, color: C.accent, label: "Direct" },
    EXPLORATORY: { bg: C.successMuted, color: C.success, label: "Exploratory" },
  };
  const s = map[status] || { bg: C.border, color: C.textMuted, label: status };
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: size === "sm" ? "2px 8px" : "4px 12px",
        borderRadius: "4px",
        background: s.bg,
        color: s.color,
        fontSize: size === "sm" ? "11px" : "12px",
        fontWeight: 500,
        letterSpacing: "0.02em",
        textTransform: "uppercase",
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      {s.label}
    </span>
  );
}

function MetricCard({ label, value, sub, trend, accent }) {
  const col = accent || C.accent;
  return (
    <div
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: "8px",
        padding: "20px 24px",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        minWidth: 0,
      }}
    >
      <span style={{ fontSize: "12px", color: C.textMuted, fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", fontFamily: "'DM Sans', sans-serif" }}>
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
        <span style={{ fontSize: "28px", fontWeight: 600, color: C.text, fontFamily: "'Instrument Serif', Georgia, serif", lineHeight: 1 }}>
          {value}
        </span>
        {trend && (
          <span style={{ fontSize: "12px", color: trend > 0 ? C.success : C.danger, fontWeight: 500, fontFamily: "'DM Sans', sans-serif" }}>
            {trend > 0 ? "+" : ""}{trend}%
          </span>
        )}
      </div>
      {sub && <span style={{ fontSize: "12px", color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>{sub}</span>}
    </div>
  );
}

function Button({ children, variant = "default", size = "md", onClick, style: extraStyle, disabled }) {
  const base = {
    display: "inline-flex", alignItems: "center", gap: "6px",
    border: "none", cursor: disabled ? "not-allowed" : "pointer",
    fontFamily: "'DM Sans', sans-serif", fontWeight: 500, letterSpacing: "0.01em",
    borderRadius: "6px", transition: "all 0.15s ease",
    opacity: disabled ? 0.5 : 1,
    fontSize: size === "sm" ? "12px" : "13px",
    padding: size === "sm" ? "6px 12px" : "8px 16px",
  };
  const variants = {
    default: { background: C.surfaceHover, color: C.text, border: `1px solid ${C.border}` },
    primary: { background: C.accent, color: "#0C0E12", fontWeight: 600 },
    danger: { background: C.dangerMuted, color: C.danger, border: `1px solid rgba(248,113,113,0.2)` },
    success: { background: C.successMuted, color: C.success, border: `1px solid rgba(74,222,128,0.2)` },
    ghost: { background: "transparent", color: C.textMuted },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{ ...base, ...variants[variant], ...extraStyle }}
    >
      {children}
    </button>
  );
}

function ProgressBar({ value, max = 100, color = C.accent, height = 4 }) {
  return (
    <div style={{ width: "100%", height, background: C.border, borderRadius: height / 2, overflow: "hidden" }}>
      <div style={{ width: `${(value / max) * 100}%`, height: "100%", background: color, borderRadius: height / 2, transition: "width 0.6s ease" }} />
    </div>
  );
}

// ─── DASHBOARD VIEW ──────────────────────────────────────────────────────────
function DashboardView() {
  const pendingDrafts = MOCK_DRAFTS.filter((d) => d.status === "PENDING").length;
  const approvedDrafts = MOCK_DRAFTS.filter((d) => d.status === "APPROVED").length;
  const escalatedComments = MOCK_COMMENTS.filter((c) => c.escalated && !c.auto_reply_sent).length;
  const latestPost = MOCK_POSTS[0];
  const totalImpressions = MOCK_POSTS.reduce((s, p) => s + p.impressions, 0);
  const avgEngagement = (MOCK_POSTS.reduce((s, p) => s + p.engagement_rate, 0) / MOCK_POSTS.length).toFixed(2);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
            Good morning, Sphiwe
          </h1>
          <p style={{ fontSize: "13px", color: C.textMuted, margin: "4px 0 0", fontFamily: "'DM Sans', sans-serif" }}>
            Sunday, 8 February 2026
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: MOCK_CONFIG.kill_switch ? C.danger : C.success }} />
          <span style={{ fontSize: "12px", color: C.textMuted, fontFamily: "'DM Sans', sans-serif" }}>
            System {MOCK_CONFIG.kill_switch ? "halted" : "active"}
          </span>
        </div>
      </div>

      {/* Attention banner */}
      {(pendingDrafts > 0 || escalatedComments > 0) && (
        <div style={{
          background: "linear-gradient(135deg, rgba(200,147,90,0.08), rgba(200,147,90,0.03))",
          border: `1px solid rgba(200,147,90,0.2)`,
          borderRadius: "8px", padding: "16px 20px",
          display: "flex", alignItems: "center", gap: "14px",
        }}>
          <div style={{ color: C.accent, flexShrink: 0 }}>{Icons.alert}</div>
          <div style={{ fontSize: "13px", color: C.text, fontFamily: "'DM Sans', sans-serif", lineHeight: 1.5 }}>
            {pendingDrafts > 0 && <span>You have <strong style={{ color: C.accent }}>{pendingDrafts} draft{pendingDrafts > 1 ? "s" : ""}</strong> awaiting approval. </span>}
            {escalatedComments > 0 && <span><strong style={{ color: C.accent }}>{escalatedComments} comment{escalatedComments > 1 ? "s" : ""}</strong> flagged for your response.</span>}
          </div>
        </div>
      )}

      {/* Metrics row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
        <MetricCard label="Impressions (7d)" value={totalImpressions.toLocaleString()} trend={12} />
        <MetricCard label="Avg Engagement" value={`${avgEngagement}%`} trend={8} />
        <MetricCard label="Posts Published" value={MOCK_POSTS.length} sub="3 in last 7 days" />
        <MetricCard label="Comments" value={MOCK_COMMENTS.length} sub={`${escalatedComments} need response`} />
      </div>

      {/* Two column layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Pending Draft */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif" }}>Next Draft</span>
            <StatusBadge status="PENDING" />
          </div>
          <div style={{ padding: "20px" }}>
            <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
              <StatusBadge status={MOCK_DRAFTS[0].format} />
              <StatusBadge status={MOCK_DRAFTS[0].tone} />
            </div>
            <p style={{ fontSize: "11px", color: C.textMuted, margin: "0 0 4px", fontFamily: "'DM Sans', sans-serif", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              {MOCK_DRAFTS[0].pillar_theme} › {MOCK_DRAFTS[0].sub_theme}
            </p>
            <p style={{ fontSize: "13px", color: C.textMuted, margin: "8px 0 16px", lineHeight: 1.6, fontFamily: "'DM Sans', sans-serif" }}>
              {truncate(MOCK_DRAFTS[0].content_body, 180)}
            </p>
            <div style={{ display: "flex", gap: "8px" }}>
              <Button variant="primary" size="sm">Approve</Button>
              <Button variant="default" size="sm">Edit</Button>
              <Button variant="danger" size="sm">Reject</Button>
            </div>
          </div>
        </div>

        {/* Escalated Comments */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif" }}>Escalated Comments</span>
            <span style={{ fontSize: "12px", color: C.accent, fontFamily: "'DM Sans', sans-serif" }}>{escalatedComments} pending</span>
          </div>
          <div style={{ padding: "0" }}>
            {MOCK_COMMENTS.filter((c) => c.escalated).map((comment, i) => (
              <div key={comment.id} style={{ padding: "16px 20px", borderBottom: i < MOCK_COMMENTS.filter(c => c.escalated).length - 1 ? `1px solid ${C.border}` : "none" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif" }}>
                    {comment.commenter_name}
                  </span>
                  <StatusBadge status="ESCALATED" />
                </div>
                <p style={{ fontSize: "12px", color: C.textDim, margin: "0 0 2px", fontFamily: "'DM Sans', sans-serif" }}>
                  {comment.commenter_follower_count?.toLocaleString()} followers · {comment.high_value_reason?.replace("_", " ")}
                </p>
                <p style={{ fontSize: "13px", color: C.textMuted, margin: "8px 0 12px", lineHeight: 1.5, fontFamily: "'DM Sans', sans-serif" }}>
                  {truncate(comment.comment_text, 140)}
                </p>
                <Button variant="primary" size="sm">Respond</Button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Performance */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif" }}>Recent Performance</span>
        </div>
        <div style={{ padding: "0" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2.5fr 1fr 1fr 1fr 1fr 1fr", padding: "10px 20px", borderBottom: `1px solid ${C.border}`, gap: "12px" }}>
            {["Post", "Format", "Impressions", "Reactions", "Comments", "Engagement"].map((h) => (
              <span key={h} style={{ fontSize: "11px", color: C.textDim, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", fontFamily: "'DM Sans', sans-serif" }}>
                {h}
              </span>
            ))}
          </div>
          {MOCK_POSTS.map((post) => (
            <div
              key={post.id}
              style={{
                display: "grid", gridTemplateColumns: "2.5fr 1fr 1fr 1fr 1fr 1fr",
                padding: "14px 20px", borderBottom: `1px solid ${C.border}`, gap: "12px",
                alignItems: "center", transition: "background 0.1s",
              }}
            >
              <div>
                <p style={{ fontSize: "13px", color: C.text, margin: 0, fontFamily: "'DM Sans', sans-serif", lineHeight: 1.4 }}>
                  {truncate(post.content_body, 70)}
                </p>
                <span style={{ fontSize: "11px", color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>
                  {formatDate(post.published_at)} · {formatTime(post.published_at)}
                </span>
              </div>
              <StatusBadge status={post.format} />
              <span style={{ fontSize: "13px", color: C.text, fontFamily: "'DM Sans', sans-serif" }}>{post.impressions.toLocaleString()}</span>
              <span style={{ fontSize: "13px", color: C.text, fontFamily: "'DM Sans', sans-serif" }}>{post.reactions}</span>
              <span style={{ fontSize: "13px", color: C.text, fontFamily: "'DM Sans', sans-serif" }}>{post.comments_count}</span>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ fontSize: "13px", color: post.engagement_rate >= 4 ? C.success : C.text, fontWeight: post.engagement_rate >= 4 ? 600 : 400, fontFamily: "'DM Sans', sans-serif" }}>
                  {post.engagement_rate}%
                </span>
                {post.engagement_rate >= 4 && <span style={{ color: C.success }}>{Icons.fire}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Learning Weights */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", padding: "20px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif", display: "block", marginBottom: "16px" }}>
            Format Distribution
          </span>
          {Object.entries(MOCK_WEIGHTS.format).map(([k, v]) => (
            <div key={k} style={{ marginBottom: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "12px", color: C.textMuted, fontFamily: "'DM Sans', sans-serif" }}>{k}</span>
                <span style={{ fontSize: "12px", color: C.text, fontFamily: "'DM Sans', sans-serif" }}>{pct(v)}</span>
              </div>
              <ProgressBar value={v * 100} color={k === "TEXT" ? C.accent : k === "IMAGE" ? C.info : C.success} />
            </div>
          ))}
        </div>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", padding: "20px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif", display: "block", marginBottom: "16px" }}>
            Tone Distribution
          </span>
          {Object.entries(MOCK_WEIGHTS.tone).map(([k, v]) => (
            <div key={k} style={{ marginBottom: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "12px", color: C.textMuted, fontFamily: "'DM Sans', sans-serif" }}>{k}</span>
                <span style={{ fontSize: "12px", color: C.text, fontFamily: "'DM Sans', sans-serif" }}>{pct(v)}</span>
              </div>
              <ProgressBar value={v * 100} color={k === "EDUCATIONAL" ? C.info : k === "OPINIONATED" ? C.warning : k === "DIRECT" ? C.accent : C.success} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── CONTENT PIPELINE VIEW ───────────────────────────────────────────────────
function ContentView() {
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleCopy = (text) => {
    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: "20px", fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
          Content Pipeline
        </h2>
        <Button variant="primary">Generate New Draft</Button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "20px", minHeight: "500px" }}>
        {/* Draft List */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: `1px solid ${C.border}` }}>
            <span style={{ fontSize: "12px", color: C.textMuted, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", fontFamily: "'DM Sans', sans-serif" }}>
              Drafts ({MOCK_DRAFTS.length})
            </span>
          </div>
          {MOCK_DRAFTS.map((draft) => (
            <div
              key={draft.id}
              onClick={() => setSelectedDraft(draft)}
              style={{
                padding: "14px 16px", borderBottom: `1px solid ${C.border}`,
                cursor: "pointer", transition: "background 0.1s",
                background: selectedDraft?.id === draft.id ? C.surfaceHover : "transparent",
                borderLeft: selectedDraft?.id === draft.id ? `2px solid ${C.accent}` : "2px solid transparent",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontSize: "12px", color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>
                  {formatDate(draft.created_at)}
                </span>
                <StatusBadge status={draft.status} />
              </div>
              <p style={{ fontSize: "12px", color: C.textMuted, margin: "0 0 4px", fontFamily: "'DM Sans', sans-serif", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                {draft.pillar_theme}
              </p>
              <p style={{ fontSize: "13px", color: C.text, margin: 0, lineHeight: 1.4, fontFamily: "'DM Sans', sans-serif" }}>
                {truncate(draft.content_body, 80)}
              </p>
              <div style={{ display: "flex", gap: "6px", marginTop: "8px" }}>
                <StatusBadge status={draft.format} />
                <StatusBadge status={draft.tone} />
              </div>
            </div>
          ))}
        </div>

        {/* Draft Detail */}
        {selectedDraft ? (
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span style={{ fontSize: "11px", color: C.textDim, fontFamily: "'DM Sans', sans-serif", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  {selectedDraft.pillar_theme} › {selectedDraft.sub_theme}
                </span>
              </div>
              <div style={{ display: "flex", gap: "6px" }}>
                <StatusBadge status={selectedDraft.format} />
                <StatusBadge status={selectedDraft.tone} />
                <StatusBadge status={selectedDraft.status} />
              </div>
            </div>

            {/* Quality Checks */}
            <div style={{ padding: "12px 20px", borderBottom: `1px solid ${C.border}`, background: "rgba(200,147,90,0.03)" }}>
              <span style={{ fontSize: "11px", color: C.textDim, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", fontFamily: "'DM Sans', sans-serif", display: "block", marginBottom: "8px" }}>
                Quality Checks
              </span>
              <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
                {[
                  { label: "Word count", value: selectedDraft.content_body.split(/\s+/).length, ok: selectedDraft.content_body.split(/\s+/).length <= 300 },
                  { label: "Hashtags", value: (selectedDraft.content_body.match(/#/g) || []).length, ok: (selectedDraft.content_body.match(/#/g) || []).length <= 3 },
                  { label: "External links", value: (selectedDraft.content_body.match(/https?:\/\//g) || []).length, ok: (selectedDraft.content_body.match(/https?:\/\//g) || []).length === 0 },
                  { label: "Guardrails", value: selectedDraft.guardrail_check_passed ? "Passed" : "Failed", ok: selectedDraft.guardrail_check_passed },
                ].map((check) => (
                  <div key={check.label} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <span style={{ color: check.ok ? C.success : C.warning }}>{check.ok ? Icons.check : Icons.alert}</span>
                    <span style={{ fontSize: "12px", color: check.ok ? C.textMuted : C.warning, fontFamily: "'DM Sans', sans-serif" }}>
                      {check.label}: {check.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Content body */}
            <div style={{ padding: "24px 20px", flex: 1, overflowY: "auto" }}>
              <p style={{
                fontSize: "14px", color: C.text, lineHeight: 1.8,
                fontFamily: "'DM Sans', sans-serif",
                whiteSpace: "pre-wrap", margin: 0,
              }}>
                {selectedDraft.content_body}
              </p>
            </div>

            {/* Actions */}
            <div style={{ padding: "16px 20px", borderTop: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", gap: "8px" }}>
                {selectedDraft.status === "PENDING" && (
                  <>
                    <Button variant="primary">Approve</Button>
                    <Button variant="default">Edit</Button>
                    <Button variant="danger">Reject</Button>
                  </>
                )}
                {selectedDraft.status === "APPROVED" && (
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ color: C.textDim, fontSize: "12px", fontFamily: "'DM Sans', sans-serif" }}>{Icons.clock}</span>
                    <span style={{ fontSize: "12px", color: C.textMuted, fontFamily: "'DM Sans', sans-serif" }}>
                      Scheduled for {formatTime(selectedDraft.scheduled_time)} · {formatDate(selectedDraft.scheduled_time)}
                    </span>
                  </div>
                )}
              </div>
              <Button variant="ghost" size="sm" onClick={() => handleCopy(selectedDraft.content_body)}>
                {Icons.copy}
                {copied ? "Copied" : "Copy draft"}
              </Button>
            </div>
          </div>
        ) : (
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <p style={{ fontSize: "13px", color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>
              Select a draft to review
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── ENGAGEMENT VIEW ─────────────────────────────────────────────────────────
function EngagementView() {
  const [filter, setFilter] = useState("all");

  const filtered = filter === "all"
    ? MOCK_COMMENTS
    : filter === "escalated"
      ? MOCK_COMMENTS.filter((c) => c.escalated)
      : MOCK_COMMENTS.filter((c) => c.auto_reply_sent);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: "20px", fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
          Engagement
        </h2>
        <Button variant="default">Poll Comments</Button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
        <MetricCard label="Total Comments" value={MOCK_COMMENTS.length} />
        <MetricCard label="Escalated" value={MOCK_COMMENTS.filter((c) => c.escalated).length} accent={C.danger} />
        <MetricCard label="Auto Replied" value={MOCK_COMMENTS.filter((c) => c.auto_reply_sent).length} accent={C.success} />
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: "4px", background: C.surface, border: `1px solid ${C.border}`, borderRadius: "6px", padding: "4px", width: "fit-content" }}>
        {["all", "escalated", "replied"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: "6px 14px", border: "none", borderRadius: "4px", cursor: "pointer",
              background: filter === f ? C.surfaceHover : "transparent",
              color: filter === f ? C.text : C.textMuted,
              fontSize: "12px", fontWeight: 500, fontFamily: "'DM Sans', sans-serif",
              textTransform: "capitalize", transition: "all 0.15s",
            }}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Comment List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {filtered.map((comment) => (
          <div key={comment.id} style={{
            background: C.surface, border: `1px solid ${comment.escalated ? "rgba(248,113,113,0.2)" : C.border}`,
            borderRadius: "8px", padding: "20px",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "14px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif" }}>
                    {comment.commenter_name}
                  </span>
                  {comment.commenter_follower_count >= 10000 && (
                    <span style={{ fontSize: "10px", color: C.accent, background: C.accentMuted, padding: "1px 6px", borderRadius: "3px", fontWeight: 600, fontFamily: "'DM Sans', sans-serif" }}>
                      INFLUENTIAL
                    </span>
                  )}
                </div>
                <span style={{ fontSize: "12px", color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>
                  {comment.commenter_follower_count?.toLocaleString()} followers
                  {comment.high_value_reason && ` · ${comment.high_value_reason.replace(/_/g, " ")}`}
                </span>
              </div>
              {comment.escalated && !comment.auto_reply_sent && <StatusBadge status="ESCALATED" />}
              {comment.auto_reply_sent && <StatusBadge status="PUBLISHED" />}
            </div>

            <p style={{ fontSize: "13px", color: C.text, lineHeight: 1.6, margin: "0 0 12px", fontFamily: "'DM Sans', sans-serif" }}>
              {comment.comment_text}
            </p>

            {comment.auto_reply_sent && comment.auto_reply_text && (
              <div style={{ marginLeft: "20px", padding: "12px 16px", background: C.bg, borderRadius: "6px", borderLeft: `2px solid ${C.accent}` }}>
                <span style={{ fontSize: "11px", color: C.textDim, display: "block", marginBottom: "4px", fontFamily: "'DM Sans', sans-serif" }}>Auto reply</span>
                <p style={{ fontSize: "13px", color: C.textMuted, margin: 0, lineHeight: 1.5, fontFamily: "'DM Sans', sans-serif" }}>
                  {comment.auto_reply_text}
                </p>
              </div>
            )}

            {comment.escalated && !comment.auto_reply_sent && (
              <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
                <Button variant="primary" size="sm">Reply</Button>
                <Button variant="ghost" size="sm">Ignore</Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── SETTINGS VIEW ───────────────────────────────────────────────────────────
function SettingsView() {
  const [config, setConfig] = useState(MOCK_CONFIG);

  const Toggle = ({ label, value, onChange, danger }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 0", borderBottom: `1px solid ${C.border}` }}>
      <span style={{ fontSize: "13px", color: C.text, fontFamily: "'DM Sans', sans-serif" }}>{label}</span>
      <button
        onClick={onChange}
        style={{
          width: "44px", height: "24px", borderRadius: "12px", border: "none", cursor: "pointer",
          background: value ? (danger ? C.danger : C.success) : C.border,
          position: "relative", transition: "background 0.2s",
        }}
      >
        <div style={{
          width: "18px", height: "18px", borderRadius: "50%", background: "#fff",
          position: "absolute", top: "3px",
          left: value ? "23px" : "3px",
          transition: "left 0.2s",
        }} />
      </button>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <h2 style={{ fontSize: "20px", fontWeight: 400, color: C.text, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>
        Settings
      </h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* System Controls */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", padding: "20px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif", display: "block", marginBottom: "8px" }}>
            System Controls
          </span>
          <Toggle
            label="Posting enabled"
            value={config.posting_enabled}
            onChange={() => setConfig((c) => ({ ...c, posting_enabled: !c.posting_enabled }))}
          />
          <Toggle
            label="Auto comment replies"
            value={config.comment_replies_enabled}
            onChange={() => setConfig((c) => ({ ...c, comment_replies_enabled: !c.comment_replies_enabled }))}
          />
          <Toggle
            label="Kill switch"
            value={config.kill_switch}
            danger
            onChange={() => setConfig((c) => ({ ...c, kill_switch: !c.kill_switch }))}
          />
        </div>

        {/* Scheduling */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", padding: "20px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif", display: "block", marginBottom: "16px" }}>
            Scheduling
          </span>
          {[
            { label: "Timezone", value: config.timezone },
            { label: "Post window start", value: config.posting_window_start },
            { label: "Post window end", value: config.posting_window_end },
            { label: "Max auto replies per post", value: config.max_auto_replies },
          ].map((item) => (
            <div key={item.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: `1px solid ${C.border}` }}>
              <span style={{ fontSize: "13px", color: C.textMuted, fontFamily: "'DM Sans', sans-serif" }}>{item.label}</span>
              <span style={{ fontSize: "13px", color: C.text, fontFamily: "'DM Sans', sans-serif", fontWeight: 500 }}>{item.value}</span>
            </div>
          ))}
        </div>

        {/* Banned Phrases */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: "8px", padding: "20px", gridColumn: "span 2" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: C.text, fontFamily: "'DM Sans', sans-serif", display: "block", marginBottom: "14px" }}>
            Banned Phrases
          </span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {["game changer", "disrupt", "synergy", "leverage", "pivot", "deep dive", "unpack", "double down", "move the needle", "low hanging fruit"].map((phrase) => (
              <span key={phrase} style={{
                padding: "4px 10px", borderRadius: "4px", fontSize: "12px",
                background: C.dangerMuted, color: C.danger, fontFamily: "'DM Sans', sans-serif",
                border: "1px solid rgba(248,113,113,0.15)",
              }}>
                {phrase}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function App() {
  const [activeView, setActiveView] = useState("dashboard");
  const [sidebarHovered, setSidebarHovered] = useState(null);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Icons.dashboard },
    { id: "content", label: "Content", icon: Icons.content },
    { id: "engagement", label: "Engagement", icon: Icons.engage },
    { id: "settings", label: "Settings", icon: Icons.settings },
  ];

  const views = {
    dashboard: <DashboardView />,
    content: <ContentView />,
    engagement: <EngagementView />,
    settings: <SettingsView />,
  };

  return (
    <div style={{
      display: "flex", height: "100vh", width: "100vw",
      background: C.bg, color: C.text, overflow: "hidden",
      fontFamily: "'DM Sans', sans-serif",
    }}>
      {/* Google Fonts */}
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Instrument+Serif&display=swap" rel="stylesheet" />

      {/* Sidebar */}
      <nav style={{
        width: "220px", minWidth: "220px",
        background: C.surface, borderRight: `1px solid ${C.border}`,
        display: "flex", flexDirection: "column",
        padding: "0",
      }}>
        {/* Logo */}
        <div style={{
          padding: "24px 20px 20px",
          borderBottom: `1px solid ${C.border}`,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "28px", height: "28px", borderRadius: "6px",
              background: `linear-gradient(135deg, ${C.accent}, ${C.accentBright})`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "14px", fontWeight: 700, color: C.bg,
              fontFamily: "'Instrument Serif', Georgia, serif",
            }}>
              S
            </div>
            <div>
              <span style={{ fontSize: "14px", fontWeight: 600, color: C.text, display: "block", lineHeight: 1.2, fontFamily: "'DM Sans', sans-serif" }}>
                Brand Engine
              </span>
              <span style={{ fontSize: "10px", color: C.textDim, letterSpacing: "0.06em", textTransform: "uppercase", fontFamily: "'DM Sans', sans-serif" }}>
                Personal Brand
              </span>
            </div>
          </div>
        </div>

        {/* Nav Items */}
        <div style={{ padding: "12px 8px", flex: 1, display: "flex", flexDirection: "column", gap: "2px" }}>
          {navItems.map((item) => {
            const isActive = activeView === item.id;
            const isHovered = sidebarHovered === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                onMouseEnter={() => setSidebarHovered(item.id)}
                onMouseLeave={() => setSidebarHovered(null)}
                style={{
                  display: "flex", alignItems: "center", gap: "10px",
                  padding: "10px 12px", border: "none", borderRadius: "6px",
                  cursor: "pointer", width: "100%", textAlign: "left",
                  background: isActive ? C.accentMuted : isHovered ? C.surfaceHover : "transparent",
                  color: isActive ? C.accent : C.textMuted,
                  fontSize: "13px", fontWeight: isActive ? 600 : 500,
                  fontFamily: "'DM Sans', sans-serif",
                  transition: "all 0.15s ease",
                }}
              >
                <span style={{ opacity: isActive ? 1 : 0.7 }}>{item.icon}</span>
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Sidebar footer */}
        <div style={{ padding: "16px 20px", borderTop: `1px solid ${C.border}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              width: 8, height: 8, borderRadius: "50%",
              background: MOCK_CONFIG.kill_switch ? C.danger : C.success,
            }} />
            <span style={{ fontSize: "11px", color: C.textDim, fontFamily: "'DM Sans', sans-serif" }}>
              {MOCK_CONFIG.kill_switch ? "System halted" : "All systems active"}
            </span>
          </div>
          <span style={{ fontSize: "10px", color: C.textDim, marginTop: "4px", display: "block", fontFamily: "'DM Sans', sans-serif" }}>
            v2.1 · SAST
          </span>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{
        flex: 1, overflow: "auto",
        padding: "32px 40px",
      }}>
        <div style={{ maxWidth: "1100px" }}>
          {views[activeView]}
        </div>
      </main>
    </div>
  );
}
