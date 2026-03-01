import sqlite3
import os

DB_PATH = "sandbox_metrics_v2.db"

def recover_junk():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- 🛠️ Simulation Recovery: Junk Reset ---")
    
    # 1. Broadly find jobs that returned 'agreement' or 'success' but have NO turns > 2 or NO price
    # These are likely due to the fallback-acceptance-on-turn-1 bug or connection failures.
    
    # First, get the job IDs from simulation_results that look like junk
    cursor.execute("""
        SELECT simulation_id FROM simulation_results 
        WHERE turns <= 2 AND final_price IS NULL
    """)
    junk_sim_ids = [row[0] for row in cursor.fetchall()]

    if not junk_sim_ids:
        print("✅ No definitive junk results found via turns+price check.")
    else:
        print(f"🔍 Found {len(junk_sim_ids)} junk results in simulation_results.")
        
        # Reset these jobs in simulation_jobs table
        placeholders = ','.join(['?'] * len(junk_sim_ids))
        cursor.execute(f"""
            UPDATE simulation_jobs 
            SET status = 'pending', started_at = NULL, completed_at = NULL, result_sim_id = NULL
            WHERE result_sim_id IN ({placeholders})
        """, junk_sim_ids)
        jobs_reset = cursor.rowcount
        
        # Delete the junk results from simulation_results
        cursor.execute(f"DELETE FROM simulation_results WHERE simulation_id IN ({placeholders})", junk_sim_ids)
        results_deleted = cursor.rowcount
        
        print(f"🔄 Reset {jobs_reset} jobs to 'pending'.")
        print(f"🗑️ Deleted {results_deleted} junk data points.")

    # 2. Also reset any jobs where status is 'completed' but we missed the result_sim_id link
    cursor.execute("""
        UPDATE simulation_jobs 
        SET status = 'pending', started_at = NULL, completed_at = NULL 
        WHERE status = 'completed' AND result_sim_id IS NULL
    """)
    orphan_reset = cursor.rowcount
    if orphan_reset:
        print(f"🩹 Reset {orphan_reset} orphaned completed jobs (missing DB links).")

    conn.commit()
    conn.close()
    print("\n🚀 Recovery complete. Start the backend to begin processing the reset jobs.")

if __name__ == "__main__":
    recover_junk()
