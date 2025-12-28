# tests/unit/test_missing_data_handling.py

"""
TEST SUITE: Fault Tolerance (Missing Data)
OBJECTIVE: Ensure the engine handles NaNs, missing assets, and corrupted advisor outputs without crashing.
EXPECTED RESULT: System defaults to NEUTRAL/0.0 for bad data and continues processing.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from simulation.engine import SimulationEngine

@patch("simulation.engine.init_db")
@patch("simulation.engine.SimulationEngine._start_run_record")
def test_nan_price_handling(mock_record, mock_init):
    """
    OBJECTIVE: Provide NaN prices in tick data.
    EXPECTED RESULT: Engine should handle it gracefully (likely skipping or using last price).
    """
    engine = SimulationEngine(load_data=False)
    engine._persist_portfolio = MagicMock() # Avoid DB
    engine.market = MagicMock()
    engine.market.assets = ["BTC-USD"]
    engine.market.current_tick_id = 1
    engine.market.current_index = 40
    engine.tick_id = 1
    
    # Corrupted Tick
    tick_data = {
        "BTC-USD": {"symbol": "BTC-USD", "price": float('nan'), "volume": 0.0, "timestamp": pd.Timestamp.now()}
    }
    engine.market.tick = MagicMock(return_value=tick_data)
    engine.market.data = {"BTC-USD": MagicMock()}
    
    # This shouldn't crash
    try:
        engine.run_tick()
    except Exception as e:
        pytest.fail(f"Engine crashed on NaN price: {e}")

@patch("simulation.engine.init_db")
@patch("simulation.engine.SimulationEngine._start_run_record")
def test_corrupted_analyst_output(mock_record, mock_init):
    """
    OBJECTIVE: Mock analyst returning malformed dict.
    EXPECTED RESULT: Engine uses safe defaults.
    """
    engine = SimulationEngine(load_data=False)
    engine._persist_portfolio = MagicMock()
    engine.market.assets = ["BTC-USD"]
    engine.tick_id = 1 # Force analyst call
    engine.last_analyst_call = {}
    
    # Mock Market Data to avoid quant error
    engine.market.data = {"BTC-USD": pd.DataFrame({
        "close": [50000]*50,
        "volume": [100]*50,
        "datetime": [pd.Timestamp.now()]*50
    })}
    engine.market.current_index = 40
    
    # Corrupted Response
    engine.analyst.run = MagicMock(return_value={"garbage": "data"})
    
    engine.run_tick()
    # If it didn't crash, it passed the fault tolerance check
