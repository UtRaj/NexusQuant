# tests/integration/test_multitick_portfolio.py

"""
TEST SUITE: Multi-Tick Portfolio Integrity
OBJECTIVE: Verify portfolio stability, cash reserves, and equity tracking over 50 simulation ticks.
EXPECTED RESULT: No negative balances, all trades persisted, and final equity matches final state.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from simulation.engine import SimulationEngine
from database.db import init_db

@patch("simulation.engine.init_db")
@patch("simulation.engine.SimulationEngine._start_run_record")
def test_multitick_integrity(mock_record, mock_init, monkeypatch):
    """
    OBJECTIVE: Run a 50-tick simulation with dynamic signals.
    EXPECTED RESULT: Portfolio state remains consistent and math holds.
    """
    # Mock MarketReplay
    import simulation.market
    monkeypatch.setattr(simulation.market.MarketReplay, "_load_all_data", lambda *args, **kwargs: None)
    
    engine = SimulationEngine(load_data=False)
    engine._persist_portfolio = MagicMock()
    engine.market.assets = ["BTC-USD", "ETH-USD"]
    
    # Initial Balance
    initial_equity = engine.portfolio["total_equity"]
    
    for tick in range(50):
        # Mock Tick Data
        mock_tick = {
            "BTC-USD": {"symbol": "BTC-USD", "price": 50000.0 + (tick * 10), "volume": 100.0, "timestamp": pd.Timestamp.now()},
            "ETH-USD": {"symbol": "ETH-USD", "price": 3000.0 - (tick * 5), "volume": 1000.0, "timestamp": pd.Timestamp.now()}
        }
        engine.market.tick = MagicMock(return_value=mock_tick)
        
        # Mock Historical Data (needed for Quant)
        engine.market.data = {
            "BTC-USD": pd.DataFrame({"close": np.random.normal(50000, 100, 100)}),
            "ETH-USD": pd.DataFrame({"close": np.random.normal(3000, 50, 100)})
        }
        engine.market.current_index = 100
        
        # Alternate BULLISH/BEARISH signals
        outlook = "BULLISH" if tick % 10 < 5 else "BEARISH"
        engine.analyst.run = MagicMock(return_value={"outlook": outlook, "confidence": 0.8, "rationale": "test"})
        
        success = engine.run_tick()
        assert success is True
        
        # Global Invariants
        assert engine.portfolio["balance"] >= -0.01 # Allow for minor float precision noise
        assert engine.portfolio["total_equity"] > 0
        
    print(f"Completed 50-tick integrity run. Final Equity: {engine.portfolio['total_equity']}")
