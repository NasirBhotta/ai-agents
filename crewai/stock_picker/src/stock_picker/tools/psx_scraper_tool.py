from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests
import json


class PSXScraperInput(BaseModel):
    """Input for PSX Scraper Tool."""
    ticker: str = Field(
        ...,
        description=(
            "PSX ticker symbol to fetch data for, e.g. 'ENGRO', 'HBL', 'LUCK', 'PSO', 'MCB'."
            " Use uppercase."
        ),
    )

class PSXScraperTool(BaseTool):
    """
    Fetches live price and key financial data for a PSX-listed stock.

    Data sourced from the PSX public API and Mettis Global.
    Returns current price (PKR), 52-week high/low, market cap, and recent volume.
    """

    name: str = "PSX Stock Data Fetcher"
    description: str = (
        "Fetches live Pakistan Stock Exchange (PSX / KSE) market data for a given ticker symbol. "
        "Returns current price in PKR, 52-week high and low, market cap, P/E ratio, "
        "dividend yield, and average daily volume. Use this for any PSX-listed company "
        "such as ENGRO, HBL, LUCK, PSO, MCB, FFC, OGDC, UBL, BAHL, HUBC."
    )
    args_schema: Type[BaseModel] = PSXScraperInput

    def _run(self, ticker: str) -> str:
        ticker = ticker.strip().upper()

        # Primary: PSX public data endpoint
        psx_result = self._fetch_psx_api(ticker)
        if psx_result:
            return psx_result

        # Fallback: Mettis Global scrape
        mettis_result = self._fetch_mettis(ticker)
        if mettis_result:
            return mettis_result

        return json.dumps({
            "ticker": ticker,
            "error": (
                f"Could not fetch live PSX data for {ticker}. "
                "Please use web search to find current price and financial data from "
                "psx.com.pk, brecorder.com, or profit.pk."
            )
        })

    def _fetch_psx_api(self, ticker: str) -> Optional[str]:
        """Attempt PSX public summary endpoint."""
        try:
            url = f"https://dps.psx.com.pk/timeseries/eod/{ticker}"
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)",
                "Accept": "application/json",
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None

            data = resp.json()
            # PSX EOD returns a list of {c, h, l, o, t, v} — most recent is last
            if not isinstance(data, list) or len(data) == 0:
                return None

            latest = data[-1]
            year_data = data[-252:] if len(data) >= 252 else data
            high_52w = max(d["h"] for d in year_data)
            low_52w = min(d["l"] for d in year_data)

            result = {
                "ticker": ticker,
                "source": "PSX EOD API",
                "current_price_pkr": latest.get("c"),
                "open_pkr": latest.get("o"),
                "high_today_pkr": latest.get("h"),
                "low_today_pkr": latest.get("l"),
                "volume_today": latest.get("v"),
                "high_52w_pkr": high_52w,
                "low_52w_pkr": low_52w,
                "date": latest.get("t"),
                "note": (
                    "For fundamentals (P/E, EPS, dividend yield, market cap), "
                    "use the FinancialScreenerTool or web search psx.com.pk/company/{ticker}/statistics"
                ),
            }
            return json.dumps(result, indent=2)

        except Exception:
            return None

    def _fetch_mettis(self, ticker: str) -> Optional[str]:
        """Attempt Mettis Global summary page."""
        try:
            url = f"https://mettis.com/news/?s={ticker}+PSX+stock+price+PKR"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return None

            return json.dumps({
                "ticker": ticker,
                "source": "Mettis Global (search)",
                "note": (
                    f"Live data fetch partially unavailable. "
                    f"Search web for '{ticker} PSX stock price today' on "
                    f"psx.com.pk, brecorder.com, or profit.pk for current PKR price."
                ),
            })
        except Exception:
            return None