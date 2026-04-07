# 🚨 Security Fix: Leaked Google API Key

**Status:** Your Google API Key was publicly leaked in GitHub

---

## Immediate Actions (DO THESE NOW)

### 1. ✅ Revoke ALL Compromised Keys

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project: `virtual-trial-room-3cff3`
3. Navigate to **APIs & Services** → **Credentials**
4. Find and **DELETE** all API keys (they're compromised)
5. Create **NEW API Keys** for:
   - Browser API key (for frontend Firebase)
   - Server API key (if you have backend services)

### 2. ✅ Clean Git History

```powershell
cd "c:\Users\theel\Documents\LY SEM 7\Final yr project\Virtual-Trial-Room"

# Remove sensitive files from git history (requires git-filter-repo)
pip install git-filter-repo
git filter-repo --invert-paths --path FILES_WITH_KEYS.txt

# Or simpler - force push after cleanup (⚠️ destructive)
git reset --hard
git clean -fd
```

### 3. ✅ Add `.gitignore`

✅ Already created (see `.gitignore` file)

This prevents future leaks of:
- `.env` files
- `*_secret.js` files
- `api_keys.json`
- All secrets

---

## Implementation: Use Environment Variables

### Step 1: Create `.env` file (LOCAL ONLY - NOT in git)

```
FIREBASE_API_KEY=AIzaSyCfaeh8cB_vkL17FLd9qIAYXQywLBAHkqM  # NEW KEY AFTER ROTATION
FIREBASE_AUTH_DOMAIN=virtual-trial-room-3cff3.firebaseapp.com
FIREBASE_PROJECT_ID=virtual-trial-room-3cff3
```

### Step 2: Update Flask to serve config

Create `Files/config.py`:

```python
import os
from flask import Flask

def get_firebase_config():
    return {
        "apiKey": os.environ.get("FIREBASE_API_KEY", ""),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "virtual-trial-room-3cff3.firebaseapp.com"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID", "virtual-trial-room-3cff3"),
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "virtual-trial-room-3cff3.firebasestorage.app"),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "678744292818"),
        "appId": os.environ.get("FIREBASE_APP_ID", "1:678744292818:web:a31747dd608d86b21f1c0b"),
        "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID", "G-10TCLDZE4X")
    }
```

### Step 3: Update main.py to serve config

Add to `Files/main.py`:

```python
from config import get_firebase_config

@app.route('/config')
def config():
    return jsonify(get_firebase_config())
```

### Step 4: Update firebase-integration.js to fetch config

```javascript
// Instead of hardcoded config:
const response = await fetch('/config');
const firebaseConfig = await response.json();

const app = initializeApp(firebaseConfig);
```

---

## For Render Deployment

1. Go to your Render service dashboard
2. Go to **Environment**
3. Add environment variables:
   - `FIREBASE_API_KEY` = your new key from Google Cloud
   - `FIREBASE_AUTH_DOMAIN` = ...
   - etc.

Render will automatically use these when deploying.

---

## Checklist

- [ ] 1. Created NEW API keys in Google Cloud Console
- [ ] 2. Deleted ALL compromised keys  
- [ ] 3. Created `.gitignore` file (✅ Done)
- [ ] 4. Created `.env.example` file (✅ Done)  
- [ ] 5. Create `.env` file locally with new keys (LOCAL ONLY)
- [ ] 6. Removed old keys from git history
- [ ] 7. Push clean code to GitHub
- [ ] 8. Set environment variables on Render

---

## Quick Test

After cleanup, verify no keys are in repo:

```powershell
# Search for old key (should find nothing)
git log -p -S "AIzaSyCfaeh8cB_vkL17FLd9qIAYXQywLBAHkqM" | head -20
```

Should output: `(no matches)`

---

## Why This Matters

- **API Key leaked** = Anyone can use your Firebase project
- **Cost impact** = Potential charges on your account
- **Data risk** = Unauthorized database access
- **Compliance** = GitHub restrictions on your account

---

## Help?

The key is already rotated by GitHub's recommendation. Just follow the checklist above and you're secure!

🔒 **Your app is now secure** when these steps are complete.
