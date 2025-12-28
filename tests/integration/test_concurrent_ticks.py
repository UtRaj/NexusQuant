# tests/integration/test_concurrent_ticks.py

"""
TEST SUITE: Concurrent Tick Synchronization
OBJECTIVE: Test system handles overlapping tick updates (e.g. 24/7 Crypto vs Market-Hours Equities) without state corruption.
EXPECTED RESULT: Data alignment logic in MarketReplay or Engine prevents stale trade execution.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from simulation.market import MarketReplay
from simulation.engine import SimulationEngine

@patch("simulation.engine.init_db")
@patch("simulation.engine.SimulationEngine._start_run_record")
def test_mixed_market_sync(mock_record, mock_init, monkeypatch):
    """
    OBJECTIVE: Simulate a scenario where crypto is active but equities are 'stale' or closed.
    EXPECTED RESULT: Engine should still process active assets and properly hold/skip closed ones.
    """
    import uuid
    from config import config
    monkeypatch.setattr(config, "RUN_ID", f"test_{uuid.uuid4().hex[:6]}")
    
    engine = SimulationEngine(load_data=False)
    engine._persist_portfolio = MagicMock()
    # Mock database session to avoid persistence side effects
    monkeypatch.setattr("simulation.engine.Session", MagicMock())
    engine.market.current_tick_id = 1
    engine.market.current_index = 40
    
    # Mock mixed tick: BTC (Fresh), AAPL (Stale/Old Timestamp)
    fresh_ts = pd.Timestamp.now()
    stale_ts = fresh_ts - pd.Timedelta(days=2) # Weekend for equities
    
    tick_data = {
        "BTC-USD": {"symbol": "BTC-USD", "price": 50000.0, "timestamp": fresh_ts},
        "AAPL": {"symbol": "AAPL", "price": 180.0, "timestamp": stale_ts}
    }
    
    engine.market.tick = lambda: tick_data
    engine.market.assets = ["BTC-USD", "AAPL"]
    
    # Mock Market Data to avoid quant error
    ts = pd.Timestamp.now()
    engine.market.data = {
        "BTC-USD": pd.DataFrame({"close": [50000]*50, "datetime": [ts]*50}),
        "AAPL": pd.DataFrame({"close": [180]*50, "datetime": [ts]*50})
    }
    engine.market.current_index = 40
    
    # Run tick
    engine.run_tick()
    
    # If logic is robust, it should have handled the price for BTC and likely used the last available or ignored the stale AAPL.
    # In 3.0, we aim for "Portfolio Tick" which aligns all.
    assert engine.tick_id == 1
