const { SpeechClient } = require('@google-cloud/speech');
const { TextToSpeechClient } = require('@google-cloud/text-to-speech');

let speechClient;
let textToSpeechClient;

if (!process.env.GOOGLE_APPLICATION_CREDENTIALS) {
  console.error(
    'GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. ' +
    'Google Cloud clients will not be initialized. ' +
    'Please set this variable to the path of your service account key file.'
  );
  // In a real application, you might throw an error or handle this more gracefully
} else {
  try {
    speechClient = new SpeechClient();
    console.log('Google Cloud SpeechClient initialized successfully.');
  } catch (error) {
    console.error('Failed to initialize Google Cloud SpeechClient:', error);
    // Handle or throw error as appropriate for your application
  }

  try {
    textToSpeechClient = new TextToSpeechClient();
    console.log('Google Cloud TextToSpeechClient initialized successfully.');
  } catch (error) {
    console.error('Failed to initialize Google Cloud TextToSpeechClient:', error);
    // Handle or throw error as appropriate for your application
  }
}

module.exports = {
  speechClient,
  textToSpeechClient,
}; 