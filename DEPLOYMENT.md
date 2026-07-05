# Deployment Guide — RE:GEN AI

This guide covers deploying the backend to Render and the frontend to Vercel.

---

## Prerequisites

- GitHub account with the RE:GEN AI repository pushed
- Render account (render.com — free tier works)
- Vercel account (vercel.com — free tier works)
- Your `GEMINI_API_KEY` ready (the app works without it, but Gemini features will use fallbacks)

---

## Part 1 — Deploy Backend to Render

### Step 1: Create a new Web Service

1. Log in to [render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub account if not already connected
4. Select your **regen-ai** repository

### Step 2: Configure the service

| Field | Value |
|---|---|
| Name | `regen-ai-backend` |
| Region | Singapore (or closest to you) |
| Branch | `main` |
| Root Directory | `backend` |
| Runtime | **Python 3** |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

### Step 3: Add environment variable

Under **Environment** → **Add Environment Variable**:

| Key | Value |
|---|---|
| `GEMINI_API_KEY` | your actual Gemini API key |

### Step 4: Deploy

Click **Create Web Service**. Render will build and deploy. Wait for status to show **Live**.

Copy the URL shown (e.g., `https://regen-ai-backend.onrender.com`). You will need this for the frontend.

### Verify

```
https://regen-ai-backend.onrender.com/health
```

Should return: `{"status": "ok"}`

---

## Part 2 — Deploy Frontend to Vercel

### Step 1: Create a new project

1. Log in to [vercel.com](https://vercel.com)
2. Click **Add New** → **Project**
3. Import your **regen-ai** GitHub repository

### Step 2: Configure the project

| Field | Value |
|---|---|
| Framework Preset | **Vite** |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |

### Step 3: Add environment variable

Under **Environment Variables**:

| Key | Value |
|---|---|
| `VITE_API_URL` | `https://regen-ai-backend.onrender.com` (your Render URL, no trailing slash) |

### Step 4: Deploy

Click **Deploy**. Vercel will build and deploy. Wait for status to show **Ready**.

Your frontend will be available at `https://regen-ai.vercel.app` (or similar auto-generated URL).

---

## Part 3 — Post-Deployment Checks

1. Open the Vercel frontend URL
2. Check that the hero section loads
3. Click **Run Agents** in the War Room section
4. Verify agents return results (may take 30–60s on first Render cold start)
5. Try the Waste Analyzer with a material (e.g., `e-waste`, 50 kg)
6. Generate and download the PDF report

---

## Notes

- **Cold starts:** Render free tier spins down after inactivity. The first request after a cold start may take 30–60 seconds. This is expected behavior on the free plan.
- **GEMINI_API_KEY is optional.** If not set, all agents return deterministic fallback text. The app is fully functional without it.
- **Do not commit `.env`** — it is listed in `.gitignore`.
- **CORS:** The backend is configured to allow all origins in development. For production, update `backend/main.py` CORS `allow_origins` to your Vercel domain if you want to restrict access.

---

## Local Development (reference)

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env        # then add your GEMINI_API_KEY
uvicorn main:app --reload --port 8000

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`
Backend: `http://localhost:8000`
