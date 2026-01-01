import React, { useEffect, useState } from 'react';

interface SubsystemStatus {
    state: 'ACTIVE' | 'WAITING' | 'FAULTY' | 'DISABLED';
}

interface HealthData {
    status: 'OK' | 'DEGRADED' | 'FAULTY';
    subsystems: Record<string, SubsystemStatus>;
}

export const StatusCorner: React.FC = () => {
    const [health, setHealth] = useState<HealthData | null>(null);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const response = await fetch('/api/health');
                if (response.ok) {
                    const data = await healthResponse(response);
                    setHealth(data);
                }
            } catch (error) {
                console.error('Failed to fetch health:', error);
            }
        };

        const healthResponse = async (res: Response) => {
            return await res.json();
        }

        fetchHealth();
        const interval = setInterval(fetchHealth, 2000);
        return () => clearInterval(interval);
    }, []);

    if (!health) return null;

    return (
        <div className="status-corner glass-panel">
            <div className={`status-indicator status-${health.status === 'OK' ? 'ACTIVE' : health.status === 'DEGRADED' ? 'WAITING' : 'FAULTY'}`} title={`System Status: ${health.status}`} />
            {Object.entries(health.subsystems).map(([name, status]) => (
                <div
                    key={name}
                    className={`status-indicator status-${status.state}`}
                    title={`${name}: ${status.state}`}
                />
            ))}
        </div>
    );
};
