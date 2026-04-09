# Environment Setup Guide

## Quick Start (Copy-Paste)

### 1. Create Backend `.env`
```bash
# From backend directory:
cp .env.example .env
```

Edit `backend/.env`:
```
PORT=8001
HOST=127.0.0.1
USE_REAL_APIS=0
```

### 2. Create Frontend `.env`
```bash
# From frontend directory:
cp .env.example .env
```

Edit `frontend/.env`:
```
VITE_API_BASE_URL=http://127.0.0.1:8001
```

### 3. Create Python Virtual Environment
```bash
# From project root:
python -m venv .venv

# Activate it
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 4. Ready to Run
```bash
# Backend
python backend/server.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

---

## File Structure

```
kerala-election-prediction/
├── .env                         ← Created locally (NOT in Git)
├── .env.example                 ← Template (IN Git, shared)
├── .gitignore                   ← Excludes .env, .venv
├── backend/
│   ├── .env                     ← Created locally (NOT in Git)
│   └── .env.example             ← Template (IN Git, shared)
├── frontend/
│   ├── .env                     ← Created locally (NOT in Git)
│   └── .env.example             ← Template (IN Git, shared)
└── .venv/                       ← Created locally (NOT in Git)
```

---

## Local Development Workflow

### First Time Setup
```bash
# 1. Clone repo
git clone https://github.com/your-user/kerala-election-prediction.git
cd kerala-election-prediction

# 2. You see .env.example files but NO .env files
# That's correct! You create your own:

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Edit .env files with your local values
nano backend/.env    # or use your editor
nano frontend/.env

# 4. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 5. Install Python packages
pip install -r requirements.txt

# 6. Install Node packages
cd frontend
npm install
cd ..

# 7. Run the app
python backend/server.py
# In another terminal:
cd frontend && npm run dev
```

### Day-to-Day
```bash
# Activate environment
.venv\Scripts\activate

# Pull latest code
git pull origin main

# Run app
python backend/server.py
cd frontend && npm run dev
```

---

## Production (Railway) Deployment

**You DON'T create `.env` files for production.**

Instead, set variables in **Railway Dashboard**:

### Backend Variables (Railway Dashboard)
```
PORT=8000
HOST=0.0.0.0
USE_REAL_APIS=0
```

### Frontend Variables (Railway Dashboard)
```
VITE_API_BASE_URL=https://your-backend.up.railway.app
```

---

## Important Rules ✅

| File | Rule | Why |
|------|------|-----|
| `.env` | ❌ NEVER commit | Contains your secrets & API keys |
| `.env.example` | ✅ ALWAYS commit | Shows team what variables are needed |
| `.venv/` | ❌ NEVER commit | Too large, everyone creates their own |
| `.gitignore` | ✅ ALWAYS commit | Protects `.env` & `.venv` from accidents |

---

## Troubleshooting

### "Cannot find module X"
```bash
# Make sure virtual environment is activated
.venv\Scripts\activate

# Reinstall packages
pip install -r requirements.txt
```

### "Frontend shows backend error"
1. Check backend is running: `python backend/server.py`
2. Check `VITE_API_BASE_URL` in `frontend/.env`
3. Test backend directly: `http://127.0.0.1:8001/api/health`

### ".env file not found"
```bash
# Create it from template
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Then edit with your values
```

---

## Summary

✅ `.env.example` = Share with team (template)  
❌ `.env` = Keep private (your secrets)  
❌ `.venv/` = Never commit (recreate locally)  
✅ `.gitignore` = Protects secrets automatically

That's it! 🎉
