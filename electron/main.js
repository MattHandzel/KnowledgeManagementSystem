const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;
let serverProcess;

function startBackendServer() {
  const serverPath = path.join(__dirname, "..", "server");
  const pythonPath = process.platform === "win32" ? "python" : "python3";

  // TODO: Check to see if the backend server is already running, if so, don't bother spawning.
  serverProcess = spawn(pythonPath, ["app.py"], {
    cwd: serverPath,
    stdio: "inherit",
    env: { ...process.env, PYTHONPATH: serverPath },
  });

  serverProcess.on("error", (err) => {
    console.error("Failed to start backend server:", err);
  });

  return new Promise((resolve) => {
    setTimeout(resolve, 3000);
  });
}

async function createWindow() {
  await startBackendServer();

  Menu.setApplicationMenu(null);

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
    icon: path.join(__dirname, "assets", "icon.png"),
  });

  mainWindow.loadURL("http://localhost:5174");

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on("before-quit", () => {
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
  }
});
