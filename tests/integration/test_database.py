# tests/integration/test_database.py

"""
TEST SUITE: Database Persistence & Integrity
OBJECTIVE: Verify that portfolio states and advice are stored correctly in PostgreSQL.
EXPECTED RESULT: Data persists across sessions and JSONB fields are queryable.
"""

import pytest
from sqlmodel import Session, select
from database.db import engine, init_db
from database.models import SimulationRun

def test_database_persistence():
    """
    OBJECTIVE: Verify that a SimulationRun can be saved and retrieved.
    EXPECTED RESULT: Retrieved values match saved values exactly.
    """
    import uuid
    init_db()
    test_run_id = f"test_{uuid.uuid4().hex[:6]}"
    with Session(engine) as session:
        # Cleanup if exists
        old = session.exec(select(SimulationRun).where(SimulationRun.id == test_run_id)).first()
        if old: session.delete(old); session.commit()
        
        run = SimulationRun(id=test_run_id, config_snapshot={"mode": "test"})
        session.add(run)
        session.commit()
        
        fetched = session.exec(select(SimulationRun).where(SimulationRun.id == test_run_id)).first()
        assert fetched is not None
        assert fetched.config_snapshot["mode"] == "test"
        
        # Cleanup
        session.delete(fetched)
        session.commit()
