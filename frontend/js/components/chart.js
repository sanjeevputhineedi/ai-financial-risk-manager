/**
 * Lightweight Canvas Chart Component (No heavy external charting dependencies)
 * Supports Donut / Pie Charts and Bar Charts.
 */
class MiniChart {
    /**
     * Render a Donut Chart
     * @param {HTMLCanvasElement} canvas
     * @param {Array<{label: string, value: number, color: string}>} data
     */
    static renderDonut(canvas, data) {
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const width = canvas.clientWidth || 260;
        const height = canvas.clientHeight || 200;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);

        const total = data.reduce((sum, d) => sum + (d.value || 0), 0);
        const centerX = width / 2;
        const centerY = height / 2 - 10;
        const radius = Math.min(centerX, centerY) - 15;
        const innerRadius = radius * 0.65;

        ctx.clearRect(0, 0, width, height);

        if (total === 0) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(255,255,255,0.08)';
            ctx.lineWidth = radius - innerRadius;
            ctx.stroke();

            ctx.fillStyle = '#64748b';
            ctx.font = '12px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('No Data', centerX, centerY);
            return;
        }

        let startAngle = -Math.PI / 2;
        data.forEach(item => {
            if (item.value <= 0) return;
            const sliceAngle = (item.value / total) * Math.PI * 2;
            const endAngle = startAngle + sliceAngle;

            ctx.beginPath();
            ctx.arc(centerX, centerY, (radius + innerRadius) / 2, startAngle, endAngle);
            ctx.strokeStyle = item.color;
            ctx.lineWidth = radius - innerRadius;
            ctx.stroke();

            startAngle = endAngle;
        });

        // Center total text
        ctx.fillStyle = '#f1f5f9';
        ctx.font = 'bold 20px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(total.toString(), centerX, centerY - 2);

        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px Inter, sans-serif';
        ctx.fillText('TOTAL', centerX, centerY + 16);
    }

    /**
     * Render a Horizontal Bar / Distribution Chart
     * @param {HTMLCanvasElement} canvas
     * @param {Array<{label: string, value: number, color: string}>} data
     */
    static renderBars(canvas, data) {
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const width = canvas.clientWidth || 300;
        const height = canvas.clientHeight || 180;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);

        ctx.clearRect(0, 0, width, height);

        const total = data.reduce((sum, d) => sum + (d.value || 0), 0) || 1;
        const barHeight = 16;
        const gap = 20;
        const startY = 15;

        data.forEach((item, index) => {
            const y = startY + index * (barHeight + gap);
            const ratio = item.value / total;
            const barWidth = Math.max(4, (width - 100) * ratio);

            // Label
            ctx.fillStyle = '#94a3b8';
            ctx.font = '12px Inter, sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(item.label, 10, y + barHeight / 2);

            // Background track
            ctx.fillStyle = 'rgba(255,255,255,0.05)';
            ctx.beginPath();
            ctx.roundRect(85, y, width - 140, barHeight, 4);
            ctx.fill();

            // Active Bar
            if (item.value > 0) {
                ctx.fillStyle = item.color;
                ctx.beginPath();
                ctx.roundRect(85, y, barWidth, barHeight, 4);
                ctx.fill();
            }

            // Value text
            ctx.fillStyle = '#f1f5f9';
            ctx.font = 'bold 12px "JetBrains Mono", monospace';
            ctx.textAlign = 'right';
            ctx.fillText(item.value.toString(), width - 10, y + barHeight / 2);
        });
    }
}
window.MiniChart = MiniChart;
