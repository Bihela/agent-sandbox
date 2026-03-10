import sys
import os
# Ensure it can find metrics.storage
sys.path.append(os.getcwd())

from metrics.storage import SessionLocal, SimulationResult, SimulationJob
from sqlalchemy import func
import datetime

def audit():
    db = SessionLocal()
    try:
        # Total results
        total = db.query(SimulationResult).count()
        print(f"Total Results: {total}")
        
        # Check for hanging jobs (Running for more than 10 mins)
        ten_mins_ago = datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - datetime.timedelta(minutes=10)
        hanging = db.query(SimulationJob).filter(SimulationJob.status == 'running', SimulationJob.created_at < ten_mins_ago).count()
        print(f"Hanging Jobs (>10 mins): {hanging}")

        # Status breakdown
        stats = db.query(SimulationResult.status, func.count(SimulationResult.id)).group_by(SimulationResult.status).all()
        print(f"Status Breakdown: {stats}")
        
        # Mean turns
        avg_turns = db.query(func.avg(SimulationResult.turns)).scalar()
        print(f"Average Turns: {avg_turns if avg_turns else 0:.2f}")
        
        # Error messages
        errors = db.query(SimulationJob.error_message, func.count(SimulationJob.id)).filter(SimulationJob.error_message.isnot(None)).group_by(SimulationJob.error_message).all()
        print(f"\n--- Error Breakdown (from Jobs) ---")
        for e in errors:
            print(f"{e[0]}: {e[1]}")

        # Price distribution (top 5)
        prices = db.query(SimulationResult.final_price, func.count(SimulationResult.id)).filter(SimulationResult.status == 'agreement').group_by(SimulationResult.final_price).order_by(func.count(SimulationResult.id).desc()).limit(5).all()
        print(f"\n--- Price Distribution (Top 5 Agreements) ---")
        for p in prices:
            print(f"Price {p[0]}: {p[1]} occurrences")

        # Recent 10 Results with basic info
        recent = db.query(SimulationResult).order_by(SimulationResult.id.desc()).limit(10).all()
        print("\n--- Recent 10 Results ---")
        for r in recent:
            print(f"ID: {r.id}, Status: {r.status}, Turns: {r.turns}, Price: {r.final_price}")

        # Let's check the terminal for local worker activity
        print("\n--- Local Worker Check ---")
        print("Note: Local workers log to the console as 'SimulationWorker-X'")
            
    finally:
        db.close()

if __name__ == "__main__":
    audit()
