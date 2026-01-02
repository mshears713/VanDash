import React, { useEffect, useState } from 'react';
import {
    Activity,
    Camera,
    Wifi,
    Box,
    Terminal,
    ShieldAlert,
    Settings2
} from 'lucide-react';

interface Subsystem {
    state: string;
    last_update: number;
    message?: string;
}

interface HealthData {
    status: string;
    subsystems: Record<string, Subsystem>;
}

const ICON_MAP: Record<string, any> = {
    networking: Wifi,
    camera_rear: Camera,
    camera_front: Camera,
    obd: Box,
    backend: Activity,
    logging: Terminal,
    system: Settings2
};

const LABEL_MAP: Record<string, string> = {
    networking: 'NET',
    camera_rear: 'REAR',
    camera_front: 'FRONT',
    obd: 'OBD',
    backend: 'API',
    logging: 'LOG',
    system: 'SYS'
};

interface StatusCornerProps {
    onNavigate?: () => void;
}

export const StatusCorner: React.FC<StatusCornerProps> = ({ onNavigate }) => {
    const [health, setHealth] = useState<HealthData | null>(null);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const res = await fetch('/api/health');
                if (res.ok) setHealth(await res.json());
            } catch (e) {
                console.error("Health poll failed", e);
            }
        };

        fetchHealth();
        const interval = setInterval(fetchHealth, 2000);
        return () => clearInterval(interval);
    }, []);

    if (!health) return null;

    return (
        <div className="status-corner">
            {Object.entries(health.subsystems).map(([name, data]) => {
                if (data.state === 'DISABLED') return null;

                const Icon = ICON_MAP[name] || Activity;
                const statusClass = `status-${data.state}`;

                return (
                    <div key={name} className="status-pill glass-panel">
                        <div className="pill-icon-container">
                            <Icon size={14} className={statusClass} />
                        </div>
                        <span className="pill-label">{LABEL_MAP[name] || name.toUpperCase()}</span>
                        <div className={`status-dot ${statusClass}`} />
                    </div>
                );
            })}

            {/* Global System Health Bar */}
            <div
                className={`system-heartbeat ${health.status}`}
                onClick={onNavigate}
                style={{ cursor: 'pointer' }}
            >
                <ShieldAlert size={14} />
                <span>SYSTEM {health.status}</span>
            </div>
        </div>
    );
};
