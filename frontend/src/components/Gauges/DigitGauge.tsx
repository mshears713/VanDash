import React from 'react';

interface DigitGaugeProps {
    value: number;
    label: string;
    unit: string;
    color?: string;
    trend?: 'up' | 'down' | 'stable';
}

export const DigitGauge: React.FC<DigitGaugeProps> = ({ value, label, unit, color = '#f1c40f' }) => {
    return (
        <div className="digit-gauge" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            minWidth: '140px'
        }}>
            <span style={{
                fontSize: '0.65rem',
                fontWeight: 900,
                color: color,
                letterSpacing: '0.1em',
                marginBottom: '4px'
            }}>
                {label.toUpperCase()}
            </span>

            <div style={{ position: 'relative' }}>
                <span style={{
                    fontSize: '3.5rem',
                    fontWeight: 800,
                    fontFamily: 'monospace',
                    color: '#fff',
                    lineHeight: 1
                }}>
                    {Math.round(value).toString().padStart(2, '0')}
                </span>
                <span style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: 'rgba(255,255,255,0.3)',
                    marginLeft: '4px'
                }}>
                    {unit}
                </span>
            </div>

            <div style={{
                width: '100%',
                height: '2px',
                background: `linear-gradient(90deg, transparent 0%, ${color} 50%, transparent 100%)`,
                marginTop: '8px',
                opacity: 0.5
            }} />
        </div>
    );
};
