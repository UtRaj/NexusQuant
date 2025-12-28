# tests/integration/test_engine_flow.py

"""
TEST SUITE: End-to-End Simulation Flow
OBJECTIVE: Verify the full multi-asset pipeline (Data -> Advice -> Logic -> Order).
EXPECTED RESULT: A single tick completes with valid portfolio updates and trade orders.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock
from simulation.engine import SimulationEngine
from database.db import init_db

def test_simulation_engine_mini_run(monkeypatch):
    """
    OBJECTIVE: Execute a mocked simulation tick and verify order generation.
    EXPECTED RESULT: Portfolio equity is calculated and holdings are updated.
    """
    # Setup
    import uuid
    from config import config
    config.RUN_ID = f"test_{uuid.uuid4().hex[:6]}"
    init_db()
    
    # Mock MarketReplay to avoid data loading in __init__
    import simulation.market
    monkeypatch.setattr(simulation.market.MarketReplay, "_load_all_data", lambda *args, **kwargs: None)
    
    engine = SimulationEngine()
    
    # Mock Market Data for 2 assets
    mock_tick = {
        "BTC-USD": {"symbol": "BTC-USD", "price": 50000.0, "volume": 100.0, "timestamp": pd.Timestamp.now()},
        "ETH-USD": {"symbol": "ETH-USD", "price": 3000.0, "volume": 1000.0, "timestamp": pd.Timestamp.now()}
    }
    
    # Override market.tick to return our mock
    engine.market.tick = MagicMock(return_value=mock_tick)
    engine.market.data = {
        "BTC-USD": pd.DataFrame({"close": [50000, 50100], "volume": [100, 101]}),
        "ETH-USD": pd.DataFrame({"close": [3000, 3050], "volume": [1000, 1005]})
    }
    engine.market.current_index = 1
    engine.market.assets = ["BTC-USD", "ETH-USD"]
    
    # Mock Analyst to avoid API calls
    engine.analyst.run = MagicMock(return_value={"outlook": "BULLISH", "confidence": 0.9, "rationale": "mock"})
    
    # Run 1 tick
    success = engine.run_tick()
    assert success is True
    
    # Verify Portfolio State
    assert engine.portfolio["total_equity"] >= 100000.0
    assert "BTC-USD" in engine.portfolio["holdings"]
    
    print("End-to-End Mini-Run Passed.")
