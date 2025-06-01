/**
 * Utility for managing global hotkey registration in Electron
 * EPIPE Error Prevention: All logging operations disabled
 */
const { globalShortcut } = require('electron');
const config = require('../../config/app-config');
// const logger = require('./logger'); // Disabled to prevent EPIPE errors

// No-op logging to prevent EPIPE errors
const safeLog = () => {};
const safeError = () => {};

/**
 * Register the activation hotkey for the voice assistant
 * @param {Function} callback Function to call when hotkey is pressed
 * @returns {boolean} Success status
 */
function registerActivationHotkey(callback) {
  try {
    const hotkey = config.get('user.activationHotkey');
    // Wrap the original callback without logging to prevent EPIPE
    const wrappedCallback = () => {
      safeLog(`[HotkeyManager] Hotkey "${hotkey}" pressed. Executing callback.`);
      callback(); // Execute the original callback (e.g., toggleWindow)
    };
    globalShortcut.register(hotkey, wrappedCallback); // Pass the wrapped callback
    safeLog(`Registered activation hotkey: ${hotkey}`);
    return true;
  } catch (error) {
    safeError('Failed to register activation hotkey', error);
    // If the configured hotkey failed, we will not attempt a fallback to Alt+Space
    // as Alt+Space is problematic on Windows.
    // The function will return false, and an error will be logged.
    return false;
  }
}

/**
 * Unregister all global shortcuts
 */
function unregisterAll() {
  globalShortcut.unregisterAll();
  safeLog('Unregistered all hotkeys');
}

/**
 * Get the current activation hotkey
 * @returns {string} Current activation hotkey
 */
function getActivationHotkey() {
  return config.get('user.activationHotkey');
}

/**
 * Set a new activation hotkey
 * @param {string} hotkey New hotkey to use (e.g., 'Alt+Space', 'CommandOrControl+Shift+V')
 * @param {Function} callback Function to call when hotkey is pressed
 * @returns {boolean} Success status
 */
function setActivationHotkey(hotkey, callback) {
  try {
    // Unregister the existing hotkey
    unregisterAll();
    
    // Try to register the new hotkey
    globalShortcut.register(hotkey, callback);
    
    // If successful, save the new hotkey
    config.set('user.activationHotkey', hotkey);
    safeLog(`Updated activation hotkey to: ${hotkey}`);
    return true;
  } catch (error) {
    safeError(`Failed to set new hotkey ${hotkey}`, error);
    
    // Reregister the previous hotkey
    const previousHotkey = config.get('user.activationHotkey');
    try {
      globalShortcut.register(previousHotkey, callback);
    } catch (reregisterError) {
      safeError('Failed to reregister previous hotkey', reregisterError);
    }
    
    return false;
  }
}

module.exports = {
  registerActivationHotkey,
  unregisterAll,
  getActivationHotkey,
  setActivationHotkey
}; 