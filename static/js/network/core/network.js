// static/js/network/core/network.js

import { NetworkRenderer } from './renderer.js';
import { NetworkSimulation } from './simulation.js';
import { EventManager } from './events.js';
import { DataProcessor } from './data-processor.js';

export class NetworkVisualization {
    constructor(container, options = {}) {
        this._validateEnvironment();
        
        // State initialization
        this.container = d3.select(container);
        this.options = options;
        this.width = this.container.node().offsetWidth;
        this.height = this.container.node().offsetHeight;
        this.isInitialized = false;

        // Components
        this.events = new EventManager();
        this.renderer = new NetworkRenderer(this.container, this.width, this.height);
        this.simulation = new NetworkSimulation(this.width, this.height);
        this.dataProcessor = new DataProcessor();

        // Selection state
        this.selectedNodes = new Set();
        this.selectionColor = null;
        this.originalColors = new Map();
        this.originalEdgeColors = new Map();
        this.transitionQueue = [];
        this.isTransitioning = false;

        // Initialize immediately
        this._initialize();
    }

    _validateEnvironment() {
        if (!window.d3) {
            console.error('D3 not loaded');
            throw new Error('D3 not available');
        }
    }
    
    async _initialize() {
        try {
            console.log('Starting network visualization initialization...');
            
            // Initialize renderer first
            await this.renderer.initialize();
            console.log('Renderer initialized successfully');

            // Initialize simulation with tick callback
            this.simulation = new NetworkSimulation(this.width, this.height);
            this.simulation.onTick(() => {
                if (this.renderer) {
                    this.renderer.updatePositions();
                }
            });

            // Connect simulation events
            this.simulation.onStabilizationProgress(progress => {
                this.events.emit('stabilizationProgress', progress);
            });

            this.simulation.onStabilizationComplete(() => {
                this.events.emit('stabilizationComplete');
            });

            // Connect events after simulation is ready
            this._connectEvents();
            
            this.isInitialized = true;           
        } catch (error) {
            console.error('Failed to initialize visualization:', error);
            throw error;
        }
    }

    _connectEvents() {
        // Node selection events
        this.network?.on('nodeSelected', nodeId => {
            console.log('Node selected:', nodeId);
            this.events.emit('nodeSelected', { nodeId });
        });

        // Node hover events with selection-aware behavior
        this.network?.on('nodeHovered', nodeId => {
            console.log('Node hovered:', nodeId);
            this.events.emit('nodeHovered', { nodeId });
        });

        // Layout events
        this.simulation?.on('stabilizationProgress', progress => {
            console.log(`Layout stabilization progress: ${progress}%`);
            this.events.emit('stabilizationProgress', progress);
        });

        this.simulation?.on('stabilizationComplete', () => {
            console.log('Layout stabilization complete');
            this.events.emit('stabilizationComplete');
        });
    }

    _initializeInteractions() {
        // Set up container interactions
        this.container.on('click', (event) => {
            if (event.target === this.container.node()) {
                this._handleBackgroundClick();
            }
        });
    }


    _handleNodeClick(node) {
        if (!node) return;

        if (this.selectedNodes.has(node.id)) {
            // Unselect node
            this._unselectNode(node);
        } else {
            // Select node
            this._selectNode(node);
        }
    }

    _selectNode(node) {
        // Store original color if first time selecting
        if (!this.originalColors.has(node.id)) {
            this.originalColors.set(node.id, node.color);
        }

        // First selected node defines selection color
        if (this.selectedNodes.size === 0) {
            this.selectionColor = node.color;
        }

        // Queue color transition
        this._queueTransition({
            type: 'select',
            nodeId: node.id,
            targetColor: this.selectionColor,
            connectedNodes: this._getConnectedNodes(node)
        });

        // Update selection state
        this.selectedNodes.add(node.id);

        // Emit event
        this.events.emit('nodeSelected', { nodeId: node.id, selectedNodes: Array.from(this.selectedNodes) });
    }

    _unselectNode(node) {
        // Queue reverse color transition
        this._queueTransition({
            type: 'unselect',
            nodeId: node.id,
            targetColor: this.originalColors.get(node.id),
            connectedNodes: this._getConnectedNodes(node)
        });

        // Update selection state
        this.selectedNodes.delete(node.id);

        // If no nodes remain selected, restore all colors
        if (this.selectedNodes.size === 0) {
            this._restoreAllColors();
        }

        // Emit event
        this.events.emit('nodeUnselected', { nodeId: node.id, selectedNodes: Array.from(this.selectedNodes) });
    }

    _handleNodeHover(node) {
        if (!node) return;

        const connectedNodes = this._getConnectedNodes(node);
        
        // During selection, only highlight unselected connected nodes
        if (this.selectedNodes.size > 0) {
            const unselectedConnections = connectedNodes.filter(n => !this.selectedNodes.has(n.id));
            this.renderer.highlightNodes(unselectedConnections);
        } else {
            // Normal hover behavior
            this.renderer.highlightNodes(connectedNodes);
        }
    }

    _handleNodeLeave() {
        // Restore non-selected nodes to default state
        this.renderer.clearHighlights(Array.from(this.selectedNodes));
    }

    _handleBackgroundClick() {
        if (this.selectedNodes.size > 0) {
            this._restoreAllColors();
        }
    }

    _queueTransition(transition) {
        this.transitionQueue.push(transition);
        if (!this.isTransitioning) {
            this._processTransitionQueue();
        }
    }

    async _processTransitionQueue() {
        if (this.isTransitioning || this.transitionQueue.length === 0) return;

        this.isTransitioning = true;
        const transition = this.transitionQueue.shift();

        try {
            await this.renderer.animateColorTransition(
                transition.nodeId,
                transition.targetColor,
                transition.connectedNodes,
                transition.type === 'unselect'
            );
        } catch (error) {
            console.error('Transition failed:', error);
        }

        this.isTransitioning = false;
        this._processTransitionQueue();
    }

    _restoreAllColors() {
        // Queue restore transitions for all selected nodes
        for (const nodeId of this.selectedNodes) {
            this._queueTransition({
                type: 'restore',
                nodeId: nodeId,
                targetColor: this.originalColors.get(nodeId),
                connectedNodes: this._getConnectedNodes({ id: nodeId })
            });
        }

        // Clear selection state
        this.selectedNodes.clear();
        this.selectionColor = null;

        // Emit event
        this.events.emit('selectionCleared');
    }

    _getConnectedNodes(node) {
        return this.renderer.getConnectedNodes(node.id);
    }
    
    _handleNodeDrag(type, node) {
        if (type === 'start') {
            this.simulation.fixNode(node);
        } else if (type === 'end') {
            this.simulation.unfixNode(node);
        }
    }

    // Public API methods
    async updateData(nodesData, edgesData) {
        if (!this.isInitialized) {
            console.warn('Network not initialized, initializing now...');
            await this._initialize();
        }

        try {
            console.log('Starting data update with:', {
                nodes: nodesData.length,
                edges: edgesData.length
            });

            // Process data
            const { processedNodes, processedEdges } = this.dataProcessor.processData(nodesData, edgesData);
            console.log('Data processed:', {
                processedNodes: processedNodes.length,
                processedEdges: processedEdges.length
            });

            // Update renderer with new elements
            await this.renderer.updateElements(processedNodes, processedEdges);
            console.log('Renderer updated with new elements');

            // Stop any existing simulation
            this.simulation.stop();
            console.log('Previous simulation stopped');

            // Set new data on simulation
            this.simulation.setData(processedNodes, processedEdges);
            console.log('New data set on simulation');

            // Start simulation
            console.log('Starting force simulation');
            this.simulation.restart();
            
            console.log('Data update complete, simulation running');

        } catch (error) {
            console.error('Error updating data:', error);
            throw error;
        }
    }

    // Event subscription methods
    on(eventName, callback) {
        this.events.on(eventName, callback);
    }

    off(eventName, callback) {
        this.events.off(eventName, callback);
    }

    cleanup() {
        console.log('Starting network cleanup');
        
        try {
            // Stop simulation first
            if (this.simulation) {
                console.log('Stopping simulation');
                this.simulation.stop();
                this.simulation = null;
            }
            
            // Clean up renderer
            if (this.renderer) {
                console.log('Cleaning up renderer');
                this.renderer.cleanup();
                this.renderer = null;
            }
            
            // Clean up events
            if (this.events) {
                console.log('Cleaning up events');
                this.events.cleanup();
                this.events = null;
            }
            
            // Reset state
            this.selectedNodes.clear();
            this.originalColors.clear();
            this.originalEdgeColors.clear();
            this.transitionQueue = [];
            this.isInitialized = false;
            
            console.log('Network cleanup complete');

        } catch (error) {
            console.error('Error during cleanup:', error);
            throw error;
        }
    }
}