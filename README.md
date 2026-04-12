# Owlytice Election Prediction

An end-to-end machine learning pipeline forecasting the 140 constituencies of the 2026 Kerala Legislative Assembly Elections.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [How We Predict Elections](#how-we-predict-elections)
3. [Project Structure](#project-structure)
4. [Local Development Setup](#local-development-setup)
5. [Running the Application](#running-the-application)
6. [Railway Deployment](#railway-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Project Overview

This project simulates and predicts electoral outcomes by fusing historical results, parliamentary momentum, local body trends, demographic data, and regional political issues.

The pipeline consists of two main components:
1. **`create_dataset.py`**: A heuristic engine that synthesizes a comprehensive 43-feature dataset for all 140 constituencies.
2. **`train.py`**: A Neural Network pipeline that trains on these features to predict winning alliances and vote shares.

### Key Features
- **Ensemble Learning**: 15 independent models voting on predictions
- **Vote Share Prediction**: Not just winner prediction, but exact vote percentages
- **Attention to Rare Events**: Special training techniques for underrepresented outcomes
- **Full-Stack Application**: Python backend API + React/TypeScript frontend dashboard

---

## How We Predict Elections

Predicting elections with data is challenging—especially in Kerala, where there are only 140 constituencies and dominant parties (LDF and UDF) win almost every seat.

### Strategy 1: The "Wisdom of Crowds" (Ensemble Learning)

Because our dataset is incredibly small (only 140 rows), training just one AI model is risky. It might memorize the data instead of learning real patterns.

**Solution**: Train **15 separate models** on different randomized slices of the state. When predicting final results, all 15 models vote on the outcome. Averaging their predictions gives a much more stable and reliable forecast.

### Strategy 2: Predicting the Score, Not Just the Winner

If we only ask the AI to predict "Who wins?", it will rarely see NDA victories and won't learn what success looks like for third parties.

**Solution**: We ask the AI to do two things:
- Predict the winning party
- Predict the **exact vote share percentage** for every party

Because every party gets *some* vote share in every constituency, the AI constantly learns what makes a party perform well, even where they ultimately lose.

### Strategy 3: Paying Extra Attention to Rare Events

An AI naturally ignores rare events (like an independent candidate winning) to focus on common patterns.

**Solution**: During training, we use specialized math techniques that force the AI to pay extra attention to these incredibly rare scenarios.

### A Word on Model Logic

Usually, true predictive AI feeds on historical data paired with outcomes. However, we don't have perfectly paired historical data stretching back decades.

Our dataset builder (`create_dataset.py`) acts as a **human logic engine**: it takes recent data (2021 results, 2024 parliamentary momentum, etc.) and uses documented political science formulas to estimate a "projected truth."

Our neural network then **learns to deeply mimic that political human logic**, smoothing out the hard math and finding hidden relationships between demographics, geography, and political momentum. It acts as an incredible digital strategist applying complex political logic statewide.

---

## Project Structure

## Project Structure

```text
kerala-election-prediction/
+-- backend/
|   +-- config.py                    # Shared backend constants/config
|   +-- create_dataset.py            # Builds all CSV datasets
|   +-- train.py                     # Trains ensemble and writes predictions
|   +-- server.py                    # Backend API (/api/health, /api/predictions)
|   +-- data/
|   |   +-- live_collectors.py       # Optional live API collectors
|   |   +-- sentiment_extractor.py
|   |   +-- __init__.py
|   +-- models/
|   |   +-- __init__.py              # Placeholder for future model modules
|   +-- utils/
|   |   +-- __init__.py
|   +-- data_files/
|   |   +-- kerala_assembly_2026.csv
|   |   +-- kerala_demographics.csv
|   |   +-- kerala_sentiment_2026.csv
|   |   +-- [other data CSVs...]
|   +-- checkpoints/                 # Runtime model checkpoints
|   +-- predictions_2026.csv         # Final model output for frontend
|   +-- __init__.py
+-- frontend/
|   +-- src/
|   |   +-- App.tsx
|   |   +-- index.css
|   |   +-- main.tsx
|   |   +-- components/
|   |   |   +-- AnimatedKpiGrid.tsx
|   |   |   +-- CompetitiveSeats.tsx
|   |   |   +-- DistrictBreakdownPanel.tsx
|   |   |   +-- FilterBar.tsx
|   |   |   +-- KPISection.tsx
|   |   |   +-- PartyBadge.tsx
|   |   |   +-- PredictionTable.tsx
|   |   |   +-- SeatDistribution.tsx
|   |   +-- hooks/
|   |   |   +-- usePredictions.ts
|   |   +-- services/api.ts
|   |   +-- types/prediction.ts
|   |   +-- utils/format.ts
|   +-- public/assets/owlytics
|   +-- package.json
|   +-- vite.config.ts
|   +-- railway.json
+-- requirements.txt
+-- run.py
+-- Procfile
+-- README.md
```

### Recent Refactoring

- Removed dead backend modules and unused dependencies
- Split frontend into 7+ reusable components and custom hooks
- Fixed package imports and organized public assets
- Reduced Python dependencies from 16 to 8
- Added proper Vercel/Railway configuration files

---

## Local Development Setup

### 1. Clone & Initial Setup

```bash
git clone https://github.com/your-user/kerala-election-prediction.git
cd kerala-election-prediction
```

### 2. Create Python Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Create Backend .env

From the `backend/` directory:
```bash
cp .env.example .env
```

Edit `backend/.env`:
```
PORT=8001
HOST=127.0.0.1
USE_REAL_APIS=0
```

### 4. Create Frontend .env

From the `frontend/` directory:
```bash
cp .env.example .env
```

Edit `frontend/.env`:
```
VITE_API_BASE_URL=http://127.0.0.1:8001
```

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Important Rules ✅

| File | Rule | Why |
|------|------|-----|
| `.env` | ❌ Never commit | Contains secrets & API keys |
| `.env.example` | ✅ Always commit | Shows team what variables are needed |
| `.venv/` | ❌ Never commit | Too large, everyone creates their own |
| `.gitignore` | ✅ Always commit | Protects `.env` & `.venv` |

---

## Running the Application

### Local Development (Both Services)

**Terminal 1 - Backend:**
```bash
# Make sure .venv is activated
python backend/server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then visit: `http://localhost:5173`

### Just the Backend API

```bash
python backend/server.py
# Available at http://127.0.0.1:8001
# - GET /api/health
# - GET /api/predictions
```

### Just the Frontend

```bash
cd frontend
npm run dev
```

### Building for Production

**Backend:** No build needed (pure Python)

**Frontend:**
```bash
cd frontend
npm run build
# Output: dist/ folder
```

### Generate Predictions Dataset

By default, predictions are pre-computed in `backend/predictions_2026.csv`.

To regenerate:
```bash
# 1. Build dataset features
python backend/create_dataset.py

# 2. Train models and save predictions
python backend/train.py
```

---

## Railway Deployment

### Prerequisites

- Railway account (https://railway.app)
- Git repository initialized
- Local build works: `npm run build` (frontend) and dataset/model files built (backend)
- `predictions_2026.csv` exists in `backend/`

### Step 1: Create Railway Projects

```bash
# Log in to Railway
npx -y @railway/cli login

# Link to workspace
npx -y @railway/cli link
```

Create TWO projects in Railway Dashboard:
- `kerala-election-backend` (Python backend)
- `kerala-election-frontend` (React frontend)

### Step 2: Configure Backend Environment Variables

In Railway Dashboard → Backend Project → Variables:

```
PORT=8000
HOST=0.0.0.0
USE_REAL_APIS=0
```

Optional (for live data):
```
X_BEARER_TOKEN=your_token
YOUTUBE_API_KEY=your_key
NEWS_API_KEY=your_key
```

### Step 3: Get Backend Public URL

In Railway Dashboard → Backend Project → Deployments:
Copy the public URL (format: `https://xxxxx.up.railway.app`)

### Step 4: Configure Frontend Environment Variables

In Railway Dashboard → Frontend Project → Variables:

```
VITE_API_BASE_URL=https://[YOUR_BACKEND_URL]
```

Replace `[YOUR_BACKEND_URL]` with your actual backend Railway URL from Step 3.

### Step 5: Deploy

```bash
git push origin main
```

Railway auto-deploys when connected. Watch the deployments in the dashboard.

### Step 6: Verify Deployment

**Test Backend Health:**
```
https://[YOUR_BACKEND_URL]/api/health
```
Should return: `{"status": "ok"}`

**Test Predictions:**
```
https://[YOUR_BACKEND_URL]/api/predictions
```

**Open Frontend:**
```
https://[YOUR_FRONTEND_URL]
```
Should load the election dashboard with data.

### Environment Variables Reference

| Variable | Component | Value | Where to Set |
|----------|-----------|-------|--------------|
| `PORT` | Backend | `8000` | Railway Dashboard |
| `HOST` | Backend | `0.0.0.0` | Railway Dashboard |
| `VITE_API_BASE_URL` | Frontend | `https://your-backend.up.railway.app` | Railway Dashboard |

### Railway Deployment Files

| File | Purpose |
|------|---------|
| `Procfile` | Tells Railway how to start backend |
| `frontend/railway.json` | Tells Railway how to build frontend |
| `requirements.txt` | Python dependencies |
| `frontend/package.json` | Node dependencies |

---

## Troubleshooting

### Python/Backend Issues

#### "Cannot find module X"
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate  # Windows

# Reinstall packages
pip install -r requirements.txt
```

#### Backend not responding locally
```bash
# Make sure backend is running
python backend/server.py

# Check it's accessible
curl http://127.0.0.1:8001/api/health
```

#### Backend won't start on Railway
```bash
# Check logs
npx -y @railway/cli logs --service backend
```

**Solution:** Verify `PORT=8000` and `HOST=0.0.0.0` in Railway Dashboard

### Frontend/React Issues

#### Frontend shows "Backend Error"
1. Check backend is running: `python backend/server.py`
2. Verify `VITE_API_BASE_URL` in `frontend/.env` is correct
3. Test backend directly in browser: `http://127.0.0.1:8001/api/health`
4. Check browser console (F12) for detailed errors

#### Frontend can't reach backend on Railway
1. Verify `VITE_API_BASE_URL` exactly matches your backend Railway URL
2. Test the URL directly in browser
3. Check browser console (F12 → Console tab) for CORS errors
4. Backend CORS headers are configured—should allow all origins

#### "Cannot compile" or build errors
```bash
cd frontend
npm run build
# Check output for specific errors
```

### Data Issues

#### "Cannot find predictions_2026.csv"

**Local:**
```bash
python backend/create_dataset.py
python backend/train.py
```

**On Railway:** Commit the generated file to git:
```bash
git add backend/predictions_2026.csv
git commit -m "Add pre-generated predictions"
git push origin main
```

#### Data not showing in frontend
1. Verify `backend/predictions_2026.csv` exists
2. Test `/api/predictions` endpoint directly
3. Check browser console for parse errors

#### Localhost and deployed prediction totals are different
1. Check deployed metadata:
```bash
curl https://<railway-domain>/api/predictions/meta
```
2. Check local metadata:
```bash
curl http://127.0.0.1:8001/api/predictions/meta
```
Local file hash (Windows PowerShell):
```powershell
Get-FileHash backend/predictions_2026.csv -Algorithm SHA256
```
3. Compare:
- `source_file` should be `predictions_2026.csv`
- `fallback_in_use` should be `false`
- `source_sha256` should match exactly
- `seat_counts` should match exactly
4. If they differ:
- Redeploy Railway backend from latest commit
- Update Vercel env `VITE_EXPECTED_PREDICTIONS_SHA256` with the deployed `/api/predictions/meta` hash
- Redeploy Vercel frontend

### Environment Variable Issues

#### .env file not found
```bash
# Create from template
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Then edit with your values
nano backend/.env
nano frontend/.env
```

#### Variables not being read
- **Frontend**: Make sure to use `VITE_` prefix for environment variables
- **Backend**: Make sure to use `os.environ.get("VARIABLE_NAME")`
- Restart dev servers after changing `.env` files

### General Debugging

**Check logs locally:**
```bash
python backend/server.py  # Shows all prints and errors
```

**Check logs on Railway:**
```bash
npx -y @railway/cli logs --service backend
npx -y @railway/cli logs --service frontend
```

**Test API endpoints:**
```bash
# Health check
curl http://127.0.0.1:8001/api/health

# Get predictions
curl http://127.0.0.1:8001/api/predictions
```

---

## Summary

✅ `.env.example` = Share with team (template)  
❌ `.env` = Keep private (your secrets)  
❌ `.venv/` = Never commit (recreate locally)  
✅ `.gitignore` = Protects secrets automatically  
✅ `predictions_2026.csv` = Commit to git (pre-generated predictions)

---

**Questions?** Check the troubleshooting section above or review logs for specific error messages.

```bash
python run.py
```

Then open:
- Frontend: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8001/api/predictions`

## Deploy Backend on Railway (for Vercel Frontend)

This repository is now Railway-ready with:
- `Procfile` (start command)
- `railway.json` (Nixpacks builder + `/api/health` health check)

### 1. Push latest code

```bash
git add .
git commit -m "prepare Railway deployment"
git push
```

### 2. Deploy backend on Railway

1. Railway -> New Project -> Deploy from GitHub Repo
2. Select this repository
3. Confirm service start command:
   - `python backend/server.py`
4. Wait for deploy success

Backend must respond at:
- `https://<railway-domain>/api/health`
- `https://<railway-domain>/api/predictions`
- `https://<railway-domain>/api/predictions/meta`

Important:
- Production now requires `backend/predictions_2026.csv` by default.
- If that file is missing, API returns an error instead of silently serving fallback data.
- Optional override for debugging only:
  - `ALLOW_ASSEMBLY_FALLBACK=1`

### 3. Connect Vercel frontend to Railway backend

In Vercel project settings -> Environment Variables, set:

```env
VITE_API_BASE_URL=https://<railway-domain>
VITE_EXPECTED_API_VERSION=2026-04-12.1
VITE_EXPECTED_PREDICTIONS_SHA256=<value from /api/predictions/meta source_sha256>
```

Note:
- Frontend also accepts `VITE_API_URL` as an alias.
- No trailing slash needed.
- If `VITE_EXPECTED_PREDICTIONS_SHA256` is set, frontend will block stale backend data automatically.

Then redeploy Vercel frontend.

Vercel build config note:
- Do not hardcode `npm --prefix frontend ...` in Dashboard commands.
- Keep project root as either repository root or `frontend/`; `vercel.json` now auto-detects both.

## Clear End-to-End Run Process

1. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Generate dataset CSVs
```bash
python backend/create_dataset.py
```

3. Train model and generate predictions
```bash
python backend/train.py
```

4. Start full app (frontend + backend together)
```bash
cd frontend && npm install && cd ..
python run.py
```

Frontend-only (React dev server):
```bash
cd frontend
npm install
npm run dev
```

5. Open in browser
- Frontend dashboard: `http://127.0.0.1:5173`
- API check: `http://127.0.0.1:8001/api/health`
