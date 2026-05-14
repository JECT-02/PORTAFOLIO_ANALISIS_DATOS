import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import (
    CONFIDENCE_LEVELS,
    GOLD_DIR,
    N_SCENARIOS,
    SILVER_DIR,
    SIMULATION_HORIZONS,
)
from src.features import (
    build_returns_matrix,
    compute_covariance_matrix,
    compute_volatilities,
    ensure_sdp_covariance,
    load_returns,
)
from src.simulation import simulate_gbm, compute_portfolio_returns
from src.utils import compute_cholesky

logger = logging.getLogger(__name__)


def calculate_var(returns: np.ndarray, alpha: float) -> float:
    return -np.percentile(returns, (1 - alpha) * 100)


def calculate_cvar(returns: np.ndarray, var_alpha: float) -> float:
    losses = -returns
    tail_losses = losses[losses > var_alpha]
    if len(tail_losses) == 0:
        return var_alpha
    return np.mean(tail_losses)


def compute_risk_metrics(returns: np.ndarray, horizon: int) -> pd.DataFrame:
    metrics = []
    max_drawdown = np.min(returns)
    prob_loss = np.sum(returns < 0) / len(returns)
    skewness = stats.skew(returns)
    kurtosis = stats.kurtosis(returns)

    for alpha in CONFIDENCE_LEVELS:
        var = calculate_var(returns, alpha)
        cvar = calculate_cvar(returns, var)
        metrics.append(
            {
                "horizon": horizon,
                "confidence": alpha,
                "VaR": var,
                "CVaR": cvar,
                "max_drawdown": max_drawdown,
                "prob_loss": prob_loss,
                "skewness": skewness,
                "kurtosis": kurtosis,
            }
        )
    return pd.DataFrame(metrics)


def kupiec_pof_test(
    total_days: int, exceptions: int, confidence: float
) -> tuple[float, float, bool]:
    p = 1 - confidence
    p_obs = exceptions / total_days if total_days > 0 else 0

    if exceptions == 0:
        lr = -2 * np.log((p**0) * ((1 - p) ** total_days))
    elif exceptions == total_days:
        lr = -2 * np.log((p**total_days) * ((1 - p) ** 0))
    else:
        num = (p**exceptions) * ((1 - p) ** (total_days - exceptions))
        den = (p_obs**exceptions) * ((1 - p_obs) ** (total_days - exceptions))
        lr = -2 * np.log(num / den)

    p_value = 1 - stats.chi2.cdf(lr, df=1)
    reject_h0 = lr > 3.841
    return lr, p_value, reject_h0


def backtest_var(
    returns_matrix: pd.DataFrame, window: int = 252
) -> pd.DataFrame:
    n_days = len(returns_matrix)
    if n_days <= window:
        logger.warning("Not enough data for backtesting. Needs %d days, has %d.", window + 1, n_days)
        return pd.DataFrame()

    alphas = [0.95, 0.99]
    exceptions_count = {a: 0 for a in alphas}
    total_test_days = n_days - window

    returns_array = returns_matrix.values
    n_assets = returns_array.shape[1]
    weights = np.full(n_assets, 1.0 / n_assets)

    logger.info("Running backtest for %d days", total_test_days)

    for t in range(window, n_days):
        window_returns_df = returns_matrix.iloc[t - window : t]
        
        volatilities = compute_volatilities(window_returns_df).values
        cov_matrix_raw = compute_covariance_matrix(window_returns_df)
        cov_matrix, _ = ensure_sdp_covariance(cov_matrix_raw)
        cholesky_lower = compute_cholesky(cov_matrix.values)

        log_returns_sim = simulate_gbm(
            volatilities, cholesky_lower, horizon_days=1, n_scenarios=2000
        )
        port_sim_returns = compute_portfolio_returns(log_returns_sim, weights)

        var_95 = calculate_var(port_sim_returns, 0.95)
        var_99 = calculate_var(port_sim_returns, 0.99)

        real_returns = returns_array[t]
        real_port_return = np.sum(weights * real_returns)

        if -real_port_return > var_95:
            exceptions_count[0.95] += 1
        if -real_port_return > var_99:
            exceptions_count[0.99] += 1

    results = []
    for alpha in alphas:
        exc = exceptions_count[alpha]
        lr, p_val, reject = kupiec_pof_test(total_test_days, exc, alpha)
        results.append(
            {
                "alpha": alpha,
                "horizon": 1,
                "total_days": total_test_days,
                "exceptions_observed": exc,
                "exception_rate": exc / total_test_days if total_test_days > 0 else 0,
                "LR_statistic": lr,
                "p_value": p_val,
                "reject_h0": reject,
                "conclusion": "Model rejected" if reject else "Model accepted",
            }
        )
    return pd.DataFrame(results)


def run_risk_metrics_pipeline() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    all_metrics = []

    for horizon in SIMULATION_HORIZONS:
        sim_file = GOLD_DIR / f"simulated_returns_{horizon}d.csv"
        if not sim_file.exists():
            logger.error("Simulation file not found: %s", sim_file)
            continue
            
        sim_df = pd.read_csv(sim_file)
        port_returns = sim_df["portfolio_return"].values
        
        metrics_df = compute_risk_metrics(port_returns, horizon)
        metrics_df.to_csv(GOLD_DIR / f"risk_metrics_{horizon}d.csv", index=False)
        all_metrics.append(metrics_df)
        logger.info("Saved risk_metrics_%dd.csv", horizon)

    if all_metrics:
        consolidated = pd.concat(all_metrics, ignore_index=True)
        consolidated.to_csv(GOLD_DIR / "risk_metrics_all.csv", index=False)
        logger.info("Saved consolidated risk_metrics_all.csv")

    returns_df = load_returns(SILVER_DIR)
    returns_matrix = build_returns_matrix(returns_df)
    
    # Check if we have enough data to do 252 days rolling. 
    # If not, adjust window to half of data length for demonstration purposes if < 252
    window_size = 252
    if len(returns_matrix) <= 252:
        window_size = len(returns_matrix) // 2
        logger.warning("Data length (%d) is <= 252. Adjusting backtest window to %d days.", len(returns_matrix), window_size)

    if window_size > 10:
        backtest_df = backtest_var(returns_matrix, window=window_size)
        if not backtest_df.empty:
            backtest_df.to_csv(GOLD_DIR / "backtest_results.csv", index=False)
            logger.info("Saved backtest_results.csv")
    else:
        logger.warning("Not enough data to run backtesting even with reduced window.")


if __name__ == "__main__":
    run_risk_metrics_pipeline()
