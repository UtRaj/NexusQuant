# tests/conftest.py

import pytest
import os
import sys
from unittest.mock import MagicMock

# Ensure project root is in path for CI/subprocess environments
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.analyst import AnalystAgent

@pytest.fixture(autouse=True)
def mock_llm_agent(monkeypatch, request):
    """
    Globally mocks AnalystAgent.run to prevent real API calls in tests.
    To use a real call, mark the test with @pytest.mark.live_api
    """
    if "live_api" in request.keywords:
        return

    def mock_run(self, symbol, context=""):
        return {
            "outlook": "BULLISH",
            "confidence": 0.85,
            "reasoning": f"MOCK: Sentiment for {symbol} is strong based on technical indicators."
        }

    monkeypatch.setattr(AnalystAgent, "run", mock_run)

def pytest_configure(config):
    config.addinivalue_line("markers", "live_api: mark test to run against real LLM API")
