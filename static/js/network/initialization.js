// static/js/network/initialization.js

import { NetworkVisualization } from './core/network.js';
import { NetworkLayout } from './core/layouts.js';
import { NetworkTheme } from './core/themes.js';
import { QtBridge } from './bridge.js';

async function waitForContainerSize() {
    const container = document.querySelector('.network-container');
    // Wait for up to 2 seconds checking every 100ms
    for (let i = 0; i < 20; i++) {
        const style = window.getComputedStyle(container);
        const height = container.offsetHeight;
        if (height > 0) {
            console.log(`Container size ready: ${container.offsetWidth}x${height}`);
            return true;
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('Container failed to initialize with proper dimensions');
}

export class NetworkManager {
    constructor() {
        this.network = null;
        this.bridge = null;
        this.container = null;
        this.isInitializing = false;
        this.isInitialized = false;
        this.loadingProgress = 0;
        this.theme = NetworkTheme.defaultTheme;
    }

    async initialize() {
        if (this.isInitializing) {
            console.warn('Network initialization already in progress');
            return;
        }

        if (this.isInitialized) {
            console.warn('Network already initialized');
            return;
        }

        this.isInitializing = true;

        try {
            console.log('Starting network visualization initialization...');
            
            // Wait for container size
            await waitForContainerSize();
            
            // Initialize Qt bridge first
            this.bridge = new QtBridge();
            await this.bridge.initialize();
            this._updateProgress(20);
            
            // Get and verify container
            this.container = document.getElementById('visualization');
            if (!this.container) {
                throw new Error('Visualization container not found');
            }
            this._updateProgress(40);

            // Calculate dimensions
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;

            // Create visualization with optimized configuration
            const layoutConfig = NetworkLayout.getOptimizedConfig({
                nodeCount: 0,
                edgeCount: 0,
                width,
                height
            });

            // Configure visualization options
            const options = {
                layout: layoutConfig,
                theme: this.theme,
                width,
                height,
                animation: {
                    colorFlow: true,
                    duration: 300,
                    staggerDelay: 50
                },
                selection: {
                    preserveOpacity: true,
                    dimOthers: true,
                    colorFlow: true
                },
                edges: {
                    useGradients: true,
                    colorTransitions: true
                }
            };

            console.log('Creating visualization with dimensions:', width, height);
            this.network = new NetworkVisualization(this.container, options);
            this._updateProgress(80);

            // Connect events after network is created
            this._connectEvents();
            
            this.isInitialized = true;
            this.isInitializing = false;
            this._updateProgress(100);
            
            console.log('Network visualization initialization complete');
            
        } catch (error) {
            this.isInitializing = false;
            this.isInitialized = false;
            console.error('Failed to initialize network:', error);
            if (this.bridge) {
                this.bridge.handleError(error);
            }
            await this.cleanup();
            throw error;
        }
    }

    _connectEvents() {
        if (!this.network || !this.bridge) {
            console.warn('Cannot connect events - components not initialized');
            return;
        }

        // Node selection events
        this.network.on('nodeSelected', nodeId => {
            console.log('Node selected:', nodeId);
            this.bridge.nodeSelected(nodeId);
        });

        // Node hover events with selection-aware behavior
        this.network.on('nodeHovered', nodeId => {
            console.log('Node hovered:', nodeId);
            this.bridge.nodeHovered(nodeId);
        });

        // Color flow events
        this.network.on('colorFlowStarted', nodeId => {
            console.log('Color flow started from:', nodeId);
        });

        this.network.on('colorFlowComplete', nodeId => {
            console.log('Color flow complete for:', nodeId);
        });

        // Selection system events
        this.network.on('selectionChanged', selection => {
            console.log('Selection changed:', selection);
        });

        this.network.on('selectionCleared', () => {
            console.log('Selection cleared');
        });

        // Layout events
        this.network.on('stabilizationProgress', progress => {
            this.bridge.stabilizationProgress(progress);
        });

        this.network.on('stabilizationComplete', () => {
            this.bridge.stabilizationComplete();
        });

        // Zoom events
        this.network.on('zoomChanged', scale => {
            this.bridge.zoomChanged(scale);
        });
    }

    _updateProgress(progress) {
        this.loadingProgress = progress;
        if (this.bridge) {
            this.bridge.stabilizationProgress(progress);
        }
    }

    async updateData(nodesData, edgesData) {
        if (!this.isInitialized) {
            console.warn('Cannot update data - network not initialized');
            await this.initialize();
        }

        try {
            // Calculate graph statistics
            const graphStats = {
                nodeCount: nodesData.length,
                edgeCount: edgesData.length,
                width: this.container.clientWidth,
                height: this.container.clientHeight
            };

            console.log('Updating network with:', graphStats);

            // Get optimized layout configuration
            const layoutConfig = NetworkLayout.getOptimizedConfig(graphStats);
            
            // Update network with new data
            await this.network.updateData(nodesData, edgesData, layoutConfig);
            
        } catch (error) {
            console.error('Error updating data:', error);
            if (this.bridge) {
                this.bridge.handleError(error);
            }
            throw error;
        }
    }

    async cleanup() {
        console.log('Starting network cleanup');
        
        try {
            if (this.network) {
                await this.network.cleanup();
                this.network = null;
            }
            
            if (this.bridge) {
                this.bridge.cleanup();
                this.bridge = null;
            }
            
            this.container = null;
            this.isInitialized = false;
            this.isInitializing = false;
            this.loadingProgress = 0;
            
            console.log('Network cleanup complete');
        } catch (error) {
            console.error('Error during cleanup:', error);
            throw error;
        }
    }
}

// Initialize visualization when module is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        window.networkManager = new NetworkManager();
        await window.networkManager.initialize();
    });
} else {
    window.networkManager = new NetworkManager();
    window.networkManager.initialize();
}