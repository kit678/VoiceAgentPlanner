const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use IPC
contextBridge.exposeInMainWorld('api', {
  // Recording controls
  startRecording: () => ipcRenderer.send('start-recording'),
  stopRecording: () => ipcRenderer.send('stop-recording'),
  
  // Temporary simulation function for MVP (now commented out in main.js)
  // simulateVoiceProcessing: (text) => ipcRenderer.send('simulate-voice-processing', text),
  
  // Result listeners
  onStartListening: (callback) => ipcRenderer.on('start-listening', callback),
  onStopListening: (callback) => ipcRenderer.on('stop-listening', callback),
  onSpeechResult: (callback) => ipcRenderer.on('speech-result', (event, data) => callback(data)),
  onShowError: (callback) => ipcRenderer.on('show-error', (event, message) => callback(message)),
  onDisplayResponseText: (callback) => ipcRenderer.on('display-response-text', (event, text) => callback(text)),
  onPlayResponseAudio: (callback) => ipcRenderer.on('play-response-audio', (event, data) => callback(data)),
  onBackendTrulyReady: (callback) => ipcRenderer.on('backend-truly-ready', callback), // Added for WebSocket sync

  // Microphone selection
  setAudioInputDevice: (deviceId) => ipcRenderer.send('set-audio-input-device', deviceId),
  // For renderer to store/retrieve preferences directly using electron-store via main process
  getStoredAudioInputDevice: () => ipcRenderer.invoke('get-stored-audio-input-device'),
  storeAudioInputDevice: (deviceId) => ipcRenderer.send('store-audio-input-device', deviceId),
  // For TTS
  synthesizeSpeech: (text) => ipcRenderer.invoke('synthesize-speech', text),
  
  // Google OAuth Authentication
  startGoogleAuth: () => ipcRenderer.invoke('start-google-auth'),
  completeGoogleAuth: (authCode) => ipcRenderer.invoke('complete-google-auth', authCode),
  getAuthStatus: () => ipcRenderer.invoke('get-auth-status'),
  sendAuthCompleted: (success) => ipcRenderer.send('auth-completed', success),
  onAuthCompleted: (callback) => ipcRenderer.on('auth-completed', (event, success) => callback(success)),
  
  // External URL opening
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // OAuth callback handling
  onOAuthCallback: (callback) => ipcRenderer.on('oauth-callback', (event, result) => callback(result))
});