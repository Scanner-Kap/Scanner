# Secrets & Credentials Reference

This document tracks where each secret lives so nothing is accidentally
committed or bundled into the APK.

## Rule: Never put API keys in EXPO_PUBLIC_* variables
EXPO_PUBLIC_* variables are embedded in the JS bundle and can be extracted
from any APK by anyone who downloads it.

## Secrets Map

| Secret | Where it lives | In APK? | In git? | Notes |
|--------|---------------|---------|---------|-------|
| `ANTHROPIC_API_KEY` | Render env vars only | No | No | Never commit |
| `POSTGRES_URL` | Render env vars only | No | No | Never commit |
| `ADMIN_KEY` | Render env vars + server.py default | No | Yes (default only) | Default is low-risk; override in prod |
| `EXPO_PUBLIC_BACKEND_URL` | eas.json + frontend/.env | Yes (safe) | eas.json yes | Public URL, safe to expose |

## Safe to commit
- `eas.json` (contains only the public backend URL)
- `backend/server.py` (reads secrets from env vars, never hardcodes real values)

## Never commit
- `frontend/.env` (gitignored ✅)
- `backend/.env` (gitignored ✅)
- Any file containing real API keys, passwords, or tokens

## Rotating a compromised key
1. Immediately generate a new key at the provider (Anthropic Console, etc.)
2. Update the Render environment variable
3. The old key is now invalid — no code changes needed
