require('dotenv').config(); // Load .env variables
const { app, BrowserWindow, ipcMain, globalShortcut, session } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const config = require('./config/app-config');
const hotkeyManager = require('./src/utils/hotkeys');
const logger = require('./src/utils/logger');
const { startRecording, stopRecording } = require('./src/audio/audioCapture');
// const { speechClient, textToSpeechClient } = require('./src/utils/googleCloudClients'); // Kept for future use, commented out to suppress credential warnings

// Keep a global reference of the window object
let mainWindow;
let currentAudioStream = null;
let recognizeStream = null;
let selectedAudioDeviceId = null; // To store the chosen device ID
let isRecording = false; // New state variable
let isHotkeyPressedToRecord = false; // To differentiate hotkey trigger from other UI actions if needed
let pipecatProcess = null; // Pipecat backend process

function createWindow() {
  logger.info('Creating main application window');
  
  // Get window settings from config
  const windowWidth = config.get('ui.windowWidth');
  const windowHeight = config.get('ui.windowHeight');
  const alwaysOnTop = config.get('ui.alwaysOnTop');
  
  mainWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    show: false,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: alwaysOnTop,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Clear cache and then load the file
  async function clearCacheAndLoad() {
    try {
      if (session && session.defaultSession) {
        await session.defaultSession.clearStorageData(); // Clears cache, cookies, storage etc.
        logger.info('[Main - createWindow] Electron session storage cleared.');
      } else {
        logger.warn('[Main - createWindow] Electron session or defaultSession not available for cache clearing.');
      }
    } catch (err) {
      logger.error('[Main - createWindow] Failed to clear session storage:', err);
    }
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  }
  clearCacheAndLoad();
  
  // Hide window initially (will be shown on hotkey press)
  mainWindow.on('ready-to-show', () => {
    logger.debug('Main window ready to show, registering hotkey');
    // mainWindow.show(); // Window will be shown by hotkey
    // mainWindow.focus(); // Window will be focused by hotkey
    
    // Register global hotkey using our utility
    if (!hotkeyManager.registerActivationHotkey(handleActivationHotkey)) {
      logger.error('[Main] FAILED TO REGISTER ACTIVATION HOTKEY. App may not be fully functional.');
      // Consider showing an error dialog to the user
    }
  });

  // Hide when focus is lost
  mainWindow.on('blur', () => {
    logger.debug('Window lost focus');
    if (mainWindow && mainWindow.isVisible()) {
      logger.debug('Window lost focus, hiding and stopping listening.');
      // Send stop listening to renderer
      mainWindow.webContents.send('stop-listening');
      mainWindow.hide();
    } else {
      logger.debug('Window lost focus but was not visible, no action.');
    }
  });
}

// Start Pipecat backend process
function startPipecatBackend() {
  logger.info('Starting Pipecat backend process...');
  
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
  const scriptPath = path.join(__dirname, 'src', 'pipecat_pipeline.py');
  
  pipecatProcess = spawn(pythonPath, [scriptPath], {
    cwd: __dirname,
    stdio: ['pipe', 'pipe', 'pipe']
  });
  
  pipecatProcess.stdout.on('data', (data) => {
    logger.info(`[Pipecat] ${data.toString().trim()}`);
  });
  
  pipecatProcess.stderr.on('data', (data) => {
    logger.error(`[Pipecat Error] ${data.toString().trim()}`);
  });
  
  pipecatProcess.on('close', (code) => {
    logger.info(`[Pipecat] Process exited with code ${code}`);
    pipecatProcess = null;
  });
  
  pipecatProcess.on('error', (error) => {
    logger.error(`[Pipecat] Failed to start: ${error.message}`);
    pipecatProcess = null;
  });
}

// Create window when Electron is ready
app.whenReady().then(() => {
  logger.info('Application ready, starting initialization');
  
  // Reset to defaults to ensure fresh config for hotkey testing
  logger.info('Resetting configuration to defaults to pick up latest hotkey.');
  config.resetToDefaults();
  
  // Set app name from config
  app.setName(config.get('app.name'));
  
  createWindow();
  
  // Start Pipecat backend after a short delay
  setTimeout(() => {
    startPipecatBackend();
  }, 2000);
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
  if (!textToSpeechClient) {
    logger.error('[Main - ipcMain synthesize-speech] TextToSpeechClient is not available.');
    return { error: 'TextToSpeech client not initialized.' };
  }
  if (!textToSynthesize) {
    logger.warn('[Main - ipcMain synthesize-speech] No text provided for synthesis.');
    return { error: 'No text provided for synthesis.' };
  }

  const request = {
    input: { text: textToSynthesize },
    voice: { languageCode: 'en-US', name: 'en-US-Standard-C' }, // Example voice
    audioConfig: { audioEncoding: 'MP3' }, // Or LINEAR16, OGG_OPUS
  };

  try {
    const [response] = await textToSpeechClient.synthesizeSpeech(request);
    const audioContent = response.audioContent.toString('base64');
    logger.info('[Main - ipcMain synthesize-speech] Speech synthesized successfully.');
    return { audioContent: audioContent, audioEncoding: request.audioConfig.audioEncoding };
  } catch (error) {
    logger.error(`[Main - ipcMain synthesize-speech] Error synthesizing speech: ${error.message}`, error);
    return { error: `TTS Error: ${error.message}` };
  }
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
  logger.info('[Main - handleActivationHotkey] Activation hotkey pressed.');
  if (mainWindow) {
    if (mainWindow.isVisible()) {
      logger.info('[Main - handleActivationHotkey] Window is visible. Hiding window and stopping listening.');
      // Send stop listening to renderer which will stop Pipecat pipeline
      logger.info("[Main - handleActivationHotkey] Sending 'stop-listening' to renderer.");
      mainWindow.webContents.send('stop-listening');
      mainWindow.hide();
      isHotkeyPressedToRecord = false;
    } else {
      logger.info('[Main - handleActivationHotkey] Window is not visible. Showing window and preparing to start listening.');
      mainWindow.show();
      mainWindow.focus();
      isHotkeyPressedToRecord = true;
      // Send a message to the renderer to indicate it should start listening
      logger.info("[Main - handleActivationHotkey] Sending 'start-listening' to renderer.");
      mainWindow.webContents.send('start-listening');
    }
  } else {
    logger.error('[Main - handleActivationHotkey] mainWindow is not defined!');
  }
}