/**
 * Main Renderer Logic for Voice Assistant
 * Integrates with preload.js API and handles all UI interactions
 */

class VoiceAssistantRenderer {
    constructor() {
        this.wsClient = null;
        this.isListening = false;
        this.isAuthenticated = false;
        this.currentMicDevice = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.currentTranscription = '';
        this.interimTranscription = '';
        
        // DOM elements
        this.elements = {};
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    async init() {
        console.log('Initializing Voice Assistant Renderer');
        
        // Cache DOM elements
        this.cacheElements();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize WebSocket client
        this.initWebSocket();
        
        // Check authentication status
        await this.checkAuthStatus();
        
        // Load microphone devices
        await this.loadMicrophoneDevices();
        
        // Setup preload API listeners
        this.setupPreloadListeners();
        
        console.log('Voice Assistant Renderer initialized');
    }
    
    cacheElements() {
        this.elements = {
            // Status indicators
            backendStatus: document.getElementById('backend-status'),
            authStatus: document.getElementById('auth-status'),
            
            // Sections
            authSection: document.getElementById('auth-section'),
            voiceSection: document.getElementById('voice-section'),
            oauthCallback: document.getElementById('oauth-callback'),
            
            // Authentication
            googleAuthBtn: document.getElementById('google-signin-button'),
            
            // Microphone
            micSelect: document.getElementById('mic-select'),
            refreshMicsBtn: document.getElementById('refresh-mics'),
            micButton: document.getElementById('mic-button'),
            voiceStatus: document.getElementById('voice-status'),
            
            // Content displays
            transcriptionDisplay: document.getElementById('transcription-display'),
            responseDisplay: document.getElementById('response-display'),
            
            // Notifications
            notificationContainer: document.getElementById('notification-container')
        };
    }
    
    setupEventListeners() {
        // Google Auth button
        this.elements.googleAuthBtn?.addEventListener('click', () => this.handleGoogleAuth());
        
        // Microphone selection
        this.elements.micSelect?.addEventListener('change', (e) => this.handleMicrophoneChange(e.target.value));
        this.elements.refreshMicsBtn?.addEventListener('click', () => this.loadMicrophoneDevices());
        
        // Microphone button
        this.elements.micButton?.addEventListener('click', () => this.toggleListening());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
    }
    
    setupPreloadListeners() {
        if (!window.api) {
            console.error('Preload API not available');
            return;
        }
        
        // Speech result listeners
        window.api.onSpeechResult((result) => {
            this.handleSpeechResult(result);
        });
        
        // Response text listener
        window.api.onDisplayResponseText((text) => {
            this.displayAssistantResponse(text);
        });
        
        // Start/stop listening listeners
        window.api.onStartListening?.(() => {
            this.updateVoiceStatus('Listening...', 'listening');
        });
        
        window.api.onStopListening?.(() => {
            this.updateVoiceStatus('Processing...', 'processing');
        });
        
        // Auth completed listener
        window.api.onAuthCompleted?.((success) => {
            this.updateAuthStatus(success);
        });
        
        // OAuth callback listener
        window.api.onOAuthCallback?.((result) => {
            this.handleOAuthCallback(result);
        });
    }
    
    initWebSocket() {
        this.wsClient = new WebSocketClient();
        
        // Set up WebSocket callbacks
        this.wsClient.setConnectionChangeCallback((status) => {
            this.updateBackendStatus(status);
        });
        
        this.wsClient.setTranscriptionUpdateCallback((data) => {
            this.updateTranscription(data);
        });
        
        this.wsClient.setResponseReceivedCallback((data) => {
            this.displayAssistantResponse(data.text);
        });
        
        this.wsClient.setErrorCallback((error) => {
            this.showNotification(error, 'error');
        });
    }
    
    async checkAuthStatus() {
        try {
            // Check if user is already authenticated
            const authResult = await window.api?.getAuthStatus?.();
            const isAuth = authResult?.authenticated || false;
            console.log('Auth status from preload:', authResult, 'Processed as:', isAuth); // Updated for debugging
            this.updateAuthStatus(isAuth);
        } catch (error) {
            console.error('Error checking auth status:', error);
            this.updateAuthStatus(false);
        }
    }
    
    async loadMicrophoneDevices() {
        try {
            // Get stored audio input device
            const storedDevice = await window.api?.getStoredAudioInputDevice?.();
            
            // Get available audio devices
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            
            // Clear existing options
            this.elements.micSelect.innerHTML = '<option value="">Select microphone...</option>';
            
            // Add device options
            audioInputs.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `Microphone ${device.deviceId.slice(0, 8)}`;
                
                if (storedDevice && device.deviceId === storedDevice) {
                    option.selected = true;
                    this.currentMicDevice = device.deviceId;
                }
                
                this.elements.micSelect.appendChild(option);
            });
            
            // If no stored device but devices available, select first one
            if (!storedDevice && audioInputs.length > 0) {
                this.elements.micSelect.selectedIndex = 1;
                this.currentMicDevice = audioInputs[0].deviceId;
                await this.handleMicrophoneChange(this.currentMicDevice);
            }
            
        } catch (error) {
            console.error('Error loading microphone devices:', error);
            this.showNotification('Error loading microphone devices', 'error');
        }
    }
    
    async handleMicrophoneChange(deviceId) {
        if (!deviceId) return;
        
        try {
            this.currentMicDevice = deviceId;
            
            // Store the selected device
            await window.api?.setAudioInputDevice?.(deviceId);
            
            this.showNotification('Microphone updated', 'success');
        } catch (error) {
            console.error('Error changing microphone:', error);
            this.showNotification('Error changing microphone', 'error');
        }
    }
    
    async handleGoogleAuth() {
        try {
            this.showOAuthCallback(true);
            
            // Start Google OAuth flow
            const result = await window.api?.startGoogleAuth?.();
            
            if (result && result.success) {
                this.updateAuthStatus(true);
                this.showNotification('Successfully authenticated with Google', 'success');
            } else {
                throw new Error(result?.error || 'Authentication failed');
            }
        } catch (error) {
            console.error('Google Auth error:', error);
            this.showNotification('Authentication failed: ' + error.message, 'error');
        } finally {
            this.showOAuthCallback(false);
        }
    }
    
    handleOAuthCallback(result) {
        console.log('OAuth callback received:', result);
        
        if (result && result.success) {
            this.updateAuthStatus(true);
            this.showNotification('Successfully authenticated with Google', 'success');
        } else {
            this.showNotification('Authentication failed: ' + (result?.error || 'Unknown error'), 'error');
        }
        
        this.showOAuthCallback(false);
    }
    
    async toggleListening() {
        if (!this.isAuthenticated) {
            this.showNotification('Please authenticate with Google first', 'warning');
            return;
        }
        
        if (!this.currentMicDevice) {
            this.showNotification('Please select a microphone first', 'warning');
            return;
        }
        
        if (!this.wsClient.isReady()) {
            this.showNotification('Backend not connected', 'error');
            return;
        }
        
        try {
            if (this.isListening) {
                await this.stopListening();
            } else {
                await this.startListening();
            }
        } catch (error) {
            console.error('Error toggling listening:', error);
            this.showNotification('Error with voice recording', 'error');
        }
    }
    
    async startListening() {
        try {
            // Start recording via preload API (this sends IPC message)
            window.api?.startRecording?.();
            
            this.isListening = true;
            this.updateVoiceStatus('Listening...', 'listening');
            this.wsClient.startListening();
            
            // Clear previous transcription
            this.currentTranscription = '';
            this.interimTranscription = '';
            this.updateTranscriptionDisplay();
            
        } catch (error) {
            console.error('Error starting listening:', error);
            throw error;
        }
    }
    
    async stopListening() {
        try {
            // Stop recording via preload API (this sends IPC message)
            window.api?.stopRecording?.();
            
            this.isListening = false;
            this.updateVoiceStatus('Processing...', 'processing');
            this.wsClient.stopListening();
            
        } catch (error) {
            console.error('Error stopping listening:', error);
            this.updateVoiceStatus('Ready', 'idle');
            throw error;
        }
    }
    
    handleSpeechResult(result) {
        if (result.isFinal) {
            this.currentTranscription = result.transcript;
            this.interimTranscription = '';
        } else {
            this.interimTranscription = result.transcript;
        }
        
        this.updateTranscriptionDisplay();
        
        // If final result, stop listening and process
        if (result.isFinal) {
            this.updateVoiceStatus('Processing...', 'processing');
            
            // Send to backend for processing
            this.wsClient.sendTextMessage(this.currentTranscription);
        }
    }
    
    updateTranscription(data) {
        if (data.isFinal) {
            this.currentTranscription = data.text;
            this.interimTranscription = '';
        } else {
            this.interimTranscription = data.text;
        }
        
        this.updateTranscriptionDisplay();
    }
    
    updateTranscriptionDisplay() {
        const display = this.elements.transcriptionDisplay;
        if (!display) return;
        
        let content = '';
        
        if (this.currentTranscription) {
            content += `<span class="final-text">${this.escapeHtml(this.currentTranscription)}</span>`;
        }
        
        if (this.interimTranscription) {
            if (content) content += ' ';
            content += `<span class="interim-text">${this.escapeHtml(this.interimTranscription)}</span>`;
        }
        
        if (!content) {
            content = '<div class="placeholder-text">Your speech will appear here...</div>';
        }
        
        display.innerHTML = content;
    }
    
    displayAssistantResponse(text) {
        const display = this.elements.responseDisplay;
        if (!display) return;
        
        // Clear placeholder
        display.innerHTML = '';
        
        // Add typing animation effect
        this.typeText(display, text);
        
        // Update voice status
        this.updateVoiceStatus('Ready', 'idle');
    }
    
    typeText(element, text, speed = 30) {
        element.innerHTML = '';
        let i = 0;
        
        const typeInterval = setInterval(() => {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
            } else {
                clearInterval(typeInterval);
                element.classList.remove('typing-animation');
            }
        }, speed);
        
        element.classList.add('typing-animation');
    }
    
    updateVoiceStatus(text, state = 'idle') {
        const statusElement = this.elements.voiceStatus;
        const micButton = this.elements.micButton;
        
        if (statusElement) {
            statusElement.textContent = text;
        }
        
        if (micButton) {
            // Remove all state classes
            micButton.classList.remove('listening', 'processing', 'idle');
            // Add current state class
            micButton.classList.add(state);
        }
    }
    
    updateRecordingStatus(status) {
        if (status.isRecording) {
            this.updateVoiceStatus('Listening...', 'listening');
        } else {
            this.updateVoiceStatus('Ready', 'idle');
        }
    }
    
    updateBackendStatus(status) {
        const statusElement = this.elements.backendStatus;
        if (!statusElement) return;
        
        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('.status-text');
        
        // Remove all status classes
        dot.classList.remove('connected', 'disconnected', 'connecting');
        
        switch (status) {
            case 'connected':
                dot.classList.add('connected');
                text.textContent = 'Connected';
                break;
            case 'connecting':
                dot.classList.add('disconnected'); // Use disconnected style for connecting
                text.textContent = 'Connecting...';
                break;
            case 'disconnected':
            case 'error':
            case 'failed':
            default:
                dot.classList.add('disconnected');
                text.textContent = 'Disconnected';
                break;
        }
    }
    
    updateAuthStatus(isAuthenticated) {
        this.isAuthenticated = isAuthenticated;
        
        const statusElement = this.elements.authStatus;
        if (statusElement) {
            const dot = statusElement.querySelector('.status-dot');
            const text = statusElement.querySelector('.status-text');
            
            dot.classList.remove('authorized', 'unauthorized');
            
            if (isAuthenticated) {
                dot.classList.add('authorized');
                text.textContent = 'Authenticated';
            } else {
                dot.classList.add('unauthorized');
                text.textContent = 'Not Authenticated';
            }
        }
        
        // Show/hide appropriate sections
        if (this.elements.authSection && this.elements.voiceSection) {
            if (isAuthenticated) {
                this.elements.authSection.style.display = 'none';
                this.elements.voiceSection.style.display = 'block';
            } else {
                this.elements.authSection.style.display = 'block';
                this.elements.voiceSection.style.display = 'none';
            }
        }
    }
    
    showOAuthCallback(show) {
        if (this.elements.oauthCallback) {
            this.elements.oauthCallback.style.display = show ? 'flex' : 'none';
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const container = this.elements.notificationContainer;
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);
    }
    
    handleKeydown(event) {
        // Handle hotkey activation (this will be triggered by main process)
        if (event.key === 'F2' || (event.ctrlKey && event.shiftKey && event.key === 'V')) {
            event.preventDefault();
            this.toggleListening();
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public methods for external access
    getConnectionStatus() {
        return {
            backend: this.wsClient?.getConnectionStatus() || 'disconnected',
            authenticated: this.isAuthenticated,
            listening: this.isListening
        };
    }
    
    async synthesizeSpeech(text) {
        try {
            await window.api?.synthesizeSpeech?.(text);
        } catch (error) {
            console.error('Error synthesizing speech:', error);
        }
    }
}

// Initialize the renderer when the script loads
const voiceAssistant = new VoiceAssistantRenderer();

// Handle Google Sign-In button click
const signInButton = document.getElementById('google-signin-button');
if (signInButton) {
  signInButton.addEventListener('click', async () => {
    console.log('Sign-in button clicked');
    // Disable button to prevent multiple clicks
    signInButton.disabled = true;
    document.getElementById('auth-status').textContent = 'Starting authentication...';
    try {
      // This now triggers the BrowserView flow in main.js
      await window.api.startGoogleAuth(); 
      // The main process will send 'auth-flow-complete' when done.
      // UI updates will be handled by the onAuthFlowComplete listener.
    } catch (error) {
      console.error('Error starting Google Auth:', error);
      document.getElementById('auth-status').textContent = `Error: ${error.message}`;
      signInButton.disabled = false; // Re-enable button on error
    }
  });
}

// Listener for when the auth flow (BrowserView) is complete
window.api.onAuthFlowComplete((result) => {
  console.log('Auth Flow Complete in Renderer:', result);
  const authStatusEl = document.getElementById('auth-status');
  const signInContainer = document.getElementById('signin-button-container');
  const logoutButton = document.getElementById('logout-button'); // Assuming you add a logout button

  if (result.success) {
    authStatusEl.textContent = 'Authenticated!';
    if (signInContainer) signInContainer.style.display = 'none';
    if (logoutButton) logoutButton.style.display = 'block'; // Show logout button
    // Potentially fetch user info or update other parts of the UI
  } else {
    authStatusEl.textContent = `Authentication Failed: ${result.error}`;
    if (signInContainer) signInContainer.style.display = 'block';
    if (logoutButton) logoutButton.style.display = 'none';
    if (signInButton) signInButton.disabled = false; // Re-enable sign-in button if it exists and failed
  }
});

// Add Logout Button Functionality
const logoutButton = document.getElementById('logout-button');
if (logoutButton) {
  logoutButton.addEventListener('click', async () => {
    console.log('Logout button clicked');
    try {
      const result = await window.api.logoutGoogle();
      if (result.success) {
        console.log('Logout successful via IPC.');
        // UI changes will be handled by onLogoutComplete and onShowAuthScreen
      } else {
        console.error('Logout failed via IPC:', result.error);
        document.getElementById('auth-status').textContent = `Logout Failed: ${result.error}`;
      }
    } catch (error) {
      console.error('Error during logout:', error);
      document.getElementById('auth-status').textContent = `Logout Error: ${error.message}`;
    }
  });
}

// Handle logout completion
window.api.onLogoutComplete(() => {
  console.log('Logout complete in renderer.');
  document.getElementById('auth-status').textContent = 'Logged out.';
  // Further UI updates might be triggered by onShowAuthScreen
});

// Handle instruction to show authentication screen (e.g., after logout)
window.api.onShowAuthScreen(() => {
  console.log('Show auth screen requested.');
  const authStatusEl = document.getElementById('auth-status');
  const signInContainer = document.getElementById('signin-button-container');
  const logoutButton = document.getElementById('logout-button');
  
  if (authStatusEl) authStatusEl.textContent = 'Please sign in.';
  if (signInContainer) signInContainer.style.display = 'block';
  if (signInButton) signInButton.disabled = false; // Ensure sign-in button is enabled
  if (logoutButton) logoutButton.style.display = 'none';
  
  // Add any other UI changes needed to revert to a pre-authenticated state
  // For example, clear user-specific data displays
});

// Initial check or setup if needed - for example, to set initial UI state
// This might involve checking auth status on load if you have such an IPC call
// window.api.getAuthStatus().then(status => { ... });

window.voiceAssistant = voiceAssistant;