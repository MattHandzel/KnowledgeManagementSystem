# Development Guide

## Dev vs Prod Configuration

The Knowledge Management System supports separate development and production environments with complete database and storage isolation.

### Running in Development Mode

```bash
cd electron
npm run dev
```

**Development Mode Features:**
- 🚧 DEV MODE banner displayed in application
- Dark theme applied by default
- All data stored in `dev/` folder (gitignored)
- Database: `dev/main-dev.db`
- Captures: `dev/capture/raw_capture/`
- Media: `dev/capture/raw_capture/media/`
- Terminal shows "🚧 RUNNING IN DEVELOPMENT MODE 🚧"

### Running in Production Mode

```bash
cd electron
npm run prod
```

**Production Mode Features:**
- Clean interface with no dev indicators
- Light theme applied by default
- Data stored in production locations
- Database: `server/main-prod.db`
- Captures: `~/notes/capture/raw_capture/`
- Media: `~/notes/capture/raw_capture/media/`

### Configuration Files

- **`config-dev.yaml`**: Development configuration with dev paths and dark theme
- **`config-prod.yaml`**: Production configuration with prod paths and light theme

### Database Isolation

Development and production modes use completely separate databases:
- Dev database is stored in the project's `dev/` folder
- Prod database is stored in the `server/` folder
- No data sharing between environments
- Safe to develop without affecting production data

### Theme Configuration

Both dev and prod configs support theme customization:

```yaml
theme:
  mode: "dark"  # or "light"
  accent_color: "#4c1d95"
  accent_hover: "#3730a3"
  accent_shadow: "rgba(76, 29, 149, 0.2)"
  background_color: "#1f2937"
  text_color: "#f9fafb"
  input_background: "#374151"
  input_border: "#4b5563"
```

### Keyboard Shortcuts

- **Save Note**: `Ctrl+Enter` (changed from Ctrl+S)
- **Toggle Help**: `F1`

### File Structure

```
KnowledgeManagementSystem/
├── dev/                          # Development data (gitignored)
│   ├── main-dev.db              # Development database
│   └── capture/raw_capture/     # Development captures
├── server/
│   └── main-prod.db             # Production database
├── config-dev.yaml              # Development configuration
├── config-prod.yaml             # Production configuration
└── electron/
    └── package.json             # Contains dev/prod npm scripts
```

### Important Notes

- The `dev/` folder is automatically excluded from version control
- Always use the appropriate npm script to ensure correct configuration
- Database isolation prevents development work from affecting production data
- Theme and save paths are automatically configured based on the selected mode
