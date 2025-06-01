/**
 * Simple logging utility for the Voice Assistant
 * EPIPE Error Prevention: All console and file operations disabled
 */

const logLevels = {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  DEBUG: 3
};

// Minimal no-op logger to prevent EPIPE errors
function setLogLevel(level) {
  // Silently accept any log level without operations
}

function error(message, error) {
  // Silently handle error logging
}

function warn(message) {
  // Silently handle warning logging
}

function info(message) {
  // Silently handle info logging
}

function debug(message) {
  // Silently handle debug logging
}

module.exports = {
  setLogLevel,
  error,
  warn,
  info,
  debug,
  logLevels
};