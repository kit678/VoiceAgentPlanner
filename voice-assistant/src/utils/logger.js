/**
 * Simple logging utility for the Voice Assistant
 */
const fs = require('fs');
const path = require('path');
const electron = require('electron');

// Use appConfig inside a function to avoid circular dependencies
let appConfig;
const getConfig = () => {
  if (!appConfig) {
    try {
      appConfig = require('../../config/app-config');
    } catch (err) {
      // If app-config is not available yet (initialization), use default settings
      return { get: () => 'INFO' };
    }
  }
  return appConfig;
};

// Determine the app data path
const userDataPath = (electron.app || electron.remote.app).getPath('userData');
const logsPath = path.join(userDataPath, 'logs');

// Ensure logs directory exists
if (!fs.existsSync(logsPath)) {
  fs.mkdirSync(logsPath, { recursive: true });
}

const logLevels = {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  DEBUG: 3
};

// Gets the current log level from config or uses the default
function getCurrentLogLevel() {
  const config = getConfig();
  const configLevel = config.get('app.logLevel');
  return logLevels[configLevel] !== undefined ? logLevels[configLevel] : logLevels.INFO;
}

/**
 * Set the current log level
 * @param {string} level - Log level ('ERROR', 'WARN', 'INFO', 'DEBUG')
 */
function setLogLevel(level) {
  if (logLevels[level] !== undefined) {
    const config = getConfig();
    config.set('app.logLevel', level);
  } else {
    console.warn(`Invalid log level: ${level}. Using default.`);
  }
}

/**
 * Format a log message with timestamp and level
 * @param {string} level - Log level
 * @param {string} message - Log message
 * @returns {string} Formatted log message
 */
function formatLogMessage(level, message) {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${level}] ${message}`;
}

/**
 * Write a log message to file
 * @param {string} formattedMessage - Formatted log message
 */
function writeToLogFile(formattedMessage) {
  const date = new Date().toISOString().split('T')[0];
  const logFile = path.join(logsPath, `voice-assistant-${date}.log`);
  
  fs.appendFileSync(logFile, formattedMessage + '\n');
}

/**
 * Log an error message
 * @param {string} message - Error message
 * @param {Error} [error] - Optional error object
 */
function error(message, error) {
  if (getCurrentLogLevel() >= logLevels.ERROR) {
    const errorMessage = error ? `${message}: ${error.message}\n${error.stack}` : message;
    const formattedMessage = formatLogMessage('ERROR', errorMessage);
    
    console.error(formattedMessage);
    writeToLogFile(formattedMessage);
  }
}

/**
 * Log a warning message
 * @param {string} message - Warning message
 */
function warn(message) {
  if (getCurrentLogLevel() >= logLevels.WARN) {
    const formattedMessage = formatLogMessage('WARN', message);
    
    console.warn(formattedMessage);
    writeToLogFile(formattedMessage);
  }
}

/**
 * Log an info message
 * @param {string} message - Info message
 */
function info(message) {
  if (getCurrentLogLevel() >= logLevels.INFO) {
    const formattedMessage = formatLogMessage('INFO', message);
    
    console.info(formattedMessage);
    writeToLogFile(formattedMessage);
  }
}

/**
 * Log a debug message
 * @param {string} message - Debug message
 */
function debug(message) {
  if (getCurrentLogLevel() >= logLevels.DEBUG) {
    const formattedMessage = formatLogMessage('DEBUG', message);
    
    console.debug(formattedMessage);
    writeToLogFile(formattedMessage);
  }
}

module.exports = {
  setLogLevel,
  error,
  warn,
  info,
  debug,
  logLevels
}; 