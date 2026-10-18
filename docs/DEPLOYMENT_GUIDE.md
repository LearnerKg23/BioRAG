# BioRAG Deployment Guide

This guide provides step-by-step instructions for deploying the **BioRAG** full-stack biomedical research application across multiple production and staging environments.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Client Web Browser        |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Frontend (React + Vite)   |
                      |   Vercel / Nginx (Port 3000)|
                      +--------------+--------------+
                                     |  /api/* (Reverse Proxy)
                                     v
                      +-----------------------------+
                      |   Backend (FastAPI)         |
                      |   Render / Uvicorn (8000)   |
                      +-------+--------------+------+
                              |              |
               +--------------+              +--------------+
               v                                            v
    +----------------------+                    +----------------------+
    |  Local Vector Store  |                    |   External Services  |
    |  - FAISS CPU         |                    |  - Groq LLaMA 3 API  |
    |  - BM25 Okapi Index  |                    |  - Europe PMC REST   |
    |  - SQLite Manifest   |                    +----------------------+
    +----------------------+
```

---

## Option 1: 100% Free Cloud PaaS (Render + Vercel) — Recommended

This architecture deploys the FastAPI backend to **Render.com** (Free Web Service) and the React frontend to **Vercel** (Global Edge CDN). It requires zero server maintenance and auto-deploys on every git push.

### Step 1: Deploy Backend on Render.com

1. Sign up or log in to [Render.com](https://render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository: `https://github.com/LearnerKg23/BioRAG`.
4. Configure the service settings:
   - **Name**: `biorag-backend`
   - **Region**: Choose the closest region (e.g., *Oregon (US West)* or *Frankfurt (EU)*)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY`: `<Your-Groq-API-Key>`
   - `EMBEDDING_MODEL_NAME`: `sentence-transformers/all-MiniLM-L6-v2`
   - `PYTHON_VERSION`: `3.11.9`
6. Click **Create Web Service**.
7. Once deployed, copy your backend URL (e.g., `https://biorag-backend-xxxx.onrender.com`).
8. Verify backend health by visiting: `https://biorag-backend-xxxx.onrender.com/api/health`.

---

### Step 2: Deploy Frontend on Vercel

1. Open [frontend/vercel.json](file:///frontend/vercel.json) in your repository and update the destination URL with your Render backend URL:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://biorag-backend-xxxx.onrender.com/api/:path*"
       },
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
2. Commit and push this change to your repository:
   ```bash
   git add frontend/vercel.json
   git commit -m "chore: configure render backend destination in vercel.json"
   git push origin main
   ```
3. Sign up or log in to [Vercel.com](https://vercel.com).
4. Click **Add New...** $\rightarrow$ **Project**.
5. Import your `BioRAG` repository.
6. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
7. Click **Deploy**.
8. In ~60 seconds, your frontend will be live on a `*.vercel.app` URL with seamless zero-CORS proxying to your backend!

---

## Option 2: Docker Compose on Cloud VPS (AWS EC2, DigitalOcean, GCP, Hetzner)

For full self-hosting with persistent indices and local control, deploy using Docker Compose on any Linux VM.

### Minimum Server Requirements
- **OS**: Ubuntu 22.04 LTS / Debian 12
- **Memory**: 2 GB RAM minimum (4 GB recommended for PyTorch/HuggingFace embeddings)
- **Disk**: 10 GB SSD

### Step 1: Install Docker & Docker Compose on your Server
```bash
# Update and install Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Step 2: Clone Repository and Configure Environment
```bash
git clone https://github.com/LearnerKg23/BioRAG.git
cd BioRAG

# Create environment file
cat <<EOF > .env
GROQ_API_KEY=your_actual_groq_api_key_here
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EOF
```

### Step 3: Launch with Docker Compose
```bash
docker compose up -d --build
```

### Step 4: Verify Containers
```bash
docker compose ps
docker compose logs -f backend
```

- **Frontend**: `http://<SERVER_IP>:3000`
- **Backend API Docs**: `http://<SERVER_IP>:8000/docs`
- **System Health**: `http://<SERVER_IP>:8000/api/health`

### Optional: Domain & SSL Setup via Nginx + Certbot
To expose BioRAG on port 80/443 with a custom domain:
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Configure Nginx reverse proxy to port 3000
sudo nano /etc/nginx/sites-available/biorag
```
Add:
```nginx
server {
    server_name biorag.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable site and obtain SSL:
```bash
sudo ln -s /etc/nginx/sites-available/biorag /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d biorag.yourdomain.com
```

---

## Option 3: Hugging Face Spaces (Free AI Showcase Space)

Hugging Face Spaces allows you to host interactive AI demonstrations for free.

1. Create a new Space on [Hugging Face Spaces](https://huggingface.co/spaces).
2. Choose **Docker** as the Space SDK and set license to **MIT**.
3. In your Space repository settings, add `GROQ_API_KEY` under **Repository Secrets**.
4. Push the BioRAG repository to the Hugging Face Space git remote.

---

## Option 4: Instant Public Demo (Cloudflare Tunnel / Ngrok)

If you have BioRAG running locally and need to share a live working demo with collaborators or an evaluator immediately without deploying to cloud:

### Using Cloudflare Quick Tunnel (Free, no account needed):
```bash
# Download cloudflared and expose port 3000
cloudflared tunnel --url http://localhost:3000
```
This generates a secure public HTTPS URL (e.g., `https://random-word.trycloudflare.com`) routing directly to your local instance.

---

## Production Health Check Verification

Once deployed, execute these smoke test queries:

```bash
# 1. Check API Health
curl https://<YOUR_DEPLOYED_URL>/api/health

# Expected response:
# {"status":"healthy","groq_configured":true,"embedding_model":"sentence-transformers/all-MiniLM-L6-v2"}

# 2. Check Corpus Statistics
curl https://<YOUR_DEPLOYED_URL>/api/papers/stats

# 3. Test Retrieval / Query Pipeline
curl -X POST https://<YOUR_DEPLOYED_URL>/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What role does KRAS mutation play in pancreatic cancer?"}'
```
