const { app, BrowserWindow, Menu } = require('electron')
const path = require('node:path')
const fs = require('node:fs')

function createWindow() {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  Menu.setApplicationMenu(null)
  win.setMenuBarVisibility(false)

  const devUrl = process.env.ELECTRON_START_URL || 'http://localhost:5173'
  const distIndex = path.join(__dirname, '../dist/index.html')

  if (process.env.NODE_ENV === 'production' && fs.existsSync(distIndex)) {
    win.loadFile(distIndex)
  } else {
    win.loadURL(devUrl)
  }
}

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
