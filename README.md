# Owlytice Election Prediction

An end-to-end machine learning pipeline forecasting the 140 constituencies of the 2026 Kerala Legislative Assembly Elections.

## Professional Project Structure

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
|   |   +-- kerala_loksabha_2024.csv
|   |   +-- kerala_sentiment_2026.csv
|   |   +-- kerala_social_media_2026.csv
|   +-- checkpoints/                 # Runtime model checkpoints
|   +-- predictions_2026.csv         # Final model output for frontend
|   +-- .env.example
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
|   +-- vercel.json
+-- requirements.txt
+-- run.py
+-- vercel.json                      # Root Vercel config for monorepo-style deploy
+-- README.md
```

### Refactor Snapshot

- Removed dead backend modules that were not used at runtime.
- Fixed broken package imports in `backend/data/__init__.py` and simplified `backend/models/__init__.py`.
- Split frontend into reusable components and custom hooks (`usePredictions`).
- Renamed frontend stylesheet entry to `src/index.css` and organized public assets under `public/assets/`.
- Added Vercel config files for reliable installs/builds in both root and frontend deployment modes.

## Refactoring Report (Integrated Summary)

### Scope

- Comprehensive cleanup of backend/frontend code organization.
- Dead code and dependency reduction without changing core product behavior.
- Folder structure normalization and modularization.

### Backend Cleanup Highlights

- Removed legacy/unused backend modules under:
  - `backend/models/` (old predictor/encoder files)
  - `backend/data/` (unused dataset/feature/historical files)
  - `backend/generate_svg.py` (standalone and not integrated in runtime pipeline)
- Simplified backend configuration layout (`backend/config.py`) to clearer constants-focused usage.
- Fixed package export hygiene in:
  - `backend/data/__init__.py`
  - `backend/models/__init__.py`

### Dependency Cleanup

- Python dependencies reduced from 16 to 8 in `requirements.txt`.
- Removed libraries marked unused in the report (visualization/scraping/NLP/testing extras).
- Kept only runtime-required packages for the current pipeline.

### Frontend Refactor Highlights

- Expanded UI into reusable components:
  - `KPISection`, `FilterBar`, `PredictionTable`, `SeatDistribution`,
    `DistrictBreakdownPanel`, `CompetitiveSeats`, and `AnimatedKpiGrid`.
- Added custom hook:
  - `frontend/src/hooks/usePredictions.ts`
- Standardized frontend structure:
  - Styles consolidated in `frontend/src/index.css`
  - Public assets organized under `frontend/public/assets/`

### Reported Impact Metrics

| Metric | Before | After |
|--------|--------|-------|
| Dead code files | 7 | 0 |
| Unused dependencies | 9 | 0 |
| Python dependencies | 16 | 8 |
| Frontend reusable components | 1 | 7+ |
| Custom hooks | 0 | 1 |

### Verification Status (from report)

- Python modules compile successfully.
- Frontend production build succeeds.
- API endpoints and data flow remain functional.
- No intentional breaking changes to endpoint contract or core business logic.

### Future Recommendations (from report)

1. Add unit tests (especially around `usePredictions` and data transforms).
2. Enable stricter TypeScript settings and add story-level UI validation.
3. Add API documentation and stronger typed interfaces across backend modules.
4. Consider deployment/runtime hardening (env management, containerization).

### Data File vs Data Folder

- `backend/data/`:
  - Python source code modules for data processing (not CSV data).
  - Example: feature extraction, historical loader, sentiment extractor.
- `backend/data_files/`:
  - Generated CSV datasets used by training.
  - These are the structured input data artifacts.
- `backend/predictions_2026.csv`:
  - Final prediction output consumed by the frontend via backend API.

## Overview

This project simulates and predicts the electoral outcomes by fusing historical results, parliamentary momentum, local body trends, demographic data, and regional political issues. 

The pipeline consists of two main components:
1. **`create_dataset.py`**: A heuristic engine that synthesizes a comprehensive 43-feature dataset for all 140 constituencies. It combines baseline 2021 results with 2024 Lok Sabha momentum, 2025 Local Body trends, demographic makeup, and constituency-specific issue impacts to generate projected vote shares.
2. **`train.py`**: A robust Neural Network pipeline that trains on these features to predict the winning alliance (LDF, UDF, NDA, OTHERS) and exact vote shares.

## How We Predict the Election

Predicting elections with data is challenging—especially in Kerala, where there are only 140 constituencies (which means a very small dataset) and where the dominant parties (LDF and UDF) win almost every seat, making it incredibly hard for an AI to learn how third fronts like the NDA or independent candidates might win.

To tackle these unique challenges, our approach uses a few clever strategies:

### 1. The "Wisdom of Crowds" (Ensemble Learning)
Because our dataset is incredibly small (only 140 rows), training just one AI model is risky. It might just memorize the data instead of learning real patterns. To fix this, we train **15 separate models** on different randomized slices of the state. When predicting the final results, we ask all 15 models to vote on the outcome. By averaging their predictions together, we get a much more stable, reliable, and highly confident forecast.

### 2. Predicting the Score, Not Just the Winner
Historically, the NDA rarely wins seats in Kerala. If we only ask the AI to predict "Who wins?", it will almost never see enough examples to effectively learn what an NDA victory looks like. 

Instead, we ask the AI to do two things at once:
* Predict the winning party.
* Predict the **exact vote share percentage** for every party.

Because every party gets *some* vote share in every constituency, the AI constantly learns what makes a party perform well, even in places where they ultimately lose. By learning how to calculate vote shares, the model organically figures out how traditional strongholds might tip toward a third party in extremely close races.

### 3. Paying Extra Attention to Rare Events
If left to its own devices, an AI will naturally ignore rare events (like an independent candidate winning a seat) to focus on the big, common patterns. During training, we use specialized math techniques that force the AI to pay extra attention to these incredibly rare scenarios, keeping it from taking the easy way out and predicting LDF/UDF every single time.

## A Word on How the Model Thinks

It's important to understand what this AI is actually doing behind the scenes. 

Usually, to build a "true" predictive AI, you feed it historical data (like 2011 election factors) and ask it to predict the 2016 outcome. Once it learns those rules against hard historical truth, you use it to predict the future. 

However, because we don't have perfectly paired historical data stretching back decades, we had to be creative. Our dataset builder (`create_dataset.py`) acts as a **human logic engine**: it takes the most recent available data (2021 results, 2024 parliamentary momentum, etc.) and uses documented political science formulas to estimate a "projected truth." 

Our neural network then trains on this data. What it's actually doing is **learning to deeply mimic that political human logic**, smoothing out the hard math, and finding hidden relationships between demographics, geography, and political momentum. It acts as an incredible digital strategist applying complex political logic statewide, rather than an independent crystal ball.

## Usage

Generate the dataset:
```bash
python backend/create_dataset.py
```

Train the ensemble and output predictions:
```bash
python backend/train.py
```

The final output is saved to `backend/predictions_2026.csv`.

## Frontend + Backend (Single Command)

This project now includes:
- `frontend/` for dashboard UI
- `backend/` for API (`/api/predictions`)

Run both with one command:

```bash
python run.py
```

Then open:
- Frontend: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8001/api/predictions`

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
