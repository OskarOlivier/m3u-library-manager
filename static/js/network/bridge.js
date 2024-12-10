// static/js/network/bridge.js

/**
 * Handles communication between Qt WebChannel and d3 network visualization.
 */
export class QtBridge {
    constructor() {
        this.bridge = null;
        this.events = null;
        this.isInitialized = false;
        this._initializationPromise = null;
        
        // Override console methods to forward to Python
        this._setupConsoleForwarding();
    }

    _setupConsoleForwarding() {
        // Store original console methods
        const originalConsole = {
            log: console.log,
            warn: console.warn,
            error: console.error,
            debug: console.debug
        };

        // Override console methods
        console.log = (...args) => this._forwardLog('log', ...args);
        console.warn = (...args) => this._forwardLog('warn', ...args);
        console.error = (...args) => this._forwardLog('error', ...args);
        console.debug = (...args) => this._forwardLog('debug', ...args);
    }

    _forwardLog(level, ...args) {
        const message = args.map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');

        if (this.bridge && this.isInitialized) {
            try {
                this.bridge.debugLog(`[${level.toUpperCase()}] ${message}`);
            } catch (e) {
                // Fallback if bridge fails
                this._fallbackLog(level, message);
            }
        } else {
            // Queue logs until bridge is ready
            this._fallbackLog(level, message);
        }
    }

    _fallbackLog(level, message) {
        // Keep basic logging functionality even if bridge fails
        const timestamp = new Date().toISOString();
        print(`${timestamp} [${level.toUpperCase()}] ${message}`);
    }

    async initialize() {
        if (this._initializationPromise) {
            return this._initializationPromise;
        }

        this._initializationPromise = new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Bridge initialization timeout'));
            }, 5000);

            const checkBridge = () => {
                if (window.bridge && window.events) {
                    clearTimeout(timeout);
                    this.bridge = window.bridge;
                    this.events = window.events;
                    this.isInitialized = true;
                    console.log("Bridge initialized successfully");
                    resolve();
                } else if (window.qt && qt.webChannelTransport) {
                    new QWebChannel(qt.webChannelTransport, channel => {
                        if (channel.objects.networkHandler && channel.objects.networkEvents) {
                            clearTimeout(timeout);
                            this.bridge = channel.objects.networkHandler;
                            this.events = channel.objects.networkEvents;
                            window.bridge = this.bridge;
                            window.events = this.events;
                            this.isInitialized = true;
                            console.log("Bridge initialized via WebChannel");
                            resolve();
                        } else {
                            reject(new Error('Network handlers not found in channel'));
                        }
                    });
                } else {
                    setTimeout(checkBridge, 100);
                }
            };

            checkBridge();
        });

        return this._initializationPromise;
    }
    
    /**
     * Emit node selection event.
     * @param {string} nodeId - Selected node ID
     */
    nodeSelected(nodeId) {
        if (!this.isInitialized || !this.events) {
            console.warn('Bridge not initialized - nodeSelected event dropped');
            return;
        }
        try {
            this.events.nodeSelected(nodeId);
        } catch (error) {
            console.error('Error in nodeSelected:', error);
            this.handleError(error);
        }
    }

    /**
     * Emit node hover event.
     * @param {string} nodeId - Hovered node ID
     */
    nodeHovered(nodeId) {
        if (!this.isInitialized || !this.events) return;
        try {
            this.events.nodeHovered(nodeId);
        } catch (error) {
            console.error('Error in nodeHovered:', error);
            this.handleError(error);
        }
    }

    /**
     * Emit zoom change event.
     * @param {number} scale - Current zoom scale
     */
     Changed(scale) {
        if (!this.isInitialized || !this.events) return;
        try {
            this.events.zoomChanged(scale);
        } catch (error) {
            console.error('Error in zoomChanged:', error);
            this.handleError(error);
        }
    }

    /**
     * Emit stabilization progress event.
     * @param {number} progress - Progress percentage (0-100)
     */
    stabilizationProgress(progress) {
        if (!this.isInitialized || !this.events) return;
        try {
            this.events.stabilizationProgress(progress);
        } catch (error) {
            console.error('Error in stabilizationProgress:', error);
            this.handleError(error);
        }
    }

    /**
     * Emit stabilization complete event.
     */
    stabilizationComplete() {
        if (!this.isInitialized || !this.events) return;
        try {
            this.events.stabilizationComplete();
        } catch (error) {
            console.error('Error in stabilizationComplete:', error);
            this.handleError(error);
        }
    }

    /**
     * Handle and forward errors to Qt.
     * @param {Error|string} error - Error to handle
     */
    handleError(error) {
        if (!this.isInitialized || !this.events) {
            console.error('Bridge not initialized - error dropped:', error);
            return;
        }

        const errorData = {
            message: error.message || String(error),
            stack: error.stack,
            time: new Date().toISOString()
        };
        
        try {
            this.events.handleError(JSON.stringify(errorData));
        } catch (e) {
            console.error('Failed to send error through bridge:', e);
            console.error('Original error:', errorData);
        }
    }
    
    nodeSelected(nodeId) {
        if (!this.isInitialized || !this.events) {
            console.warn('Bridge not initialized - nodeSelected event dropped');
            return;
        }
        try {
            console.log('Node selected:', nodeId);
            this.events.nodeSelected(nodeId);

            // Update visualization if available
            if (window.networkManager && window.networkManager.network) {
                window.networkManager.network.updateNodeSelection(nodeId);
            }
        } catch (error) {
            console.error('Error in nodeSelected:', error);
            this.handleError(error);
        }
    }

    nodeHovered(nodeId) {
        if (!this.isInitialized || !this.events) return;
        try {
            console.log('Node hovered:', nodeId);
            this.events.nodeHovered(nodeId);

            // Update visualization if available
            if (window.networkManager && window.networkManager.network) {
                window.networkManager.network.updateNodeHover(nodeId);
            }
        } catch (error) {
            console.error('Error in nodeHovered:', error);
            this.handleError(error);
        }
    }

    /**
     * Clean up bridge resources.
     */
    cleanup() {
        this.bridge = null;
        this.events = null;
        this.isInitialized = false;
        this._initializationPromise = null;
    }
}