#!/bin/bash
# Build script for India First Android APK
# Requirements: Node.js, Java 17+, Android SDK (ANDROID_HOME must be set)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== India First - Android Build ==="

# Check prerequisites
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required. Install from https://nodejs.org/"
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo "Error: Java 17+ is required."
    exit 1
fi

if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    echo "Error: ANDROID_HOME or ANDROID_SDK_ROOT must be set."
    echo "Install Android SDK from https://developer.android.com/studio"
    exit 1
fi

echo "1/4 Installing dependencies..."
yarn install

echo "2/4 Running expo prebuild..."
npx expo prebuild --platform android --no-install

echo "3/4 Building release APK..."
cd android
chmod +x gradlew
./gradlew assembleRelease

echo "4/4 Build complete!"
APK_PATH="app/build/outputs/apk/release/app-release.apk"
if [ -f "$APK_PATH" ]; then
    echo "APK location: $(pwd)/$APK_PATH"
    echo "APK size: $(du -h "$APK_PATH" | cut -f1)"
else
    echo "APK location: Check app/build/outputs/apk/ for output files"
fi
