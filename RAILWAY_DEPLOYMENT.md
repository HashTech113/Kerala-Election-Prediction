# Railway Deployment Guide

This guide explains how to deploy the Kerala Election Prediction project to Railway.

## Prerequisites

- Railway account (https://railway.app)
- `npm` and `python` installed locally
- Git repository initialized

## Step 1: Create Railway Projects

You need to create TWO separate Railway projects:
1. **Backend** (Python) - for the prediction API
2. **Frontend** (React/TypeScript) - for the Vite dashboard

### Creating Backend Project

```bash
# Log in to Railway
npx -y @railway/cli login

# Link to workspace
npx -y @railway/cli link

# Select your workspace and create a new project named "kerala-election-backend"
npx -y @railway/cli init

# Set service name to "python"
# This creates railwayproject.backend.json
```

### Creating Frontend Project

```bash
# In the same workspace, create another project for frontend
# You can create it via the Railway dashboard or CLI

# Or create it in the same repository under a different service
npx -y @railway/cli link

# Select your workspace and create project "kerala-election-frontend"
```

## Step 2: Configure Environment Variables

### Backend Environment Variables (Railway Dashboard)

Go to Railway Dashboard → Your Backend Project → Variables

Add these variables:

```
RAILWAY_ENVIRONMENT=production
PORT=8000
USE_REAL_APIS=0

# Optional: Add API keys if you want to use real data sources
X_BEARER_TOKEN=
YOUTUBE_API_KEY=
NEWS_API_KEY=
```

### Frontend Environment Variables (Railway Dashboard)

Go to Railway Dashboard → Your Frontend Project → Variables

Add this variable (replace with your actual backend Railway URL):

```
VITE_API_BASE_URL=https://your-backend-app.up.railway.app
```

**To find your backend URL:**
1. Go to Railway Dashboard → Backend Project
2. Click "Deployments"
3. Find the public URL in the deployment details
4. Use that URL (without `/api/...`) as the `VITE_API_BASE_URL`

## Step 3: Configure Build & Start Commands

### Backend Configuration

Your `backend/` needs a way for Railway to find and run the Python server.

**Option A: Python with Gunicorn (Recommended)**

Create `Procfile` in root:
```
web: gunicorn -w 1 -b 0.0.0.0:$PORT backend.server:app
```

But since we use built-in HTTP server, use:

```
web: python -c "from backend.server import main; main('0.0.0.0', int(__import__('os').environ.get('PORT', 8000)))"
```

**Option B: Direct Python (Simpler)**

Modify your `backend/server.py` to read PORT from environment:

```python
def main(host="0.0.0.0", port=None):
    import os
    if port is None:
        port = int(os.environ.get("PORT", 8001))
    
    server = ThreadingHTTPServer((host, port), ElectionAPIHandler)
    print(f"Backend API running on http://{host}:{port}")
    server.serve_forever()
```

### Frontend Configuration

Create `railway.json` in frontend directory:

```json
{
  "build": {
    "builder": "nixpacks",
    "buildCommand": "npm install && npm run build"
  },
  "start": "npm run preview"
}
```

Or add to `package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0 --port $PORT"
  }
}
```

## Step 4: Update Backend to Accept Railway PORT

Modify `backend/server.py` main function:

```python
def main(host=None, port=None):
    import os
    
    if host is None:
        host = os.environ.get("RAILWAY_HOST", "127.0.0.1")
    if port is None:
        port = int(os.environ.get("PORT", os.environ.get("RAILWAY_PORT", 8001)))
    
    server = ThreadingHTTPServer((host, port), ElectionAPIHandler)
    print(f"Backend API running on http://{host}:{port}")
    server.serve_forever()
```

## Step 5: Deploy to Railway

### Deploy Backend

```bash
# In project root
npx -y @railway/cli up --service backend

# Or via Railway Dashboard - push to linked git branch
```

### Deploy Frontend

```bash
# In project root
npx -y @railway/cli up --service frontend

# Or specify frontend directory
npx -y @railway/cli up --service frontend --path frontend
```

## Step 6: Verify Deployment

### Test Backend Health

Open in browser (replace URL):
```
https://your-backend-app.up.railway.app/api/health
```

Should return:
```json
{"status": "ok"}
```

### Test Frontend

Open in browser (replace URL):
```
https://your-frontend-app.up.railway.app
```

Should load dashboard and display data.

## Troubleshooting

### Backend API Not Responding

Check Railway logs:
```bash
npx -y @railway/cli logs --service backend
```

Common issues:
- PORT not set → Add PORT to environment variables
- Missing predictions_2026.csv → Run `python backend/create_dataset.py` locally and commit to git
- CORS errors → Verify Access-Control headers are present (they already are)

### Frontend Cannot Reach Backend

1. Verify `VITE_API_BASE_URL` is set correctly in frontend environment
2. Check console errors (F12 → Console tab)
3. Test backend health endpoint directly in browser
4. Verify CORS headers from backend:
   ```bash
   curl -I https://your-backend-app.up.railway.app/api/health
   ```

### Build Fails

Check Railway logs for detailed error:
```bash
npx -y @railway/cli logs --service frontend
```

## Environment URLs Reference

**Local Development:**
- Frontend: http://127.0.0.1:5173
- Backend: http://127.0.0.1:8001

**Production (Railway):**
- Frontend: https://your-app.up.railway.app
- Backend: https://your-backend.up.railway.app
- Frontend API config: `VITE_API_BASE_URL=https://your-backend.up.railway.app`

## Next Steps

1. Create Railway projects via dashboard
2. Link with CLI: `npx -y @railway/cli link`
3. Set environment variables in Railway Dashboard
4. Push code to git (Railway auto-deploys on push)
5. Monitor via Railway Dashboard or `npx -y @railway/cli logs`

## Useful Commands

```bash
# Check current environment
npx -y @railway/cli whoami

# View logs
npx -y @railway/cli logs

# Deploy specific service
npx -y @railway/cli up --service backend
npx -y @railway/cli up --service frontend

# Set environment variable
npx -y @railway/cli variables set VITE_API_BASE_URL https://...

# List variables
npx -y @railway/cli variables
```

---

**Ready to deploy!** 🚀
