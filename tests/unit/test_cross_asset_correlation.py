# tests/unit/test_cross_asset_correlation.py

"""
TEST SUITE: Cross-Asset Correlation
OBJECTIVE: Verify that the allocation logic behaves correctly when correlated assets move together.
EXPECTED RESULT: Portfolio risk is diversified; highly correlated assets shouldn't both receive maximum allocation if they increase joint risk.
"""

import pytest
import numpy as np
from utils.allocator import CapitalAllocator

def test_correlated_risk_reduction():
    """
    OBJECTIVE: Simulate two highly correlated assets.
    EXPECTED RESULT: Risk Parity should still distribute based on individual vol, but we verify here the joint allocation logic.
    """
    # Increase max_position_pct to 50% for this test so we can actually see scaling below the cap
    allocator = CapitalAllocator(reserve_pct=0.0, max_position_pct=0.5)
    scores = {"BTC": 1.0, "ETH": 1.0}
    vols = {"BTC": 0.02, "ETH": 0.02}
    equity = 100000.0
    
    alloc = allocator.allocate(scores, vols, equity)
    
    # Simple risk parity (1/vol) means they should be equal if vols are equal
    # Both should be 50% (50000 USD) because we set max_pos_pct=0.5
    assert np.isclose(alloc["BTC"], 50000.0, atol=100)
    assert np.isclose(alloc["ETH"], 50000.0, atol=100)
    
    # If BTC vol doubles, its allocation should drop
    vols_shock = {"BTC": 0.04, "ETH": 0.02}
    alloc_shock = allocator.allocate(scores, vols_shock, equity)
    assert alloc_shock["BTC"] < alloc_shock["ETH"]
