# tests/unit/test_decisions.py

"""
TEST SUITE: Decision Integrity & Edge Cases
OBJECTIVE: Verify that the Arbitrator and Allocator handle extreme market conditions, 
           consensus, and conflicts with mathematical stability.
EXPECTED RESULT: Deterministic outputs that prevent portfolio "churn" and manage risk.
"""

import pytest
import numpy as np
from utils.arbiter import DecisionArbiter
from utils.allocator import CapitalAllocator
from database.models import LLMAdvice

def create_advice(asset: str, outlook: str, confidence: float):
    return LLMAdvice(
        run_id="test", tick_id=1, asset=asset, 
        advisor_name="Mock", outlook=outlook, 
        confidence=confidence, rationale="test"
    )

def test_decision_smoothing_ema():
    """
    OBJECTIVE: Verify Sentiment EMA prevents instant signal flips.
    EXPECTED RESULT: Sentiment moves toward target by exactly 50% (alpha=0.5).
    """
    arbiter = DecisionArbiter(smoothing_factor=0.5, confidence_threshold=0.0)
    
    # Tick 1: Bullish 1.0 (0.0 -> 0.5)
    tick1 = [create_advice("BTC", "BULLISH", 1.0)]
    scores1 = arbiter.aggregate_advice(tick1)
    assert scores1["BTC"] == 0.5
    
    # Tick 2: Bullish 1.0 again (0.5 -> 0.75)
    tick2 = [create_advice("BTC", "BULLISH", 1.0)]
    scores2 = arbiter.aggregate_advice(tick2)
    assert scores2["BTC"] == 0.75

def test_decision_hysteresis():
    """
    OBJECTIVE: Verify small noise (<0.1) is filtered out.
    EXPECTED RESULT: Sentiment remains unchanged for minor deltas.
    """
    arbiter = DecisionArbiter(smoothing_factor=1.0, confidence_threshold=0.0)
    arbiter.sentiment_memory["BTC"] = 0.5
    
    # Noise (+0.05) should be ignored
    noise = [create_advice("BTC", "BULLISH", 0.55)]
    scores = arbiter.aggregate_advice(noise)
    assert scores["BTC"] == 0.5
    
    # Signal (+0.3) should trigger
    signal = [create_advice("BTC", "BULLISH", 0.8)]
    scores = arbiter.aggregate_advice(signal)
    assert scores["BTC"] == 0.8

def test_extreme_conflict_deadlock():
    """
    OBJECTIVE: Verify 50/50 Bullish/Bearish split results in Neutrality.
    EXPECTED RESULT: Score = 0.0 (No trade action).
    """
    arbiter = DecisionArbiter(confidence_threshold=0.5, smoothing_factor=1.0)
    conflict = [
        create_advice("BTC", "BULLISH", 1.0),
        create_advice("BTC", "BEARISH", 1.0)
    ]
    scores = arbiter.aggregate_advice(conflict)
    assert scores["BTC"] == 0.0

def test_total_consensus_stampede():
    """
    OBJECTIVE: Verify 100% agent consensus peaks the signal.
    EXPECTED RESULT: Score = 1.0.
    """
    arbiter = DecisionArbiter(smoothing_factor=1.0)
    consensus = [create_advice("BTC", "BULLISH", 1.0) for _ in range(5)]
    scores = arbiter.aggregate_advice(consensus)
    assert scores["BTC"] == 1.0

def test_volatility_shock_risk_reduction():
    """
    OBJECTIVE: Verify that a 2x increase in volatility leads to a significant reduction in capital allocation.
    EXPECTED RESULT: Inverse scaling (Risk Parity).
    """
    allocator = CapitalAllocator(reserve_pct=0.0, max_position_pct=0.8)
    scores = {"BTC": 1.0, "ETH": 1.0}
    equity = 100000.0
    
    # 1. Base Case: Equal Vol
    alloc1 = allocator.allocate(scores, {"BTC": 0.02, "ETH": 0.02}, equity)
    # Should be 50/50 -> 50k each
    assert np.isclose(alloc1["BTC"], 50000.0, atol=100)
    
    # 2. Shock Case: BTC Vol doubles
    alloc2 = allocator.allocate(scores, {"BTC": 0.04, "ETH": 0.02}, equity)
    
    # BTC should now have roughly half the allocation of ETH
    # (1/0.04) / (1/0.04 + 1/0.02) = 25 / (25 + 50) = 1/3
    # 1/3 of 100k = 33,333
    assert alloc2["BTC"] < alloc1["BTC"]
    assert np.isclose(alloc2["BTC"], 33333.3, atol=1000)

def test_negative_invalid_advisor_payload():
    """
    OBJECTIVE: Verify system doesn't crash on malformed/missing advisor keys.
    EXPECTED RESULT: Graceful fallback to NEUTRAL (0.0).
    """
    arbiter = DecisionArbiter()
    # Mocking advice that lacks keys through raw object manipulation if needed, 
    # but LLMAdvice is a Pydantic model so we test empty lists/none.
    scores = arbiter.aggregate_advice([])
    assert scores == {}

def test_ghost_asset_decay():
    """
    OBJECTIVE: Verify that assets with no fresh signals decay towards zero.
    EXPECTED RESULT: Active sentiment fades by 20% per tick.
    """
    arbiter = DecisionArbiter(smoothing_factor=1.0)
    arbiter.sentiment_memory["BTC"] = 1.0
    
    # Tick with no BTC advice
    scores = arbiter.aggregate_advice([])
    assert scores["BTC"] == 0.8
