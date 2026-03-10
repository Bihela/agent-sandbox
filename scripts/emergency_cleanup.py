import sys
import os
sys.path.append(os.getcwd())
from metrics.storage import SessionLocal, SimulationJob
import datetime

def post_upgrade_cleanup():
    db = SessionLocal()
    try:
        # Cleanup any jobs that have been 'running' for more than 15 minutes.
        # These are definitely ghosts from previous Colab sessions.
        cut_off = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        
        ghost_jobs = db.query(SimulationJob).filter(
            SimulationJob.status == 'running',
            SimulationJob.started_at < cut_off
        ).all()
        
        count = len(ghost_jobs)
        for job in ghost_jobs:
            job.status = 'pending'
            job.started_at = None
        
        db.commit()
        print(f"✅ Successfully purged {count} ghost jobs from pre-upgrade sessions.")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    post_upgrade_cleanup()
