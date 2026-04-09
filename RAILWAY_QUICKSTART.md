# Railway Deployment - Quick Start

## What's Already Done ✅

**Backend:**
- ✅ `PORT` environment variable support (reads from Railway)
- ✅ CORS headers configured correctly
- ✅ `Procfile` setup for Railway
- ✅ API endpoints `/api/health` and `/api/predictions` ready

**Frontend:**
- ✅ Environment variables with `VITE_API_BASE_URL`
- ✅ API service configured to use environment URL
- ✅ `railway.json` configuration
- ✅ Production build ready

## 5-Minute Railway Setup

### 1️⃣ Create Backend Project on Railway

```bash
npx -y @railway/cli login
npx -y @railway/cli link

# Select workspace
# Create NEW project named "kerala-election-backend"
```

**Set Backend Environment Variables:**
- `PORT` = `8000`
- `HOST` = `0.0.0.0` (optional, defaults to it)

### 2️⃣ Create Frontend Project on Railway

In Railway Dashboard, create another NEW project: `kerala-election-frontend`

### 3️⃣ Get Your Backend URL

In Railway Dashboard:
- Go to Backend Project → Deployments
- Copy the PUBLIC URL (format: `https://xxxxx.up.railway.app`)

### 4️⃣ Set Frontend Environment Variable

In Railway Dashboard → Frontend Project → Variables:

```
VITE_API_BASE_URL=https://[YOUR_BACKEND_URL]
```

Replace `[YOUR_BACKEND_URL]` with URL from step 3.

### 5️⃣ Deploy

```bash
git push origin main
```

Railway auto-deploys when connected. Watch the deployments in the dashboard.

## Verify It Works

**Test Backend:**
```
https://[YOUR_BACKEND_URL]/api/health
```
Should return: `{"status": "ok"}`

**Open Frontend:**
```
https://[YOUR_FRONTEND_URL]
```

Should see the election dashboard with data!

## Troubleshooting

### Backend not responding
- Check `PORT` environment variable is set to `8000`
- Check `HOST` is `0.0.0.0` or not set
- View logs: `npx -y @railway/cli logs`

### Frontend shows "Backend Error"
- Verify `VITE_API_BASE_URL` matches your backend URL exactly
- Test the URL directly in browser
- Check browser console (F12) for errors

### "Cannot find predictions_2026.csv"
- Run locally: `python backend/create_dataset.py`
- Run: `python backend/train.py`
- Commit `predictions_2026.csv` to git
- Push to trigger redeploy

---

## Environment Variables Summary

| Variable | Backend/Frontend | Value | Where to Set |
|----------|-----------------|-------|--------------|
| `PORT` | Backend | `8000` | Railway Dashboard |
| `HOST` | Backend | `0.0.0.0` | Railway Dashboard (optional) |
| `VITE_API_BASE_URL` | Frontend | `https://your-backend.up.railway.app` | Railway Dashboard |

---

**That's it!** Your app is on Railway! 🚀

For detailed guides, see:
- `RAILWAY_DEPLOYMENT.md` – Full deployment guide
- `RAILWAY_CHECKLIST.md` – Step-by-step checklist
- `RAILWAY_VERIFICATION.md` – Component verification
