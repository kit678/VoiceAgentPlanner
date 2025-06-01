/**
 * Google Cloud client initialization utility
 * EPIPE Error Prevention: Console operations disabled
 */
const { SpeechClient } = require('@google-cloud/speech');
const { TextToSpeechClient } = require('@google-cloud/text-to-speech');

// No-op logging to prevent EPIPE errors
const safeLog = () => {};
const safeError = () => {};

function initializeGoogleSpeechClient() {
  try {
    const speechClient = new SpeechClient();
    safeLog('Google Cloud SpeechClient initialized successfully.');
    return speechClient;
  } catch (error) {
    safeError('Failed to initialize Google Cloud SpeechClient:', error);
    return null;
  }
}

function initializeGoogleTextToSpeechClient() {
  try {
    const ttsClient = new TextToSpeechClient();
    safeLog('Google Cloud TextToSpeechClient initialized successfully.');
    return ttsClient;
  } catch (error) {
    safeError('Failed to initialize Google Cloud TextToSpeechClient:', error);
    return null;
  }
}

module.exports = {
  initializeGoogleSpeechClient,
  initializeGoogleTextToSpeechClient
}; 