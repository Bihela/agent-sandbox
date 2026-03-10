# Agent Sandbox - Kaggle Acceleration Script
# This script should be copied and pasted into a Kaggle Notebook.
# IMPORTANT: In the right sidebar of the Kaggle editor, ensure:
# 1. 'Internet' is set to ON
# 2. 'Accelerator' is set to GPU T4 x2 (if available) or GPU P100

import os
import sys
import subprocess
import time

# 1. Clean Slate & Clone into the working directory
# Kaggle's /kaggle/input is read-only, so we must use /kaggle/working
os.chdir('/kaggle/working')
!rm -rf agent-sandbox
!git clone https://github.com/Bihela/agent-sandbox.git
os.chdir('/kaggle/working/agent-sandbox')

PROJECT_ROOT = os.getcwd()
sys.path.append(PROJECT_ROOT)
print(f"Working in: {PROJECT_ROOT}")

# 2. Install Dependencies, Ollama, and start it in the background
print("Installing extraction dependencies...")
!sudo apt-get update -y && sudo apt-get install zstd pciutils lshw -y

print("Installing Ollama...")
!curl -fsSL https://ollama.com/install.sh | sh

print("Starting Ollama server...")
# Force Ollama to see the Kaggle Nvidia Drivers
os.environ["LD_LIBRARY_PATH"] = "/usr/local/nvidia/lib:/usr/local/nvidia/lib64:" + os.environ.get("LD_LIBRARY_PATH", "")
os.environ["OLLAMA_NUM_PARALLEL"] = "20" # Optimize for dual T4 32GB
process = subprocess.Popen(
    ["ollama", "serve"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(15) # Give it ample time to boot on Kaggle

# 3. Pull required models
print("Downloading Mistral and Llama3 models... This may take a few minutes.")
!ollama pull mistral
!ollama pull llama3

# 4. Install project dependencies
print("Installing Python requirements...")
!pip install -r requirements.txt -q

# 5. Configure the worker
# Replace with your active Cloudflare tunnel URL
BACKEND_URL = "INSERT_YOUR_TUNNEL_URL_HERE"

# 6. Run Multiple Workers (Kaggle's Dual GPUs can handle 20 effortlessly)
os.environ["PYTHONPATH"] = PROJECT_ROOT

print(f"Connecting 20 workers to {BACKEND_URL}...")
workers = []
for i in range(20):
    p = subprocess.Popen(["python", "scripts/remote_worker.py", BACKEND_URL])
    workers.append(p)
    print(f"🚀 Kaggle Worker {i+1} started.")
    time.sleep(0.5) # Slight stagger to prevent DB locks on the backend

# Keep the cell alive and monitor worker health
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("Shutting down workers...")
    for p in workers:
        p.terminate()
