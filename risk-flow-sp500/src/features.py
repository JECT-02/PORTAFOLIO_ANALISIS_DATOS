import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import GOLD_DIR, SILVER_DIR
from src.utils import compute_cholesky, ledoit_wolf_shrinkage, verify_sdp

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252


def load_returns(silver_dir: Path) -> pd.DataFrame:
    parquet_path = silver_dir / "returns.parquet"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    csv_path = silver_dir / "returns.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path, parse_dates=["date"])
    raise FileNotFoundError("No returns file found in silver/")


def build_returns_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    pivot = returns_df.pivot(index="date", columns="symbol", values="return_log")
    pivot = pivot.dropna(how="all")
    pivot = pivot.dropna(axis=1, how="any")
    return pivot.sort_index()


def compute_mean_returns(returns_matrix: pd.DataFrame) -> pd.Series:
    return returns_matrix.mean() * TRADING_DAYS_PER_YEAR


def compute_volatilities(returns_matrix: pd.DataFrame) -> pd.Series:
    return returns_matrix.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)


def compute_correlation_matrix(returns_matrix: pd.DataFrame) -> pd.DataFrame:
    return returns_matrix.corr(method="pearson")


def compute_covariance_matrix(returns_matrix: pd.DataFrame) -> pd.DataFrame:
    return returns_matrix.cov()


def ensure_sdp_covariance(covariance_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    symbols = covariance_df.columns.tolist()
    cov_array = covariance_df.values
    is_sdp, min_eigenvalue = verify_sdp(cov_array)
    if not is_sdp:
        logger.warning(
            "Covariance matrix not SDP (min eigenvalue=%.2e). Applying Ledoit-Wolf shrinkage.",
            min_eigenvalue,
        )
        cov_array = ledoit_wolf_shrinkage(cov_array)
        is_sdp, min_eigenvalue = verify_sdp(cov_array)
        if not is_sdp:
            logger.warning(
                "Still not SDP after shrinkage (min eigenvalue=%.2e). Applying nearest PSD.",
                min_eigenvalue,
            )
            from src.utils import nearest_psd
            cov_array = nearest_psd(cov_array)
        shrinkage_applied = True
    else:
        logger.info("Covariance matrix is SDP (min eigenvalue=%.2e)", min_eigenvalue)
        shrinkage_applied = False
    return pd.DataFrame(cov_array, index=symbols, columns=symbols), shrinkage_applied


def run_feature_pipeline() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger.info("Loading silver returns")
    returns_df = load_returns(SILVER_DIR)

    returns_matrix = build_returns_matrix(returns_df)
    logger.info(
        "Returns matrix: %d dates x %d symbols", *returns_matrix.shape
    )

    mean_returns = compute_mean_returns(returns_matrix)
    volatilities = compute_volatilities(returns_matrix)
    correlation_matrix = compute_correlation_matrix(returns_matrix)
    covariance_matrix_raw = compute_covariance_matrix(returns_matrix)

    covariance_matrix, shrinkage_applied = ensure_sdp_covariance(covariance_matrix_raw)
    if shrinkage_applied:
        logger.info("Ledoit-Wolf shrinkage was applied to covariance matrix")

    cholesky_lower = compute_cholesky(covariance_matrix.values)
    symbols = covariance_matrix.columns.tolist()
    cholesky_df = pd.DataFrame(
        cholesky_lower, index=symbols, columns=symbols
    )

    mean_returns.to_csv(GOLD_DIR / "mean_returns.csv", header=["mean_return_annual"])
    volatilities.to_csv(GOLD_DIR / "volatilities.csv", header=["volatility_annual"])
    correlation_matrix.to_csv(GOLD_DIR / "correlation_matrix.csv")
    covariance_matrix.to_csv(GOLD_DIR / "covariance_matrix.csv")
    cholesky_df.to_csv(GOLD_DIR / "cholesky_lower.csv")

    logger.info(
        "Feature pipeline complete. Saved gold/ files for %d symbols.", len(symbols)
    )
    returns_matrix.to_parquet(GOLD_DIR / "returns_matrix.parquet")


if __name__ == "__main__":
    run_feature_pipeline()
