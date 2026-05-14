import json
import logging
from pathlib import Path

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_frontend_data():
    gold_dir = Path("data/gold")
    silver_dir = Path("data/silver")
    frontend_data = {}

    try:
        # Load risk metrics
        metrics_df = pd.read_csv(gold_dir / "risk_metrics_all.csv")
        frontend_data["risk_metrics"] = metrics_df.to_dict(orient="records")

        # Load stock info and volatilities
        stock_info_df = pd.read_csv(silver_dir / "stock_info.csv")
        vol_df = pd.read_csv(gold_dir / "volatilities.csv", index_col=0)
        
        # Merge volatilities into stock info
        stock_info = []
        for _, row in stock_info_df.iterrows():
            sym = row["symbol"]
            vol = vol_df.loc[sym, "volatility_annual"] if sym in vol_df.index else 0
            stock_info.append({
                "symbol": sym,
                "name": row.get("name", sym),
                "sector": row.get("sector", "Unknown"),
                "price": row.get("lastPrice", 0),
                "volatility": vol,
            })
        frontend_data["stock_info"] = stock_info

        # Load correlation matrix
        corr_df = pd.read_csv(gold_dir / "correlation_matrix.csv", index_col=0)
        frontend_data["correlation"] = {
            "symbols": corr_df.columns.tolist(),
            "matrix": corr_df.values.tolist()
        }

        # Load backtest results
        if (gold_dir / "backtest_results.csv").exists():
            bt_df = pd.read_csv(gold_dir / "backtest_results.csv")
            frontend_data["backtest"] = bt_df.to_dict(orient="records")
        else:
            frontend_data["backtest"] = []

        # Load simulated data (subset for charts to keep JSON size manageable)
        simulations = {}
        for h in [1, 5, 20]:
            try:
                ret_df = pd.read_csv(gold_dir / f"simulated_returns_{h}d.csv")
                price_df = pd.read_csv(gold_dir / f"simulated_prices_{h}d.csv")
                
                # Portfolio returns for histogram
                port_ret = ret_df["portfolio_return"].values.tolist()
                
                # Random 100 paths for prices
                n_paths = min(100, len(price_df))
                idx = np.random.choice(len(price_df), n_paths, replace=False)
                sampled_prices = price_df.iloc[idx].to_dict(orient="list")
                
                simulations[str(h)] = {
                    "portfolio_returns": port_ret,
                    "price_paths": sampled_prices
                }
            except Exception as e:
                logger.error(f"Error loading {h}d simulation: {e}")
                
        frontend_data["simulations"] = simulations

        # Save to JSON
        out_path = gold_dir / "frontend_data.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(frontend_data, f)
        
        logger.info(f"Frontend data generated successfully at {out_path}")

    except Exception as e:
        logger.error(f"Failed to generate frontend data: {e}")

if __name__ == "__main__":
    generate_frontend_data()
