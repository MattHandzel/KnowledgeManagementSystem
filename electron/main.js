const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;
let serverProcess;
let frontendProcess;

function startBackendServer() {
  const serverPath = path.join(__dirname, "..", "server");
  const pythonPath = process.platform === "win32" ? "python" : "python3";
  
  const configFile = process.env.npm_lifecycle_event === 'dev' ? '../config-dev.yaml' : '../config-prod.yaml';

  // TODO: Check to see if the backend server is already running, if so, don't bother spawning.
  serverProcess = spawn(pythonPath, ["app.py", "--config", configFile], {
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

function startFrontendServer() {
  const webPath = path.join(__dirname, "..", "web");
  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";

  frontendProcess = spawn(npmCommand, ["run", "dev"], {
    cwd: webPath,
    stdio: "inherit",
    env: { ...process.env },
  });

  frontendProcess.on("error", (err) => {
    console.error("Failed to start frontend server:", err);
  });

  return new Promise((resolve) => {
    setTimeout(resolve, 5000);
  });
}

async function createWindow() {
  await startBackendServer();
  await startFrontendServer();

  Menu.setApplicationMenu(null);

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 725,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
    icon: path.join(__dirname, "assets", "icon.png"),
  });

  mainWindow.loadURL("http://localhost:5173");

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
  }
  if (frontendProcess) {
    frontendProcess.kill("SIGTERM");
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
  if (frontendProcess) {
    frontendProcess.kill("SIGTERM");
  }
});
