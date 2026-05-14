import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import BRONZE_DIR, HISTORICAL_DAYS, SILVER_DIR

logger = logging.getLogger(__name__)

MIN_VALID_DAYS = 200
FORWARD_FILL_LIMIT = 2


def load_bronze_historical(bronze_dir: Path) -> pd.DataFrame:
    historical_dir = bronze_dir / "historical"
    records: list[dict] = []
    for json_file in sorted(historical_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as fh:
            raw = json.load(fh)
        data = raw if isinstance(raw, list) else [raw]
        for entry in data:
            symbol = entry.get("symbol", json_file.stem.split("_")[0])
            rows = entry.get("historical", None)
            if rows is None:
                for row in (entry if isinstance(entry, list) else [entry]):
                    if "date" in row:
                        row["symbol"] = symbol
                        records.append(row)
            else:
                for row in rows:
                    row["symbol"] = symbol
                    records.append(row)
    if not records:
        logger.error("No historical records found in %s", historical_dir)
        return pd.DataFrame()
    return pd.DataFrame(records)


def load_stock_info(bronze_dir: Path) -> pd.DataFrame:
    info_files = sorted(bronze_dir.glob("stock_info_*.json"))
    if not info_files:
        return pd.DataFrame()
    with open(info_files[-1], encoding="utf-8") as fh:
        raw = json.load(fh)
    return pd.DataFrame(raw)


def normalize_prices(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    if "adjClose" not in df.columns:
        df["adjClose"] = df["close"]
    base_cols = ["symbol", "date", "adjClose", "open", "high", "low", "close", "volume"]
    available = [c for c in base_cols if c in df.columns]
    df = df[available].copy()
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    return df


def filter_sufficient_symbols(prices_df: pd.DataFrame) -> pd.DataFrame:
    counts = prices_df.groupby("symbol")["adjClose"].count()
    valid_symbols = counts[counts >= MIN_VALID_DAYS].index.tolist()
    removed = set(counts.index) - set(valid_symbols)
    if removed:
        logger.warning(
            "Removed %d symbols with insufficient data: %s", len(removed), sorted(removed)
        )
    logger.info(
        "Keeping %d symbols with >= %d valid days", len(valid_symbols), MIN_VALID_DAYS
    )
    return prices_df[prices_df["symbol"].isin(valid_symbols)].copy()


def apply_forward_fill(prices_df: pd.DataFrame) -> pd.DataFrame:
    filled_parts: list[pd.DataFrame] = []
    for symbol, group in prices_df.groupby("symbol"):
        group = group.set_index("date").sort_index()
        all_dates = pd.date_range(group.index.min(), group.index.max(), freq="B")
        group = group.reindex(all_dates)
        group["symbol"] = symbol
        for col in group.select_dtypes(include="number").columns:
            group[col] = group[col].ffill(limit=FORWARD_FILL_LIMIT)
        group = group.dropna(subset=["adjClose"])
        group = group.reset_index().rename(columns={"index": "date"})
        filled_parts.append(group)
    return pd.concat(filled_parts, ignore_index=True)


def compute_log_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    returns_parts: list[pd.DataFrame] = []
    for symbol, group in prices_df.groupby("symbol"):
        group = group.sort_values("date").copy()
        group["return_log"] = np.log(
            group["adjClose"] / group["adjClose"].shift(1)
        )
        group = group.dropna(subset=["return_log"])
        returns_parts.append(group[["date", "symbol", "return_log"]])
    return pd.concat(returns_parts, ignore_index=True)


def run_clean_pipeline() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger.info("Loading bronze historical data")
    raw_df = load_bronze_historical(BRONZE_DIR)
    if raw_df.empty:
        logger.error("No data to clean. Run fetch_data first.")
        return

    logger.info("Raw records: %d across %d symbols", len(raw_df), raw_df["symbol"].nunique())

    prices_df = normalize_prices(raw_df)
    prices_df = filter_sufficient_symbols(prices_df)
    prices_df = apply_forward_fill(prices_df)

    prices_path = SILVER_DIR / "prices.parquet"
    try:
        prices_df.to_parquet(prices_path, index=False)
        logger.info("Saved prices.parquet: %d rows, %d symbols", len(prices_df), prices_df["symbol"].nunique())
    except Exception as exc:
        logger.warning("pyarrow unavailable (%s), saving as CSV", exc)
        prices_df.to_csv(SILVER_DIR / "prices.csv", index=False)

    returns_df = compute_log_returns(prices_df)
    returns_path = SILVER_DIR / "returns.parquet"
    try:
        returns_df.to_parquet(returns_path, index=False)
        logger.info("Saved returns.parquet: %d rows", len(returns_df))
    except Exception as exc:
        logger.warning("pyarrow unavailable (%s), saving as CSV", exc)
        returns_df.to_csv(SILVER_DIR / "returns.csv", index=False)

    stock_info_df = load_stock_info(BRONZE_DIR)
    active_symbols = prices_df["symbol"].unique().tolist()
    if not stock_info_df.empty:
        stock_info_df = stock_info_df[stock_info_df["symbol"].isin(active_symbols)].copy()

    last_prices = (
        prices_df.sort_values("date")
        .groupby("symbol")["adjClose"]
        .last()
        .reset_index()
        .rename(columns={"adjClose": "lastPrice"})
    )
    if not stock_info_df.empty:
        stock_info_df = stock_info_df.merge(last_prices, on="symbol", how="left")
    else:
        stock_info_df = last_prices

    stock_info_df.to_csv(SILVER_DIR / "stock_info.csv", index=False)
    logger.info("Saved stock_info.csv: %d symbols", len(stock_info_df))
    logger.info("Clean pipeline complete.")


if __name__ == "__main__":
    run_clean_pipeline()
