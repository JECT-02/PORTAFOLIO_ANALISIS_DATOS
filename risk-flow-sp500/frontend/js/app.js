document.addEventListener('DOMContentLoaded', async () => {
    // Estado de la aplicacion
    let state = {
        horizon: 1,
        confidence: 0.95,
        showPaths: true
    };

    // Inicializar datos
    const data = await api.loadData();
    if (!data) return;

    // Elementos DOM
    const horizonBtns = document.querySelectorAll('#horizon-toggles .toggle-btn');
    const confBtns = document.querySelectorAll('#confidence-toggles .toggle-btn');
    const togglePaths = document.getElementById('toggle-paths');
    const recalcBtn = document.getElementById('recalc-btn');
    const updateDataBtn = document.getElementById('update-data-btn');

    // Setup event listeners
    horizonBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            horizonBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            state.horizon = parseInt(e.target.dataset.value);
            updateDashboard();
        });
    });

    confBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            confBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            state.confidence = parseFloat(e.target.dataset.value);
            updateDashboard();
        });
    });

    togglePaths.addEventListener('change', (e) => {
        state.showPaths = e.target.checked;
        updateDashboard();
    });

    recalcBtn.addEventListener('click', () => {
        // En una app real aqui se enviarian los pesos al backend
        // Como es un prototipo estatico, solo simulamos un recalc visual
        recalcBtn.textContent = 'Calculando...';
        setTimeout(() => {
            updateDashboard();
            recalcBtn.textContent = 'Recalcular Riesgo';
        }, 500);
    });

    updateDataBtn.addEventListener('click', async () => {
        updateDataBtn.disabled = true;
        updateDataBtn.innerHTML = '<span class="loading-spinner"></span> Actualizando...';
        
        const newData = await api.updateData();
        
        updateDataBtn.disabled = false;
        updateDataBtn.innerHTML = 'Actualizar Data';
        
        if (newData) {
            updateTable();
            updateDashboard();
            renderStaticCharts();
        }
    });

    // Funciones de actualizacion
    function updateTable() {
        const stockInfo = api.getStockInfo();
        const tbody = document.getElementById('portfolio-body');
        tbody.innerHTML = '';
        
        const weight = (100 / stockInfo.length).toFixed(2);
        
        stockInfo.forEach(stock => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <strong>${stock.symbol}</strong><br>
                    <small style="color:var(--text-muted)">${stock.sector}</small>
                </td>
                <td>
                    <input type="number" class="weight-input" value="${weight}" min="0" max="100" step="0.1">
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    function formatPercent(value) {
        return (value * 100).toFixed(2) + '%';
    }

    function updateDashboard() {
        const metrics = api.getRiskMetrics(state.horizon, state.confidence);
        if (!metrics) return;

        // Panel de Resumen Narrativo
        const summaryPanel = document.getElementById('summary-panel');
        summaryPanel.innerHTML = `
            <h2>Proyeccion a ${state.horizon} ${state.horizon === 1 ? 'Dia' : 'Dias'}</h2>
            <p>Con un nivel de confianza del <strong>${formatPercent(state.confidence)}</strong>, se estima que la perdida maxima de su portafolio en los proximos <strong>${state.horizon} dias</strong> no excedera el <strong><span style="color:var(--danger)">${formatPercent(metrics.VaR)}</span></strong> en condiciones normales de mercado. En caso de presentarse un evento extremo (superando el VaR), la perdida promedio esperada (CVaR) seria de <strong><span style="color:var(--danger)">${formatPercent(metrics.CVaR)}</span></strong>. Existe una probabilidad del <strong>${formatPercent(metrics.prob_loss)}</strong> de obtener rendimientos negativos en este periodo.</p>
        `;

        // Actualizar tarjetas
        document.getElementById('val-var').textContent = formatPercent(metrics.VaR);
        document.getElementById('val-cvar').textContent = formatPercent(metrics.CVaR);
        document.getElementById('val-mdd').textContent = formatPercent(metrics.max_drawdown);
        document.getElementById('val-prob').textContent = formatPercent(metrics.prob_loss);

        // Colores condicionales
        document.getElementById('val-var').className = `metric-value ${metrics.VaR > 0.05 ? 'negative' : ''}`;
        document.getElementById('val-cvar').className = `metric-value negative`;
        document.getElementById('val-mdd').className = `metric-value negative`;

        // Actualizar graficos
        const simData = api.getSimulations(state.horizon);
        if (simData) {
            charts.renderHistogram('histChart', simData.portfolio_returns, metrics.VaR, metrics.CVaR);
            charts.renderPaths('pathsChart', simData.price_paths, state.showPaths);
            charts.renderMarkovianPaths('markovChart', api.getStockInfo(), simData.price_paths, state.horizon);
        }

        const metrics1d = api.getRiskMetrics(1, state.confidence);
        const metrics5d = api.getRiskMetrics(5, state.confidence);
        const metrics20d = api.getRiskMetrics(20, state.confidence);
        charts.renderHorizonMetrics('horizonChart', metrics1d, metrics5d, metrics20d);
    }

    // Renderizados iniciales estaticos (no dependen del horizonte)
    function renderStaticCharts() {
        const corrData = api.getCorrelationMatrix();
        if (corrData) {
            charts.renderCorrelationMatrix('corrChart', corrData);
        }

        const stockInfo = api.getStockInfo();
        if (stockInfo.length > 0) {
            charts.renderSectorPie('sectorChart', stockInfo);
            charts.renderScatter('scatterChart', stockInfo);
        }
    }

    // Init
    updateTable();
    updateDashboard();
    renderStaticCharts();
});
