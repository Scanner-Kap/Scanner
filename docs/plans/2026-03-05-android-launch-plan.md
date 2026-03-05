# India First — Android Launch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Get the India First app running on a real Android device via Expo Go, then build and publish to the Google Play Store.

**Architecture:** Expo Go for instant device testing → EAS cloud build for signed APK/AAB → Play Store Internal Testing → Production. Backend hosted on Railway/Render for production users.

**Tech Stack:** Expo / React Native, EAS CLI, FastAPI, PostgreSQL, Railway or Render

---

## Phase 1 — Test on Android with Expo Go

### Task 1: Find your local IP address

**Step 1: Get your machine's local IP**

On Mac:
```bash
ipconfig getifaddr en0
```
Expected output: something like `192.168.1.42`

Save this IP — you'll use it in the next task.

---

### Task 2: Create frontend environment file

**Files:**
- Create: `frontend/.env`

**Step 1: Create the file**

```bash
cd ~/Scanner/frontend
```

Create `frontend/.env` with this content (replace `<YOUR_IP>` with the IP from Task 1):
```
EXPO_PUBLIC_BACKEND_URL=http://<YOUR_IP>:8000
```

Example:
```
EXPO_PUBLIC_BACKEND_URL=http://192.168.1.42:8000
```

**Step 2: Verify the file exists**

```bash
cat frontend/.env
```
Expected: shows your EXPO_PUBLIC_BACKEND_URL line.

---

### Task 3: Start the backend

**Step 1: Start PostgreSQL (if not running)**

```bash
brew services start postgresql@14
```
Or if you use the default:
```bash
brew services start postgresql
```

**Step 2: Start the FastAPI backend**

```bash
cd ~/Scanner/backend
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Step 3: Verify it's running** (in a new terminal tab)

```bash
curl http://localhost:8000/api/
```
Expected: `{"message":"India First - FMCG Intelligence API","version":"1.0"}`

Leave this terminal running.

---

### Task 4: Start the Expo dev server

**Step 1: Install dependencies (if not done)**

```bash
cd ~/Scanner/frontend
npm install --legacy-peer-deps
```

**Step 2: Start Expo**

```bash
npx expo start
```

Expected: A QR code appears in the terminal.

**Step 3: Install Expo Go on your Android device**

On your Android phone, open the Play Store and install **Expo Go** (by Expo).

**Step 4: Scan the QR code**

Open Expo Go → tap "Scan QR code" → scan the QR code in your terminal.

Expected: India First app loads on your phone within 30 seconds.

**Step 5: Test the app**

Navigate through: Home → Search → tap a brand → verify India Interest Score displays correctly.

---

## Phase 2 — EAS Build (Signed APK/AAB)

### Task 5: Set up EAS account and CLI

**Step 1: Create a free Expo account**

Go to [expo.dev](https://expo.dev) → Sign Up → verify your email.

**Step 2: Install EAS CLI**

```bash
npm install -g eas-cli
```

**Step 3: Login**

```bash
eas login
```

Enter your expo.dev email and password when prompted.

**Step 4: Verify login**

```bash
eas whoami
```
Expected: your expo.dev email address.

---

### Task 6: Configure EAS for the project

**Files:**
- Create: `frontend/eas.json`

**Step 1: Run EAS configure**

```bash
cd ~/Scanner/frontend
eas build:configure
```

When asked "Which platforms would you like to configure?" → select **Android**.

**Step 2: Replace the generated eas.json with this content**

Edit `frontend/eas.json`:
```json
{
  "cli": {
    "version": ">= 16.0.0"
  },
  "build": {
    "preview": {
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```

**Step 3: Commit**

```bash
git add frontend/eas.json
git commit -m "Add EAS build configuration"
git push origin claude/build-scanner-app-axlSK
```

---

### Task 7: Build preview APK (for device testing)

**Step 1: Run EAS preview build**

```bash
cd ~/Scanner/frontend
eas build --platform android --profile preview
```

When asked "Generate a new Android Keystore?" → Yes.

Expected: Build queued in Expo's cloud. You'll get a URL to monitor progress.

**Step 2: Wait for build to complete (~15-20 min)**

Monitor at the URL printed in terminal, or at [expo.dev/builds](https://expo.dev/builds).

**Step 3: Download and install the APK**

When complete, download the `.apk` file from the Expo dashboard.

Send it to your Android device (email, Google Drive, AirDrop equivalent) and install it.

If prompted "Install from unknown sources" → allow it in Android Settings → Security.

**Step 4: Test barcode scanning**

Open the installed app → tap Scanner → point at any product barcode.

Verify the scan works and the India Interest Score displays.

---

## Phase 3 — Backend Hosting

### Task 8: Deploy backend to Railway

**Step 1: Create Railway account**

Go to [railway.app](https://railway.app) → Sign up with GitHub.

**Step 2: Create a new project**

Click "New Project" → "Deploy from GitHub repo" → select `Scanner-Kap/Scanner`.

**Step 3: Configure the service**

In Railway dashboard:
- Set **Root Directory** to `backend`
- Set **Start Command** to: `uvicorn server:app --host 0.0.0.0 --port $PORT`

**Step 4: Add PostgreSQL**

In Railway project → click "New" → "Database" → "PostgreSQL".

Railway will automatically set `DATABASE_URL`. You need to add it as `POSTGRES_URL`:
- Go to your backend service → Variables tab
- Add: `POSTGRES_URL` = (copy the value of `DATABASE_URL` shown by Railway)

**Step 5: Get your public URL**

In Railway dashboard → your backend service → "Settings" → copy the generated domain.

It will look like: `https://scanner-backend-production.up.railway.app`

**Step 6: Test it**

```bash
curl https://<your-railway-url>/api/
```
Expected: `{"message":"India First - FMCG Intelligence API","version":"1.0"}`

---

### Task 9: Update EAS to use hosted backend

**Files:**
- Modify: `frontend/eas.json`

**Step 1: Add production backend URL to eas.json**

Edit `frontend/eas.json` to add env variables:

```json
{
  "cli": {
    "version": ">= 16.0.0"
  },
  "build": {
    "preview": {
      "android": {
        "buildType": "apk",
        "env": {
          "EXPO_PUBLIC_BACKEND_URL": "https://<your-railway-url>"
        }
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle",
        "env": {
          "EXPO_PUBLIC_BACKEND_URL": "https://<your-railway-url>"
        }
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```

Replace `<your-railway-url>` with your actual Railway URL from Task 8.

**Step 2: Build production AAB**

```bash
cd ~/Scanner/frontend
eas build --platform android --profile production
```

Wait ~15-20 minutes. Download the `.aab` file when complete.

**Step 3: Commit**

```bash
git add frontend/eas.json
git commit -m "Configure EAS with hosted backend URL"
git push origin claude/build-scanner-app-axlSK
```

---

## Phase 4 — Publish to Play Store

### Task 10: Create Play Store listing

**Step 1: Create Google Play Developer account**

Go to [play.google.com/console](https://play.google.com/console) → pay $25 one-time fee → verify identity.

**Step 2: Create a new app**

- Click "Create app"
- App name: `India First`
- Default language: English (or Hindi)
- App type: App
- Free/Paid: Free
- Accept policies → Create app

**Step 3: Fill in store listing**

Go to "Store listing" and fill in:
- Short description (80 chars max): `Scan barcodes to check if products are truly Indian-made`
- Full description: Describe the India Interest Score, scoring factors, and supported brands
- App icon: upload `frontend/assets/images/icon.png` (must be 512x512 PNG)
- Screenshots: take at least 2 screenshots from your Android device running the app

**Step 4: Create a privacy policy**

The Play Store requires a privacy policy URL. Create a simple one using [privacypolicygenerator.info](https://privacypolicygenerator.info) and host it (GitHub Pages, Notion public page, etc.).

Add the URL in Play Console → Store listing → Privacy policy.

---

### Task 11: Upload AAB to Internal Testing

**Step 1: Go to Internal Testing track**

Play Console → Testing → Internal testing → Create new release.

**Step 2: Upload AAB**

Upload the `.aab` file downloaded from EAS in Task 9.

**Step 3: Add testers**

Go to "Testers" tab → add email addresses of people who should test the app (up to 100).

**Step 4: Share the opt-in link**

Copy the Internal Testing opt-in URL → share with your testers.

Testers install via Play Store (not sideloading) — no Google review needed for Internal Testing.

---

### Task 12: Promote to Production

**Step 1: Verify with testers**

Confirm with at least 1-2 testers that:
- App installs correctly
- Barcode scanning works
- India Interest Score displays correctly
- Search works

**Step 2: Promote to Production**

Play Console → Internal testing → your release → "Promote release" → Production.

Fill in release notes (what's new): `Initial release of India First.`

**Step 3: Submit for review**

Click "Review release" → "Start rollout to Production".

Google review takes 1-3 business days for new apps.

**Step 4: App goes live**

Once approved, your app is searchable on the Play Store at:
`https://play.google.com/store/apps/details?id=com.indiafirst.app`

---

## Success Criteria

- [ ] App loads on Android device via Expo Go (Task 4)
- [ ] Signed APK installs and barcode scanning works (Task 7)
- [ ] Backend responds at hosted URL (Task 8)
- [ ] Production AAB built with hosted backend URL (Task 9)
- [ ] Internal testers can install from Play Store (Task 11)
- [ ] App visible in Play Store Production track (Task 12)
