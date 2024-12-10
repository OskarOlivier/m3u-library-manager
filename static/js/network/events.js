// static/js/network/events.js

export class NetworkEvents {
    constructor(network, bridge) {
        this.network = network;
        this.bridge = bridge;
        this._lastHoveredNode = null;
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Node click handler
        this.network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                this.bridge.nodeSelected(nodeId);
            }
        });

        // Node hover handling with physics toggling
        this.network.on('hoverNode', (params) => {
            this.network.disablePhysics();  // Freeze the layout
            this._handleNodeHover(params.node);
            this.bridge.nodeHovered(params.node);
        });

        this.network.on('leaveNode', () => {
            this._handleNodeLeave();
            this.network.enablePhysics();  // Resume physics
        });

        // Network state events
        this.network.on('zoom', (params) => {
            this.bridge.zoomChanged(params.scale);
        });

        this.network.on('stabilizationProgress', (params) => {
            const progress = Math.round(params.iterations / params.total * 100);
            this.bridge.stabilizationProgress(progress);
        });

        this.network.on('stabilizationIterationsDone', () => {
            this.bridge.stabilizationComplete();
        });

        // Error handling
        window.onerror = (message, source, lineno, colno, error) => {
            if (error) {
                this.bridge.handleError({
                    message: error.message,
                    stack: error.stack,
                    source: source,
                    line: lineno
                });
            }
            return false;
        };
    }

    _handleNodeHover(nodeId) {
        if (this._lastHoveredNode === nodeId) return;
        this._lastHoveredNode = nodeId;

        // Get connected elements
        const connectedNodes = this.network.getConnectedNodes(nodeId);
        const connectedEdges = this.network.getConnectedEdges(nodeId);

        // Highlight connected elements
        this._highlightNode(nodeId, true);
        connectedNodes.forEach(id => this._highlightNode(id));
        connectedEdges.forEach(id => this._highlightEdge(id));
    }

    _handleNodeLeave() {
        if (!this._lastHoveredNode) return;

        // Reset all elements to default state
        this.network.body.data.nodes.forEach((node) => {
            this._resetNode(node.id);
        });

        this.network.body.data.edges.forEach((edge) => {
            this._resetEdge(edge.id);
        });

        this._lastHoveredNode = null;
    }

    _highlightNode(nodeId, isHovered = false) {
        const node = this.network.body.data.nodes.get(nodeId);
        if (node) {
            this.network.body.data.nodes.update({
                id: nodeId,
                borderWidth: isHovered ? 3 : 2,
                borderColor: '#FFFFFF',
                font: {
                    size: isHovered ? 16 : 14,
                    color: '#FFFFFF'
                }
            });
        }
    }

    _highlightEdge(edgeId) {
        const edge = this.network.body.data.edges.get(edgeId);
        if (edge) {
            this.network.body.data.edges.update({
                id: edgeId,
                color: {
                    color: '#FFFFFF',
                    opacity: 1
                }
            });
        }
    }

    _resetNode(nodeId) {
        const node = this.network.body.data.nodes.get(nodeId);
        if (node) {
            this.network.body.data.nodes.update({
                id: nodeId,
                borderWidth: 2,
                borderColor: '#2D2D2D',
                font: {
                    size: 14,
                    color: '#FFFFFF'
                }
            });
        }
    }

    _resetEdge(edgeId) {
        const edge = this.network.body.data.edges.get(edgeId);
        if (edge) {
            this.network.body.data.edges.update({
                id: edgeId,
                color: {
                    inherit: 'both',
                    opacity: 0.8
                }
            });
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
}