import sys
import os
sys.path.append(os.getcwd())
from metrics.storage import SessionLocal, SimulationJob
import datetime

def cleanup():
    db = SessionLocal()
    try:
        # Define 'stale' as running for more than 15 minutes
        ten_mins_ago = datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - datetime.timedelta(minutes=15)
        stale_jobs = db.query(SimulationJob).filter(
            SimulationJob.status == 'running', 
            SimulationJob.created_at < ten_mins_ago
        ).all()
        
        count = len(stale_jobs)
        for job in stale_jobs:
            job.status = 'pending'
        
        db.commit()
        print(f"✅ Successfully reset {count} stale jobs back to 'pending'.")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
