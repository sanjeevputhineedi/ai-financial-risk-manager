/**
 * Animated SVG Risk Gauge Component
 * Renders a circular gauge showing a risk score from 0 to 100 with color transitions.
 */
class RiskGauge {
    /**
     * @param {string} containerId - Target element ID
     * @param {Object} options - Configuration options
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            size: options.size || 160,
            strokeWidth: options.strokeWidth || 12,
            title: options.title || 'Risk Score',
            showValue: options.showValue !== false,
            animated: options.animated !== false,
            ...options
        };
        this.value = 0;
        this.init();
    }

    init() {
        if (!this.container) return;
        const { size, strokeWidth } = this.options;
        const radius = (size - strokeWidth) / 2;
        const center = size / 2;
        // 240 degree arc
        const arcLength = 2 * Math.PI * radius * (240 / 360);
        const circumference = 2 * Math.PI * radius;

        this.container.innerHTML = `
            <div class="gauge-wrapper" style="width: ${size}px; text-align: center;">
                <svg width="${size}" height="${size * 0.85}" viewBox="0 0 ${size} ${size * 0.85}" class="gauge-svg">
                    <defs>
                        <linearGradient id="gaugeGradLow" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#10b981" />
                            <stop offset="100%" stop-color="#34d399" />
                        </linearGradient>
                        <linearGradient id="gaugeGradMedium" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#f59e0b" />
                            <stop offset="100%" stop-color="#fbbf24" />
                        </linearGradient>
                        <linearGradient id="gaugeGradHigh" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#ef4444" />
                            <stop offset="100%" stop-color="#f87171" />
                        </linearGradient>
                        <linearGradient id="gaugeGradCritical" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#ec4899" />
                            <stop offset="100%" stop-color="#f43f5e" />
                        </linearGradient>
                    </defs>
                    <!-- Background Arc -->
                    <circle
                        cx="${center}"
                        cy="${center}"
                        r="${radius}"
                        fill="none"
                        stroke="rgba(255,255,255,0.08)"
                        stroke-width="${strokeWidth}"
                        stroke-linecap="round"
                        stroke-dasharray="${arcLength} ${circumference}"
                        transform="rotate(150 ${center} ${center})"
                    />
                    <!-- Active Arc -->
                    <circle
                        id="gauge-fill-${this.container.id}"
                        cx="${center}"
                        cy="${center}"
                        r="${radius}"
                        fill="none"
                        stroke="url(#gaugeGradLow)"
                        stroke-width="${strokeWidth}"
                        stroke-linecap="round"
                        stroke-dasharray="0 ${circumference}"
                        transform="rotate(150 ${center} ${center})"
                        style="transition: stroke-dasharray 0.8s cubic-bezier(0.34, 1.56, 0.64, 1), stroke 0.4s ease;"
                    />
                    <!-- Value Text in Center -->
                    <text
                        id="gauge-val-${this.container.id}"
                        x="${center}"
                        y="${center + 5}"
                        text-anchor="middle"
                        font-family="var(--font-mono, monospace)"
                        font-size="${size * 0.22}px"
                        font-weight="800"
                        fill="#f1f5f9"
                    >0</text>
                    <text
                        id="gauge-lvl-${this.container.id}"
                        x="${center}"
                        y="${center + size * 0.16}"
                        text-anchor="middle"
                        font-family="var(--font-sans, sans-serif)"
                        font-size="${size * 0.08}px"
                        font-weight="700"
                        letter-spacing="0.05em"
                        fill="#94a3b8"
                    >LOW</text>
                </svg>
                <div style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); margin-top: -8px;">
                    ${this.options.title}
                </div>
            </div>
        `;

        this.fillEl = document.getElementById(`gauge-fill-${this.container.id}`);
        this.valEl = document.getElementById(`gauge-val-${this.container.id}`);
        this.lvlEl = document.getElementById(`gauge-lvl-${this.container.id}`);
        this.arcLength = arcLength;
        this.circumference = circumference;
    }

    /**
     * Set gauge value (0-100) and animate
     * @param {number} score
     */
    setValue(score) {
        this.value = Math.max(0, Math.min(100, Number(score) || 0));
        if (!this.fillEl) return;

        const ratio = this.value / 100;
        const currentDash = ratio * this.arcLength;
        this.fillEl.setAttribute('stroke-dasharray', `${currentDash} ${this.circumference}`);

        let gradientId = 'gaugeGradLow';
        let levelText = 'LOW';
        let levelColor = '#34d399';

        if (this.value >= 90) {
            gradientId = 'gaugeGradCritical';
            levelText = 'CRITICAL';
            levelColor = '#f43f5e';
        } else if (this.value >= 70) {
            gradientId = 'gaugeGradHigh';
            levelText = 'HIGH';
            levelColor = '#f87171';
        } else if (this.value >= 40) {
            gradientId = 'gaugeGradMedium';
            levelText = 'MEDIUM';
            levelColor = '#fbbf24';
        }

        this.fillEl.setAttribute('stroke', `url(#${gradientId})`);
        if (this.valEl) {
            this.animateNumber(this.valEl, this.value);
        }
        if (this.lvlEl) {
            this.lvlEl.textContent = levelText;
            this.lvlEl.setAttribute('fill', levelColor);
        }
    }

    animateNumber(el, target) {
        const start = parseInt(el.textContent) || 0;
        const duration = 600;
        const startTime = performance.now();

        const step = (now) => {
            const progress = Math.min((now - startTime) / duration, 1);
            const current = Math.round(start + (target - start) * progress);
            el.textContent = current;
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }
}
window.RiskGauge = RiskGauge;
