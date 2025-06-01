/**
 * Audio capture functionality
 * EPIPE Error Prevention: Console operations disabled
 */

// No-op logging to prevent EPIPE errors
const safeLog = () => {};
const safeError = () => {};

const MicModule = require('node-mic');
// console.log('[AudioCapture] Inspecting MicModule:', MicModule); // Removed inspection log
const { PassThrough } = require('stream');

let micInstance = null;
let micInputStream = null;
let audioStreamRelay = null; // A PassThrough stream to relay audio data
let isRecording = false;

const defaultMicOptions = {
  rate: '16000', // Sample rate (Hz)
  channels: '1', // Number of channels
  debug: false, // Set to true for verbose logging from node-mic
  exitOnSilence: 0, // Number of seconds of silence before exiting (0 means disabled)
  // device: 'plughw:0,0', // Specific device, e.g., for Linux. Default usually works.
  fileType: 'raw', // Output format
};

function startRecording(captureOptions = {}) {
  if (isRecording) {
    safeLog('[AudioCapture] Recording is already in progress.');
    return null;
  }

  let actualMicOptions = { ...defaultMicOptions };
  
  // Handle device selection for microphone
  if (captureOptions.device && captureOptions.device !== 'default') {
    // If user provided a specific device ID, use it
    actualMicOptions.device = captureOptions.device;
    safeLog(`[AudioCapture] Attempting to use specific microphone device ID: ${actualMicOptions.device}`);
  } else if (captureOptions.device === 'default') {
    // If user explicitly chose "default", use null (system default)
    actualMicOptions.device = null;
    safeLog(`[AudioCapture] Received device hint '${captureOptions.device}'. Using system default microphone.`);
  } else {
    // If no device provided, use system default
    safeLog('[AudioCapture] No specific device provided. Using system default microphone.');
  }

  safeLog('[AudioCapture] Final NodeMic options:', actualMicOptions);

  try {
    micInstance = MicModule(actualMicOptions);
  } catch (err) {
    safeError('[AudioCapture] Error initializing Mic instance:', err);
    return null;
  }
  
  micInputStream = micInstance.getAudioStream();
  audioStreamRelay = new PassThrough(); // Create a new relay for each recording session

  micInputStream.pipe(audioStreamRelay);

  micInputStream.on('data', (data) => {
    // Silently handle audio data
  });

  micInputStream.on('error', (error) => {
    safeError('[AudioCapture] Error from microphone stream:', error);
  });

  micInputStream.on('silence', () => {
    safeLog('Silence detected from microphone.');
  });

  micInputStream.on('processExitComplete', () => {
    safeLog('Microphone process exited.');
  });
  
  micInstance.start();
  safeLog('Audio recording started.');
  isRecording = true;

  return audioStreamRelay;
}

function stopRecording() {
  if (micInstance && isRecording) {
    micInstance.stop();
    safeLog('Audio recording stopped.');
    isRecording = false;
    micInstance = null;
    micInputStream = null; 
    if (audioStreamRelay) {
      audioStreamRelay.end(); // Signal no more data will be written
      audioStreamRelay = null;
    }
    return true;
  } else {
    safeLog('Recording is not in progress.');
    return false;
  }
}

module.exports = {
  startRecording,
  stopRecording,
}; 