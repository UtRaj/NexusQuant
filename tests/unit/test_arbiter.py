# tests/unit/test_arbiter.py

"""
TEST SUITE: Decision Arbiter Logic
OBJECTIVE: Verify signal aggregation, weighting, and confidence gating.
EXPECTED RESULT: Normalized sentiment scores between -1.0 and 1.0.
"""

import pytest
from database.models import LLMAdvice
from utils.arbiter import DecisionArbiter

def test_aggregate_advice_basic():
    """
    OBJECTIVE: Verify basic bullish consensus moves score positively.
    EXPECTED RESULT: Score > 0 and reflects mean of inputs.
    """
    arbiter = DecisionArbiter(confidence_threshold=0.5, smoothing_factor=1.0)
    advice = [
        LLMAdvice(asset="BTC-USD", outlook="BULLISH", confidence=0.8, advisor_name="A1", rationale="test", tick_id=1, run_id="test"),
        LLMAdvice(asset="BTC-USD", outlook="BULLISH", confidence=0.6, advisor_name="A2", rationale="test", tick_id=1, run_id="test"),
    ]
    scores = arbiter.aggregate_advice(advice)
    assert scores["BTC-USD"] > 0
    assert 0.6 < scores["BTC-USD"] < 0.8

def test_aggregate_advice_mixed():
    """
    OBJECTIVE: Verify opposing signals result in 0.0 neutrality.
    EXPECTED RESULT: Score = 0.0.
    """
    arbiter = DecisionArbiter(confidence_threshold=0.5, smoothing_factor=1.0)
    advice = [
        LLMAdvice(asset="BTC-USD", outlook="BULLISH", confidence=0.8, advisor_name="A1", rationale="test", tick_id=1, run_id="test"),
        LLMAdvice(asset="BTC-USD", outlook="BEARISH", confidence=0.8, advisor_name="A2", rationale="test", tick_id=1, run_id="test"),
    ]
    scores = arbiter.aggregate_advice(advice)
    assert scores["BTC-USD"] == 0.0

def test_confidence_thresholding():
    """
    OBJECTIVE: Verify signals below confidence threshold are ignored.
    EXPECTED RESULT: Score = 0.0.
    """
    arbiter = DecisionArbiter(confidence_threshold=0.7)
    advice = [
        LLMAdvice(asset="ETH-USD", outlook="BULLISH", confidence=0.4, advisor_name="A1", rationale="test", tick_id=1, run_id="test"),
    ]
    scores = arbiter.aggregate_advice(advice)
    assert scores["ETH-USD"] == 0.0
