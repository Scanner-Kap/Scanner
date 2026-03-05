# India First — Android Testing & Play Store Launch Design

**Date:** 2026-03-05
**Status:** Approved

## Context

India First is an FMCG product intelligence app (React Native/Expo frontend, FastAPI + PostgreSQL backend) that scans barcodes and calculates an "India Interest Score". The native Android project has been generated via `expo prebuild`. The goal is to test on a real Android device and publish to the Play Store as quickly as possible.

## Architecture Assessment

The current stack requires no changes:
- FastAPI + PostgreSQL backend is production-ready
- Expo/React Native frontend targets iOS, Android, and Web
- Native Android project already generated (`frontend/android/`)

The only gap is deployment — the backend currently runs locally and needs hosting before the app can serve real users.

## Chosen Approach

**Option C (Expo Go) → Option A (EAS Build + Play Store)**

Test immediately on a real Android device using Expo Go, then build and publish via EAS cloud build service. No local Java or Android SDK required.

## Phases

### Phase 1 — Test Today with Expo Go

**Goal:** Validate the app works on a real Android device within minutes.

**Steps:**
1. Create `frontend/.env` with `EXPO_PUBLIC_BACKEND_URL=http://<local-ip>:8000`
2. Start backend: `python3 -m uvicorn server:app --host 0.0.0.0 --port 8000`
3. Start Expo dev server: `cd frontend && npx expo start`
4. Install **Expo Go** from Play Store on Android device
5. Scan the QR code shown in terminal → app loads on device

**Limitation:** Barcode scanning via camera may not work fully in Expo Go. All other screens (home, search, brand/product detail, scoring) will work.

### Phase 2 — Real Build via EAS

**Goal:** Build a signed APK/AAB in Expo's cloud with no local tooling required.

**Steps:**
1. Create free account at [expo.dev](https://expo.dev)
2. Install EAS CLI: `npm install -g eas-cli`
3. Login: `eas login`
4. Configure: `eas build:configure` (generates `eas.json`)
5. Build: `eas build --platform android --profile preview` (APK for direct install)
6. Build: `eas build --platform android --profile production` (AAB for Play Store)
7. Download APK → install on device to test real barcode scanning

**Build time:** ~15-20 minutes in Expo's cloud.

### Phase 3 — Play Store Publish

**Goal:** Publish the app to the Google Play Store.

**Steps:**
1. Create Google Play Developer account at [play.google.com/console](https://play.google.com/console) ($25 one-time fee)
2. Create new app in Play Console
3. Fill in store listing: description, screenshots, privacy policy URL
4. Upload `.aab` from Phase 2 to **Internal Testing** track
5. Share internal testing link with testers (up to 100, immediate, no review)
6. Promote to **Production** when validated (1-3 day Google review)

### Phase 4 — Backend Hosting

**Goal:** Host the backend so the app works for all users, not just local.

**Recommended:** Railway or Render (both have free tiers, support FastAPI + PostgreSQL)

**Steps:**
1. Deploy backend to Railway or Render
2. Provision a PostgreSQL database (both platforms support this)
3. Set `POSTGRES_URL` environment variable on the hosting platform
4. Update `EXPO_PUBLIC_BACKEND_URL` in `eas.json` / EAS environment variables to the hosted URL
5. Rebuild with `eas build` before submitting to Play Store

## eas.json Structure

```json
{
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
  }
}
```

## Success Criteria

- [ ] App loads and navigates correctly on a real Android device
- [ ] Barcode scanning works in the real APK build
- [ ] Backend is reachable from the device (not just localhost)
- [ ] App passes Play Store review and is visible in Production track
