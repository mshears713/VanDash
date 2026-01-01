import React, { useEffect, useState } from 'react';

interface OBDData {
    RPM?: number;
    SPEED?: number;
    COOLANT_TEMP?: number;
    THROTTLE_POS?: number;
    ELM_VOLTAGE?: number;
    timestamp: number;
    simulated?: boolean;
}

export const TelemetryGrid: React.FC = () => {
    const [data, setData] = useState<OBDData | null>(null);
    const [isLive, setIsLive] = useState(false);

    useEffect(() => {
        const eventSource = new EventSource('/api/obd/stream');

        eventSource.onmessage = (event) => {
            setData(JSON.parse(event.data));
            setIsLive(true);
        };

        eventSource.onerror = () => {
            setIsLive(false);
            eventSource.close();
            // Retry after 5s
            setTimeout(() => {
                // This will trigger re-run of effect
            }, 5000);
        };

        return () => eventSource.close();
    }, []);

    const Tile = ({ label, value, unit, color = 'var(--accent-color)' }: any) => (
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>{label}</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color }}>{value ?? '--'}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{unit}</div>
        </div>
    );

    return (
        <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 className="title" style={{ fontSize: '1.2rem' }}>Vehicle Telemetry</h2>
                <div style={{ fontSize: '0.7rem', color: isLive ? 'var(--success-color)' : 'var(--danger-color)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div className="status-indicator" style={{ width: '8px', height: '8px', background: 'currentColor' }} />
                    {isLive ? 'LIVE' : 'DISCONNECTED'}
                    {data?.simulated && <span style={{ color: 'var(--warning-color)', marginLeft: '8px' }}>(SIMULATED)</span>}
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr', gap: '16px', flex: 1 }}>
                <Tile label="Engine RPM" value={data?.RPM} unit="RPM" />
                <Tile label="Speed" value={data?.SPEED} unit="KM/H" color="var(--success-color)" />
                <Tile label="Coolant" value={data?.COOLANT_TEMP} unit="°C" color={data?.COOLANT_TEMP && data.COOLANT_TEMP > 100 ? 'var(--danger-color)' : 'var(--accent-color)'} />
                <Tile label="Battery" value={data?.ELM_VOLTAGE} unit="VOLTS" color="var(--warning-color)" />
            </div>

            {data?.timestamp && (
                <div style={{ textAlign: 'right', fontSize: '0.6rem', color: 'var(--text-secondary)' }}>
                    Last update: {new Date(data.timestamp * 1000).toLocaleTimeString()}
                </div>
            )}
        </div>
    );
};
