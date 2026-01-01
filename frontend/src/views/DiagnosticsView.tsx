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

export const DiagnosticsView: React.FC = () => {
    const [health, setHealth] = useState<HealthData | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [source, setSource] = useState<string>('');
    const [sources, setSources] = useState<string[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const hRes = await fetch('/api/health');
                if (hRes.ok) setHealth(await hRes.json());

                const sRes = await fetch('/api/logs/sources');
                if (sRes.ok) setSources(await sRes.json());

                const lRes = await fetch(`/api/logs/tail${source ? `?source=${source}` : ''}`);
                if (lRes.ok) setLogs(await lRes.json());
            } catch (err) {
                console.error(err);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 3000);
        return () => clearInterval(interval);
    }, [source]);

    return (
        <div className="diagnostics-view" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', height: '100%', overflow: 'hidden' }}>
            <section className="glass-panel" style={{ padding: '16px', overflowY: 'auto' }}>
                <h3 style={{ marginBottom: '16px' }}>Subsystems</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {health && Object.entries(health.subsystems).map(([name, status]) => (
                        <div key={name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                            <div>
                                <div style={{ fontWeight: 'bold', textTransform: 'capitalize' }}>{name.replace('_', ' ')}</div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                    Restarts: {status.restart_count}
                                </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <span className={`status-${status.state}`} style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem' }}>
                                    {status.state}
                                </span>
                                {status.state === 'FAULTY' && (
                                    <div style={{ color: 'var(--danger-color)', fontSize: '0.7rem', marginTop: '4px', fontWeight: 'bold' }}>
                                        MANUAL RESET REQUIRED
                                    </div>
                                )}
                                {status.last_error && (
                                    <div style={{ fontSize: '0.7rem', color: 'var(--danger-color)', marginTop: '4px', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={status.last_error}>
                                        {status.last_error}
                                    </div>
                                )}
                            </div>
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
