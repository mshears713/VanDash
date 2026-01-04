import React, { useEffect, useState } from 'react';
import { ArcGauge } from './Gauges/ArcGauge';
import { BeamGauge } from './Gauges/BeamGauge';
import { DigitGauge } from './Gauges/DigitGauge';

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
        };

        return () => eventSource.close();
    }, []);

    const getCoolantColor = (temp: number) => {
        if (temp < 40) return '#00d2ff'; // Cold (Aqua)
        if (temp > 100) return '#e74c3c'; // Hot (Red)
        if (temp > 95) return '#f1c40f'; // Warm (Yellow)
        return '#2ecc71'; // Normal (Green)
    };

    const speedMph = (data?.SPEED || 0) * 0.621371;

    return (
        <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 className="title" style={{ fontSize: '1.2rem' }}>Vehicle Systems</h2>
                <div style={{ fontSize: '0.7rem', color: isLive ? 'var(--success-color)' : 'var(--danger-color)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div className="status-indicator" style={{ width: '8px', height: '8px', background: 'currentColor' }} />
                    {isLive ? 'SYSTEM LINK ACTIVE' : 'NO DATA LINK'}
                    {data?.simulated && <span style={{ color: 'var(--warning-color)', marginLeft: '8px' }}>[MAINTENANCE SIM]</span>}
                </div>
            </div>

            <div className="gauge-showcase" style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '20px',
                justifyContent: 'center',
                alignItems: 'center'
            }}>
                {/* Arc Gauges: RPM and Speed */}
                <div className="glass-panel" style={{ padding: '10px', display: 'flex', gap: '10px' }}>
                    <ArcGauge
                        value={data?.RPM || 0}
                        min={0}
                        max={8000}
                        unit="rpm"
                        label="Engine"
                        color="#00d2ff"
                    />
                    <ArcGauge
                        value={speedMph}
                        min={0}
                        max={140}
                        unit="mph"
                        label="Velocity"
                        color="#2ecc71"
                        subValue={Math.round(data?.SPEED || 0)}
                        subUnit="km/h"
                    />
                </div>

                {/* Beam Gauge: Coolant Temp (Dynamic Color) */}
                <div className="glass-panel" style={{ padding: '10px' }}>
                    <BeamGauge
                        value={data?.COOLANT_TEMP || 0}
                        min={0}
                        max={120}
                        label="Coolant"
                        unit="°C"
                        color={getCoolantColor(data?.COOLANT_TEMP || 0)}
                    />
                </div>

                {/* Digit Gauge: Voltage */}
                <div className="glass-panel" style={{ padding: '10px' }}>
                    <DigitGauge
                        value={data?.ELM_VOLTAGE || 0}
                        label="Battery"
                        unit="v"
                        color="#f1c40f"
                    />
                </div>
            </div>

            {data?.timestamp && (
                <div style={{ textAlign: 'right', fontSize: '0.6rem', color: 'var(--text-secondary)', marginTop: 'auto' }}>
                    HUB_TIME: {new Date(data.timestamp * 1000).toLocaleTimeString()}
                </div>
            )}
        </div>
    );
};
