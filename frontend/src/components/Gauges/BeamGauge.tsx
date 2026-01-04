import React, { useEffect, useRef } from 'react';

interface BeamGaugeProps {
    value: number;
    min: number;
    max: number;
    label: string;
    unit: string;
    color?: string;
}

export const BeamGauge: React.FC<BeamGaugeProps> = ({ value, min, max, label, unit, color = '#2ecc71' }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const w = 80;
        const h = 200;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        ctx.scale(dpr, dpr);

        const barW = 12;
        const barH = 140;
        const barX = (w - barW) / 2;
        const barY = 30;

        const percent = Math.min(Math.max((value - min) / (max - min), 0), 1);
        const fillH = barH * percent;

        ctx.clearRect(0, 0, w, h);

        // Track
        ctx.fillStyle = 'rgba(255,255,255,0.05)';
        ctx.roundRect(barX, barY, barW, barH, 4);
        ctx.fill();

        // Fill
        const gradient = ctx.createLinearGradient(0, barY + barH, 0, barY);
        gradient.addColorStop(0, color + '44');
        gradient.addColorStop(1, color);

        ctx.fillStyle = gradient;
        ctx.shadowBlur = 10;
        ctx.shadowColor = color;
        ctx.beginPath();
        ctx.roundRect(barX, barY + barH - fillH, barW, fillH, 4);
        ctx.fill();

        // Labels
        ctx.shadowBlur = 0;
        ctx.textAlign = 'center';
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 16px Inter';
        ctx.fillText(Math.round(value).toString(), w / 2, barY - 10);

        ctx.font = '800 9px Inter';
        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.fillText(label.toUpperCase(), w / 2, barY + barH + 15);
        ctx.fillText(unit.toUpperCase(), w / 2, barY + barH + 28);

    }, [value, min, max, label, unit, color]);

    return <canvas ref={canvasRef} style={{ width: '80px', height: '200px' }} />;
};
