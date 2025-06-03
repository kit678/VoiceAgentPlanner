require('dotenv').config({ path: '../.env' }); // Load .env variables from project root

// Global error handlers to prevent EPIPE crashes
process.on('uncaughtException', (error) => {
  if (error.code === 'EPIPE') {
    // Silently ignore EPIPE errors to prevent crashes
    return;
  }
  // Log other errors silently without console operations
});

process.on('unhandledRejection', (reason, promise) => {
  // Silently handle unhandled rejections
});

// Wrap stdout/stderr to prevent EPIPE errors
if (process.stdout && process.stdout.on) {
  process.stdout.on('error', (err) => {
    if (err.code === 'EPIPE') {
      // Silently ignore EPIPE errors
      return;
    }
  });
}

if (process.stderr && process.stderr.on) {
  process.stderr.on('error', (err) => {
    if (err.code === 'EPIPE') {
      // Silently ignore EPIPE errors
      return;
    }
  });
}

const { app, BrowserWindow, ipcMain, globalShortcut, session } = require('electron');
const fs = require('fs'); // Added for logging
const path = require('path');
const { spawn, execSync } = require('child_process'); // Added execSync
const config = require('./config/app-config');
const hotkeyManager = require('./src/utils/hotkeys');
const logger = require('./src/utils/logger');
const { startRecording, stopRecording } = require('./src/audio/audioCapture');
// const { speechClient, textToSpeechClient } = require('./src/utils/googleCloudClients'); // Kept for future use, commented out to suppress credential warnings

// Authentication state
let isAuthenticated = false;
let authWindow = null;

// Keep a global reference of the window object
let mainWindow;
let currentAudioStream = null;
let recognizeStream = null;
let selectedAudioDeviceId = null; // To store the chosen device ID
let isRecording = false; // New state variable
let isHotkeyPressedToRecord = false; // To differentiate hotkey trigger from other UI actions if needed
let pipecatProcess = null; // Pipecat backend process
let backendReady = false; // Track backend status

// --- Start of Logging Setup ---
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const getTimestamp = () => {
  const now = new Date();
  return now.toISOString().replace(/[:.]/g, '-'); // Format: YYYY-MM-DDTHH-mm-ss-SSSZ
};

const logFileName = `main-process-${getTimestamp()}.log`;
const logFilePath = path.join(logsDir, logFileName);
const logStream = fs.createWriteStream(logFilePath, { flags: 'a' });

// Redirect console.log, console.error, console.warn, console.info, console.debug
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalConsoleInfo = console.info;
const originalConsoleDebug = console.debug;

console.log = (...args) => {
  const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg).join(' ');
  logStream.write(`[LOG] ${new Date().toISOString()}: ${message}\n`);
  originalConsoleLog.apply(console, args); // Also log to original console (optional)
};

console.error = (...args) => {
  const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg).join(' ');
  logStream.write(`[ERROR] ${new Date().toISOString()}: ${message}\n`);
  originalConsoleError.apply(console, args);
};

console.warn = (...args) => {
  const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg).join(' ');
  logStream.write(`[WARN] ${new Date().toISOString()}: ${message}\n`);
  originalConsoleWarn.apply(console, args);
};

console.info = (...args) => {
  const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg).join(' ');
  logStream.write(`[INFO] ${new Date().toISOString()}: ${message}\n`);
  originalConsoleInfo.apply(console, args);
};

console.debug = (...args) => {
  const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg).join(' ');
  logStream.write(`[DEBUG] ${new Date().toISOString()}: ${message}\n`);
  originalConsoleDebug.apply(console, args);
};

// Log unhandled exceptions and rejections to the file as well
process.on('uncaughtException', (error, origin) => {
  const message = `Uncaught Exception: ${error.message}\nStack: ${error.stack}\nOrigin: ${origin}`;
  logStream.write(`[FATAL] ${new Date().toISOString()}: ${message}\n`);
  originalConsoleError('Unhandled Exception:', error, 'Origin:', origin);
  // It's generally recommended to exit after an uncaught exception
  // process.exit(1); // Consider if this is appropriate for your app
});

process.on('unhandledRejection', (reason, promise) => {
  const message = `Unhandled Rejection at: ${promise}, reason: ${reason instanceof Error ? reason.stack : reason}`;
  logStream.write(`[FATAL] ${new Date().toISOString()}: ${message}\n`);
  originalConsoleError('Unhandled Rejection:', reason, 'Promise:', promise);
});

console.log('Main process logging initialized.');
// --- End of Logging Setup ---

function createWindow() {
  console.log('=== DEBUG: createWindow() called ==='); // This will now go to the log file
  // logger.info('Creating main application window'); // This uses the old logger, can be removed or updated
  console.info('Creating main application window.'); // Using new console.info for file logging
  
  // Get window settings from config
  console.log('=== DEBUG: Getting window settings ===');
  const windowWidth = config.get('ui.windowWidth');
  const windowHeight = config.get('ui.windowHeight');
  const alwaysOnTop = config.get('ui.alwaysOnTop');
  
  console.log('=== DEBUG: Creating BrowserWindow ==='); // Direct debug
  mainWindow = new BrowserWindow({
    width: 400, // Keep width or adjust as needed
    height: 750, // Increased height
    show: false,
    frame: false,
    fullscreenable: false,
    resizable: false,
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Clear cache and then load the file
  async function clearCacheAndLoad() {
    console.log('=== DEBUG: clearCacheAndLoad() called ===');
    try {
      if (session && session.defaultSession) {

        // await session.defaultSession.clearStorageData(); // Clears cache, cookies, storage etc.
        // logger.info('[Main - createWindow] Electron session storage cleared.');
        console.info('[Main - createWindow] Skipping Electron session storage clearing for diagnostics.');
      } else {
        console.warn('[Main - createWindow] Electron session or defaultSession not available for cache clearing.');
      }
    } catch (err) {
      console.error('[Main - createWindow] Failed to clear session storage:', err);
    }
    console.log('=== DEBUG: Loading HTML file ===');
    // Load the new UI from the renderer directory
    const rendererPath = path.join(__dirname, '..', 'renderer', 'index.html');
    console.log('=== DEBUG: Renderer path:', rendererPath, '===');
    mainWindow.loadFile(rendererPath);
    console.log('=== DEBUG: HTML file load initiated ==='); // Direct debug
  }
  clearCacheAndLoad();
  
  // Hide window initially (will be shown on hotkey press)
  mainWindow.on('ready-to-show', () => {
    console.log('=== DEBUG: Window ready-to-show event ===');
    // logger.debug('Main window ready to show, registering hotkey');
    console.debug('Main window ready to show, registering hotkey');
    // mainWindow.show(); // Window will be shown by hotkey
    // mainWindow.focus(); // Window will be focused by hotkey
    
    console.log('=== DEBUG: Registering hotkey ===');
    // Register global hotkey using our utility
    if (!hotkeyManager.registerActivationHotkey(handleActivationHotkey)) {
      console.log('=== DEBUG: HOTKEY REGISTRATION FAILED ===');
      // logger.error('[Main] FAILED TO REGISTER ACTIVATION HOTKEY. App may not be fully functional.');
      console.error('[Main] FAILED TO REGISTER ACTIVATION HOTKEY. App may not be fully functional.');
      // Consider showing an error dialog to the user
    } else {
      console.log('=== DEBUG: HOTKEY REGISTERED SUCCESSFULLY ===');
    }
  });

  // Hide when focus is lost
  mainWindow.on('blur', () => {
    // logger.debug('Window lost focus');
    console.debug('Window lost focus');
    if (mainWindow && mainWindow.isVisible()) {
      // logger.debug('Window lost focus, hiding and stopping listening.');
      console.debug('Window lost focus, hiding and stopping listening.');
      // Send stop listening to renderer
      mainWindow.webContents.send('stop-listening');
      mainWindow.hide();
    } else {
      // logger.debug('Window lost focus but was not visible, no action.');
      console.debug('Window lost focus but was not visible, no action.');
    }
  });
  
  console.log('=== DEBUG: createWindow() completed ===');
}

// const { exec } = require('child_process'); // No longer needed for getPythonExecutable
// const fs = require('fs'); // No longer needed for getPythonExecutable
// const os = require('os'); // No longer needed for getPythonExecutable

// Start Pipecat backend process
async function startPipecatBackend() {
  console.log('=== DEBUG: startPipecatBackend() called ===');
  if (pipecatProcess) {
    console.log('=== DEBUG: Existing Pipecat process found ===');
    // logger.info('Existing Pipecat process found. Attempting to terminate it...');
    console.info('Existing Pipecat process found. Attempting to terminate it...');
    pipecatProcess.kill('SIGTERM');
    // Optionally, wait a moment for the process to terminate
    // await new Promise(resolve => setTimeout(resolve, 1000)); 
    pipecatProcess = null; // Clear the reference
  }
  console.log('=== DEBUG: Starting new Pipecat process ===');
  // logger.info('Starting Pipecat backend process...');
  console.info('Starting Pipecat backend process...');
  
  const scriptPath = path.join(__dirname, 'src', 'main.py');
  console.log('=== DEBUG: Script path:', scriptPath, '===');
  
  // Handle conda environment activation for Windows
  let command, args;
  if (process.platform === 'win32') {
    if (process.env.CONDA_PREFIX) {
      // Use conda environment python
      const pythonPath = path.join(process.env.CONDA_PREFIX, 'python.exe');
      console.log('=== DEBUG: Using conda python:', pythonPath, '===');
      // logger.info(`Using conda python: ${pythonPath}`);
      console.info(`Using conda python: ${pythonPath}`);
      command = pythonPath;
      args = [scriptPath];
    } else {
      // Activate conda environment and run python
      console.log('=== DEBUG: No CONDA_PREFIX, using cmd activation ===');
      // logger.warn('CONDA_PREFIX environment variable not set. Attempting to activate voiceapp environment.');
      console.warn('CONDA_PREFIX environment variable not set. Attempting to activate voiceapp environment.');
      command = 'cmd.exe';
      args = ['/c', `conda activate voiceapp && python "${scriptPath}"`];
    }
  } else {
    // Unix-like systems
    command = 'python3';
    args = [scriptPath];
  }
  
  console.log('=== DEBUG: Spawning command:', command, 'with args:', args, '===');
  // logger.info(`Attempting to spawn: ${command} ${args.join(' ')}`);
  console.info(`Attempting to spawn: ${command} ${args.join(' ')}`);

  try {
    pipecatProcess = spawn(command, args, {
      cwd: path.join(__dirname, 'src'), // Ensure CWD is the src directory for main.py
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { 
        ...process.env,
        PYTHONUNBUFFERED: '1', // Useful for seeing python logs immediately
      },
      shell: process.platform === 'win32' && !process.env.CONDA_PREFIX // Use shell only when activating conda
    });
    
    console.log('=== DEBUG: Process spawned successfully ===');

    let backendReady = false;
    
    pipecatProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      console.log('=== DEBUG: Python stdout:', output, '===');
      logger.info(`[Pipecat] ${output}`);
      
      // Check for backend ready signal
      if (output.includes('BACKEND_READY')) {
        backendReady = true;
        console.log('=== DEBUG: BACKEND_READY signal received ===');
        logger.info('[Main] Pipecat backend is ready for connections');
        
        // Notify renderer that backend is ready
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('backend-ready'); // Existing notification
          mainWindow.webContents.send('backend-truly-ready'); // New notification for WebSocket connection
        }
      }
    });
    
    pipecatProcess.stderr.on('data', (data) => {
      const error = data.toString().trim();
      console.log('=== DEBUG: Python stderr:', error, '===');
      logger.error(`[Pipecat Error] ${error}`);
      
      // Check for critical errors
      if (error.includes('GOOGLE_API_KEY not found') || error.includes('Failed to start backend')) {
        logger.error('[Main] Critical backend error detected');
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('backend-error', error);
        }
      }
    });
    
    pipecatProcess.on('close', (code) => {
      console.log('=== DEBUG: Process closed with code:', code, '===');
      logger.info(`[Pipecat] Process exited with code ${code}`);
      pipecatProcess = null;
      
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('backend-closed', code);
      }
    });
    
    pipecatProcess.on('error', (error) => {
      console.log('=== DEBUG: Process error:', error.message, '===');
      logger.error(`[Pipecat] Failed to start: ${error.message}`);
      pipecatProcess = null;
      
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('backend-error', error.message);
      }
    });
    
    // Timeout check for backend startup
    setTimeout(() => {
      if (!backendReady && pipecatProcess) {
        console.log('=== DEBUG: Backend startup timeout ===');
        logger.warn('[Main] Backend startup timeout - may have issues');
      }
    }, 30000); // 30 second timeout (increased from 10 seconds)
    
  } catch (error) {
    console.log('=== DEBUG: Error spawning process:', error.message, '===');
    logger.error(`[Main] Error starting Pipecat process: ${error.message}`);
  }
  
  console.log('=== DEBUG: startPipecatBackend() completed ===');
}

// Authentication functions
async function checkAuthenticationStatus() {
  try {
    logger.info('Checking Google OAuth authentication status...');
    
    // Run Python script to check authentication
    const pythonScript = `
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.auth.google_oauth import GoogleOAuthManager

async def check_auth():
    try:
        oauth_manager = GoogleOAuthManager()
        credentials = await oauth_manager.load_credentials()
        if credentials and await oauth_manager.is_authenticated():
            print('AUTHENTICATED')
        else:
            print('NOT_AUTHENTICATED')
    except Exception as e:
        print(f'ERROR: {e}')

if __name__ == '__main__':
    asyncio.run(check_auth())
`;
    
    const fs = require('fs');
    const tempScriptPath = path.join(__dirname, 'temp_auth_check.py');
    fs.writeFileSync(tempScriptPath, pythonScript);
    
    const result = execSync(`python "${tempScriptPath}"`, { 
      cwd: __dirname,
      encoding: 'utf8',
      timeout: 10000
    }).trim();
    
    // Clean up temp file
    fs.unlinkSync(tempScriptPath);
    
    isAuthenticated = result === 'AUTHENTICATED';
    logger.info(`Authentication status: ${isAuthenticated ? 'Authenticated' : 'Not authenticated'}`);
    
    return isAuthenticated;
  } catch (error) {
    logger.error(`Failed to check authentication status: ${error.message}`);
    isAuthenticated = false;
    return false;
  }
}

function createAuthWindow() {
  logger.info('Creating authentication window');
  
  authWindow = new BrowserWindow({
    width: 800,
    height: 600,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  
  authWindow.loadFile(path.join(__dirname, '..', 'renderer', 'auth-flow.html'));
  
  authWindow.once('ready-to-show', () => {
    authWindow.show();
    authWindow.focus();
  });
  
  authWindow.on('closed', () => {
    authWindow = null;
  });
  
  return authWindow;
}

async function handleAuthenticationFlow() {
  logger.info('Starting sophisticated OAuth authentication flow...');
  
  return new Promise(async (resolve) => {
    try {
      // Start OAuth callback server first
      await startOAuthCallbackServer();
      
      // Create and show auth window with sophisticated UI
      createAuthWindow();
      
      // Listen for authentication completion from auth window
      ipcMain.once('auth-completed', async (event, success) => {
        logger.info(`Authentication completed via UI: ${success}`);
        
        if (authWindow) {
          authWindow.close();
          authWindow = null;
        }
        
        // Close OAuth server
        if (oauthServer) {
          oauthServer.close();
          oauthServer = null;
        }
        
        if (success) {
          isAuthenticated = true;
          resolve(true);
        } else {
          resolve(false);
        }
      });
      
      // Handle auth window closure without completion
      if (authWindow) {
        authWindow.on('closed', () => {
          if (authWindow) {
            logger.info('Authentication window closed without completion');
            // Close OAuth server
            if (oauthServer) {
              oauthServer.close();
              oauthServer = null;
            }
            resolve(false);
          }
        });
      }
      
    } catch (error) {
      logger.error(`Failed to start authentication flow: ${error.message}`);
      resolve(false);
    }
  });
}

// Helper function to start Google auth flow
async function startGoogleAuthFlow() {
  try {
    logger.info('Starting Google OAuth flow from main process...');
    
    // Start the callback server first
    await startOAuthCallbackServer();
    
    const pythonScript = `
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.auth.google_oauth import GoogleOAuthManager

try:
    oauth_manager = GoogleOAuthManager()
    auth_url = oauth_manager.initialize_flow(['tasks', 'calendar', 'drive', 'docs'])
    print(f'AUTH_URL:{auth_url}')
except Exception as e:
    print(f'ERROR: {e}')
`;
    
    const fs = require('fs');
    const tempScriptPath = path.join(__dirname, 'temp_start_auth_main.py');
    fs.writeFileSync(tempScriptPath, pythonScript);
    
    const result = execSync(`python "${tempScriptPath}"`, { 
      cwd: __dirname,
      encoding: 'utf8',
      timeout: 10000
    }).trim();
    
    // Clean up temp file
    fs.unlinkSync(tempScriptPath);
    
    if (result.startsWith('AUTH_URL:')) {
      const authUrl = result.replace('AUTH_URL:', '');
      logger.info('Google OAuth URL generated successfully');
      
      // Set up promise to wait for callback (but don't return it)
      const callbackPromise = new Promise((resolve) => {
        oauthPromise = { resolve };
        
        // Timeout after 5 minutes
        setTimeout(() => {
          resolve({ success: false, error: 'Authentication timeout' });
        }, 300000);
      });
      
      // Only return serializable data
      return { success: true, authUrl };
    } else {
      logger.error(`Failed to generate auth URL: ${result}`);
      return { success: false, error: result };
    }
  } catch (error) {
    logger.error(`Failed to start Google auth: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Helper function to complete Google auth
async function completeGoogleAuth(authCode) {
  try {
    logger.info('Completing Google OAuth flow...');
    
    const pythonScript = `
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.auth.google_oauth import GoogleOAuthManager

async def complete_auth():
    try:
        oauth_manager = GoogleOAuthManager()
        oauth_manager.initialize_flow(['tasks', 'calendar', 'drive', 'docs'])
        success = await oauth_manager.handle_callback('${authCode}')
        if success:
            print('AUTH_SUCCESS')
        else:
            print('AUTH_FAILED')
    except Exception as e:
        print(f'ERROR: {e}')

if __name__ == '__main__':
    asyncio.run(complete_auth())
`;
    
    const fs = require('fs');
    const tempScriptPath = path.join(__dirname, 'temp_complete_auth_main.py');
    fs.writeFileSync(tempScriptPath, pythonScript);
    
    const result = execSync(`python "${tempScriptPath}"`, { 
      cwd: __dirname,
      encoding: 'utf8',
      timeout: 15000
    }).trim();
    
    // Clean up temp file
    fs.unlinkSync(tempScriptPath);
    
    const success = result === 'AUTH_SUCCESS';
    logger.info(`Google OAuth completion: ${success ? 'Success' : 'Failed'}`);
    
    return { success, result };
  } catch (error) {
    logger.error(`Failed to complete Google auth: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Create window when Electron is ready
app.whenReady().then(async () => { // Made async
  console.log('=== DEBUG: app.whenReady() called ==='); // Direct debug
  logger.info('Application ready, starting initialization');
  
  // Reset to defaults to ensure fresh config for hotkey testing
  console.log('=== DEBUG: Resetting config ==='); // Direct debug
  logger.info('Resetting configuration to defaults to pick up latest hotkey.');
  config.resetToDefaults();
  
  // Set app name from config
  console.log('=== DEBUG: Setting app name ==='); // Direct debug
  app.setName(config.get('app.name'));
  
  // Check authentication status first
  const authStatus = await checkAuthenticationStatus();
  
  if (!authStatus) {
    logger.info('User not authenticated, starting sophisticated OAuth flow...');
    
    try {
      // Use the sophisticated authentication flow with UI
      const authResult = await handleAuthenticationFlow();
      
      if (!authResult) {
        logger.error('Authentication failed or was cancelled');
        app.quit();
         return;
       }
       
       logger.info('Authentication completed successfully');
       isAuthenticated = true;
       
     } catch (error) {
       logger.error(`Authentication flow error: ${error.message}`);
       app.quit();
       return;
     }
   }
  
  console.log('=== DEBUG: Proceeding with app startup ==='); // Direct debug
  logger.info('User authenticated, proceeding with application startup');
  
  console.log('=== DEBUG: Calling createWindow() ==='); // Direct debug
  createWindow();
  
  // Start Pipecat backend after a short delay
  console.log('=== DEBUG: Setting timeout for backend startup ==='); // Direct debug
  setTimeout(async () => { // Made async
    console.log('=== DEBUG: Timeout triggered, starting backend ==='); // Direct debug
    await startPipecatBackend(); // Await the async function
  }, 1000); // Delay to allow window to initialize
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
  logger.info('All windows closed');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  logger.debug('App activated');
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Unregister shortcuts when app is quitting
app.on('will-quit', () => {
  logger.info('Application quitting, cleaning up');
  hotkeyManager.unregisterAll();
  
  // Clean up Pipecat process
  if (pipecatProcess) {
    logger.info('Terminating Pipecat process...');
    pipecatProcess.kill('SIGTERM');
    pipecatProcess = null;
  }
});

// IPC Events for Microphone Selection
ipcMain.handle('get-stored-audio-input-device', async () => {
  const deviceId = config.get('audio.selectedDeviceId');
  logger.info(`Retrieved stored audio input device ID: ${deviceId}`);
  return deviceId;
});

ipcMain.on('store-audio-input-device', (event, deviceId) => {
  config.set('audio.selectedDeviceId', deviceId);
  logger.info(`Stored audio input device ID: ${deviceId}`);
});

ipcMain.on('set-audio-input-device', (event, deviceId) => {
  selectedAudioDeviceId = deviceId;
  logger.info(`Audio input device set to: ${deviceId}`);
  // Potentially stop and restart recording if already in progress with a different device
  // For now, new device will be used on next 'start-recording'
});

// Authentication IPC handlers
// OAuth callback server
const express = require('express');
let oauthServer = null;
let oauthPromise = null;

function startOAuthCallbackServer() {
  return new Promise((resolve, reject) => {
    if (oauthServer) {
      resolve({ port: 8080 });
      return;
    }
    
    const app = express();
    
    app.get('/oauth/callback', async (req, res) => {
      const code = req.query.code;
      const error = req.query.error;
      
      if (error) {
        logger.error(`OAuth callback error: ${error}`);
        res.send(`
          <html>
            <head><title>Authentication Failed</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
              <h1 style="color: #d32f2f;">Authentication Failed</h1>
              <p>There was an error during authentication: ${error}</p>
              <p>You can close this window and return to the application.</p>
              <script>setTimeout(() => window.close(), 3000);</script>
            </body>
          </html>
        `);
        
        // Notify auth window of failure
        if (authWindow && !authWindow.isDestroyed()) {
          authWindow.webContents.send('oauth-callback', { success: false, error });
        }
        
        if (oauthPromise) {
          oauthPromise.resolve({ success: false, error });
        }
      } else if (code) {
        logger.info('OAuth callback received authorization code, completing authentication...');
        
        try {
          // Complete authentication with the received code
          const completeResult = await completeGoogleAuth(code);
          
          if (completeResult.success) {
            logger.info('Google authentication completed successfully');
            
            res.send(`
              <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                  <h1 style="color: #4caf50;">Authentication Successful!</h1>
                  <p>You have successfully authenticated with Google.</p>
                  <p>You can close this window and return to the application.</p>
                  <script>setTimeout(() => window.close(), 3000);</script>
                </body>
              </html>
            `);
            
            // Notify auth window of success
            if (authWindow && !authWindow.isDestroyed()) {
              authWindow.webContents.send('oauth-callback', { success: true });
            }
            
            if (oauthPromise) {
              oauthPromise.resolve({ success: true, code });
            }
          } else {
            logger.error('Failed to complete authentication');
            
            res.send(`
              <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                  <h1 style="color: #d32f2f;">Authentication Failed</h1>
                  <p>Failed to complete the authentication process.</p>
                  <p>You can close this window and try again.</p>
                  <script>setTimeout(() => window.close(), 3000);</script>
                </body>
              </html>
            `);
            
            // Notify auth window of failure
            if (authWindow && !authWindow.isDestroyed()) {
              authWindow.webContents.send('oauth-callback', { success: false, error: 'Failed to complete authentication' });
            }
            
            if (oauthPromise) {
              oauthPromise.resolve({ success: false, error: 'Failed to complete authentication' });
            }
          }
        } catch (error) {
          logger.error(`Error completing authentication: ${error.message}`);
          
          res.send(`
            <html>
              <head><title>Authentication Failed</title></head>
              <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #d32f2f;">Authentication Failed</h1>
                <p>An error occurred during authentication: ${error.message}</p>
                <p>You can close this window and try again.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
              </body>
            </html>
          `);
          
          // Notify auth window of failure
          if (authWindow && !authWindow.isDestroyed()) {
            authWindow.webContents.send('oauth-callback', { success: false, error: error.message });
          }
          
          if (oauthPromise) {
            oauthPromise.resolve({ success: false, error: error.message });
          }
        }
      }
      
      // Close server after handling callback
      setTimeout(() => {
        if (oauthServer) {
          oauthServer.close();
          oauthServer = null;
        }
      }, 5000);
    });
    
    oauthServer = app.listen(8080, (err) => {
      if (err) {
        logger.error(`Failed to start OAuth callback server: ${err.message}`);
        reject(err);
      } else {
        logger.info('OAuth callback server started on port 8080');
        resolve({ port: 8080 });
      }
    });
    
    oauthServer.on('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        logger.warn('Port 8080 already in use, OAuth callback may not work properly');
      }
      reject(err);
    });
  });
}

ipcMain.handle('start-google-auth', async () => {
  // This handler is now handled directly in the main process startup
  // Keeping for potential future use or renderer process calls
  return await startGoogleAuthFlow();
});

ipcMain.handle('complete-google-auth', async (event, authCode) => {
  try {
    logger.info('Completing Google OAuth flow...');
    
    const pythonScript = `
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.auth.google_oauth import GoogleOAuthManager

async def complete_auth():
    try:
        oauth_manager = GoogleOAuthManager()
        oauth_manager.initialize_flow(['tasks', 'calendar', 'drive', 'docs'])
        success = await oauth_manager.handle_callback('${authCode}')
        if success:
            print('AUTH_SUCCESS')
        else:
            print('AUTH_FAILED')
    except Exception as e:
        print(f'ERROR: {e}')

if __name__ == '__main__':
    asyncio.run(complete_auth())
`;
    
    const fs = require('fs');
    const tempScriptPath = path.join(__dirname, 'temp_complete_auth.py');
    fs.writeFileSync(tempScriptPath, pythonScript);
    
    const result = execSync(`python "${tempScriptPath}"`, { 
      cwd: __dirname,
      encoding: 'utf8',
      timeout: 15000
    }).trim();
    
    // Clean up temp file
    fs.unlinkSync(tempScriptPath);
    
    const success = result === 'AUTH_SUCCESS';
    logger.info(`Google OAuth completion: ${success ? 'Success' : 'Failed'}`);
    
    if (success) {
      isAuthenticated = true;
    }
    
    return { success, result };
  } catch (error) {
    logger.error(`Failed to complete Google auth: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-auth-status', () => {
  return { authenticated: isAuthenticated };
});

// Handle opening external URLs
ipcMain.handle('open-external', async (event, url) => {
  const { shell } = require('electron');
  await shell.openExternal(url);
  return { success: true };
});

// Handle auth completion from auth window
ipcMain.on('auth-completed', (event, success) => {
  logger.info(`Authentication completed with status: ${success}`);
  isAuthenticated = success;
  
  if (authWindow) {
    authWindow.close();
    authWindow = null;
  }
  
  // Continue with app startup if authentication was successful
  if (success && !backendReady) {
    startPipecatBackend();
  } else if (!success) {
    logger.info('Authentication failed or skipped, exiting application');
    app.quit();
  }
});

// IPC Events

// Start recording
ipcMain.on('start-recording', () => {
  logger.info(`[Main - ipcMain start-recording] Received 'start-recording'. isRecording: ${isRecording}, isHotkeyPressedToRecord: ${isHotkeyPressedToRecord}. SelectedMic: ${selectedAudioDeviceId || 'system default'}`);
  
  if (isRecording || currentAudioStream || recognizeStream) {
    logger.warn('[Main - ipcMain start-recording] Recording or STT was already in progress. Stopping previous.');
    stopFullRecordingProcess();
  }

  isRecording = false;
  isHotkeyPressedToRecord = false;

  try {
    logger.info(`[Main - ipcMain start-recording] Calling audioCapture.startRecording with device: ${selectedAudioDeviceId}`);
    currentAudioStream = startRecording({ device: selectedAudioDeviceId });

    if (currentAudioStream) {
      logger.info('[Main - ipcMain start-recording] Audio capture stream obtained.');

      if (!speechClient) {
        logger.error('[Main - ipcMain start-recording] Google SpeechClient is not available. Check GOOGLE_APPLICATION_CREDENTIALS.');
        if (mainWindow && mainWindow.webContents) {
          mainWindow.webContents.send('show-error', 'Speech client not initialized. Check credentials.');
        }
        stopRecording(); // From audioCapture
        currentAudioStream = null;
        isRecording = false;
        return;
      }

      const requestConfig = {
        config: {
          encoding: 'LINEAR16',
          sampleRateHertz: 16000,
          languageCode: 'en-US',
          enableAutomaticPunctuation: true,
        },
        interimResults: true,
      };

      recognizeStream = speechClient
        .streamingRecognize(requestConfig)
        .on('error', (err) => {
          logger.error('[Main - STT Stream] Google Speech API Error:', err);
          if (mainWindow && mainWindow.webContents) {
            mainWindow.webContents.send('show-error', `Speech API Error: ${err.message}`);
          }
          stopFullRecordingProcess(); // Use new helper for full cleanup
        })
        .on('data', (data) => {
          const transcriptData = data.results[0] && data.results[0].alternatives[0]
            ? `${data.results[0].alternatives[0].transcript}`
            : '';
          const isFinal = data.results[0] && data.results[0].isFinal;
          
          if (transcriptData && mainWindow && mainWindow.webContents) {
            mainWindow.webContents.send('speech-result', { transcript: transcriptData, isFinal });
          }

          if (isFinal && transcriptData) { // Ensure transcriptData is not empty
            logger.info(`[Main - STT Stream] Final STT Result: "${transcriptData}"`);
            handleCommand(transcriptData); // Call the new command handler
          }
        })
        .on('end', () => {
          logger.info('[Main - STT Stream] Google Speech API stream ended gracefully.');
          if(isRecording) { // If it ended but we thought we were still recording, clean up.
              stopFullRecordingProcess();
          }
        });

      logger.info('[Main - ipcMain start-recording] Piping audio stream to Google Speech API.');
      currentAudioStream.pipe(recognizeStream);
      
      isRecording = true; 
      logger.info('[Main - ipcMain start-recording] Successfully started recording and STT stream. isRecording=true');

    } else {
      logger.error('[Main - ipcMain start-recording] Failed to start audio capture or obtain stream from audioCapture.js.');
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('show-error', 'Failed to start microphone (audioCapture module).');
      }
      isRecording = false;
    }
  } catch (error) {
    logger.error(`[Main - ipcMain start-recording] Error during setup: ${error.message}`);
    stopFullRecordingProcess();
    isRecording = false;
  }
});

// Stop recording
ipcMain.on('stop-recording', () => {
  logger.info("[Main - ipcMain] Received 'stop-recording' (likely from renderer or STT end).");
  // This is a passive stop, active stop is via hotkey or error
  // stopFullRecordingProcess(); // Call the main stop function to ensure full cleanup
  // Let's refine this: this IPC is often from renderer which has limited scope.
  // The hotkey calls stopFullRecordingProcess directly.
  // If STT stream ends, it should also call stopFullRecordingProcess or parts of it.
  // For now, ensure audioCapture.stopRecording() is called.
  stopRecording(); // from audioCapture.js
  currentAudioStream = null;
  if (recognizeStream && !recognizeStream.destroyed) {
      logger.info('[Main - ipcMain stop-recording] Manually ending Google Speech API stream if not already destroyed.');
      recognizeStream.end(); 
      // recognizeStream = null; // Nullify in its own 'end' or 'error' handler
  }
  isRecording = false; // Update state
});

// Handle errors from renderer for logging in main
ipcMain.on('show-error-in-main', (event, message) => {
  logger.error(`Error reported from renderer: ${message}`);
});

// Comment out or remove the old simulate-voice-processing handler if no longer needed
// ipcMain.on('simulate-voice-processing', (event, text) => {
//   logger.info(`Simulating voice processing for: "${text}"`);
//   // Simulate validation
//   const validatedText = `Validated: ${text}`;
//   mainWindow.webContents.send('validation-result', validatedText);
//
//   // Simulate LLM response
//   setTimeout(() => {
//     const mockResponse = `Mock response to: "${validatedText}"`;
//     mainWindow.webContents.send('response-ready', mockResponse);
//     logger.info('Simulated response sent to renderer.');
//   }, 1500);
// }); 

// Basic Command Handler
async function handleCommand(transcribedText) {
  logger.info(`[Main - handleCommand] Received command: "${transcribedText}"`);
  
  // For now, just echo the command as the response
  const responseText = `You said: ${transcribedText}`;
  logger.info(`[Main - handleCommand] Prepared response: "${responseText}"`);

  // Send response text to UI
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('display-response-text', responseText);
  }

  // Synthesize speech for the response
  if (textToSpeechClient && responseText) {
    const ttsRequest = {
      input: { text: responseText },
      voice: { languageCode: 'en-US', name: 'en-US-Standard-C' },
      audioConfig: { audioEncoding: 'MP3' },
    };
    try {
      logger.info('[Main - handleCommand] Requesting speech synthesis for response.');
      const [ttsResponse] = await textToSpeechClient.synthesizeSpeech(ttsRequest);
      const audioContent = ttsResponse.audioContent.toString('base64');
      logger.info('[Main - handleCommand] Speech synthesized successfully for command response.');
      
      // Send audio to renderer to be played
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('play-response-audio', { 
          audioContent: audioContent, 
          audioEncoding: ttsRequest.audioConfig.audioEncoding 
        });
      }
    } catch (error) {
      logger.error(`[Main - handleCommand] Error synthesizing speech for command response: ${error.message}`, error);
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('show-error', `TTS Error for response: ${error.message}`);
      }
    }
  } else {
    if (!textToSpeechClient) logger.error('[Main - handleCommand] textToSpeechClient not available for response.');
    if (!responseText) logger.warn('[Main - handleCommand] No response text to synthesize.');
  }
}

// IPC Event for Text-to-Speech (used by Test TTS button, can also be used internally if needed)
ipcMain.handle('synthesize-speech', async (event, textToSynthesize) => {
  logger.info(`[Main - ipcMain synthesize-speech] Received request to synthesize: "${textToSynthesize}"`);
  logger.warn('[Main - ipcMain synthesize-speech] Direct TTS through main.js is deprecated. TTS should be handled via Pipecat.');
  // To prevent errors if textToSpeechClient is not defined due to the import being commented out:
  // if (!textToSpeechClient) { ... } block is no longer relevant if we don't intend to use it.
  
  if (!textToSynthesize) {
    logger.warn('[Main - ipcMain synthesize-speech] No text provided for synthesis.');
    return { error: 'No text provided for synthesis.' };
  }

  // Placeholder: Logic to send TTS request to Pipecat backend would go here.
  // For now, return an error indicating this path is not implemented for Pipecat.
  return { error: 'Direct TTS via main.js is deprecated. Please implement TTS through Pipecat.' };
});

// New helper function to stop recording and STT stream
function stopFullRecordingProcess() {
  logger.info('[Main - stopFullRecordingProcess] Initiating full stop of recording and STT.');
  
  // Stop the external audio capture process
  stopRecording(); // This is from audioCapture.js
  if (recognizeStream) {
    logger.debug('[Main - stopFullRecordingProcess] Destroying existing STT recognizeStream.');
    recognizeStream.destroy(); // Use destroy for immediate cleanup if needed, or end()
    recognizeStream = null;
  }
  currentAudioStream = null;
  isRecording = false; // Ensure state is updated
  logger.info('[Main - stopFullRecordingProcess] Full stop process complete. isRecording=false');
  // Optionally, send a message to renderer that recording has explicitly stopped
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('recording-stopped-by-main'); 
  }
}

function handleActivationHotkey() {
  console.log('=== DEBUG: handleActivationHotkey() called ==='); // Direct debug
  logger.info('[Main - handleActivationHotkey] Activation hotkey pressed.');
  if (mainWindow) {
    console.log('=== DEBUG: mainWindow exists ==='); // Direct debug
    if (mainWindow.isVisible()) {
      console.log('=== DEBUG: Window is visible, hiding ==='); // Direct debug
      logger.info('[Main - handleActivationHotkey] Window is visible. Hiding window and stopping listening.');
      // Send stop listening to renderer which will stop Pipecat pipeline
      logger.info("[Main - handleActivationHotkey] Sending 'stop-listening' to renderer.");
      mainWindow.webContents.send('stop-listening');
      mainWindow.hide();
      isHotkeyPressedToRecord = false;
    } else {
      console.log('=== DEBUG: Window is not visible, showing ==='); // Direct debug
      logger.info('[Main - handleActivationHotkey] Window is not visible. Showing window and preparing to start listening.');
      mainWindow.show();
      mainWindow.focus();
      isHotkeyPressedToRecord = true;
      // Send a message to the renderer to indicate it should start listening
      logger.info("[Main - handleActivationHotkey] Sending 'start-listening' to renderer.");
      mainWindow.webContents.send('start-listening');
    }
  } else {
    console.log('=== DEBUG: mainWindow is NULL! ==='); // Direct debug
    logger.error('[Main - handleActivationHotkey] mainWindow is not defined!');
  }
  console.log('=== DEBUG: handleActivationHotkey() completed ==='); // Direct debug
}

// IPC handler to restart the Pipecat backend
ipcMain.handle('restart-pipecat-backend', async () => {
  logger.info('Received request to restart Pipecat backend.');
  if (pipecatProcess) {
    logger.info('Stopping existing Pipecat backend process...');
    return new Promise((resolve) => {
      pipecatProcess.on('close', async () => {
        logger.info('Existing Pipecat backend process stopped. Starting new one...');
        await startPipecatBackend();
        resolve({ success: true, message: 'Pipecat backend restarted.' });
      });
      pipecatProcess.kill();
      pipecatProcess = null; // Ensure it's nullified after kill initiated
    });
  } else {
    logger.info('No existing Pipecat backend process found. Starting new one...');
    await startPipecatBackend();
    return { success: true, message: 'Pipecat backend started.' };
  }
});