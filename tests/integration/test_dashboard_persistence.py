# tests/integration/test_dashboard_persistence.py

"""
TEST SUITE: Dashboard Persistence
OBJECTIVE: Validate that DB, log, and dashboard states are consistent across simulation ticks.
EXPECTED RESULT: PortfolioState in DB matches the Engine's internal state.
"""

import pytest
from sqlmodel import Session, select
from database.db import engine, init_db
from database.models import PortfolioState
from simulation.engine import SimulationEngine

def test_state_persistence_consistency():
    """
    OBJECTIVE: Run 5 ticks and verify DB entries.
    EXPECTED RESULT: 5 PortfolioState records exist with correct equity.
    """
    import uuid
    from config import config
    config.RUN_ID = f"test_{uuid.uuid4().hex[:6]}"
    init_db()
    sim = SimulationEngine()
    # No need to manually call _start_run_record() as __init__ does it
    
    for _ in range(5):
        sim.run_tick()
        
    with Session(engine) as session:
        states = session.exec(select(PortfolioState).where(PortfolioState.run_id == sim.run_id)).all()
        assert len(states) >= 5
        # Verify last state
        last_state = states[-1]
        assert abs(last_state.total_equity - sim.portfolio["total_equity"]) < 0.01
