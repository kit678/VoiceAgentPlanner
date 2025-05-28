const MicModule = require('node-mic');
// console.log('[AudioCapture] Inspecting MicModule:', MicModule); // Removed inspection log
const { PassThrough } = require('stream');

let micInstance = null;
let micInputStream = null;
let audioStreamRelay = null; // A PassThrough stream to relay audio data

const defaultMicOptions = {
  rate: '16000', // Sample rate (Hz)
  channels: '1', // Number of channels
  debug: false, // Set to true for verbose logging from node-mic
  exitOnSilence: 0, // Number of seconds of silence before exiting (0 means disabled)
  // device: 'plughw:0,0', // Specific device, e.g., for Linux. Default usually works.
  fileType: 'raw', // Output format
};

function startRecording(captureOptions = {}) { // captureOptions might contain { device: 'deviceId' }
  if (micInstance) {
    console.log('[AudioCapture] Recording is already in progress.');
    return audioStreamRelay;
  }

  let actualMicOptions = { ...defaultMicOptions };
  
  // Handle deviceId carefully
  // 'default' and 'communications' are special device IDs from enumerateDevices.
  // Other long strings are actual device IDs.
  // node-mic expects either a system-specific name or to be omitted for system default.
  if (captureOptions.device && typeof captureOptions.device === 'string' && 
      captureOptions.device !== 'default' && captureOptions.device !== 'communications') {
    // If we have a specific deviceId (that is not 'default' or 'communications'), pass it along.
    // This relies on node-mic/SoX/arecord being able to use this ID directly, which is uncertain.
    actualMicOptions.device = captureOptions.device;
    console.log(`[AudioCapture] Attempting to use specific microphone device ID: ${actualMicOptions.device}`);
  } else if (captureOptions.device) {
    // If it's 'default' or 'communications', or any other non-specific case, we explicitly don't set the device, 
    // letting node-mic use the system default microphone.
    console.log(`[AudioCapture] Received device hint '${captureOptions.device}'. Using system default microphone.`);
    // actualMicOptions.device remains unset (or default from defaultMicOptions, which is commented out)
  } else {
    console.log('[AudioCapture] No specific device provided. Using system default microphone.');
    // actualMicOptions.device remains unset
  }

  console.log('[AudioCapture] Final NodeMic options:', actualMicOptions);

  try {
    micInstance = new MicModule.default(actualMicOptions);
  } catch (err) {
    console.error('[AudioCapture] Error initializing Mic instance:', err);
    // Propagate this error or handle it, maybe return null or throw
    return null; // Indicate failure to start
  }
  
  micInputStream = micInstance.getAudioStream();
  audioStreamRelay = new PassThrough(); // Create a new relay for each recording session

  micInputStream.pipe(audioStreamRelay);

  micInputStream.on('data', (data) => {
    // console.log('Audio data received:', data.length);
    // Data is already being piped to audioStreamRelay
  });

  micInputStream.on('error', (error) => {
    console.error('[AudioCapture] Error from microphone stream:', error);
    stopRecording(); // Clean up on error
    if (audioStreamRelay) {
        audioStreamRelay.emit('error', error); // Propagate error to relay listeners if they exist
    }
  });

  micInputStream.on('silence', () => {
    console.log('Silence detected from microphone.');
    // Handle silence if needed, e.g., auto-stop recording
  });

  micInputStream.on('processExitComplete', () => {
    console.log('Microphone process exited.');
  });
  
  micInstance.start();
  console.log('Audio recording started.');
  return audioStreamRelay; // Return the relay stream for consumers
}

function stopRecording() {
  if (micInstance) {
    micInstance.stop();
    console.log('Audio recording stopped.');
    micInstance = null;
    micInputStream = null; 
    if (audioStreamRelay) {
      audioStreamRelay.end(); // Signal no more data will be written
      audioStreamRelay = null;
    }
  } else {
    console.log('Recording is not in progress.');
  }
}

module.exports = {
  startRecording,
  stopRecording,
}; 