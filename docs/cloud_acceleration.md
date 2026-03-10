# Cloud Acceleration Guide 🚀

The Agent Sandbox supports horizontal scaling via remote workers. This allows you to leverage free cloud GPUs (like Google Colab) to accelerate the 24,000 simulation benchmark.

## How it works
1. **Local Backend**: Your PC acts as the "Command Center," holding the simulation queue and database.
2. **Tunnel**: A secure bridge (**Cloudflare Tunnel**) allows cloud workers to communicate with your local PC without port forwarding.
3. **Remote Workers**: Google Colab or **Kaggle Notebooks** acquire jobs, run them on their GPUs (via Ollama), and report results back.

## Setup Instructions

### 1. Start your Local Backend
Ensure your simulation sweep is running locally:
```bash
python -m uvicorn backend.main:app --port 8000
```

### 2. Create the Cloudflare Tunnel
Open a new terminal and run:
```bash
cloudflared tunnel --url http://localhost:8000
```
Note the dynamic URL provided (e.g., `https://demand-select-supplemental-architect.trycloudflare.com`).

### 3. Deploy Cloud Workers

#### Option A: Kaggle Swarm (Recommended - Dual T4 GPUs)
1. Open a new [Kaggle Notebook](https://www.kaggle.com/code/new).
2. Right Sidebar: Set **Internet ON** and **Accelerator: GPU T4 x2**.
3. Copy-paste the content of `scripts/kaggle_setup.py` into a cell.
4. Replace `YOUR_TUNNEL_URL` with your Cloudflare link and hit Play.

#### Option B: Google Colab Runner
1. Open [Google Colab](https://colab.research.google.com/).
2. Set Runtime to **T4 GPU**.
3. Use `scripts/colab_setup.py` to initialize.

## Stability & The "Ghost" Purger
Large-scale simulations are prone to cloud disconnects. This project includes an automated **Stale Job Reaper** and an `emergency_cleanup.py` script that resets jobs stuck in 'running' for more than 15 minutes. This ensures that if a cloud instance hits its daily quota, the jobs are safely returned to the queue for other workers.
