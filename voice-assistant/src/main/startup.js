const { app, BrowserWindow, session } = require('electron');
const path = require('path');
const config = require('../../config/app-config');
const hotkeyManager = require('../utils/hotkeys');
const logger = require('../utils/logger');

let mainWindow;
let pipecatProcess;

function handleActivationHotkey() {
  if (mainWindow) {
    if (mainWindow.isVisible()) {
      mainWindow.webContents.send('stop-listening');
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.focus();
      mainWindow.webContents.send('start-listening');
    }
  }
}

function createWindow() {
  const windowWidth = config.get('ui.windowWidth');
  const windowHeight = config.get('ui.windowHeight');
  mainWindow = new BrowserWindow({
    width: windowWidth || 400,
    height: windowHeight || 750,
    show: false,
    frame: false,
    fullscreenable: false,
    resizable: false,
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, "../../preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.on('ready-to-show', () => {
    if (!hotkeyManager.registerActivationHotkey(handleActivationHotkey)) {
      logger.error('[Main] FAILED TO REGISTER ACTIVATION HOTKEY. App may not be fully functional.');
    }
  });
  mainWindow.on('blur', () => {
    if (mainWindow && mainWindow.isVisible()) {
      mainWindow.webContents.send('stop-listening');
      mainWindow.hide();
    }
  });
  const rendererPath = path.join(__dirname, '../../renderer/index.html');
  mainWindow.loadFile(rendererPath);
}

async function startPipecatBackend() {
  const { spawn } = require('child_process');
  const scriptPath = path.join(__dirname, '../../src/main.py');
  let command, args;
  if (process.platform === 'win32') {
    if (process.env.CONDA_PREFIX) {
      const pythonPath = path.join(process.env.CONDA_PREFIX, 'python.exe');
      command = pythonPath;
      args = [scriptPath];
    } else {
      command = 'cmd.exe';
      args = ['/c', `conda activate voiceapp && python "${scriptPath}"`];
    }
  } else {
    command = 'python3';
    args = [scriptPath];
  }
  pipecatProcess = spawn(command, args, {
    cwd: path.join(__dirname, '../../src'),
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    shell: process.platform === 'win32' && !process.env.CONDA_PREFIX
  });
  pipecatProcess.stdout.on('data', (data) => {
    const output = data.toString().trim();
    if (output.includes('BACKEND_READY') && mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('backend-ready');
      mainWindow.webContents.send('backend-truly-ready');
    }
  });
  pipecatProcess.stderr.on('data', (data) => {
    const error = data.toString().trim();
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('backend-error', error);
    }
  });
  pipecatProcess.on('close', (code) => {
    pipecatProcess = null;
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('backend-closed', code);
    }
  });
  pipecatProcess.on('error', (error) => {
    pipecatProcess = null;
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('backend-error', error.message);
    }
  });
}

module.exports = {
  handleActivationHotkey,
  createWindow,
  startPipecatBackend,
  get mainWindow() { return mainWindow; },
  get pipecatProcess() { return pipecatProcess; }
};