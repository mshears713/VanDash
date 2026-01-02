import { useState } from 'react';
import { StatusCorner } from './components/StatusCorner';
import { SentinelView } from './views/SentinelView';
import { TelemetryGrid } from './components/TelemetryGrid';
import './index.css';

type View = 'dashboard' | 'rear' | 'front' | 'sentinel';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  return (
    <div className="layout">
      <header className="header">
        <h1 className="title" onClick={() => setCurrentView('dashboard')} style={{ cursor: 'pointer' }}>VanDash</h1>
        <nav style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`glass-panel nav-button ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={`glass-panel nav-button ${currentView === 'front' ? 'active' : ''}`}
            onClick={() => setCurrentView('front')}
          >
            Front
          </button>
          <button
            className={`glass-panel nav-button ${currentView === 'rear' ? 'active' : ''}`}
            onClick={() => setCurrentView('rear')}
          >
            Rear
          </button>
          <button
            className={`glass-panel nav-button ${currentView === 'sentinel' ? 'active' : ''}`}
            onClick={() => setCurrentView('sentinel')}
          >
            Sentinel
          </button>
        </nav>
      </header>

      <main className="main-content" style={{ overflow: 'hidden' }}>
        {currentView === 'dashboard' && <TelemetryGrid />}

        {currentView === 'front' && (
          <div className="glass-panel" style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <h2>Front Camera (Not Configured)</h2>
          </div>
        )}

        {currentView === 'rear' && (
          <div className="glass-panel" style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
            <h2 style={{ position: 'absolute', top: '20px', zIndex: 10 }}>Rear View</h2>
            <div style={{ width: '100%', height: '100%', background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src="/api/camera/rear/stream"
                alt="Rear Camera Stream"
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'https://via.placeholder.com/640x480?text=Camera+Offline';
                }}
              />
            </div>
          </div>
        )}

        {currentView === 'sentinel' && <SentinelView />}
      </main>

      <StatusCorner onNavigate={() => setCurrentView('sentinel')} />

      <style>{`
        .nav-button {
          background: var(--glass-bg);
          border: 1px solid var(--glass-border);
          color: var(--text-secondary);
          padding: 8px 16px;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 500;
        }
        .nav-button:hover {
          background: rgba(255,255,255,0.1);
          color: white;
        }
        .nav-button.active {
          background: var(--accent-color);
          color: var(--bg-color);
          border-color: var(--accent-color);
        }
      `}</style>
    </div>
  );
}

export default App;
