/**
 * Application configuration settings
 */
const Store = require('electron-store');

// Create a store with defaults
const store = new Store({
  defaults: {
    // General app settings
    app: {
      name: 'Voice Assistant',
      version: '1.0.0',
      logLevel: 'INFO',  // ERROR, WARN, INFO, DEBUG
    },
    
    // User preferences
    user: {
      activationHotkey: 'CommandOrControl+Shift+X',
      voiceType: 'female',  // male, female
      theme: 'dark',        // dark, light
    },
    
    // Voice processing settings
    voice: {
      recordingTimeoutMs: 10000,  // 10 seconds
      quietThreshold: 0.05,       // Used for auto-stopping recording
      useStreamingRecognition: true,
    },
    
    // UI settings
    ui: {
      windowWidth: 450,
      windowHeight: 280,  // Reduced height since we removed manual controls
      alwaysOnTop: true,
      autoHideAfterResponse: true,
      autoHideDelayMs: 5000,  // 5 seconds
    },
    
    // LLM settings
    llm: {
      provider: 'openai',  // openai, google, anthropic
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      maxTokens: 200,
    },
  }
});

/**
 * Get a specific configuration value
 * @param {string} key - The configuration key (e.g., 'app.logLevel', 'voice.recordingTimeoutMs')
 * @param {*} defaultValue - Default value if the key doesn't exist
 * @returns {*} The configuration value
 */
function get(key, defaultValue) {
  return store.get(key, defaultValue);
}

/**
 * Set a specific configuration value
 * @param {string} key - The configuration key
 * @param {*} value - The value to set
 */
function set(key, value) {
  store.set(key, value);
}

/**
 * Get the entire configuration
 * @returns {Object} The full configuration object
 */
function getConfig() {
  return store.store;
}

/**
 * Reset configuration to defaults
 */
function resetToDefaults() {
  store.clear();
}

module.exports = {
  getConfig,
  get,
  set,
  resetToDefaults
}; 