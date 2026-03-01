from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
from metrics.storage import SimulationJob, DATABASE_URL

def reset_failed_jobs():
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        # Update all 'failed' jobs to 'pending'
        stmt = update(SimulationJob).where(
            SimulationJob.status == "failed"
        ).values(
            status="pending",
            error_message=None,
            started_at=None,
            completed_at=None
        )
        result = session.execute(stmt)
        session.commit()
        print(f"Successfully reset {result.rowcount} failed jobs to 'pending'.")

if __name__ == "__main__":
    reset_failed_jobs()
