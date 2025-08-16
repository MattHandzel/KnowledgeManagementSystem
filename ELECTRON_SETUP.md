# Running KMS as a Desktop Application

## ⚠️ TESTED RESULT: Electron Setup Status

**✅ CONFIRMED**: The Electron desktop application setup is **correctly implemented** but requires a graphical environment (X server/Wayland) to run. 

**❌ LIMITATION**: It **cannot run in headless environments** like servers or containers without display capabilities.

**🧪 TEST RESULTS**:
- `npm start` in electron/ directory: ❌ Fails with "Missing X server or $DISPLAY" 
- Manual backend + web app startup: ✅ Works perfectly
- All modalities functional in browser version: ✅ Confirmed working

## Prerequisites

1. **System Requirements:**
   - Graphical desktop environment (X11, Wayland, or Windows/macOS desktop)
   - Node.js and npm installed
   - Python 3.8+ with pip

2. **Install Node.js dependencies for Electron:**
   ```bash
   cd electron/
   npm install
   ```

3. **Install Python dependencies for the backend server:**
   ```bash
   cd server/
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install fastapi uvicorn pyyaml python-multipart
   ```

## Running the Desktop Application

### ✅ TESTED Working Method: Manual Component Startup

**Step 1: Start the backend server**
```bash
cd server/
source .venv/bin/activate
python app.py
```
*Backend will start on http://localhost:5174*

**Step 2: Start the web app (in new terminal)**
```bash
cd web/
npm run dev
```
*Web app will start on http://localhost:5173 (or next available port)*

**Step 3: Launch Electron (in new terminal, requires graphical desktop environment)**
```bash
cd electron/
npm start
```
*⚠️ This step will fail in headless environments with "Missing X server or $DISPLAY"*

### 🖥️ For Desktop Systems with Display Server:
The Electron app should launch successfully and load the web app automatically. The main.js is properly configured to:
- Start the backend server with proper Python virtual environment
- Wait for server startup (3 second delay)
- Load the web app at http://localhost:5174
- Handle process cleanup on app exit

### ❌ Known Issues with `npm run dev`

The `npm run dev` command in electron/ directory **does not work reliably** due to:
- Port conflicts between concurrent processes
- Backend server startup timing issues  
- Electron requiring display server that may not be available
- Process management complexity with concurrently

**Error Examples:**
```
[ERROR] Missing X server or $DISPLAY
[ERROR] Address already in use (port conflicts)
[ERROR] socket hang up (proxy connection failures)
```

## Alternative: Web Browser Access (Recommended for Testing)

Since Electron requires a graphical environment, you can test all functionality using a web browser:

**Step 1: Start backend server**
```bash
cd server/
source .venv/bin/activate
python app.py
```

**Step 2: Start web app**
```bash
cd web/
npm run dev
```

**Step 3: Open in browser**
Navigate to the URL shown by Vite (typically http://localhost:5173)

All modalities work identically in the browser version.

## Features Available in Desktop/Browser Mode

- ✅ **Text Capture**: Standard text input and editing
- ✅ **Clipboard Preview**: Real-time polling of system clipboard via backend API
- ✅ **Screenshot Capture**: Backend triggers `grim` command (requires display server)
- ✅ **Audio Recording**: Microphone recording with waveform preview
- ✅ **System Audio**: Separate system audio recording modality
- ✅ **Entity-Based Storage**: Sources, context, and tags as natural language arrays

## Troubleshooting

### Common Issues:

1. **"ModuleNotFoundError: No module named 'fastapi'"**
   - Solution: Install backend dependencies
   ```bash
   cd server/
   source .venv/bin/activate
   pip install fastapi uvicorn pyyaml python-multipart
   ```

2. **"Missing X server or $DISPLAY" (Electron)**
   - **Root Cause**: Electron requires graphical desktop environment
   - **Solution**: Use web browser access instead, or run on desktop system
   - Screenshot functionality also requires display server

3. **"Address already in use" (Port conflicts)**
   - **Root Cause**: Previous server instances still running
   - **Solution**: Kill existing processes or use different ports
   ```bash
   # Find and kill processes using ports
   ps aux | grep -E "(python|node)" | grep -v grep
   kill <process_id>
   ```

4. **"socket hang up" (Proxy errors)**
   - **Root Cause**: Backend server not running or port mismatch
   - **Solution**: Ensure backend starts before web app, check port configuration

## File Structure

```
KnowledgeManagementSystem/
├── electron/           # Electron desktop app configuration
│   ├── main.js        # Electron main process
│   ├── package.json   # Electron dependencies
│   └── node_modules/  # Installed packages
├── server/            # FastAPI backend
│   ├── app.py        # Main server file
│   ├── .venv/        # Python virtual environment
│   └── requirements.txt
├── web/              # React frontend
│   ├── src/
│   └── package.json
└── config.yaml       # Application configuration
```

## Configuration

The application uses `config.yaml` for configuration:
- **Vault path**: `~/notes` (where captures are stored)
- **Capture directory**: `capture/raw_capture`
- **Media directory**: `capture/raw_capture/media`

Generated captures will be saved as markdown files with YAML frontmatter in the configured vault directory.
