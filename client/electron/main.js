import { app, BrowserWindow } from "electron"
import { fileURLToPath } from "url"
import { dirname, join } from "path"

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

let mainWindow

function createWindow() {
  const isDev = process.env.VITE_DEV_SERVER_URL || process.env.ELECTRON_START_URL
  mainWindow = new BrowserWindow({
    width: 960,
    height: 700,
    backgroundColor: "#000000",
    webPreferences: {
      preload: join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    },
    autoHideMenuBar: true
  })

  if (isDev) {
    const url = process.env.VITE_DEV_SERVER_URL || process.env.ELECTRON_START_URL
    mainWindow.loadURL(url)
  } else {
    const indexPath = join(__dirname, "..", "dist", "index.html")
    mainWindow.loadFile(indexPath)
  }

  mainWindow.on("closed", () => {
    mainWindow = null
  })
}

app.whenReady().then(() => {
  createWindow()

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit()
  }
})
