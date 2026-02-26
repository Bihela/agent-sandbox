from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
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

class SimulationJob(Base):
    __tablename__ = "simulation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    config_json = Column(JSON)  # Stores SimulationConfig as JSON
    scenario_type = Column(String)
    priority = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result_sim_id = Column(String, nullable=True) # ID of the resulting SimulationResult

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

# ─── Queue Helper Functions ───

def add_job(scenario_type: str, config: dict, priority: int = 0):
    db = SessionLocal()
    try:
        job = SimulationJob(
            scenario_type=scenario_type,
            config_json=config,
            priority=priority,
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    finally:
        db.close()

def get_next_job():
    db = SessionLocal()
    try:
        # Get highest priority, oldest pending job
        job = db.query(SimulationJob).filter(
            SimulationJob.status == "pending"
        ).order_by(
            SimulationJob.priority.desc(),
            SimulationJob.created_at.asc()
        ).first()
        return job
    finally:
        db.close()

def update_job_status(job_id: int, status: str, error: str = None, sim_id: str = None):
    db = SessionLocal()
    try:
        job = db.query(SimulationJob).filter(SimulationJob.id == job_id).first()
        if job:
            job.status = status
            if status == "running":
                job.started_at = datetime.utcnow()
            elif status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()
                job.error_message = error
                job.result_sim_id = sim_id
            db.commit()
        return job
    finally:
        db.close()
