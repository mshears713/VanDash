import React, { useEffect, useState } from 'react';

interface LogEntry {
    timestamp: string;
    source: string;
    level: string;
    message: string;
}

interface SubsystemStatus {
    state: string;
    message?: string;
    last_update: number;
    restart_count: number;
    last_error?: string;
}

interface HealthData {
    status: string;
    subsystems: Record<string, SubsystemStatus>;
}

export const SentinelView: React.FC = () => {
    const [health, setHealth] = useState<HealthData | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [source, setSource] = useState<string>('');
    const [sources, setSources] = useState<string[]>([]); // Keep sources state

    const handleReset = async (subsystem: string) => {
        try {
            await fetch(`/api/system/reset/${subsystem}`, { method: 'POST' });
        } catch (e) {
            console.error("Reset failed", e);
        }
    };

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const res = await fetch('/api/health');
                if (res.ok) setHealth(await res.json());
            } catch (err) {
                console.error("Failed to fetch health data", err);
            }
        };
        fetchHealth();
        const interval = setInterval(fetchHealth, 2000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const fetchLogsAndSources = async () => {
            try {
                const sRes = await fetch('/api/logs/sources');
                if (sRes.ok) setSources(await sRes.json());

                const url = source ? `/api/logs/tail?source=${source}` : '/api/logs/tail';
                const res = await fetch(url);
                if (res.ok) setLogs(await res.json());
            } catch (err) {
                console.error("Failed to fetch logs or sources", err);
            }
        };
        fetchLogsAndSources();
        const interval = setInterval(fetchLogsAndSources, 2000);
        return () => clearInterval(interval);
    }, [source]);

    return (
        <div className="diagnostics-view" style={{ width: '100%', height: '100%', padding: '20px', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px', overflow: 'hidden' }}>
            <section className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
                <h3 style={{ borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px' }}>Sentinel</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {health && Object.entries(health.subsystems).map(([name, status]) => (
                        <div
                            key={name}
                            onClick={() => handleReset(name)}
                            style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '12px',
                                background: status.state === 'FAULTY' ? 'rgba(231, 76, 60, 0.15)' : 'rgba(255,255,255,0.05)',
                                borderRadius: '8px',
                                border: status.state === 'FAULTY' ? '1px solid var(--danger-color)' : '1px solid transparent',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            className="subsystem-row"
                        >
                            <div style={{ textAlign: 'left' }}>
                                <div style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>{name.toUpperCase()}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                    {status.state} • {status.restart_count} restarts
                                </div>
                                {status.last_error && (
                                    <div style={{ fontSize: '0.65rem', color: 'var(--danger-color)', marginTop: '4px' }}>
                                        {status.last_error}
                                    </div>
                                )}
                                {status.state === 'FAULTY' && (
                                    <div style={{ fontSize: '0.7rem', color: '#fff', background: 'var(--danger-color)', padding: '2px 6px', borderRadius: '4px', marginTop: '6px', textAlign: 'center', fontWeight: 'bold' }}>
                                        TAP TO RESET
                                    </div>
                                )}
                            </div>
                            <div className={`status-indicator status-${status.state}`}></div>
                        </div>
                    ))}
                    {health && health.status === 'FAULTY' && (
                        <div className="glass-panel" style={{ padding: '12px', background: 'rgba(231, 76, 60, 0.1)', border: '1px solid var(--danger-color)', borderRadius: '8px', marginTop: '16px' }}>
                            <h4 style={{ color: 'var(--danger-color)', marginBottom: '8px' }}>Critical System Failure</h4>
                            <p style={{ fontSize: '0.8rem' }}>
                                One or more core subsystems have failed after multiple restart attempts.
                                Please check hardware connections and restart the Hub.
                            </p>
                        </div>
                    )}
                </div>
            </section>

            <section className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3>Logs</h3>
                    <select
                        value={source}
                        onChange={(e) => setSource(e.target.value)}
                        style={{ background: 'var(--bg-color)', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '4px', padding: '4px' }}
                    >
                        <option value="">All Sources</option>
                        {sources.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '8px', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {logs.map((log, i) => (
                        <div key={i} style={{ marginBottom: '4px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '2px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                            <span style={{ color: log.level === 'ERROR' ? 'var(--danger-color)' : log.level === 'WARN' ? 'var(--warning-color)' : 'var(--accent-color)' }}>{log.source.toUpperCase()}</span>:{' '}
                            {log.message}
                        </div>
                    ))}
                    {logs.length === 0 && <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '20px' }}>No logs available</div>}
                </div>
            </section>
        </div>
    );
};
