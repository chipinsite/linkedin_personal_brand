import { useEffect, useState } from 'react';
import Sidebar from './components/layout/Sidebar';
import DashboardView from './components/views/DashboardView';
import ContentView from './components/views/ContentView';
import EngagementView from './components/views/EngagementView';
import SettingsView from './components/views/SettingsView';
import { C } from './constants/theme';

export default function App() {
  const [activeView, setActiveView] = useState(() => {
    try {
      return localStorage.getItem('app.activeView') || 'dashboard';
    } catch {
      return 'dashboard';
    }
  });
  const [config, setConfig] = useState({ kill_switch: false });

  useEffect(() => {
    try {
      localStorage.setItem('app.activeView', activeView);
    } catch {
      // ignore storage write failures in constrained environments
    }
  }, [activeView]);

  function handleResetUiPreferences() {
    try {
      localStorage.removeItem('app.activeView');
      localStorage.removeItem('app.dashboard.publishFilter');
    } catch {
      // ignore storage write failures in constrained environments
    }
    setActiveView('dashboard');
  }

  const views = {
    dashboard: <DashboardView />,
    content: <ContentView />,
    engagement: <EngagementView />,
    settings: <SettingsView onConfigChange={setConfig} onResetUiPreferences={handleResetUiPreferences} />,
  };

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        background: C.bg,
        color: C.text,
        overflow: 'hidden',
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      <a
        href="#main-content"
        style={{
          position: 'absolute',
          left: '-9999px',
          top: '8px',
          zIndex: 100,
          background: C.accent,
          color: C.bg,
          padding: '8px 16px',
          borderRadius: '6px',
          fontSize: '13px',
          fontWeight: 600,
          textDecoration: 'none',
        }}
        onFocus={(e) => { e.target.style.left = '8px'; }}
        onBlur={(e) => { e.target.style.left = '-9999px'; }}
      >
        Skip to main content
      </a>
      <Sidebar activeView={activeView} setActiveView={setActiveView} config={config} />
      <main
        id="main-content"
        aria-label={`${activeView.charAt(0).toUpperCase() + activeView.slice(1)} view`}
        style={{ flex: 1, overflow: 'auto', padding: '32px 40px' }}
      >
        <div style={{ maxWidth: '1100px' }}>{views[activeView]}</div>
      </main>
    </div>
  );
}
