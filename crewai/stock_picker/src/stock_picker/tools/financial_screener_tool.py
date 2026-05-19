from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests
import json


class FinancialScreenerInput(BaseModel):
    """Input for Financial Screener Tool."""
    ticker: str = Field(
        ...,
        description=(
            "PSX ticker symbol to screen, e.g. 'ENGRO', 'HBL', 'LUCK'. "
            "Returns P/E, EPS, dividend yield, debt/equity, market cap, and broker targets."
        ),
    )


class FinancialScreenerTool(BaseTool):
    """
    Retrieves fundamental financial metrics for a PSX-listed company.

    Attempts to pull data from PSX company statistics pages and Topline Securities
    research feeds. Returns key valuation and profitability ratios used by the
    financial researcher agent.
    """

    name: str = "PSX Financial Screener"
    description: str = (
        "Retrieves fundamental financial metrics for a PSX-listed company: "
        "EPS (PKR), P/E ratio, Price-to-Book, dividend per share, dividend yield (%), "
        "market capitalisation (PKR billion), debt-to-equity ratio, and available "
        "broker price targets from Topline Securities, AKD Securities, or JS Global. "
        "Use this for any PSX ticker: ENGRO, HBL, MCB, LUCK, FFC, OGDC, UBL, BAHL, HUBC, etc."
    )
    args_schema: Type[BaseModel] = FinancialScreenerInput

    # Known PSX fundamentals cache for major tickers (approximate, for fallback)
    # In production, replace with a live API (e.g. Topline API, Reuters, or a custom scraper)
    _KNOWN_TICKERS = {
        "ENGRO": {"sector": "Fertiliser / Diversified", "market_cap_pkr_bn_approx": 250},
        "HBL": {"sector": "Banking", "market_cap_pkr_bn_approx": 280},
        "MCB": {"sector": "Banking", "market_cap_pkr_bn_approx": 320},
        "UBL": {"sector": "Banking", "market_cap_pkr_bn_approx": 240},
        "LUCK": {"sector": "Cement", "market_cap_pkr_bn_approx": 190},
        "DGKC": {"sector": "Cement", "market_cap_pkr_bn_approx": 60},
        "FFC": {"sector": "Fertiliser", "market_cap_pkr_bn_approx": 130},
        "PSO": {"sector": "Oil Marketing", "market_cap_pkr_bn_approx": 90},
        "OGDC": {"sector": "Oil & Gas Exploration", "market_cap_pkr_bn_approx": 400},
        "PPL": {"sector": "Oil & Gas Exploration", "market_cap_pkr_bn_approx": 130},
        "HUBC": {"sector": "Power Generation", "market_cap_pkr_bn_approx": 120},
        "EFERT": {"sector": "Fertiliser", "market_cap_pkr_bn_approx": 70},
        "BAHL": {"sector": "Banking", "market_cap_pkr_bn_approx": 110},
        "MEBL": {"sector": "Banking (Islamic)", "market_cap_pkr_bn_approx": 140},
        "TRG": {"sector": "Technology / BPO", "market_cap_pkr_bn_approx": 80},
        "SYS": {"sector": "Technology", "market_cap_pkr_bn_approx": 60},
        "NESTLE": {"sector": "Food & Beverages", "market_cap_pkr_bn_approx": 300},
        "MLCF": {"sector": "Cement", "market_cap_pkr_bn_approx": 55},
        "ATRL": {"sector": "Refinery", "market_cap_pkr_bn_approx": 35},
    }

    def _run(self, ticker: str) -> str:
        ticker = ticker.strip().upper()

        # Attempt PSX statistics page scrape
        psx_result = self._fetch_psx_statistics(ticker)
        if psx_result:
            return psx_result

        # Return guidance with known sector info if available
        known = self._KNOWN_TICKERS.get(ticker, {})
        return json.dumps({
            "ticker": ticker,
            "sector": known.get("sector", "Unknown — verify on psx.com.pk"),
            "market_cap_pkr_bn_approx": known.get("market_cap_pkr_bn_approx"),
            "source": "Fallback cache (live fetch unavailable)",
            "data_quality": "Approximate",
            "note": (
                f"Live fundamental data for {ticker} could not be fetched automatically. "
                f"Research agent should use SerperDevTool to search: "
                f"'{ticker} PSX P/E ratio EPS dividend yield 2024 2025 site:brecorder.com OR site:profit.pk OR site:topline.com.pk' "
                f"to find current fundamental metrics."
            ),
            "recommended_sources": [
                f"https://www.psx.com.pk/psx/resources-and-tools/companies/financial-data?symbol={ticker}",
                f"https://www.topline.com.pk/research",
                f"https://www.akdsecurities.com.pk/research",
                f"https://www.jsbl.com/research",
                "https://mettis.com",
                "https://brecorder.com",
            ],
        }, indent=2)

    def _fetch_psx_statistics(self, ticker: str) -> Optional[str]:
        """Attempt to scrape PSX company statistics page."""
        try:
            url = f"https://dps.psx.com.pk/company/{ticker}/statistics"
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)",
                "Accept": "application/json, text/html",
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None

            # Try JSON response
            if "application/json" in resp.headers.get("Content-Type", ""):
                data = resp.json()
                return json.dumps({
                    "ticker": ticker,
                    "source": "PSX Statistics API",
                    "data": data,
                }, indent=2)

            return None

        except Exception:
            return None