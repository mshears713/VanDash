import React, { useEffect, useRef } from 'react';

interface ArcGaugeProps {
    value: number;
    min: number;
    max: number;
    unit: string;
    label: string;
    color?: string;
    subValue?: number | string;
    subUnit?: string;
}

export const ArcGauge: React.FC<ArcGaugeProps> = ({ value, min, max, unit, label, color = '#00d2ff', subValue, subUnit }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear and scale
        const dpr = window.devicePixelRatio || 1;
        const size = 180;
        canvas.width = size * dpr;
        canvas.height = size * dpr;
        ctx.scale(dpr, dpr);

        const centerX = size / 2;
        const centerY = size / 2;
        const radius = 70;
        const startAngle = 0.75 * Math.PI;
        const endAngle = 2.25 * Math.PI;

        // Normalized value for angle
        const range = max - min;
        const percent = Math.min(Math.max((value - min) / range, 0), 1);
        const currentAngle = startAngle + (endAngle - startAngle) * percent;

        // Draw Background Track
        ctx.clearRect(0, 0, size, size);
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.lineWidth = 12;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Draw Active Value Arc
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, currentAngle);
        ctx.strokeStyle = color;
        ctx.lineWidth = 12;
        ctx.lineCap = 'round';
        // Add Glow
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.stroke();

        // Draw Centers
        ctx.shadowBlur = 0;
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 28px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(Math.round(value).toString(), centerX, centerY + 5);

        ctx.font = '500 12px Inter';
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.fillText(unit.toUpperCase(), centerX, centerY + 25);

        // Draw Sub Value (if provided)
        if (subValue !== undefined) {
            ctx.font = '600 10px Inter';
            ctx.fillStyle = 'rgba(255,255,255,0.3)';
            ctx.fillText(`${subValue} ${subUnit || ''}`.toUpperCase(), centerX, centerY + 42);
        }

        ctx.font = '800 10px Inter';
        ctx.fillStyle = color;
        ctx.fillText(label.toUpperCase(), centerX, centerY - 25);

    }, [value, min, max, unit, label, color, subValue, subUnit]);

    return (
        <canvas
            ref={canvasRef}
            style={{ width: '180px', height: '180px' }}
        />
    );
};
