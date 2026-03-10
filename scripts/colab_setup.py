# Agent Sandbox - Google Colab Acceleration Script
# This script should be copied and pasted into a Google Colab notebook.

import os

# 1. Clean Slate & Clone
!rm -rf agent-sandbox
!git clone https://github.com/Bihela/agent-sandbox.git
%cd agent-sandbox

# If your repo has a nested structure, this finds the REAL root
import os, sys
def find_and_go_to_root():
    for root, dirs, files in os.walk("."):
        if "world" in dirs and "agents" in dirs:
            root_path = os.path.abspath(root)
            os.chdir(root_path)
            return root_path
    return os.getcwd()

PROJECT_ROOT = find_and_go_to_root()
sys.path.append(PROJECT_ROOT)
print(f"Working in: {PROJECT_ROOT}")

# 2. Install Ollama and models on Colab GPU
!curl -fsSL https://ollama.com/install.sh | sh
import subprocess
import time
# Start Ollama server in background with parallel request support
os.environ["OLLAMA_NUM_PARALLEL"] = "10"
process = subprocess.Popen(["ollama", "serve"])
time.sleep(10) # Wait for server to start

# 3. Pull the exact same models as your local setup
!ollama pull mistral
!ollama pull llama3

# 4. Install project dependencies
!pip install -r requirements.txt

# 5. Configure the worker
# Replace with your localtunnel URL from Step 1
BACKEND_URL = "INSERT_YOUR_TUNNEL_URL_HERE"

# 6. Run Multiple Workers (T4 can easily handle 2-3 workers for these models)
# We set PYTHONPATH to the project root so it can find 'world', 'agents', etc.
import os
os.environ["PYTHONPATH"] = PROJECT_ROOT

# Launching 10 workers in the background to maximize GPU usage
for i in range(10):
    subprocess.Popen(["python", "scripts/remote_worker.py", BACKEND_URL])
    print(f"🚀 Worker {i+1} started.")

# Keep the cell alive
while True:
    time.sleep(60)
