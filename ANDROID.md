# KMS Android App

This adds an Android WebView application tightly coupled with the existing web frontend and file format.

- Web UI: reuses web/ React app, built to static assets
- Native bridge: exposes KMS.pickVaultDirectory / KMS.getVaultInfo / KMS.saveMarkdownAndMedia via JS interface
- Storage: uses Android Storage Access Framework (SAF) to write into a user-chosen directory
- File format: identical to desktop (Markdown + YAML frontmatter)
  - importance defaults to null
  - no extra newline after closing frontmatter `---`

## Build the Web Assets

```
cd web
npm install
npm run build
```

This generates web/dist. Copy the dist to Android assets:

```
mkdir -p ../androidApp/app/src/main/assets/www
rsync -a dist/ ../androidApp/app/src/main/assets/www/
```

## Build the Android App

```
cd androidApp
./gradlew :app:assembleDebug
```

APK will be at androidApp/app/build/outputs/apk/debug/app-debug.apk

Install on device (USB debugging enabled):

```
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## First Run

1) Tap “Pick Notes Directory” (visible when running natively) to select your root notes folder via the Android folder picker (SAF).  
2) Grant access; the app persists access to that folder across restarts.  
3) After picking, the app shows the effective target paths:
   - Capture dir: capture/raw_capture
   - Media dir: capture/raw_capture/media
4) Create a note with text, clipboard, image/screenshot, and/or audio, then Save. The app writes:
   - Markdown to {vault}/capture/raw_capture/{capture_id}.md
## Permissions

- The app requests and grants WebView permissions at runtime (e.g., microphone, camera) via the WebView’s permission request handler.
- CAMERA permission is declared to support image capture/selection from within the WebView.
- File inputs in the WebView are supported for images (e.g., when attaching a screenshot/photo), opening the system picker.


   - Media to {vault}/capture/raw_capture/media/{filename}

## Modalities

- Text: use main input
- Clipboard: enable and it will include current clipboard if permission allows
- Image/Screenshot: tap Screenshot; on Android it opens the native file chooser (image/*) and can attach a captured or selected image
- Audio (microphone): now supported in-app on Android via WebView getUserMedia + MediaRecorder. Enable the “audio” modality and use the Record/Stop button; the recording is saved into the media folder and referenced from the markdown. If your device’s WebView disallows mic capture, you’ll see a permission prompt. If recording still doesn’t work on your device, please report back and we can add a native MediaRecorder fallback via the JS bridge.

## Notes on Coupling and Shared Logic

- web/src/shared/serialization.ts: shared serializer that matches Python SafeMarkdownWriter formatting
- web/src/shared/platform.ts: platform bridge used by web UI. In Android, a native JS interface provides KMS methods used by the web app.

## Known Gaps / Next Steps

- Implement native audio recording on Android and wire to the same save flow (store in media folder and reference in markdown as type "audio").
- Optional: Clipboard polling via native if needed for background capture. Current version reads when saving.
- Optional: MediaProjection-based screenshots; current flow allows image attachment via camera/gallery, which is portable and privacy friendly.
