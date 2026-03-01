from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from metrics.storage import SimulationJob, DATABASE_URL

def diagnose_failures():
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        # Get up to 5 failed jobs
        stmt = select(SimulationJob).where(SimulationJob.status == "failed").limit(5)
        failed_jobs = session.scalars(stmt).all()
        
        if not failed_jobs:
            print("No failed jobs found in the database.")
            return
            
        print(f"Found {len(failed_jobs)} failed jobs. Error samples:")
        for job in failed_jobs:
            print(f"--- Job ID: {job.id} ---")
            print(f"Scenario: {job.scenario_type}")
            print(f"Error: {job.error_message}")
            print("-" * 20)

if __name__ == "__main__":
    diagnose_failures()
