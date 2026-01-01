import { useState } from 'react';
import { StatusCorner } from './components/StatusCorner';
import { DiagnosticsView } from './views/DiagnosticsView';
import { TelemetryGrid } from './components/TelemetryGrid';
import './index.css';

type View = 'drive' | 'reverse' | 'diagnostics';

function App() {
  const [currentView, setCurrentView] = useState<View>('drive');

  return (
    <div className="layout">
      <header className="header">
        <h1 className="title" onClick={() => setCurrentView('drive')} style={{ cursor: 'pointer' }}>VanDash</h1>
        <nav style={{ display: 'flex', gap: '12px' }}>
          <button
            className={`glass-panel nav-button ${currentView === 'drive' ? 'active' : ''}`}
            onClick={() => setCurrentView('drive')}
          >
            Drive
          </button>
          <button
            className={`glass-panel nav-button ${currentView === 'reverse' ? 'active' : ''}`}
            onClick={() => setCurrentView('reverse')}
          >
            Reverse
          </button>
          <button
            className={`glass-panel nav-button ${currentView === 'diagnostics' ? 'active' : ''}`}
            onClick={() => setCurrentView('diagnostics')}
          >
            Diag
          </button>
        </nav>
      </header>

      <main className="main-content" style={{ overflow: 'hidden' }}>
        {currentView === 'drive' && <TelemetryGrid />}

        {currentView === 'reverse' && (
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
            <div style={{ position: 'absolute', bottom: '20px', left: '0', right: '0', textAlign: 'center', color: 'var(--danger-color)', fontWeight: 'bold', background: 'rgba(0,0,0,0.5)', padding: '8px', zIndex: 10 }}>
              CHECK SURROUNDINGS FOR SAFETY
            </div>
          </div>
        )}

        {currentView === 'diagnostics' && <DiagnosticsView />}
      </main>

      <StatusCorner />

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
