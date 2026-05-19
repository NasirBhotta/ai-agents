#!/usr/bin/env python
"""
PSX Stock Picker — Pakistan Stock Exchange Investment Research Agent
====================================================================
A hierarchical multi-agent CrewAI system that:
  1. Scans Pakistani financial news for KSE-100 trending stocks
  2. Analyzes Pakistan's macroeconomic environment (SBP rates, PKR, IMF)
  3. Conducts deep fundamental analysis of shortlisted companies
  4. Performs technical analysis with PSX-specific signals
  5. Assesses Pakistan-specific investment risks (currency, political, IMF)
  6. Synthesizes all research into a scored final recommendation

Supported sectors:
  Technology, Banking, Cement, Fertiliser, Oil & Gas, Textile,
  Power, Automobile, Food & Beverages, Pharma, General (all sectors)
"""

import sys
import warnings
import os
from datetime import datetime

from stock_picker.crew import StockPicker

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


# ── Configuration ───────────────────────────────────────────────────────────────

# Set to a specific PSX sector or "General" to scan across all KSE-100 sectors.
# Valid options: Technology, Banking, Cement, Fertiliser, Oil & Gas Exploration,
#                Oil Marketing, Textile, Power Generation, Automobile Assembler,
#                Food & Beverages, Pharma, Chemical, General
TARGET_SECTOR = os.getenv("PSX_SECTOR", "General")


# ── Output directory ────────────────────────────────────────────────────────────

def ensure_output_dir() -> None:
    os.makedirs("output", exist_ok=True)


# ── Main ────────────────────────────────────────────────────────────────────────

def run() -> None:
    """
    Run the PSX Stock Picker research crew.

    Environment variables:
      PSX_SECTOR          - Target PSX sector (default: General)
      OPENAI_API_KEY      - Required for LLM calls (gpt-4o-mini / gpt-4o)
      SERPER_API_KEY      - Required for SerperDevTool web search
      PUSHOVER_USER       - Required for push notifications
      PUSHOVER_TOKEN      - Required for push notifications
    """
    ensure_output_dir()

    inputs = {
        "sector": TARGET_SECTOR,
        "current_date": datetime.now().strftime("%A, %d %B %Y"),
        # Placeholder; will be populated by macro task output
        "macro_environment": "Refer to macro analysis task output.",
    }

    print("\n" + "=" * 60)
    print("  PSX STOCK PICKER — PAKISTAN EQUITY RESEARCH AGENT")
    print("=" * 60)
    print(f"  Target sector : {TARGET_SECTOR}")
    print(f"  Run date      : {inputs['current_date']}")
    print(f"  Exchange      : Pakistan Stock Exchange (KSE-100 / KSE-30)")
    print("=" * 60 + "\n")

    result = StockPicker().crew().kickoff(inputs=inputs)

    print("\n" + "=" * 60)
    print("  FINAL INVESTMENT DECISION")
    print("=" * 60 + "\n")
    print(result.raw)
    print("\n" + "=" * 60)
    print("  Full reports saved to: output/")
    print("  • output/trending_stocks.json   — KSE trending companies")
    print("  • output/macro_report.json      — Pakistan macro analysis")
    print("  • output/financial_research.json — Fundamental analysis")
    print("  • output/technical_analysis.json — Technical signals")
    print("  • output/risk_assessment.json   — Pakistan risk assessment")
    print("  • output/decision.md            — Final investment report")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run()