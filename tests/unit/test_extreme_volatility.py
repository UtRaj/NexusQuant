# tests/unit/test_extreme_volatility.py

"""
TEST SUITE: Extreme Volatility Resilience
OBJECTIVE: Verify that Risk Parity (Inverse Volatility Scaling) correctly collapses allocations during 10x volatility spikes.
EXPECTED RESULT: Allocation should drop significantly (70-90%) when vol spikes from 2% to 20%.
"""

import pytest
import numpy as np
from utils.allocator import CapitalAllocator

def test_extreme_vol_shock():
    """
    OBJECTIVE: Simulate a market crash (2% -> 20% vol).
    EXPECTED RESULT: Position size should be drastically reduced.
    """
    allocator = CapitalAllocator(reserve_pct=0.0, max_position_pct=1.0)
    scores = {"BTC": 1.0, "ETH": 1.0}
    equity = 100000.0
    
    # 1. Baseline (2% Vol for both)
    alloc1 = allocator.allocate(scores, {"BTC": 0.02, "ETH": 0.02}, equity)
    
    # 2. Extreme Shock (BTC Vol -> 20%, ETH stays at 2%)
    alloc2 = allocator.allocate(scores, {"BTC": 0.20, "ETH": 0.02}, equity)
    
    # BTC share calculation: (1/0.2) / (1/0.2 + 1/0.02) = 5 / (5 + 50) = 5/55 = ~9%
    # ETH share calculation: 50/55 = ~91%
    
    assert alloc2["BTC"] < alloc1["BTC"] * 0.2 # Should be way less than 20% of original
    assert np.isclose(alloc2["BTC"], (5/55) * equity, atol=1000)
    assert alloc2["ETH"] > alloc1["ETH"] # Capital flows to the safer asset
