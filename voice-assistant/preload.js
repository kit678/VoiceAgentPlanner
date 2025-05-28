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
  // onSpeechResult now receives { transcript, isFinal }
  onSpeechResult: (callback) => ipcRenderer.on('speech-result', (event, data) => callback(data)),
  onValidationResult: (callback) => ipcRenderer.on('validation-result', (event, text) => callback(text)),
  onResponseReady: (callback) => ipcRenderer.on('response-ready', (event, text) => callback(text)),
  onDisplayResponseText: (callback) => ipcRenderer.on('display-response-text', (event, text) => callback(text)),
  onPlayResponseAudio: (callback) => ipcRenderer.on('play-response-audio', (event, data) => callback(data)),
  
  // Error handling
  onShowError: (callback) => ipcRenderer.on('show-error', (event, message) => callback(message)),
  showErrorInMain: (message) => ipcRenderer.send('show-error-in-main', message),

  // Microphone / Audio Input Selection
  setAudioInputDevice: (deviceId) => ipcRenderer.send('set-audio-input-device', deviceId),
  // For renderer to store/retrieve preferences directly using electron-store via main process
  getStoredAudioInputDevice: () => ipcRenderer.invoke('get-stored-audio-input-device'),
  storeAudioInputDevice: (deviceId) => ipcRenderer.send('store-audio-input-device', deviceId),
  // For TTS
  synthesizeSpeech: (text) => ipcRenderer.invoke('synthesize-speech', text)
}); 