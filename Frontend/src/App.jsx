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

  const views = {
    dashboard: <DashboardView />,
    content: <ContentView />,
    engagement: <EngagementView />,
    settings: <SettingsView onConfigChange={setConfig} />,
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
      <Sidebar activeView={activeView} setActiveView={setActiveView} config={config} />
      <main style={{ flex: 1, overflow: 'auto', padding: '32px 40px' }}>
        <div style={{ maxWidth: '1100px' }}>{views[activeView]}</div>
      </main>
    </div>
  );
}
