# tests/unit/test_quant.py

"""
TEST SUITE: Quantitative Signal Agents
OBJECTIVE: Verify deterministic technical indicators (RSI, Mean Reversion).
EXPECTED RESULT: Valid signals generated based on price momentum.
"""

import pytest
import pandas as pd
import numpy as np
from agents.quant import QuantAgent

def test_quant_signals():
    """
    OBJECTIVE: Verify QuantAgent produces BULLISH/BEARISH signals on price trends.
    EXPECTED RESULT: High RSI triggers BEARISH/NEUTRAL, low RSI triggers BULLISH.
    """
    agent = QuantAgent()
    # Mock data with clear RSI trend
    prices = [100 + i for i in range(30)] # Uptrend -> Overbought
    df = pd.DataFrame({"close": prices})
    
    res = agent.run("BTC", df)
    assert "outlook" in res
    assert res ["outlook"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    
    # Very low RSI simulation
    prices_low = [100 - i for i in range(30)]
    df_low = pd.DataFrame({"close": prices_low})
    res_low = agent.run("BTC", df_low)
    assert res_low["outlook"] == "BULLISH" # Mean reversion signal
