# tests/unit/test_llm_cooldown.py

"""
TEST SUITE: LLM Cooldown Integrity
OBJECTIVE: Confirm repeated LLM advice within the cooldown window does not trigger new LLM analyst calls.
EXPECTED RESULT: Analyst run() should only be called once if within the cooldown tick window.
"""

import pytest
from unittest.mock import MagicMock, patch
from simulation.engine import SimulationEngine
from config import config

@patch("simulation.engine.init_db")
@patch("simulation.engine.SimulationEngine._start_run_record")
def test_llm_cooldown_logic(mock_record, mock_init):
    """
    OBJECTIVE: Verify that consecutive ticks within the cooldown period do not trigger the LLM analyst.
    EXPECTED RESULT: Analyst.run() called exactly once for 2 ticks if cooldown is 20.
    """
    # Force cooldown to something predictable
    config.LLM_COOLDOWN_TICKS = 10
    
    engine = SimulationEngine(load_data=False)
    engine.market = MagicMock()
    engine.market.assets = ["BTC-USD"]
    engine.market.current_tick_id = 0
    engine.market.current_index = 10
    engine.tick_id = 0
    
    # Mock tick data
    tick_data = {
        "BTC-USD": {"symbol": "BTC-USD", "price": 50000.0}
    }
    engine.market.tick = MagicMock(return_value=tick_data)
    engine.market.data = {"BTC-USD": MagicMock()} # Placeholder for quant
    
    # Mock Analyst
    engine.analyst.run = MagicMock(return_value={"outlook": "BULLISH", "confidence": 0.8, "reasoning": "test"})
    
    # Mock Quant to avoid issues
    engine.quant.run = MagicMock(return_value={"outlook": "BULLISH", "confidence": 0.5, "reasoning": "q"})
    
    # Mock rebalance and persist to avoid DB/Execution overhead
    engine._execute_rebalance = MagicMock()
    engine._persist_portfolio = MagicMock()
    engine._start_run_record = MagicMock()

    # Tick 0: Should trigger LLM
    engine.run_tick()
    assert engine.analyst.run.call_count == 1
    
    # Tick 1: Should NOT trigger LLM (within 10 ticks)
    engine.tick_id = 1
    engine.run_tick()
    assert engine.analyst.run.call_count == 1
    
    # Tick 10: SHOULD trigger LLM
    engine.tick_id = 11 # 11 - 1 = 10 (>= 10)
    engine.market.current_tick_id = 11
    engine.run_tick()
    assert engine.analyst.run.call_count == 2
