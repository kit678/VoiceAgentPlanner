// DOM elements
const statusIndicator = document.querySelector('.status-indicator');
const transcript = document.getElementById('transcript');
const response = document.getElementById('response');
const micSelect = document.getElementById('mic-select');
const refreshMicListBtn = document.getElementById('refresh-mic-list-btn');
const testTtsBtn = document.getElementById('test-tts-btn');

console.log('[Renderer.js] Script loaded. Version: 1.0.2'); // Incremented version

// Initialize WebSocket connection to Pipecat backend
let pipecatConnected = false;

// WebSocket event handlers
window.pipecatClient.on('connected', () => {
  console.log('[Renderer] Connected to Pipecat backend');
  pipecatConnected = true;
  // Update UI to show backend connection status
  if (transcript.textContent === 'Connecting to backend...') {
    transcript.textContent = 'Ready';
  }
});

window.pipecatClient.on('disconnected', () => {
  console.log('[Renderer] Disconnected from Pipecat backend');
  pipecatConnected = false;
  transcript.textContent = 'Backend disconnected';
  setIdleState();
});

window.pipecatClient.on('status', (data) => {
  console.log('[Renderer] Received status from Pipecat:', data);
  if (data.message) {
    response.textContent = data.message;
  }
});

window.pipecatClient.on('transcription', (data) => {
  console.log('[Renderer] Received transcription from Pipecat:', data);
  if (data.text) {
    transcript.textContent = data.text;
    if (data.is_final) {
      setProcessingState();
    } else {
      setListeningState();
    }
  }
});

window.pipecatClient.on('response_text', (data) => {
  console.log('[Renderer] Received response text from Pipecat:', data);
  if (data.text) {
    response.textContent = data.text;
    if (data.source === 'llm_response') {
      setSpeakingState();
    }
  }
});

window.pipecatClient.on('audio_started', () => {
  console.log('[Renderer] Pipecat started generating audio');
  setSpeakingState();
});

window.pipecatClient.on('audio_stopped', () => {
  console.log('[Renderer] Pipecat stopped generating audio');
  setIdleState();
});

window.pipecatClient.on('error', (data) => {
  console.error('[Renderer] Pipecat error:', data);
  transcript.textContent = `Backend error: ${data.message || 'Unknown error'}`;
  setIdleState();
});

// Connect to Pipecat backend on load
window.addEventListener('DOMContentLoaded', () => {
  transcript.textContent = 'Connecting to backend...';
  window.pipecatClient.connect();
});



// UI state handling
function setListeningState() {
  statusIndicator.className = 'status-indicator listening';
  transcript.textContent = 'Listening...';
  response.textContent = '';
}

function setProcessingState() {
  statusIndicator.className = 'status-indicator processing';
}

function setSpeakingState() {
  statusIndicator.className = 'status-indicator speaking';
}

function setIdleState() {
  statusIndicator.className = 'status-indicator';
}

// Voice Assistant API events - now integrated with Pipecat WebSocket
window.api.onStartListening(() => {
  console.log('[Renderer.js] onStartListening event received.');
  if (pipecatConnected) {
    console.log('[Renderer] Starting Pipecat listening via WebSocket');
    window.pipecatClient.startListening();
    setListeningState();
  } else {
    console.log('[Renderer] Pipecat not connected, showing connection status');
    transcript.textContent = 'Connecting to voice assistant...';
    response.textContent = 'Please wait for backend to connect';
  }
});

window.api.onStopListening(() => {
  console.log('[Renderer.js] onStopListening event received.');
  if (pipecatConnected) {
    console.log('[Renderer] Stopping Pipecat listening via WebSocket');
    window.pipecatClient.stopListening();
    setIdleState();
  }
});

window.api.onSpeechResult((data) => { // data is now { transcript, isFinal }
  if (data && data.transcript) {
    transcript.textContent = data.transcript;
    if (data.isFinal) {
      console.log('[Renderer] Final speech result received:', data.transcript);
      setProcessingState(); // Or some other state indicating final transcript received
      // Here you might trigger next steps like sending to validation or LLM
      // For now, main.js handles logging final result. Renderer just displays.
    } else {
      // Interim result, just update transcript
      setListeningState(); // Keep in listening state, but update transcript
      transcript.textContent = data.transcript;
    }
  }
});

// Handle errors from main process
window.api.onShowError((message) => {
  console.error('Renderer received error:', message);
  transcript.textContent = `ERROR: ${message}`;
  setIdleState(); // Go to idle on error
  // Optionally, send to main process log as well
  // window.api.showErrorInMain(`Renderer displayed error: ${message}`);
});

// New: Handle display-response-text from main process
window.api.onDisplayResponseText((text) => {
  console.log(`[Renderer] Received response text to display: "${text}"`);
  response.textContent = text;
  setIdleState(); // Or a state indicating response received
});

// New: Handle play-response-audio from main process
window.api.onPlayResponseAudio((data) => {
  if (data && data.audioContent) {
    console.log('[Renderer] Received synthesized audio for command response.');
    response.textContent = "Playing response..."; // Update UI briefly
    setSpeakingState();
    const audioSource = `data:audio/${data.audioEncoding === 'MP3' ? 'mpeg' : 'ogg'};base64,${data.audioContent}`;
    const audio = new Audio(audioSource);
    audio.play();
    audio.onended = () => {
      response.textContent = response.textContent; // Keep the displayed text
      setIdleState();
      console.log('[Renderer] Response audio finished playing.');
    };
    audio.onerror = (err) => {
      console.error('[Renderer] Error playing response audio:', err);
      response.textContent = 'Error playing response audio.';
      setIdleState();
      window.api.showErrorInMain(`Renderer: Error playing response audio - ${err.message}`);
    };
  } else {
    console.error('[Renderer] Invalid audio data received for play-response-audio.', data);
    response.textContent = 'Error: Invalid audio data for response.';
    setIdleState();
  }
});

// --- Microphone Selection --- //

async function populateAudioInputList() {
  console.log('[Renderer] Attempting to populate audio input list...');
  transcript.textContent = 'Requesting microphone permissions...';
  micSelect.innerHTML = '<option value="">Loading mics...</option>'; // Initial placeholder

  try {
    console.log('[Renderer] Requesting media device access (getUserMedia for audio).');
    await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log('[Renderer] Microphone permission granted.');
    transcript.textContent = 'Fetching microphone list...';

    const devices = await navigator.mediaDevices.enumerateDevices();
    console.log('[Renderer] Enumerated devices:', devices);
    const audioInputDevices = devices.filter(device => device.kind === 'audioinput');
    console.log('[Renderer] Filtered audio input devices:', audioInputDevices);
    
    micSelect.innerHTML = ''; // Clear placeholder/previous options

    if (audioInputDevices.length === 0) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No microphones found';
      micSelect.appendChild(option);
      console.warn('[Renderer] No audio input devices found.');
      transcript.textContent = 'No microphones found.';
      return;
    }

    audioInputDevices.forEach((device, index) => {
      const option = document.createElement('option');
      option.value = device.deviceId;
      option.textContent = device.label || `Mic ${index + 1} (ID: ${device.deviceId.substring(0,10)}...)`;
      micSelect.appendChild(option);
      console.log(`[Renderer] Added mic to dropdown: ${option.textContent} (ID: ${device.deviceId})`);
    });
    
    transcript.textContent = 'Microphone list updated.';
    console.log('[Renderer] Microphone dropdown populated.');

    // Load and apply stored preference
    console.log('[Renderer] Attempting to get stored audio input device...');
    const storedDeviceId = await window.api.getStoredAudioInputDevice();
    console.log('[Renderer] Got stored audio input device ID from main:', storedDeviceId);

    if (storedDeviceId && micSelect.querySelector(`option[value="${storedDeviceId}"]`)) {
      micSelect.value = storedDeviceId;
      console.log('[Renderer] Applied stored microphone preference:', storedDeviceId);
      window.api.setAudioInputDevice(storedDeviceId); // Inform main process
    } else if (micSelect.options.length > 0) {
      micSelect.selectedIndex = 0; // Select the first one if no valid stored one
      console.log('[Renderer] No valid stored preference or it was not found in current list. Selected first available mic:', micSelect.value);
      window.api.setAudioInputDevice(micSelect.value);
      window.api.storeAudioInputDevice(micSelect.value); // Also store this initial selection
    } else {
        console.log('[Renderer] No microphones available to select as default after attempting to load stored.');
    }

  } catch (err) {
    console.error('[Renderer] Error in populateAudioInputList:', err);
    transcript.textContent = `Error getting mics: ${err.name} - ${err.message}`;
    micSelect.innerHTML = '<option value="">Error fetching mics</option>';
    if (window.api && window.api.showErrorInMain) {
        window.api.showErrorInMain(`[Renderer] Error populating audio input list: ${err.name} - ${err.message}`);
    }
  }
}

micSelect.addEventListener('change', (event) => {
  const selectedDeviceId = event.target.value;
  console.log('[Renderer] micSelect change event. Selected deviceId:', selectedDeviceId);
  if (selectedDeviceId) {
    window.api.setAudioInputDevice(selectedDeviceId);
    window.api.storeAudioInputDevice(selectedDeviceId);
  } else {
    console.warn('[Renderer] micSelect changed to an empty value.');
  }
});

refreshMicListBtn.addEventListener('click', () => {
  console.log('[Renderer] refreshMicListBtn click event.');
  populateAudioInputList();
});

// --- Restored Test TTS Button Click Handler (Top Level) ---
if (testTtsBtn) {
  console.log('[Renderer] testTtsBtn element found at top level. Attaching FULL TTS listener.');
  testTtsBtn.addEventListener('click', async () => {
    console.log('[Renderer] Test TTS button clicked (FULL listener).');
    response.textContent = 'Synthesizing speech...';
    setProcessingState();
    const textToSpeak = "Hello, this is a test of the text to speech system.";
    try {
      const result = await window.api.synthesizeSpeech(textToSpeak);
      if (result.audioContent) {
        console.log('[Renderer] Received synthesized audio.');
        response.textContent = 'Playing audio...';
        setSpeakingState();
        const audioSource = `data:audio/mpeg;base64,${result.audioContent}`;
        const audio = new Audio(audioSource);
        audio.play();
        audio.onended = () => {
          response.textContent = 'Audio finished.';
          setIdleState();
        };
        audio.onerror = (err) => {
          console.error('[Renderer] Error playing audio:', err);
          response.textContent = 'Error playing audio.';
          setIdleState();
          window.api.showErrorInMain(`Renderer: Error playing synthesized audio - ${err.message}`);
        };
      } else if (result.error) {
        console.error('[Renderer] TTS Error:', result.error);
        response.textContent = `TTS Error: ${result.error}`;
        setIdleState();
      }
    } catch (error) {
      console.error('[Renderer] Error calling synthesizeSpeech:', error);
      response.textContent = `Error: ${error.message}`;
      setIdleState();
      window.api.showErrorInMain(`Renderer: Error invoking synthesizeSpeech - ${error.message}`);
    }
  });
} else {
  console.error('[Renderer] testTtsBtn element NOT found at top level.');
}

// Initial population of the microphone list on load
window.addEventListener('DOMContentLoaded', () => {
  console.log('[Renderer] DOMContentLoaded event. Calling populateAudioInputList.');
  populateAudioInputList();
}); 