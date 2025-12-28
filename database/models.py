import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

class SimulationRun(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], primary_key=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    config_snapshot: Dict[str, Any] = Field(sa_column=Column(JSON))
    status: str = "RUNNING"

class MarketData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    tick_id: int
    symbol: str = Field(index=True)
    price: float
    volume: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LLMAdvice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    tick_id: int
    asset: str
    advisor_name: str
    outlook: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float
    rationale: str
    raw_response: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PortfolioState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    tick_id: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    balance: float
    holdings: Dict[str, float] = Field(sa_column=Column(JSON))
    total_equity: float
    unrealized_pnl: float = 0.0
    max_drawdown: float = 0.0

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    tick_id: int
    symbol: str
    side: str 
    quantity: float
    filled_price: float
    status: str 
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserPolicy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    policy_type: str  # RISK_LIMIT, ASSET_EXCLUSION, etc.
    value: Dict[str, Any] = Field(sa_column=Column(JSON))
    active_from: datetime
    active_until: Optional[datetime] = None
