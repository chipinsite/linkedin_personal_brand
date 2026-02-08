import { createElement as h } from 'react';

export const C = {
  bg: '#0C0E12',
  surface: '#14161C',
  surfaceHover: '#1A1D25',
  border: '#23272F',
  borderLight: '#2C3140',
  text: '#E8E9EC',
  textMuted: '#8B8F9A',
  textDim: '#5A5F6E',
  accent: '#C8935A',
  accentMuted: 'rgba(200,147,90,0.15)',
  accentBright: '#E0A96A',
  success: '#4ADE80',
  successMuted: 'rgba(74,222,128,0.12)',
  warning: '#FBBF24',
  warningMuted: 'rgba(251,191,36,0.12)',
  danger: '#F87171',
  dangerMuted: 'rgba(248,113,113,0.12)',
  info: '#60A5FA',
  infoMuted: 'rgba(96,165,250,0.12)',
};

export const formatDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' });
};

export const formatTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' });
};

export const truncate = (str, len = 120) => (str?.length > len ? `${str.slice(0, len)}...` : str || '');

export const pct = (n) => `${Math.round(n * 100)}%`;

const svgBase = {
  fill: 'none',
  stroke: 'currentColor',
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

const svg18 = (children, strokeWidth = '1.8') =>
  h('svg', { width: '18', height: '18', viewBox: '0 0 24 24', ...svgBase, strokeWidth }, ...children);
const svg16 = (children, strokeWidth = '2') =>
  h('svg', { width: '16', height: '16', viewBox: '0 0 24 24', ...svgBase, strokeWidth }, ...children);
const svg14 = (children, strokeWidth = '2') =>
  h('svg', { width: '14', height: '14', viewBox: '0 0 24 24', ...svgBase, strokeWidth }, ...children);

export const Icons = {
  dashboard: svg18([
    h('rect', { key: 'r1', x: '3', y: '3', width: '7', height: '7', rx: '1' }),
    h('rect', { key: 'r2', x: '14', y: '3', width: '7', height: '7', rx: '1' }),
    h('rect', { key: 'r3', x: '3', y: '14', width: '7', height: '7', rx: '1' }),
    h('rect', { key: 'r4', x: '14', y: '14', width: '7', height: '7', rx: '1' }),
  ]),
  content: svg18([
    h('path', { key: 'p1', d: 'M12 20h9' }),
    h('path', { key: 'p2', d: 'M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z' }),
  ]),
  publish: svg18([
    h('path', { key: 'p1', d: 'M22 2L11 13' }),
    h('path', { key: 'p2', d: 'M22 2l-7 20-4-9-9-4 20-7z' }),
  ]),
  engage: svg18([h('path', { key: 'p1', d: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z' })]),
  analytics: svg18([
    h('path', { key: 'p1', d: 'M18 20V10' }),
    h('path', { key: 'p2', d: 'M12 20V4' }),
    h('path', { key: 'p3', d: 'M6 20v-6' }),
  ]),
  settings: svg18([
    h('circle', { key: 'c1', cx: '12', cy: '12', r: '3' }),
    h('path', {
      key: 'p1',
      d: 'M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.32 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z',
    }),
  ]),
  alert: svg16([
    h('circle', { key: 'c1', cx: '12', cy: '12', r: '10' }),
    h('line', { key: 'l1', x1: '12', y1: '8', x2: '12', y2: '12' }),
    h('line', { key: 'l2', x1: '12', y1: '16', x2: '12.01', y2: '16' }),
  ]),
  check: svg16([h('polyline', { key: 'p1', points: '20 6 9 17 4 12' })], '2.5'),
  copy: svg14([
    h('rect', { key: 'r1', x: '9', y: '9', width: '13', height: '13', rx: '2' }),
    h('path', { key: 'p1', d: 'M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1' }),
  ]),
  clock: svg14([
    h('circle', { key: 'c1', cx: '12', cy: '12', r: '10' }),
    h('polyline', { key: 'p1', points: '12 6 12 12 16 14' }),
  ]),
  chevron: svg16([h('polyline', { key: 'p1', points: '9 18 15 12 9 6' })]),
  fire: svg14([h('path', { key: 'p1', d: 'M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z' })]),
};
