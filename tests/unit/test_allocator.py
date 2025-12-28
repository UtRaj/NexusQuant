# tests/unit/test_allocator.py

"""
TEST SUITE: Capital Allocation Engine
OBJECTIVE: Verify Risk Parity (Inverse Volatility) and position capping.
EXPECTED RESULT: Capital is concentrated in low-volatility, high-confidence assets.
"""

import pytest
from utils.allocator import CapitalAllocator

def test_risk_parity_allocation():
    """
    OBJECTIVE: Verify assets with half the volatility get double the allocation.
    EXPECTED RESULT: Linear inverse relationship.
    """
    # Set high cap (0.8) so it doesn't interfere with the 2x ratio expectation
    allocator = CapitalAllocator(max_position_pct=0.8, reserve_pct=0.0)
    scores = {"BTC": 1.0, "ETH": 1.0}
    vols = {"BTC": 0.02, "ETH": 0.04}
    equity = 100000.0
    
    allocs = allocator.allocate(scores, vols, equity)
    
    # BTC is half as volatile as ETH, so it should get ~2x the weight
    assert allocs["BTC"] > allocs["ETH"]
    assert round(allocs["BTC"] / allocs["ETH"]) == 2

def test_max_position_cap():
    """
    OBJECTIVE: Verify that no single asset exceeds the MAX_POSITION_PCT limit.
    EXPECTED RESULT: Allocation <= 10% of total equity.
    """
    allocator = CapitalAllocator(max_position_pct=0.1)
    scores = {"BTC": 1.0}
    vols = {"BTC": 0.02}
    equity = 100000.0
    
    allocs = allocator.allocate(scores, vols, equity)
    assert allocs["BTC"] <= 10000.0 # 10% of 100k

def test_zero_sentiment():
    """
    OBJECTIVE: Verify that assets with neutral/bearish sentiment get zero capital.
    EXPECTED RESULT: Allocation = 0.0.
    """
    allocator = CapitalAllocator()
    scores = {"BTC": 0.0}
    vols = {"BTC": 0.02}
    allocs = allocator.allocate(scores, vols, 100000)
    assert allocs["BTC"] == 0.0
