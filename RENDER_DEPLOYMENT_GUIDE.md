# Render Deployment Guide for Virtual Trial Room

## Important Note ⚠️
**Webcam & GUI features won't work on Render** because:
- Render is a headless server (no physical camera)
- The try-on scripts use tkinter (requires GUI display)

**Solution:** Keep video processing on your local machine. Deploy APIs that don't require webcam.

---

## Step 1: Prepare Your GitHub Repository

```bash
cd "c:\Users\theel\Documents\LY SEM 7\Final yr project\Virtual-Trial-Room"
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

**Make sure your repo has:**
- ✅ `requirements.txt` (already configured)
- ✅ `render.yaml` (just created)
- ✅ `Files/` folder with Flask app
- ✅ `Files/templates/` with HTML files
- ✅ `Files/static/` with CSS, JS, images

---

## Step 2: Create Render Account & Connect Repository

1. Go to https://render.com
2. Click **"Sign up"** → Sign up with GitHub
3. Authorize Render to access your GitHub repositories
4. Create New → **Web Service**
5. Select your Virtual-Trial-Room repository
6. Click "Connect"

---

## Step 3: Configure Deployment Settings

| Setting | Value |
|---------|-------|
| **Name** | `virtual-trial-room` |
| **Environment** | `Python 3` |
| **Start Command** | `gunicorn -w 2 -b 0.0.0.0 -t 120 Files.main:app` |
| **Branch** | `main` |
| **Plan** | `Free` (if available) or `Starter` |

---

## Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for build & deployment (3-5 minutes)
3. Your app will be live at: `https://virtual-trial-room.onrender.com`

---

## Step 5: Test Your Deployment

Once deployed, only these features will work on Render:

✅ **Working on Render:**
- Product pages (`/product`, `/contact`, `/about`)
- Shopping cart (`/cart`)
- Checkout page (`/checkout`)
- All frontend routes

❌ **NOT working on Render:**
- `/video_feed` (requires server camera)
- `/tryon/<path>` (launches tkinter GUI)
- Try-on scripts that open windows

---

## Alternative: Hybrid Deployment

**Best approach for your project:**

| Component | Where | Why |
|-----------|-------|-----|
| **Frontend** | Render or Vercel | Static HTML/CSS/JS |
| **Backend APIs** | Render | Shopping cart, checkout, products |
| **Video Processing** | Your Local Machine | Needs webcam & GUI |
| **Try-on** | Your Local Machine | Needs tkinter & OpenCV display |

---

## Troubleshooting

### Build fails with "ModuleNotFoundError: No module named 'cv2'"
- This is normal! OpenCV requires system libraries not available on free tier
- Solution: Use Render's Standard plan or remove unused try-on imports

### App crashes after deploy
Check logs: https://dashboard.render.com → select your service → "Logs"

### Need more features?
Contact Render support or upgrade to paid plan (Standard/Pro)

---

## Monitoring & Updates

After deployment:
1. Visit https://dashboard.render.com
2. Select your service
3. View real-time logs
4. Automatic redeploy on every `git push`

---

## Local Development Still Works!

Your local app at `http://localhost:5000` will continue to work perfectly:
- Webcam video feed ✅
- Try-on with GUI ✅
- Full functionality ✅

---

## Next Steps

1. Prepare GitHub repo
2. Sign up for Render
3. Deploy using these settings
4. Test at the provided URL
5. Share your cloud URL!

Good luck! 🚀
