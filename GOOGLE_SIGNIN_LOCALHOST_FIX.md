# 🔧 Google Sign-In Localhost Fix

## Problem
Google Sign-In doesn't work on `localhost:5000` because Firebase requires authorized domains to be configured.

## Solution

### Step 1: Add Localhost to Firebase Authorized Domains

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **virtual-trial-room-3cff3**
3. Navigate to: **Authentication** → **Settings** → **Authorized domains**
4. Click **"Add domain"**
5. Add these domains:
   - `localhost`
   - `127.0.0.1`
   - `127.0.0.1:5000` (if needed)

### Step 2: Configure OAuth Consent Screen (Google Cloud Console)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: **virtual-trial-room-3cff3**
3. Navigate to: **APIs & Services** → **OAuth consent screen**
4. Under **Authorized JavaScript origins**, add:
   - `http://localhost:5000`
   - `http://127.0.0.1:5000`
5. Under **Authorized redirect URIs**, add:
   - `http://localhost:5000`
   - `http://127.0.0.1:5000`

### Step 3: Verify Firebase Config

The code already includes:
```javascript
provider.setCustomParameters({
    prompt: 'select_account'
});
```

This helps with account selection on localhost.

### Step 4: Test

1. Clear browser cache
2. Try Google Sign-In again
3. Check browser console for errors

## Alternative: Use ngrok for Testing

If localhost still doesn't work, use ngrok:

1. Install ngrok: `npm install -g ngrok`
2. Run: `ngrok http 5000`
3. Use the ngrok URL (e.g., `https://abc123.ngrok.io`)
4. Add this URL to Firebase authorized domains
5. Access your app via the ngrok URL

## Code Changes Made

✅ Updated `firebase-integration.js`:
- Added `prompt: 'select_account'` to Google provider
- This ensures account selection works properly

## Status

- ✅ Code updated to support localhost
- ⚠️ **Action Required**: Add localhost to Firebase Console authorized domains
- ⚠️ **Action Required**: Configure OAuth consent screen in Google Cloud Console

---

**Note**: The code is ready, but you need to configure Firebase Console and Google Cloud Console for localhost to work.


