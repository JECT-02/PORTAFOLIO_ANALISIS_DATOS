import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import (
    CONFIDENCE_LEVELS,
    GOLD_DIR,
    N_SCENARIOS,
    SILVER_DIR,
    SIMULATION_HORIZONS,
)

logger = logging.getLogger(__name__)

RANDOM_SEED = 42


def load_gold_features(gold_dir: Path) -> tuple[pd.Series, pd.Series, np.ndarray, list[str]]:
    mean_returns = pd.read_csv(gold_dir / "mean_returns.csv", index_col=0).squeeze()
    volatilities = pd.read_csv(gold_dir / "volatilities.csv", index_col=0).squeeze()
    cholesky_df = pd.read_csv(gold_dir / "cholesky_lower.csv", index_col=0)
    symbols = cholesky_df.columns.tolist()
    cholesky_lower = cholesky_df.values
    mean_returns = mean_returns.reindex(symbols)
    volatilities = volatilities.reindex(symbols)
    return mean_returns, volatilities, cholesky_lower, symbols


def load_last_prices(silver_dir: Path, symbols: list[str]) -> pd.Series:
    try:
        prices_df = pd.read_parquet(silver_dir / "prices.parquet")
    except Exception:
        prices_df = pd.read_csv(silver_dir / "prices.csv", parse_dates=["date"])
    last_prices = (
        prices_df.sort_values("date")
        .groupby("symbol")["adjClose"]
        .last()
    )
    return last_prices.reindex(symbols)


def simulate_gbm(
    volatilities: np.ndarray,
    cholesky_lower: np.ndarray,
    horizon_days: int,
    n_scenarios: int,
    mu_drift: float = 0.0,
) -> np.ndarray:
    n_assets = len(volatilities)
    dt = horizon_days / 252.0
    rng = np.random.default_rng(RANDOM_SEED)
    standard_normals = rng.standard_normal((n_assets, n_scenarios))
    correlated_shocks = cholesky_lower @ standard_normals
    drift_term = (mu_drift - 0.5 * volatilities ** 2) * dt
    diffusion_term = volatilities[:, np.newaxis] * np.sqrt(dt) * correlated_shocks
    log_returns = drift_term[:, np.newaxis] + diffusion_term
    return log_returns


def compute_price_paths(
    last_prices: np.ndarray,
    log_returns: np.ndarray,
) -> np.ndarray:
    return last_prices[:, np.newaxis] * np.exp(log_returns)


def compute_portfolio_returns(
    log_returns: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    asset_returns = np.exp(log_returns) - 1.0
    return (weights[:, np.newaxis] * asset_returns).sum(axis=0)


def run_simulation_pipeline() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    mean_returns, volatilities, cholesky_lower, symbols = load_gold_features(GOLD_DIR)
    last_prices = load_last_prices(SILVER_DIR, symbols)
    n_assets = len(symbols)
    equal_weights = np.full(n_assets, 1.0 / n_assets)

    vol_array = volatilities.values
    last_prices_array = last_prices.values

    for horizon in SIMULATION_HORIZONS:
        logger.info("Simulating %d scenarios for horizon=%dd", N_SCENARIOS, horizon)
        log_returns = simulate_gbm(vol_array, cholesky_lower, horizon, N_SCENARIOS)
        simulated_prices = compute_price_paths(last_prices_array, log_returns)
        portfolio_returns = compute_portfolio_returns(log_returns, equal_weights)

        asset_returns_matrix = np.exp(log_returns) - 1.0
        returns_df = pd.DataFrame(
            asset_returns_matrix.T, columns=symbols
        )
        returns_df["portfolio_return"] = portfolio_returns
        returns_df.to_csv(
            GOLD_DIR / f"simulated_returns_{horizon}d.csv", index=False
        )

        prices_df = pd.DataFrame(simulated_prices.T, columns=symbols)
        prices_df.to_csv(
            GOLD_DIR / f"simulated_prices_{horizon}d.csv", index=False
        )
        logger.info(
            "Saved simulated_returns_%dd.csv and simulated_prices_%dd.csv", horizon, horizon
        )

    logger.info("Simulation pipeline complete for horizons: %s", SIMULATION_HORIZONS)


if __name__ == "__main__":
    run_simulation_pipeline()
