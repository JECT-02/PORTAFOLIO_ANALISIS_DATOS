class ApiService {
    constructor() {
        this.dataPath = '../data/gold/frontend_data.json';
        this.data = null;
    }

    async loadData() {
        try {
            const response = await fetch(this.dataPath);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.data = await response.json();
            return this.data;
        } catch (error) {
            console.error("Could not load data:", error);
            // Si falla por CORS (abriendo archivo local directo), mostrar mensaje
            alert("Error cargando datos. Asegurese de usar un servidor local (ej: python -m http.server)");
            return null;
        }
    }

    async updateData() {
        try {
            const response = await fetch('/api/update_data', {
                method: 'POST'
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            if (result.status === 'success') {
                return await this.loadData();
            } else {
                throw new Error("El backend reporto un error al actualizar datos.");
            }
        } catch (error) {
            console.error("Could not update data:", error);
            alert("Error ejecutando el pipeline de datos en el servidor.");
            return null;
        }
    }

    getRiskMetrics(horizon, confidence) {
        if (!this.data) return null;
        const metrics = this.data.risk_metrics;
        return metrics.find(m => m.horizon == horizon && Math.abs(m.confidence - confidence) < 0.001);
    }

    getAllMetricsForHorizon(horizon) {
        if (!this.data) return null;
        return this.data.risk_metrics.filter(m => m.horizon == horizon);
    }

    getStockInfo() {
        return this.data ? this.data.stock_info : [];
    }

    getSimulations(horizon) {
        return this.data ? this.data.simulations[horizon] : null;
    }

    getCorrelationMatrix() {
        return this.data ? this.data.correlation : null;
    }
}

const api = new ApiService();
