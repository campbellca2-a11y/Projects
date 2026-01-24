class MouseDistanceTracker {
    constructor() {
        this.totalDistance = 0;
        this.sessionDistance = 0;
        this.lastX = null;
        this.lastY = null;
        this.currentSpeed = 0;
        this.speedSamples = [];
        this.lastTime = Date.now();

        // DPI and conversion constants
        this.pixelsPerInch = 96; // Standard web DPI
        this.inchesToMeters = 0.0254;

        this.loadData();
        this.initEventListeners();
        this.initCapsules();
        this.updateDisplay();
        this.startSpeedCalculation();
    }

    loadData() {
        const saved = localStorage.getItem('mouseDistanceData');
        if (saved) {
            const data = JSON.parse(saved);
            this.totalDistance = data.totalDistance || 0;
        }
    }

    saveData() {
        localStorage.setItem('mouseDistanceData', JSON.stringify({
            totalDistance: this.totalDistance
        }));
    }

    initEventListeners() {
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        document.getElementById('resetBtn').addEventListener('click', () => this.resetTotal());
        document.getElementById('resetSessionBtn').addEventListener('click', () => this.resetSession());
    }

    handleMouseMove(e) {
        if (this.lastX !== null && this.lastY !== null) {
            const dx = e.clientX - this.lastX;
            const dy = e.clientY - this.lastY;
            const pixelDistance = Math.sqrt(dx * dx + dy * dy);

            // Convert pixels to meters
            const meters = (pixelDistance / this.pixelsPerInch) * this.inchesToMeters;

            this.totalDistance += meters;
            this.sessionDistance += meters;

            // Calculate speed
            const now = Date.now();
            const timeDiff = (now - this.lastTime) / 1000; // Convert to seconds
            if (timeDiff > 0) {
                const speed = meters / timeDiff;
                this.speedSamples.push(speed);
                if (this.speedSamples.length > 10) {
                    this.speedSamples.shift();
                }
            }
            this.lastTime = now;

            this.updateDisplay();
            this.saveData();
        }

        this.lastX = e.clientX;
        this.lastY = e.clientY;
    }

    startSpeedCalculation() {
        setInterval(() => {
            if (this.speedSamples.length > 0) {
                this.currentSpeed = this.speedSamples.reduce((a, b) => a + b, 0) / this.speedSamples.length;
            } else {
                this.currentSpeed = 0;
            }
            this.updateDisplay();
        }, 100);
    }

    resetTotal() {
        if (confirm('Are you sure you want to reset the total distance?')) {
            this.totalDistance = 0;
            this.sessionDistance = 0;
            this.saveData();
            this.updateDisplay();
        }
    }

    resetSession() {
        this.sessionDistance = 0;
        this.updateDisplay();
    }

    formatDistance(meters) {
        if (meters < 1) {
            return `${(meters * 100).toFixed(2)} cm`;
        } else if (meters < 1000) {
            return `${meters.toFixed(2)} m`;
        } else {
            return `${(meters / 1000).toFixed(2)} km`;
        }
    }

    formatSpeed(metersPerSecond) {
        if (metersPerSecond < 1) {
            return `${(metersPerSecond * 100).toFixed(1)} cm/s`;
        } else {
            return `${metersPerSecond.toFixed(2)} m/s`;
        }
    }

    updateDisplay() {
        document.getElementById('totalDistance').textContent = this.formatDistance(this.totalDistance);
        document.getElementById('sessionDistance').textContent = this.formatDistance(this.sessionDistance);
        document.getElementById('currentSpeed').textContent = this.formatSpeed(this.currentSpeed);

        this.updateCapsules();
    }

    initCapsules() {
        this.capsules = [
            {
                id: 'moon',
                icon: '🌙',
                title: 'Journey to the Moon',
                description: 'The average distance from Earth to the Moon',
                targetDistance: 384400000, // meters
                color: '#667eea'
            },
            {
                id: 'earth',
                icon: '🌍',
                title: 'Around the Earth',
                description: 'Earth\'s circumference at the equator',
                targetDistance: 40075000, // meters
                color: '#4ecdc4'
            },
            {
                id: 'everest',
                icon: '🏔️',
                title: 'Climbing Mount Everest',
                description: 'Height of the world\'s tallest mountain',
                targetDistance: 8849, // meters
                color: '#95e1d3'
            },
            {
                id: 'greatwall',
                icon: '🏯',
                title: 'The Great Wall of China',
                description: 'Total length including all branches',
                targetDistance: 21196000, // meters
                color: '#f38181'
            },
            {
                id: 'marathon',
                icon: '🏃',
                title: 'Marathon Distance',
                description: 'Official marathon race distance',
                targetDistance: 42195, // meters
                color: '#aa96da'
            },
            {
                id: 'eiffeltower',
                icon: '🗼',
                title: 'Eiffel Tower Height',
                description: 'Including antenna',
                targetDistance: 330, // meters
                color: '#fcbad3'
            },
            {
                id: 'football',
                icon: '⚽',
                title: 'Football Field',
                description: 'Length of an American football field',
                targetDistance: 91.44, // meters
                color: '#a8d8ea'
            },
            {
                id: 'mariana',
                icon: '🌊',
                title: 'Mariana Trench',
                description: 'Deepest known point in Earth\'s oceans',
                targetDistance: 10994, // meters
                color: '#6c5ce7'
            }
        ];

        this.renderCapsules();
    }

    renderCapsules() {
        const grid = document.getElementById('capsulesGrid');
        grid.innerHTML = this.capsules.map(capsule => `
            <div class="capsule" id="capsule-${capsule.id}">
                <div class="capsule-header">
                    <div class="capsule-icon">${capsule.icon}</div>
                    <div class="capsule-title">${capsule.title}</div>
                </div>
                <div class="capsule-description">${capsule.description}</div>
                <div class="progress-container">
                    <div class="progress-bar" id="progress-${capsule.id}" style="width: 0%"></div>
                    <div class="progress-text" id="progress-text-${capsule.id}">0%</div>
                </div>
                <div class="capsule-stats">
                    <div class="capsule-stat">
                        <div class="capsule-stat-value" id="times-${capsule.id}">0</div>
                        <div class="capsule-stat-label">Times Completed</div>
                    </div>
                    <div class="capsule-stat">
                        <div class="capsule-stat-value" id="remaining-${capsule.id}">-</div>
                        <div class="capsule-stat-label">Remaining</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateCapsules() {
        this.capsules.forEach(capsule => {
            const percentage = (this.totalDistance / capsule.targetDistance) * 100;
            const displayPercentage = Math.min(percentage, 100);
            const timesCompleted = Math.floor(this.totalDistance / capsule.targetDistance);
            const remaining = capsule.targetDistance - (this.totalDistance % capsule.targetDistance);

            const progressBar = document.getElementById(`progress-${capsule.id}`);
            const progressText = document.getElementById(`progress-text-${capsule.id}`);
            const timesElement = document.getElementById(`times-${capsule.id}`);
            const remainingElement = document.getElementById(`remaining-${capsule.id}`);

            if (progressBar) {
                progressBar.style.width = `${displayPercentage}%`;
                progressBar.style.background = `linear-gradient(90deg, ${capsule.color} 0%, ${this.lightenColor(capsule.color, 20)} 100%)`;
            }

            if (progressText) {
                progressText.textContent = `${displayPercentage.toFixed(2)}%`;
            }

            if (timesElement) {
                timesElement.textContent = timesCompleted;
            }

            if (remainingElement) {
                remainingElement.textContent = this.formatDistance(remaining);
            }
        });
    }

    lightenColor(color, percent) {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255))
            .toString(16).slice(1);
    }
}

// Initialize the tracker when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MouseDistanceTracker();
});
