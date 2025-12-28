# config.py

import os
import uuid
import logging
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class SimulationConfig(BaseSettings):
    # === Project Identity ===
    PROJECT_NAME: str = "NexusQuant"
    VERSION: str = "3.0.0"
    RUN_ID: str = str(uuid.uuid4())[:8]
    
    # === PostgreSQL Connection ===
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nexusquant")
    

    # === Multi-Asset Universe (CORE ONLY) ===
    ASSET_UNIVERSE: List[str] = [
        "BTC-USD", "ETH-USD", "SOL-USD", # Crypto
        "AAPL", "MSFT", "NVDA", "TSLA",  # Tech
        "SPY", "QQQ", "GLD"               # Macro
    ]

    
    # === Capital & Allocation ===
    INITIAL_CAPITAL: float = 100000.0
    MAX_POSITION_PCT: float = 0.15       # Max 15% per single asset
    PORTFOLIO_CASH_RESERVE: float = 0.05 # Keep 5% in cash
    
    # === Risk Management ===
    MAX_DRAWDOWN_PCT: float = 0.15
    VOLATILITY_LOOKBACK: int = 20        # Ticks for vol calculation
    
    # === LLM Advisory ===
    LLM_COOLDOWN_TICKS: int = 20         # Min ticks between advisor calls
    LLM_COOLDOWN_SECONDS: int = 300      # 5 minute cooldown (legacy/real-time)
    CONFIDENCE_THRESHOLD: float = 0.6    # Advisor threshold
    
    # === Execution ===
    SYMBOL: str = "BTC-USD"              # Legacy support
    TIMEFRAME: str = "5m"
    HISTORY_DAYS: int = 30
    
    model_config = {"env_prefix": "ALPHAPULSE_"}

config = SimulationConfig()
