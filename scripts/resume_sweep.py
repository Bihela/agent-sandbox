from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
from metrics.storage import SimulationJob, DATABASE_URL

def resume_maintenance():
    print("--- 🛠️ Agent Sandbox: Sweep Maintenance ---")
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        # 1. Reset 'running' jobs (that got stuck due to power off)
        stuck_cnt = session.execute(
            update(SimulationJob).where(SimulationJob.status == "running").values(status="pending")
        ).rowcount
        
        # 2. Reset 'failed' jobs (optional, but good for retries)
        failed_cnt = session.execute(
            update(SimulationJob).where(SimulationJob.status == "failed").values(status="pending")
        ).rowcount
        
        session.commit()
        print(f"✅ Reset {stuck_cnt} 'stuck' running jobs to pending.")
        print(f"✅ Reset {failed_cnt} failed jobs to pending.")
        print("\n🚀 System is now ready to resume. Run 'python -m uvicorn backend.main:app' to continue.")

if __name__ == "__main__":
    resume_maintenance()
