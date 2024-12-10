// static/js/network/core/renderer.js

export class NetworkRenderer {
    constructor(container, width, height) {
        this.container = container;
        this.width = width;
        this.height = height;
        
        // Elements
        this.svg = null;
        this.mainGroup = null;
        this.nodeGroup = null;
        this.edgeGroup = null;
        this.nodeElements = null;
        this.edgeElements = null;
        
        // State
        this.transform = null;
        this.highlightedNodes = new Set();
        this.selectedNodes = new Set();
        this.colorFlowTransitions = new Map();
        
        // Event callbacks
        this.callbacks = {
            nodeClick: null,
            nodeHover: null,
            nodeDrag: null,
            backgroundClick: null,
            transitionComplete: null
        };
    }

    initialize() {
        console.log('[Renderer] Starting initialization');
        console.log(`[Renderer] Container dimensions: ${this.container.node().offsetWidth}x${this.container.node().offsetHeight}`);

        try {
            // Create SVG
            this.svg = this.container
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
                .style('background-color', 'transparent');

            // Create layers
            this.mainGroup = this.svg.append('g')
                .attr('class', 'main-group')
                .attr('transform', 'translate(0,0)');  // Explicit initial transform

            this.edgeGroup = this.mainGroup.append('g')
                .attr('class', 'edges');

            this.nodeGroup = this.mainGroup.append('g')
                .attr('class', 'nodes');

            // Initialize zoom
            this._initializeZoom();

            // Add background click handler
            this.svg.on('click', (event) => {
                if (event.target === this.svg.node()) {
                    this.callbacks.backgroundClick?.();
                }
            });

            // Verify DOM elements
            this._verifyDOMElements();

        } catch (error) {
            console.error('[Renderer] Initialization error:', error);
            throw error;
        }
    }

    _verifyDOMElements() {
        // Verify all critical DOM elements are present
        const elements = {
            'SVG': this.svg,
            'Main Group': this.mainGroup,
            'Edge Group': this.edgeGroup,
            'Node Group': this.nodeGroup
        };

        for (const [name, element] of Object.entries(elements)) {
            if (!element || element.empty()) {
                console.error(`[Renderer] Missing DOM element: ${name}`);
            } else {
                const node = element.node();
                console.log(`[Renderer] ${name} verified:`, {
                    'tag': node.tagName,
                    'class': node.getAttribute('class'),
                    'transform': node.getAttribute('transform')
                });
            }
        }
    }

    async updateElements(nodes, edges) {
        try {
            // Update edges
            this.edgeElements = this.edgeGroup
                .selectAll('.edge')
                .data(edges, d => `${d.source.id}-${d.target.id}`);

            this.edgeElements.exit().remove();

            const edgesEnter = this.edgeElements.enter()
                .append('path')
                .attr('class', 'edge')
                .style('fill', 'none');

            this.edgeElements = edgesEnter.merge(this.edgeElements)
                .style('stroke-width', d => d.width)
                .style('stroke', d => d.color);

            // Update nodes
            this.nodeElements = this.nodeGroup
                .selectAll('.node')
                .data(nodes, d => d.id);

            this.nodeElements.exit().remove();

            const nodesEnter = this.nodeElements.enter()
                .append('g')
                .attr('class', 'node')
                .call(this._initializeDrag());

            this._createNodeVisuals(nodesEnter);
            this._addNodeInteractions(nodesEnter);

            this.nodeElements = nodesEnter.merge(this.nodeElements);

            // Verify final state
            this._verifyVisualElements();

        } catch (error) {
            console.error('[Renderer] Error updating elements:', error);
            throw error;
        }
    }

    _verifyVisualElements() {
        // Verify node elements
        const nodeCount = this.nodeElements.size();
        const nodeCircles = this.nodeGroup.selectAll('circle').size();
        const nodeLabels = this.nodeGroup.selectAll('text').size();
        
        console.log('[Renderer] Element verification:', {
            'Total Nodes': nodeCount,
            'Node Circles': nodeCircles,
            'Node Labels': nodeLabels,
            'Total Edges': this.edgeElements.size()
        });

        if (nodeCount !== nodeCircles || nodeCount !== nodeLabels) {
            console.warn('[Renderer] Mismatch in node elements!');
        }
    }


    async animateColorTransition(nodeId, targetColor, connectedNodes, isReverse = false) {
        return new Promise((resolve) => {
            const node = this.nodeElements.filter(d => d.id === nodeId);
            const duration = 300; // 300ms transition

            // Animate node color
            node.select('circle')
                .transition()
                .duration(duration)
                .style('fill', targetColor);

            // Get connected edges
            const connectedEdges = this.edgeElements.filter(d => 
                d.source.id === nodeId || d.target.id === nodeId
            );

            // Animate edge gradients
            connectedEdges.each((d, i, edges) => {
                const edge = d3.select(edges[i]);
                const sourceColor = d.source.id === nodeId ? targetColor : d.source.color;
                const targetColor = d.target.id === nodeId ? targetColor : d.target.color;

                // Create gradient
                const gradientId = `gradient-${d.source.id}-${d.target.id}`;
                const gradient = this._createGradient(gradientId, sourceColor, targetColor);

                // Animate edge color
                edge.transition()
                    .duration(duration)
                    .style('stroke', `url(#${gradientId})`);

                // Queue connected node transitions if needed
                if (connectedNodes && connectedNodes.length > 0) {
                    setTimeout(() => {
                        const nextNode = connectedNodes.shift();
                        if (nextNode) {
                            this.animateColorTransition(nextNode.id, targetColor, connectedNodes, isReverse);
                        }
                    }, duration);
                }
            });

            // Notify transition complete
            setTimeout(() => {
                this.callbacks.transitionComplete?.();
                resolve();
            }, duration);
        });
    }

    _createGradient(id, startColor, endColor) {
        // Create or update gradient definition
        let gradient = this.svg.select(`#${id}`);
        if (gradient.empty()) {
            gradient = this.svg.append('defs')
                .append('linearGradient')
                .attr('id', id);
        }

        gradient
            .attr('gradientUnits', 'userSpaceOnUse')
            .selectAll('stop')
            .data([
                { offset: '0%', color: startColor },
                { offset: '100%', color: endColor }
            ])
            .join('stop')
            .attr('offset', d => d.offset)
            .attr('stop-color', d => d.color);

        return gradient;
    }

    highlightNodes(nodes) {
        // Clear previous highlights
        this.nodeElements
            .filter(d => !this.selectedNodes.has(d.id))
            .transition()
            .duration(200)
            .style('opacity', 0.3);

        // Highlight specified nodes
        nodes.forEach(node => {
            this.nodeElements
                .filter(d => d.id === node.id)
                .transition()
                .duration(200)
                .style('opacity', 1);

            // Highlight connected edges
            this.edgeElements
                .filter(d => d.source.id === node.id || d.target.id === node.id)
                .transition()
                .duration(200)
                .style('opacity', 1);
        });

        this.highlightedNodes = new Set(nodes.map(n => n.id));
    }

    clearHighlights(excludeNodes = []) {
        // Restore non-excluded nodes to full opacity
        this.nodeElements
            .filter(d => !excludeNodes.includes(d.id))
            .transition()
            .duration(200)
            .style('opacity', 1);

        // Restore edges
        this.edgeElements
            .transition()
            .duration(200)
            .style('opacity', 1);

        this.highlightedNodes.clear();
    }

    getConnectedNodes(nodeId) {
        const connectedNodes = new Set();
        this.edgeElements.each(d => {
            if (d.source.id === nodeId) {
                connectedNodes.add(d.target);
            } else if (d.target.id === nodeId) {
                connectedNodes.add(d.source);
            }
        });
        return Array.from(connectedNodes);
    }

    _createNodeVisuals(nodes) {
        try {
            // Add circle
            const circles = nodes.append('circle')
                .attr('r', d => {
                    return d.size;
                })
                .style('fill', d => d.color)

            // Add label
            const labels = nodes.append('text')
                .attr('dy', '.35em')
                .attr('x', d => d.size + 5)
                .style('fill', '#ffffff')
                .style('font-family', 'Segoe UI')
                .style('font-size', '24px')
                .text(d => d.label);

        } catch (error) {
            console.error('[Renderer] Error creating node visuals:', error);
            throw error;
        }
    }

    _initializeDrag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation?.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
                this.callbacks.nodeDrag?.('start', d);
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
                this.callbacks.nodeDrag?.('drag', d);
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation?.alphaTarget(0);
                d.fx = null;
                d.fy = null;
                this.callbacks.nodeDrag?.('end', d);
            });
    }

    _addNodeInteractions(nodes) {
        nodes
            .on('click', (event, d) => {
                event.stopPropagation();
                this.callbacks.nodeClick?.(d);
            })
            .on('mouseover', (event, d) => {
                this.callbacks.nodeHover?.(d);
            })
            .on('mouseout', () => {
                this.callbacks.nodeHover?.(null);
            });
    }

    _initializeZoom() {
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.transform = event.transform;
                this.mainGroup.attr('transform', event.transform);
            });

        this.svg.call(zoom);
    }

    updatePositions() {
        if (!this.nodeElements || !this.edgeElements) {
            console.warn('[Renderer] Cannot update positions - elements not initialized');
            return;
        }

        try {
            // Remove loading message if present
            d3.select('.loading').style('display', 'none');

            // Make sure container is visible
            this.container.style('visibility', 'visible');
            
            // Update edges with curved paths
            this.edgeElements
                .style('visibility', 'visible') // Ensure edges are visible
                .attr('d', d => {
                    // Ensure we have valid positions
                    if (!d.source.x || !d.source.y || !d.target.x || !d.target.y) {
                        console.warn('[Renderer] Invalid positions for edge:', d);
                        return '';
                    }

                    const dx = d.target.x - d.source.x;
                    const dy = d.target.y - d.source.y;
                    
                    // Calculate control point for curve
                    const midX = (d.source.x + d.target.x) / 2;
                    const midY = (d.source.y + d.target.y) / 2;
                    
                    return `M${d.source.x},${d.source.y} Q${midX},${midY} ${d.target.x},${d.target.y}`;
                });

            // Update node group positions
            this.nodeElements
                .style('visibility', 'visible') // Ensure nodes are visible
                .attr('transform', d => {
                    // Ensure we have valid positions
                    if (!d.x || !d.y) {
                        console.warn('[Renderer] Invalid positions for node:', d);
                        return '';
                    }
                    return `translate(${d.x},${d.y})`;
                });

            // Log the first few positions for debugging
            const sampleNodes = this.nodeElements.data().slice(0, 3);
        } catch (error) {
            console.error('[Renderer] Error updating positions:', error);
        }
    }

    setupNodeInteractions(handlers) {
        this.callbacks = { ...this.callbacks, ...handlers };
    }

    onTransitionComplete(callback) {
        this.callbacks.transitionComplete = callback;
    }

    onBackgroundClick(callback) {
        this.callbacks.backgroundClick = callback;
    }

    cleanup() {
        try {
            if (this.svg) {
                this.svg.remove();
            }
            this.nodeElements = null;
            this.edgeElements = null;
            this.colorFlowTransitions.clear();
            this.highlightedNodes.clear();
            this.selectedNodes.clear();
        } catch (error) {
            console.error('[Renderer] Error during cleanup:', error);
        }
    }
}