// Configuracion global de Chart.js para modo oscuro
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';

class ChartManager {
    constructor() {
        this.charts = {};
    }

    destroyChart(id) {
        if (this.charts[id]) {
            this.charts[id].destroy();
        }
    }

    renderHistogram(id, returns, varValue, cvarValue) {
        this.destroyChart(id);
        const ctx = document.getElementById(id).getContext('2d');
        
        // Crear bins simples
        const min = Math.min(...returns);
        const max = Math.max(...returns);
        const bins = 50;
        const binWidth = (max - min) / bins;
        const histogram = new Array(bins).fill(0);
        
        returns.forEach(r => {
            let binIndex = Math.floor((r - min) / binWidth);
            if (binIndex === bins) binIndex--;
            histogram[binIndex]++;
        });

        const labels = Array.from({length: bins}, (_, i) => (min + i * binWidth).toFixed(4));

        // Lineas verticales para VaR y CVaR (nota: VaR/CVaR estan en terminos de perdidas, 
        // asique -VaR es el cuantil en el espacio de retornos)
        const varRet = -varValue;
        const cvarRet = -cvarValue;

        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Frecuencia',
                    data: histogram,
                    backgroundColor: '#3b82f6',
                    borderWidth: 0,
                    barPercentage: 1.0,
                    categoryPercentage: 1.0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false },
                    annotation: { // Requiere plugin, lo simulamos simple si no esta
                    }
                },
                scales: {
                    x: {
                        ticks: { maxTicksLimit: 10 }
                    }
                }
            }
        });
    }

    renderPaths(id, pathsData, showPaths) {
        this.destroyChart(id);
        if (!showPaths) return;
        
        const ctx = document.getElementById(id).getContext('2d');
        
        // pathsData is an object with symbols as keys and arrays of prices as values.
        // For a portfolio path, we just show individual asset paths here for simplicity, 
        // or we could show top 5 assets.
        const symbols = Object.keys(pathsData).slice(0, 5); // top 5
        const datasets = symbols.map((sym, i) => {
            const colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6'];
            return {
                label: sym,
                data: pathsData[sym],
                borderColor: colors[i % colors.length],
                borderWidth: 1,
                fill: false,
                pointRadius: 0
            };
        });

        const labels = Array.from({length: pathsData[symbols[0]].length}, (_, i) => `T+${i}`);

        this.charts[id] = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } }
            }
        });
    }

    renderMarkovianPaths(id, stockInfo, pathsData, horizon) {
        this.destroyChart(id);
        const ctx = document.getElementById(id).getContext('2d');
        
        // Seleccionar top 5 acciones por mayor volatilidad
        const topStocks = [...stockInfo].sort((a, b) => b.volatility - a.volatility).slice(0, 5);
        const colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6'];
        
        const datasets = [];
        
        topStocks.forEach((stock, idx) => {
            const sym = stock.symbol;
            const currentPrice = stock.price;
            const simPrices = pathsData[sym];
            
            if (!simPrices) return; // Evitar errores si falta el dato

            // Colores con opacidad para crear "dimensionalidad" (efecto calor/densidad)
            const rgbaColors = ['rgba(59, 130, 246, 0.3)', 'rgba(16, 185, 129, 0.3)', 'rgba(239, 68, 68, 0.3)', 'rgba(245, 158, 11, 0.3)', 'rgba(139, 92, 246, 0.3)'];
            
            const dataPoints = [];
            // Para dibujar lineas que se abren como abanico sin conectarse entre si,
            // insertamos NaN en lugar de null para evitar crashes internos de Chart.js
            simPrices.forEach(simP => {
                dataPoints.push({ x: 0, y: currentPrice });
                dataPoints.push({ x: horizon, y: simP });
                dataPoints.push({ x: NaN, y: NaN });
            });
            
            datasets.push({
                label: sym,
                data: dataPoints,
                borderColor: rgbaColors[idx % rgbaColors.length],
                borderWidth: 1.5,
                borderDash: [4, 4], // lineas punteadas mas notorias
                showLine: true,
                pointRadius: 0,
                fill: false,
                tension: 0
            });
            
            // Dataset extra para el punto actual
            datasets.push({
                label: sym + ' (Actual)',
                data: [{ x: 0, y: currentPrice }],
                backgroundColor: colors[idx % colors.length],
                borderColor: '#ffffff',
                borderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8,
                showLine: false
            });
        });

        this.charts[id] = new Chart(ctx, {
            type: 'scatter',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            filter: function(item) {
                                return !item.text.includes('(Actual)');
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                if (context.raw && context.raw.x === 0) {
                                    return `${context.dataset.label.replace(' (Actual)', '')}: Precio Actual $${context.raw.y.toFixed(2)}`;
                                } else if (context.raw && context.raw.x === horizon) {
                                    return `${context.dataset.label}: Futuro Simulado $${context.raw.y.toFixed(2)}`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Horizonte de Simulacion' },
                        ticks: {
                            stepSize: horizon,
                            callback: function(value) {
                                if (value === 0) return 'Hoy (T=0)';
                                if (value === horizon) return `T+${horizon}`;
                                return value;
                            }
                        },
                        min: -0.1 * horizon,
                        max: horizon * 1.1
                    },
                    y: {
                        title: { display: true, text: 'Precio ($)' }
                    }
                }
            }
        });
    }

    renderCorrelationMatrix(id, corrData) {
        this.destroyChart(id);
        const ctx = document.getElementById(id).getContext('2d');
        
        // Select top 15 symbols to avoid clutter
        const n = Math.min(15, corrData.symbols.length);
        const symbols = corrData.symbols.slice(0, n);
        const data = [];
        
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                data.push({
                    x: symbols[i],
                    y: symbols[j],
                    v: corrData.matrix[i][j]
                });
            }
        }

        this.charts[id] = new Chart(ctx, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Correlacion',
                    data: data,
                    backgroundColor(context) {
                        const value = context.dataset.data[context.dataIndex].v;
                        const alpha = Math.abs(value);
                        return value > 0 
                            ? `rgba(59, 130, 246, ${alpha})` // blue
                            : `rgba(239, 68, 68, ${alpha})`; // red
                    },
                    width: ({chart}) => (chart.chartArea || {}).width / n - 1,
                    height: ({chart}) => (chart.chartArea || {}).height / n - 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { type: 'category', labels: symbols },
                    y: { type: 'category', labels: symbols, offset: true }
                }
            }
        });
    }

    renderHorizonMetrics(id, metrics1d, metrics5d, metrics20d) {
        this.destroyChart(id);
        const ctx = document.getElementById(id).getContext('2d');
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['1 Dia', '5 Dias', '20 Dias'],
                datasets: [
                    {
                        label: 'VaR',
                        data: [metrics1d.VaR, metrics5d.VaR, metrics20d.VaR],
                        backgroundColor: '#f59e0b'
                    },
                    {
                        label: 'CVaR',
                        data: [metrics1d.CVaR, metrics5d.CVaR, metrics20d.CVaR],
                        backgroundColor: '#ef4444'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    }

    renderSectorPie(id, stockInfo) {
        this.destroyChart(id);
        const ctx = document.getElementById(id).getContext('2d');
        
        const sectors = {};
        stockInfo.forEach(s => {
            sectors[s.sector] = (sectors[s.sector] || 0) + 1;
        });

        const labels = Object.keys(sectors);
        const data = Object.values(sectors);

        this.charts[id] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6',
                        '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'right' } }
            }
        });
    }

    renderScatter(id, stockInfo) {
        this.destroyChart(id);
        const ctx = document.getElementById(id).getContext('2d');
        
        // Mock expected return = volatility * 0.5 for demonstration
        const data = stockInfo.map(s => ({
            x: s.volatility * 100, // Riesgo %
            y: (s.volatility * 0.5) * 100, // Retorno esperado % (simplificado)
            symbol: s.symbol
        }));

        this.charts[id] = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Activos',
                    data: data,
                    backgroundColor: '#3b82f6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.raw.symbol}: Vol ${ctx.raw.x.toFixed(1)}%, Ret ${ctx.raw.y.toFixed(1)}%`
                        }
                    }
                },
                scales: {
                    x: { title: { display: true, text: 'Volatilidad (Riesgo) %' } },
                    y: { title: { display: true, text: 'Retorno %' } }
                }
            }
        });
    }
}

const charts = new ChartManager();
