import json
from metrics.storage import SessionLocal, SimulationJob

def switch_to_groq(limit=1000):
    db = SessionLocal()
    try:
        # Get pending jobs with 'mistral' or 'llama3' model
        jobs = db.query(SimulationJob).filter(
            SimulationJob.status == "pending"
        ).limit(limit).all()
        
        count = 0
        for job in jobs:
            config = job.config_json
            current_model = config.get("model_name", "")
            
            if current_model in ["mistral", "llama3"] and "groq:" not in current_model:
                config["model_name"] = f"groq:{current_model}"
                job.config_json = config
                # jobs.append(job) # not needed, it's already in the list
                count += 1
        
        db.commit()
        print(f"Successfully switched {count} jobs to Groq acceleration.")
    except Exception as e:
        db.rollback()
        print(f"Error switching to Groq: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    limit = 1000
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    switch_to_groq(limit)
