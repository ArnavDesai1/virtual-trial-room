# 🚀 Railway Deployment Guide

This guide will help you deploy the Virtual Trial Room to **Railway.app** for **FREE**.

## What is Railway?
Railway is a modern hosting platform that supports Python applications and costs only what you use (generously free tier).

---

## Prerequisites

1. **GitHub Account** (already have it)
2. **Railway Account** - Sign up at https://railway.app (FREE)
3. **Your repository pushed to GitHub** ✅ (already done)

---

## Step-by-Step Deployment

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Click **"Start Project"**
3. Sign up with GitHub (recommended)
4. Authorize Railway to access your GitHub

### Step 2: Create New Project
1. On Railway dashboard, click **"+ New Project"**
2. Select **"Deploy from GitHub repo"**
3. Find your repo: **virtual-trial-room**
4. Click **"Import GitHub Repo"**

### Step 3: Configure Environment
Railway will automatically:
- Detect Python from `runtime.txt`
- Install dependencies from `requirements.txt`
- Run the command from `Procfile`

**That's it!** No additional configuration needed.

### Step 4: Monitor Deployment
1. You'll see logs starting to appear
2. Wait for deployment to complete (takes ~2-5 minutes)
3. You'll get a URL like: `https://your-app.railway.app`

### Step 5: Access Your Site
- Navigate to the Railway-generated URL
- Your Virtual Trial Room is now **LIVE!** 🎉

---

## What's Different from Local?

| Feature | Local | Railway |
|---------|-------|---------|
| URL | `localhost:5000` | `your-app.railway.app` |
| Debug Mode | ✅ Enabled | ❌ Production mode |
| Port | 5000 | Auto-assigned (via PORT env var) |
| Hostname | `localhost` | `0.0.0.0` |

---

## Camera Try-On on Deployed Site

**Important:** Camera access requires:
- **HTTPS** (Railway provides this automatically ✅)
- Browser permission to access camera (users will be prompted)
- Works on mobile AND desktop

---

## Troubleshooting

### "Build Failed"
- Check logs for specific errors
- Usually: missing dependency in `requirements.txt`
- Fix in local code → Push to GitHub → Railway auto-redeploys

### "App crashes after deploy"
- Check Railway logs for error messages
- Common: PORT not set (fixed in our config)
- Redeploy by pushing a new commit

### "Camera not working"
- Make sure you access via HTTPS (not HTTP)
- Check browser console for errors
- Ensure `tryOn_stable.py` is accessible

---

## File Changes Made for Deployment

These files were created/modified for Railway compatibility:

1. **Procfile** - Tells Railway how to run your app
2. **runtime.txt** - Specifies Python 3.10
3. **requirements.txt** - Updated with `gunicorn` and numpy fix
4. **Files/main.py** - Updated to support PORT env variable

---

## Redeploying After Changes

Every time you push to GitHub:
```bash
git add .
git commit -m "Your message"
git push
```

Railway automatically re-deploys! 🔄

---

## Production Tips

1. **Keep debug=False** ✅ (already set)
2. **Use gunicorn** ✅ (added to requirements)
3. **Monitor logs** on Railway dashboard
4. **Set up alerts** for failures

---

## Cost

- **Free tier**: Up to $5/month worth of compute
- Your Virtual Trial Room should fit easily in free tier
- Charges only apply after $5 usage

---

## Need Help?

- Railway Docs: https://docs.railway.app
- GitHub Issues: Report problems in your repo
- Railway Support: Available on dashboard

---

## Summary

✅ Repository ready
✅ Procfile created
✅ runtime.txt set
✅ requirements.txt updated
✅ App configured for production

**You're ready to deploy!** Follow Step 1-5 above to go live. 🚀

