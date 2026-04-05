# 🚨 QUICK FIX: Google Sign-In Error (auth/unauthorized-domain)

## The Problem
You're seeing: `Firebase: Error (auth/unauthorized-domain)`

This happens because Firebase requires you to explicitly authorize `localhost` and `127.0.0.1` as valid domains.

---

## ✅ SOLUTION (Takes 2 Minutes)

### Step 1: Open Firebase Console
1. Go to: https://console.firebase.google.com/
2. Select your project: **virtual-trial-room-3cff3**

### Step 2: Add Authorized Domains
1. Click **Authentication** in the left sidebar
2. Click **Settings** tab (at the top)
3. Scroll down to **Authorized domains** section
4. You'll see domains like:
   - `virtual-trial-room-3cff3.firebaseapp.com`
   - `virtual-trial-room-3cff3.web.app`
5. Click **"Add domain"** button
6. Add these domains one by one:
   - `localhost`
   - `127.0.0.1`
7. Click **"Add"** for each

### Step 3: Verify
After adding, you should see:
- ✅ `localhost`
- ✅ `127.0.0.1`
- ✅ `virtual-trial-room-3cff3.firebaseapp.com`
- ✅ `virtual-trial-room-3cff3.web.app`

### Step 4: Test
1. Refresh your browser page (clear cache: Ctrl+Shift+R)
2. Try Google Sign-In again
3. It should work now! ✅

---

## 📸 Visual Guide

```
Firebase Console
├─ Authentication
│  └─ Settings
│     └─ Authorized domains
│        ├─ virtual-trial-room-3cff3.firebaseapp.com
│        ├─ virtual-trial-room-3cff3.web.app
│        ├─ localhost          ← ADD THIS
│        └─ 127.0.0.1          ← ADD THIS
```

---

## ⚠️ If Still Not Working

### Option 1: Check Google Cloud Console
1. Go to: https://console.cloud.google.com/
2. Select project: **virtual-trial-room-3cff3**
3. Navigate to: **APIs & Services** → **OAuth consent screen**
4. Under **Authorized JavaScript origins**, add:
   - `http://localhost:5000`
   - `http://127.0.0.1:5000`
5. Click **Save**

### Option 2: Use ngrok (Alternative)
If localhost still doesn't work:

1. Install ngrok:
   ```bash
   npm install -g ngrok
   ```

2. Run ngrok:
   ```bash
   ngrok http 5000
   ```

3. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

4. Add this URL to Firebase authorized domains

5. Access your app via the ngrok URL instead of localhost

---

## ✅ What I Fixed in Code

I've updated the error handling to show a clearer message when this error occurs. The code now detects `auth/unauthorized-domain` and provides helpful instructions.

**File Modified:**
- `Files/static/js/firebase-integration.js` - Better error handling

---

## 🎯 Quick Checklist

- [ ] Opened Firebase Console
- [ ] Went to Authentication → Settings
- [ ] Added `localhost` to authorized domains
- [ ] Added `127.0.0.1` to authorized domains
- [ ] Refreshed browser (Ctrl+Shift+R)
- [ ] Tested Google Sign-In

---

## 💡 Why This Happens

Firebase requires explicit authorization for security. By default, only your Firebase hosting domains are authorized. For local development, you must manually add `localhost` and `127.0.0.1`.

This is a **one-time setup** - once configured, it will work for all future development sessions.

---

**After completing Step 2, Google Sign-In should work immediately!** 🎉


