# Agent Sandbox - Google Colab Acceleration Script
# This script should be copied and pasted into a Google Colab notebook.

import os

# 1. Clone the repository
!git clone https://github.com/Bihela/agent-sandbox.git
%cd agent-sandbox

# 2. Install Ollama and models on Colab GPU
!curl -fsSL https://ollama.com/install.sh | sh
import subprocess
import time
# Start Ollama server in background
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

# 6. Run the worker
# This will now use the LOCAL Ollama running on Colab's GPU
!python scripts/remote_worker.py {BACKEND_URL}
