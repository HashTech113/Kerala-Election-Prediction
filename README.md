# Owlytice Election Prediction

An end-to-end machine learning pipeline forecasting the 140 constituencies of the 2026 Kerala Legislative Assembly Elections.

## Professional Project Structure

```text
election/
├── backend/
│   ├── server.py                 # API server (serves /api/health and /api/predictions)
│   ├── create_dataset.py         # Generates election dataset CSVs
│   ├── train.py                  # Trains ensemble + writes predictions
│   ├── config.py                 # Shared configuration/constants
│   ├── data/                     # Data processing modules (loaders/extractors)
│   ├── models/                   # Model architecture modules
│   ├── utils/                    # Visualization and helper utilities
│   ├── data_files/               # Generated input datasets for training
│   │   ├── kerala_assembly_2026.csv
│   │   ├── kerala_demographics.csv
│   │   ├── kerala_loksabha_2024.csv
│   │   ├── kerala_sentiment_2026.csv
│   │   └── kerala_social_media_2026.csv
│   ├── checkpoints/              # Trained model checkpoints
│   ├── predictions_2026.csv      # Final model output used by frontend
│   └── instagram_post_2026.svg   # Generated static visual
├── frontend/
│   ├── index.html                # Frontend dashboard
│   └── package-lock.json
├── run.py                        # One-command launcher for backend + frontend
├── requirements.txt              # Python dependencies
└── README.md
```

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
