import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import BRONZE_DIR, HISTORICAL_DAYS, SP500_TOP50
from src.fmp_client import FMPClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_quotes_and_profiles(client: FMPClient, symbols: list[str]) -> list[dict]:
    combined: list[dict] = []
    for symbol in symbols:
        quote = client.get_quote(symbol)
        profile = client.get_profile(symbol)
        if quote is not None:
            record = {
                "symbol": symbol,
                "price": quote.get("price"),
                "marketCap": quote.get("marketCap"),
                "name": profile.get("companyName") if profile else symbol,
                "sector": profile.get("sector") if profile else "Unknown",
                "exchange": quote.get("exchange"),
            }
            combined.append(record)
            logger.info("Fetched quote+profile for %s (mktcap=%.0f)", symbol, record["marketCap"] or 0)
        else:
            logger.warning("No quote for %s — skipping", symbol)
    return combined


def fetch_historical_prices(
    client: FMPClient, symbols: list[str], from_date: str, to_date: str
) -> list[str]:
    successful: list[str] = []
    for symbol in symbols:
        existing = list(BRONZE_DIR.glob(f"historical/{symbol}_{from_date}_{to_date}.json"))
        if existing:
            logger.info("Using cached historical for %s", symbol)
            successful.append(symbol)
            continue
        records = client.get_historical_prices(symbol, from_date, to_date)
        if records and len(records) >= 50:
            successful.append(symbol)
            logger.info("Fetched %d historical records for %s", len(records), symbol)
        else:
            logger.warning(
                "Insufficient historical data for %s (%d records)",
                symbol,
                len(records) if records else 0,
            )
    return successful


def run_fetch_pipeline() -> list[str]:
    client = FMPClient()

    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=HISTORICAL_DAYS + 40)).strftime("%Y-%m-%d")

    logger.info("Fetching quotes and profiles for %d symbols", len(SP500_TOP50))
    stock_info = fetch_quotes_and_profiles(client, SP500_TOP50)

    today = datetime.now().strftime("%Y-%m-%d")
    info_path = BRONZE_DIR / f"stock_info_{today}.json"
    with open(info_path, "w", encoding="utf-8") as fh:
        json.dump(stock_info, fh, indent=2)
    logger.info("Saved stock info for %d symbols", len(stock_info))

    symbols_with_quotes = [r["symbol"] for r in stock_info]

    logger.info("Fetching historical prices from %s to %s", from_date, to_date)
    successful_symbols = fetch_historical_prices(client, symbols_with_quotes, from_date, to_date)

    selected_path = BRONZE_DIR / "selected_symbols.json"
    with open(selected_path, "w", encoding="utf-8") as fh:
        json.dump(successful_symbols, fh, indent=2)

    total_calls = len(SP500_TOP50) * 2 + len(successful_symbols)
    logger.info(
        "Fetch pipeline complete. %d symbols with historical data. Approx %d API calls used.",
        len(successful_symbols),
        total_calls,
    )
    return successful_symbols


if __name__ == "__main__":
    run_fetch_pipeline()
