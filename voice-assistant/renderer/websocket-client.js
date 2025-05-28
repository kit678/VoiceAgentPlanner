class PipecatWebSocketClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.eventHandlers = {};
        
        // Bind methods to preserve 'this' context
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.send = this.send.bind(this);
        this.on = this.on.bind(this);
    }
    
    connect(url = 'ws://localhost:8765') {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }
        
        console.log(`Connecting to Pipecat WebSocket: ${url}`);
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
            console.log('Connected to Pipecat backend');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this.emit('connected');
            
            // Request initial status
            this.send('get_status');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('Received message:', message);
                this.handleMessage(message);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            this.isConnected = false;
            this.emit('disconnected');
            
            // Attempt to reconnect if not manually closed
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.attemptReconnect();
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', error);
        };
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Manual disconnect');
            this.ws = null;
        }
        this.isConnected = false;
    }
    
    attemptReconnect() {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);
        
        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    }
    
    send(type, data = {}) {
        if (!this.isConnected || !this.ws) {
            console.warn('WebSocket not connected, cannot send message');
            return false;
        }
        
        const message = {
            type: type,
            data: data,
            timestamp: Date.now()
        };
        
        try {
            this.ws.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
    
    handleMessage(message) {
        const { type, data } = message;
        
        switch (type) {
            case 'status':
                this.emit('status', data);
                break;
            case 'transcription':
                this.emit('transcription', data);
                break;
            case 'response_text':
                this.emit('response_text', data);
                break;
            case 'audio_started':
                this.emit('audio_started', data);
                break;
            case 'audio_stopped':
                this.emit('audio_stopped', data);
                break;
            case 'error':
                this.emit('error', data);
                break;
            default:
                console.warn('Unknown message type:', type);
        }
    }
    
    // Event system
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    off(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
        }
    }
    
    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    // Convenience methods for common actions
    startListening() {
        return this.send('start_listening');
    }
    
    stopListening() {
        return this.send('stop_listening');
    }
    
    sendText(text) {
        return this.send('send_text', { text });
    }
    
    getStatus() {
        return this.send('get_status');
    }
}

// Create global instance
window.pipecatClient = new PipecatWebSocketClient(); 