# Running KMS as a Desktop Application

## Prerequisites

1. **Install Node.js dependencies for Electron:**
   ```bash
   cd electron/
   npm install
   ```

2. **Install Python dependencies for the backend server:**
   ```bash
   cd server/
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the Desktop Application

### Option 1: Development Mode (Recommended)
```bash
cd electron/
npm run dev
```

This will:
- Start the React web app (Vite dev server)
- Start the FastAPI backend server
- Launch Electron with the application

### Option 2: Manual Setup
If you prefer to start components separately:

1. **Start the backend server:**
   ```bash
   cd server/
   source .venv/bin/activate
   python app.py
   ```

2. **Start the web app:**
   ```bash
   cd web/
   npm run dev
   ```

3. **Launch Electron:**
   ```bash
   cd electron/
   npm start
   ```

## Features Available in Desktop Mode

- ✅ **Text Capture**: Standard text input and editing
- ✅ **Clipboard Preview**: Real-time polling of system clipboard
- ✅ **Screenshot Capture**: Uses `grim` command (requires display server)
- ✅ **Audio Recording**: Microphone recording with waveform preview
- ✅ **System Audio**: Separate system audio recording modality
- ✅ **Entity-Based Storage**: Sources, context, and tags as natural language arrays

## Troubleshooting

### Common Issues:

1. **"ModuleNotFoundError: No module named 'fastapi'"**
   - Solution: Activate the Python virtual environment and install dependencies
   ```bash
   cd server/
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **"Missing X server or $DISPLAY"**
   - This is expected in headless environments
   - Screenshot functionality requires a graphical environment
   - All other features work normally

3. **"Port already in use"**
   - The app will automatically find available ports
   - Default ports: 5173 (web), 5174 (backend)

4. **Electron won't start**
   - Ensure you're in the `electron/` directory
   - Run `npm install` to install Electron dependencies

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
