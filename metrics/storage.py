from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./sandbox_metrics.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String, index=True)
    agent_a_name = Column(String)
    agent_b_name = Column(String)
    status = Column(String) # e.g. "agreement", "timeout", "error"
    turns = Column(Integer)
    final_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def save_simulation_result(
    sim_id: str, 
    agent_a: str, 
    agent_b: str, 
    status: str, 
    turns: int, 
    final_price: float = None
):
    """
    Saves a simulation result to the SQLite database.
    """
    db = SessionLocal()
    try:
        db_result = SimulationResult(
            simulation_id=sim_id,
            agent_a_name=agent_a,
            agent_b_name=agent_b,
            status=status,
            turns=turns,
            final_price=final_price
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    finally:
        db.close()
