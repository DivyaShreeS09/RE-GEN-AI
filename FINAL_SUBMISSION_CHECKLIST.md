# RE:GEN AI — Final Submission Checklist

Google Kaggle AI Agents: Intensive Vibe Coding Capstone Project 2026

---

## Build & Runtime

- [ ] `cd frontend && npm run build` — passes with no errors
- [ ] Backend starts: `cd backend && uvicorn main:app --reload --port 8000`
- [ ] Frontend starts: `cd frontend && npm run dev`
- [ ] War Room agents return results at `http://localhost:5173/#warroom`
- [ ] Waste Analyzer returns result for `e-waste`, 50 kg
- [ ] Hazardous material (e.g., `chemical waste`) shows warning, suppresses financials
- [ ] PDF report generates and downloads

## Security

- [ ] `.env` is NOT committed (check `git status` — it should not appear)
- [ ] `backend/.env.example` is committed with placeholder only (`your_gemini_api_key_here`)
- [ ] No API key visible in any source file or notebook

## Repository

- [ ] `README.md` present — complete, under 500 lines
- [ ] `capstone_writeup.md` present — all 15 sections complete
- [ ] `regen_ai_capstone_demo.ipynb` present — runs without backend server
- [ ] `docs/demo_video_script.md` present
- [ ] `DEPLOYMENT.md` present — Render + Vercel instructions
- [ ] `FINAL_SUBMISSION_CHECKLIST.md` present (this file)
- [ ] `docs/screenshots/README.md` present with capture instructions
- [ ] `backend/.env.example` present

## Cleanup

- [ ] No stray debug files at repo root
- [ ] No unused npm packages in `frontend/package.json`
- [ ] `frontend/public/icons.svg` removed (unused)
- [ ] `hero_skip.png` removed (unused)

## Content Accuracy

- [ ] README states "simulated data" clearly
- [ ] Writeup does not claim exact profit
- [ ] Writeup does not claim real IoT hardware
- [ ] Gemini usage section explains what Gemini does and does not do
- [ ] Limitations section is honest
- [ ] Disclaimer present in documentation

## Screenshots

- [ ] `docs/screenshots/hero.png` — **MANUAL CAPTURE REQUIRED**
- [ ] `docs/screenshots/digital-twin.png` — **MANUAL CAPTURE REQUIRED**
- [ ] `docs/screenshots/war-room.png` — **MANUAL CAPTURE REQUIRED**
- [ ] `docs/screenshots/waste-agent.png` — **MANUAL CAPTURE REQUIRED**
- [ ] `docs/screenshots/report.png` — **MANUAL CAPTURE REQUIRED**

See [docs/screenshots/README.md](docs/screenshots/README.md) for capture instructions.

## Demo Video

- [ ] Demo video recorded (see [docs/demo_video_script.md](docs/demo_video_script.md))
- [ ] Video uploaded to YouTube or Loom
- [ ] `README.md` demo link updated with actual URL
- [ ] `capstone_writeup.md` demo link updated with actual URL

## Deployment

- [ ] Backend deployed to Render
- [ ] Frontend deployed to Vercel
- [ ] `VITE_API_URL` set correctly on Vercel
- [ ] `GEMINI_API_KEY` set on Render (or confirmed fallback works without it)
- [ ] Live demo URL tested end-to-end
- [ ] `README.md` deployment URLs updated
- [ ] `capstone_writeup.md` deployment URL updated

## Kaggle Notebook

- [ ] `regen_ai_capstone_demo.ipynb` uploaded to Kaggle
- [ ] Notebook runs top-to-bottom without errors on Kaggle (no backend required)
- [ ] Gemini section gracefully skips if no API key found

## Git

- [ ] All files committed: `git status` shows clean working tree
- [ ] Commit message is descriptive
- [ ] Branch is `main`
- [ ] Pushed to GitHub (with user approval)

---

## Remaining Manual Steps Summary

1. Capture 5 screenshots per `docs/screenshots/README.md`
2. Record 3-minute demo video per `docs/demo_video_script.md`
3. Deploy backend to Render, frontend to Vercel per `DEPLOYMENT.md`
4. Update demo video and deployment links in `README.md` and `capstone_writeup.md`
5. Upload notebook to Kaggle and verify it runs
6. Push final commit to GitHub
