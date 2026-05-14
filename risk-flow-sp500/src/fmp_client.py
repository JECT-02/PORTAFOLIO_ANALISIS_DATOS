import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

from src.config import API_KEY, BASE_URL, BRONZE_DIR, RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)


class FMPClient:
    def __init__(
        self,
        api_key: str = API_KEY,
        base_url: str = BASE_URL,
        rate_limit_delay: float = RATE_LIMIT_DELAY,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()

    def _request(self, path: str, params: dict | None = None) -> dict | list | None:
        url = f"{self.base_url}{path}"
        query_params = {"apikey": self.api_key}
        if params:
            query_params.update(params)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(self.rate_limit_delay)
                response = self.session.get(url, params=query_params, timeout=30)
                if response.status_code == 402:
                    logger.error("Endpoint restricted for free plan: %s", url)
                    return None
                if response.status_code != 200:
                    logger.warning(
                        "HTTP %s for %s (attempt %d/%d)",
                        response.status_code,
                        url,
                        attempt + 1,
                        max_retries,
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    continue
                data = response.json()
                if isinstance(data, list) and len(data) == 0:
                    logger.warning("Empty response from %s", url)
                    return None
                if isinstance(data, dict) and "Error Message" in data:
                    logger.error("API error from %s: %s", url, data["Error Message"])
                    return None
                return data
            except requests.exceptions.RequestException as exc:
                logger.error("Request failed for %s: %s", url, exc)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _save_bronze(self, filename: str, data: dict | list) -> None:
        target_path = BRONZE_DIR / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2)
        logger.info("Saved bronze: %s", target_path)

    def get_quote(self, symbol: str) -> dict | None:
        data = self._request("/quote", params={"symbol": symbol})
        if data is None:
            return None
        record = data[0] if isinstance(data, list) and data else data
        return record

    def get_profile(self, symbol: str) -> dict | None:
        data = self._request("/profile", params={"symbol": symbol})
        if data is None:
            return None
        return data[0] if isinstance(data, list) and data else data

    def get_historical_prices(
        self, symbol: str, from_date: str, to_date: str
    ) -> list[dict] | None:
        data = self._request(
            "/historical-price-eod/full",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )
        if data is None:
            logger.warning("No historical data for %s", symbol)
            return None
        records = data if isinstance(data, list) else [data]
        filename = f"historical/{symbol}_{from_date}_{to_date}.json"
        self._save_bronze(filename, records)
        return records
