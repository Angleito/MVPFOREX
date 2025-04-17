class ChartHandler {
    constructor() {
        this.chart = null;
        this.candlesData = [];
        this.chartType = 'candlestick';
        this.timeframe = 'H1';
        this.initializeChart();
        this.setupEventListeners();
    }

    initializeChart() {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // Register candlestick element
        Chart.register({
            id: 'candlestick',
            beforeInit: function(chart) {
                chart.legend.options.labels.generateLabels = function() {
                    return [];
                };
            }
        });

        this.chart = new Chart(ctx, {
            type: this.chartType,
            data: {
                datasets: [{
                    label: 'XAUUSD',
                    data: []
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'hour',
                            displayFormats: {
                                hour: 'HH:mm',
                                day: 'MMM d'
                            }
                        },
                        ticks: {
                            source: 'auto'
                        }
                    },
                    y: {
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Price (USD)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const data = context.raw;
                                if (this.chartType === 'candlestick') {
                                    return [
                                        `O: $${data.o.toFixed(2)}`,
                                        `H: $${data.h.toFixed(2)}`,
                                        `L: $${data.l.toFixed(2)}`,
                                        `C: $${data.c.toFixed(2)}`
                                    ];
                                }
                                return `$${data.c.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    setupEventListeners() {
        // Timeframe selector
        document.getElementById('timeframeSelect').addEventListener('change', (e) => {
            this.timeframe = e.target.value;
            this.fetchData();
        });

        // Chart type selector
        document.querySelectorAll('[data-chart-type]').forEach(button => {
            button.addEventListener('click', (e) => {
                // Update active state
                document.querySelectorAll('[data-chart-type]').forEach(btn => {
                    btn.classList.remove('active');
                });
                e.target.classList.add('active');

                // Update chart type
                this.chartType = e.target.dataset.chartType;
                this.updateChartType();
            });
        });
    }

    async fetchData() {
        try {
            const response = await fetch('/api/candles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    instrument: 'XAU_USD',
                    granularity: this.timeframe
                })
            });

            if (!response.ok) {
                throw new Error('Failed to fetch market data');
            }

            const data = await response.json();
            if (data.status === 'ok' && data.candles) {
                this.candlesData = data.candles.map(candle => ({
                    t: luxon.DateTime.fromISO(candle.timestamp).valueOf(),
                    o: candle.open,
                    h: candle.high,
                    l: candle.low,
                    c: candle.close
                }));
                this.updateChart();
            }
        } catch (error) {
            console.error('Error fetching market data:', error);
            // Show error message to user
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger';
            errorDiv.textContent = 'Failed to load market data. Please try again later.';
            document.querySelector('.chart-container').prepend(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    }

    updateChartType() {
        if (this.chartType === 'line') {
            this.chart.config.type = 'line';
            this.chart.config.data.datasets[0].data = this.candlesData.map(d => ({
                x: d.t,
                y: d.c
            }));
        } else {
            this.chart.config.type = 'candlestick';
            this.chart.config.data.datasets[0].data = this.candlesData;
        }
        this.chart.update();
    }

    updateChart() {
        this.chart.data.datasets[0].data = this.chartType === 'line'
            ? this.candlesData.map(d => ({ x: d.t, y: d.c }))
            : this.candlesData;
        this.chart.update();
    }

    updateMarketOverview(data) {
        // Update trend information
        document.getElementById('currentPrice').textContent = `$${data.trend_info.current_price.toFixed(2)}`;
        const directionEl = document.getElementById('trendDirection');
        directionEl.textContent = data.trend_info.direction;
        directionEl.className = `trend-indicator trend-${data.trend_info.direction.toLowerCase()}`;
        document.getElementById('trendStrength').textContent = data.trend_info.strength;

        // Update moving averages
        document.getElementById('sma20').textContent = data.trend_info.sma20 
            ? `$${data.trend_info.sma20.toFixed(2)}` 
            : '-';
        document.getElementById('sma50').textContent = data.trend_info.sma50 
            ? `$${data.trend_info.sma50.toFixed(2)}` 
            : '-';

        // Update Fibonacci levels if available
        if (data.ote_zone) {
            document.getElementById('fiboEntry').textContent = `$${data.ote_zone.entry_price.toFixed(2)}`;
            document.getElementById('fiboSL').textContent = `$${data.ote_zone.stop_loss.toFixed(2)}`;
            document.getElementById('fiboTP').textContent = `$${data.ote_zone.take_profit1.toFixed(2)}`;
        }
    }
}

// Initialize chart handler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chartHandler = new ChartHandler();
    window.chartHandler.fetchData();
});