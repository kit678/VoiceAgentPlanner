/**
 * WebSocket Client for Voice Assistant
 * Handles communication with Pipecat backend
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.messageQueue = [];
        
        // Event callbacks
        this.onConnectionChange = null;
        this.onTranscriptionUpdate = null;
        this.onResponseReceived = null;
        this.onError = null;
        
        // Backend configuration
        this.backendUrl = 'ws://localhost:8765'; // Default Pipecat WebSocket port
        
        this.init();
    }
    
    init() {
        this.connect();
    }
    
    connect() {
        try {
            console.log('Attempting to connect to backend:', this.backendUrl);
            this.updateConnectionStatus('connecting');
            
            this.ws = new WebSocket(this.backendUrl);
            
            this.ws.onopen = this.handleOpen.bind(this);
            this.ws.onmessage = this.handleMessage.bind(this);
            this.ws.onclose = this.handleClose.bind(this);
            this.ws.onerror = this.handleError.bind(this);
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus('error');
            this.scheduleReconnect();
        }
    }
    
    handleOpen(event) {
        console.log('WebSocket connected successfully');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.updateConnectionStatus('connected');
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Send queued messages
        this.flushMessageQueue();
        
        // Send initial configuration
        // this.sendMessage({
        //     type: 'config',
        //     data: {
        //         audio_format: 'webm',
        //         sample_rate: 16000,
        //         channels: 1
        //     }
        // });
    }
    
    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('Received message:', message);
            
            switch (message.type) {
                case 'transcription':
                    this.handleTranscription(message.data);
                    break;
                    
                case 'response':
                    this.handleResponse(message.data);
                    break;
                    
                case 'audio_response':
                    this.handleAudioResponse(message.data);
                    break;
                    
                case 'status':
                    this.handleStatusUpdate(message.data);
                    break;
                    
                case 'error':
                    this.handleBackendError(message.data);
                    break;
                    
                case 'pong':
                    this.handlePong();
                    break;
                    
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    handleClose(event) {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        this.updateConnectionStatus('disconnected');
        
        // Attempt to reconnect unless it was a clean close
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }
    
    handleError(event) {
        console.error('WebSocket error:', event);
        this.updateConnectionStatus('error');
        
        if (this.onError) {
            this.onError('WebSocket connection error');
        }
    }
    
    handleTranscription(data) {
        if (this.onTranscriptionUpdate) {
            this.onTranscriptionUpdate({
                text: data.text,
                isFinal: data.is_final || false,
                confidence: data.confidence || 0
            });
        }
    }
    
    handleResponse(data) {
        if (this.onResponseReceived) {
            this.onResponseReceived({
                text: data.text,
                type: data.type || 'text',
                metadata: data.metadata || {}
            });
        }
    }
    
    handleAudioResponse(data) {
        // Handle TTS audio response
        if (data.audio_data) {
            this.playAudioResponse(data.audio_data);
        }
    }
    
    handleStatusUpdate(data) {
        console.log('Backend status update:', data);
        // Handle backend status updates (processing, idle, etc.)
    }
    
    handleBackendError(data) {
        console.error('Backend error:', data);
        if (this.onError) {
            this.onError(data.message || 'Backend error occurred');
        }
    }
    
    handlePong() {
        // Clear heartbeat timeout
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.sendMessage({ type: 'ping' });
                
                // Set timeout for pong response
                this.heartbeatTimeout = setTimeout(() => {
                    console.log('Heartbeat timeout - connection may be lost');
                    this.ws.close();
                }, 5000);
            }
        }, 30000); // Send ping every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);
        
        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
    }
    
    sendMessage(message) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Error sending message:', error);
                return false;
            }
        } else {
            // Queue message for later
            this.messageQueue.push(message);
            console.log('Message queued (not connected):', message.type);
            return false;
        }
    }
    
    flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.sendMessage(message);
        }
    }
    
    sendAudioData(audioBlob) {
        if (!this.isConnected) {
            console.warn('Cannot send audio data - not connected');
            return false;
        }
        
        // Convert blob to base64 for transmission
        const reader = new FileReader();
        reader.onload = () => {
            const base64Data = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
            this.sendMessage({
                type: 'audio_data',
                data: {
                    audio: base64Data,
                    format: 'webm',
                    timestamp: Date.now()
                }
            });
        };
        reader.readAsDataURL(audioBlob);
        return true;
    }
    
    sendTextMessage(text) {
        return this.sendMessage({
            type: 'text_input',
            data: {
                text: text,
                timestamp: Date.now()
            }
        });
    }
    
    startListening() {
        return this.sendMessage({
            type: 'start_listening',
            data: {
                timestamp: Date.now()
            }
        });
    }
    
    stopListening() {
        return this.sendMessage({
            type: 'stop_listening',
            data: {
                timestamp: Date.now()
            }
        });
    }
    
    playAudioResponse(audioData) {
        try {
            // Decode base64 audio data and play it
            const audioBlob = this.base64ToBlob(audioData, 'audio/wav');
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };
            
            audio.play().catch(error => {
                console.error('Error playing audio response:', error);
            });
        } catch (error) {
            console.error('Error processing audio response:', error);
        }
    }
    
    base64ToBlob(base64Data, contentType) {
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        
        const byteArray = new Uint8Array(byteNumbers);
        return new Blob([byteArray], { type: contentType });
    }
    
    updateConnectionStatus(status) {
        if (this.onConnectionChange) {
            this.onConnectionChange(status);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.stopHeartbeat();
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
    }
    
    // Event listener setters
    setConnectionChangeCallback(callback) {
        this.onConnectionChange = callback;
    }
    
    setTranscriptionUpdateCallback(callback) {
        this.onTranscriptionUpdate = callback;
    }
    
    setResponseReceivedCallback(callback) {
        this.onResponseReceived = callback;
    }
    
    setErrorCallback(callback) {
        this.onError = callback;
    }
    
    // Utility methods
    getConnectionStatus() {
        if (!this.ws) return 'disconnected';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'connected';
            case WebSocket.CLOSING:
                return 'disconnecting';
            case WebSocket.CLOSED:
                return 'disconnected';
            default:
                return 'unknown';
        }
    }
    
    isReady() {
        return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Export for use in renderer.js
window.WebSocketClient = WebSocketClient;