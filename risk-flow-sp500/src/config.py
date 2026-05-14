from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_KEY: str = os.getenv("API_KEY", "")
BASE_URL: str = "https://financialmodelingprep.com/stable"

MAX_STOCKS: int = 50
HISTORICAL_DAYS: int = 252
SIMULATION_HORIZONS: list[int] = [1, 5, 20]
CONFIDENCE_LEVELS: list[float] = [0.90, 0.95, 0.99]
N_SCENARIOS: int = 10000
BATCH_SIZE_QUOTES: int = 1
BATCH_SIZE_HISTORICAL: int = 1
RATE_LIMIT_DELAY: float = 0.35

DATA_DIR: Path = Path(__file__).resolve().parents[1] / "data"
BRONZE_DIR: Path = DATA_DIR / "bronze"
SILVER_DIR: Path = DATA_DIR / "silver"
GOLD_DIR: Path = DATA_DIR / "gold"

SP500_TOP50: list[str] = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META",
    "GOOGL", "BRK-B", "TSLA", "AVGO", "JPM",
    "LLY", "UNH", "V", "XOM", "MA",
    "COST", "HD", "PG", "JNJ", "ABBV",
    "WMT", "BAC", "NFLX", "CRM", "ORCL",
    "CVX", "MRK", "KO", "AMD", "PEP",
    "TMO", "ACN", "CSCO", "LIN", "ABT",
    "MCD", "TXN", "ADBE", "NEE", "PM",
    "DIS", "QCOM", "WFC", "IBM", "GE",
    "INTU", "AMGN", "RTX", "SPGI", "CAT",
]

for _dir in (BRONZE_DIR / "historical", SILVER_DIR, GOLD_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
