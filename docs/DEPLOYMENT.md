# Deployment

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.11 |
| Node.js | 18 |
| npm | 9 |

---

## Local Development

### 1. Clone

```bash
git clone https://github.com/<your-username>/regen-ai.git
cd regen-ai
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

No environment variables required — the backend reads only local files.

### 3. Frontend setup

```bash
cd frontend
npm install
```

No `.env` file required. The Vite dev server proxies `/api/*` to `http://localhost:8000`
via `vite.config.js`.

### 4. Run backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### 5. Run frontend (separate terminal)

```bash
cd frontend
npm run dev
```

App: `http://localhost:5173`

---

## Production Build

```bash
cd frontend
npm run build
```

Output goes to `frontend/dist/`. Approximate bundle sizes:
- **JS:** ~741 kB (Recharts is the primary contributor)
- **CSS:** ~41 kB

---

## Cloud Deployment

### Backend (Render / Railway / Fly.io)

Set the start command to:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The platform injects `$PORT`. No other environment variables are needed for the
prototype — all data is read from the local `backend/data/` files bundled in the repo.

### Frontend (Vercel / Netlify)

| Setting | Value |
|---------|-------|
| Build command | `npm run build` |
| Output directory | `dist` |
| Root directory | `frontend` |

**Important:** Update the Vite proxy in `vite.config.js` to point `/api` at your deployed
backend URL, or set `VITE_API_BASE_URL` and switch the `api.js` base URL to use it.

---

## Docker (optional)

A minimal `Dockerfile` for the backend:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t regen-ai-backend .
docker run -p 8000:8000 regen-ai-backend
```

---

## Notes

- CORS is currently `allow_origins=["*"]`. Restrict to your frontend domain in production.
- All 7 API endpoints are unauthenticated. Add an API key or OAuth layer before any
  public-facing deployment.
- The `backend/data/` directory must be present at runtime — it is read on every request
  (except the waste KB, which is cached in module scope after first load).

---

*See also: [API.md](API.md) · [SECURITY.md](SECURITY.md)*
