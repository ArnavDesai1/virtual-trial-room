# Render Deployment - Complete Setup Guide

## Status: Ready to Deploy! ✅

Your code has been pushed to GitHub with all security fixes.

---

## Step-by-Step Render Deployment

### Step 1: Create Render Account (if you don't have one)

1. Go to https://render.com
2. Click **"Sign Up"**
3. Choose **"Sign up with GitHub"**
4. Authorize Render to access your repositories
5. Done!

---

### Step 2: Create a New Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** button
3. Select **"Web Service"**
4. Find and select `virtual-trial-room` repository
5. Click **"Connect"**

---

### Step 3: Configure Service Settings

Fill in the form with these values:

| Setting | Value |
|---------|-------|
| **Name** | `virtual-trial-room` |
| **Environment** | `Python 3` |
| **Region** | Pick closest to you (US/EU) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -w 2 -b 0.0.0.0 -t 120 Files.main:app` |
| **Plan** | `Free` (if available) or `Starter` |

---

### Step 4: Add Environment Variables

This is IMPORTANT - your API key goes here, NOT in the code:

1. In the same form, find **"Environment"** section
2. Click **"Add Secret File"** or **"Add Environment Variable"**
3. Add these variables:

```
FLASK_ENV=production

FIREBASE_API_KEY=AIzaSyCfaeh8cB_vkL17FLd9qIAYXQywLBAHkqM
FIREBASE_AUTH_DOMAIN=virtual-trial-room-3cff3.firebaseapp.com
FIREBASE_PROJECT_ID=virtual-trial-room-3cff3
FIREBASE_STORAGE_BUCKET=virtual-trial-room-3cff3.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=678744292818
FIREBASE_APP_ID=1:678744292818:web:a31747dd608d86b21f1c0b
FIREBASE_MEASUREMENT_ID=G-10TCLDZE4X
```

**IMPORTANT:** These are set in Render's secure dashboard, NOT in your code!

---

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait for build and deployment (3-5 minutes)
3. You'll see deployment logs in real-time
4. Once deployed, Render gives you a URL like: `https://virtual-trial-room.onrender.com`

---

## Test Your Deployment

Once deployed, test these:

### Test 1: Homepage works
```
https://your-render-url/
```
Should load your homepage ✅

### Test 2: Firebase Config endpoint
```
https://your-render-url/api/firebase-config
```
Should return JSON with Firebase settings ✅

### Test 3: Product page
```
https://your-render-url/product
```
Should load products ✅

### Test 4: Firebase Login (in browser console)
Visit your site and check:
- Open DevTools (F12)
- Go to Console tab
- Should see "Firebase initialized successfully" ✅

---

## How Your App Works on Render

```
User visits https://your-render-url
    ↓
App loads index.html
    ↓
JavaScript loads and requests /api/firebase-config
    ↓
Backend sends Firebase config (with API key from env variable)
    ↓
Frontend initializes Firebase with config
    ↓
Login, cart, checkout all work! ✅
```

**Key Security Point:** Your API key never goes to the browser - it's only visible on the backend server!

---

## Important Notes

### What Works on Render:
- ✅ Homepage, Products, Contact, About
- ✅ Shopping Cart
- ✅ Checkout page
- ✅ Firebase Authentication (Google/Email)
- ✅ All frontend features

### What Doesn't Work on Render:
- ❌ Video Feed (`/video_feed`) - No camera on server
- ❌ Try-on Scripts (`/tryon/<path>`) - No GUI on server
- ❌ Tkinter windows - No display server

**This is expected!** These features need webcam & GUI, which aren't available in cloud.

---

## Monitoring & Logs

### View Live Logs
1. Go to https://dashboard.render.com
2. Select your service
3. Click **"Logs"** tab
4. See real-time server output

### Watch for Errors
If something breaks:
1. Check the Logs
2. Common issues:
   - Missing environment variable → Add to dashboard
   - Module not found → Check requirements.txt
   - Port error → Render auto-assigns port

---

## Updates & Redeploy

### Auto-Redeploy on Push
Render automatically redeploys when you push to GitHub!

```powershell
# Make changes locally
git add .
git commit -m "Your changes"
git push origin main

# Render automatically deploys! Check dashboard for status
```

### Manual Redeploy
If needed, in Render dashboard:
1. Select your service
2. Click **"Manual Deploy"**
3. Choose branch (main)
4. Click **"Deploy"**

---

## Troubleshooting

### Build Failed
- Check logs for error messages
- Common: Missing dependency → Add to requirements.txt
- Run locally to verify: `python Files/main.py`

### App crashes after deploy
- Check environment variables are set correctly
- Verify FIREBASE_API_KEY is in Render variables
- Check build command output

### Firebase not initializing
- Open DevTools Console
- Look for error messages
- Ensure /api/firebase-config endpoint is working

### Need more details?
Visit https://render.com/docs for full documentation

---

## You're All Set! 🚀

- ✅ Code pushed to GitHub
- ✅ API key secured (in env variables)
- ✅ Ready for Render deployment
- ✅ All instructions prepared

**Next Step:** Follow the steps above to create and deploy on Render!

**Your App URL will be:** `https://virtual-trial-room.onrender.com`

Share this URL to show your awesome project! 🎉

---

## Quick Checklist Before Deploying

- [ ] GitHub account ready
- [ ] Render account created
- [ ] Repository connected to Render
- [ ] Environment variables added in Render dashboard
- [ ] Ready to click "Create Web Service"

All set? Click that button and watch your app go live! 🚀
