# Railway Deployment Checklist

This checklist helps you deploy the Kerala Election Prediction app to Railway.

## Pre-Deployment Checklist ✅

- [ ] Railway account created (https://railway.app)
- [ ] Git repository initialized and pushed to GitHub
- [ ] Local build works: `npm run build` (frontend) and `python backend/train.py` (backend)
- [ ] `predictions_2026.csv` exists locally in `backend/` folder

## Backend Deployment

### Step 1: Create Backend Project
```bash
cd /path/to/project
npx -y @railway/cli login
npx -y @railway/cli link

# Select workspace and create NEW project "kerala-election-backend"
```

### Step 2: Set Environment Variables (Railway Dashboard)
Go to: Railway Dashboard → Backend Project → Variables

Add:
```
PORT=8000
HOST=0.0.0.0
```

Optional (for live data):
```
USE_REAL_APIS=0
X_BEARER_TOKEN=your_twitter_token
YOUTUBE_API_KEY=your_youtube_key
NEWS_API_KEY=your_news_api_key
```

### Step 3: Push/Deploy
```bash
git push origin main
# Railway auto-deploys when you linked it with `railway link`
```

### Step 4: Verify Backend
Open in browser (get URL from Railway Dashboard → Deployments):
```
https://your-backend.up.railway.app/api/health
```
Should return: `{"status": "ok"}`

## Frontend Deployment

### Step 1: Create Frontend Project
```bash
# In Dashboard, create NEW project "kerala-election-frontend"
# Or use CLI in frontend directory after linking
```

### Step 2: Set Environment Variables (Railway Dashboard)
Go to: Railway Dashboard → Frontend Project → Variables

Replace `YOUR_BACKEND_URL` with your actual backend Railway URL (from Step 4 above):

```
VITE_API_BASE_URL=https://YOUR_BACKEND_URL
```

Example:
```
VITE_API_BASE_URL=https://kerala-election-backend-production.up.railway.app
```

### Step 3: Push/Deploy
```bash
git push origin main
# Railway auto-deploys
```

### Step 4: Verify Frontend
Open in browser (get URL from Railway Dashboard → Deployments):
```
https://your-frontend.up.railway.app
```

Should load the dashboard and display election predictions.

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
npx -y @railway/cli logs --service backend
```

**Solution:** Make sure `PORT` environment variable is set to `8000` in Railway Dashboard

### Frontend Shows "Backend Error"
1. Check browser console (F12 → Console)
2. Verify `VITE_API_BASE_URL` is correct in Railway Dashboard
3. Test backend directly: `https://your-backend.up.railway.app/api/health`
4. CORS should be fine (headers already set)

### "Cannot find predictions_2026.csv"
1. Run locally: `python backend/create_dataset.py` and `python backend/train.py`
2. Commit `predictions_2026.csv` to git repo
3. Push to GitHub
4. Redeploy on Railway

### 404 on Frontend Routes
The frontend uses client-side routing (Vite), so Railway might need configuration. Check `frontend/vite.config.ts` - it should handle this automatically.

## Final URLs to Test

**Backend Health:**
```
https://your-backend.up.railway.app/api/health
```

**Backend Predictions:**
```
https://your-backend.up.railway.app/api/predictions
```

**Frontend:**
```
https://your-frontend.up.railway.app
```

## After Successful Deployment

1. Share your frontend URL: `https://your-app.up.railway.app`
2. Monitor logs: `npx -y @railway/cli logs`
3. Update env vars if needed: `npx -y @railway/cli variables set KEY VALUE`
4. Redeploy if code changes: `git push origin main` (auto-deploys with Railway connected)

---

**Deployed! Your app is live on Railway!** 🚀
