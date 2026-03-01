import json
from metrics.storage import add_job, update_job_status, SessionLocal, SimulationJob

class QueueManager:
    """Manages the simulation queue and job submission."""

    @staticmethod
    def schedule_simulations(scenario_type: str, config: dict, count: int = 1, priority: int = 0):
        """Enqueues N simulations with the same config."""
        import uuid
        batch_id = str(uuid.uuid4())
        jobs = []
        for _ in range(count):
            job = add_job(scenario_type, config, priority, batch_id=batch_id)
            jobs.append(job)
        return {"batch_id": batch_id, "job_count": len(jobs)}

    @staticmethod
    def get_queue_stats():
        """Returns statistics about the simulation queue."""
        db = SessionLocal()
        try:
            pending = db.query(SimulationJob).filter(SimulationJob.status == "pending").count()
            running = db.query(SimulationJob).filter(SimulationJob.status == "running").count()
            completed = db.query(SimulationJob).filter(SimulationJob.status == "completed").count()
            failed = db.query(SimulationJob).filter(SimulationJob.status == "failed").count()
            
            return {
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "total": pending + running + completed + failed
            }
        finally:
            db.close()

    @staticmethod
    def get_recent_jobs(limit: int = 50):
        """Returns the most recent jobs."""
        db = SessionLocal()
        try:
            jobs = db.query(SimulationJob).order_by(SimulationJob.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": j.id,
                    "status": j.status,
                    "scenario_type": j.scenario_type,
                    "created_at": j.created_at.isoformat(),
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "error": j.error_message,
                    "sim_id": j.result_sim_id
                }
                for j in jobs
            ]
        finally:
            db.close()
