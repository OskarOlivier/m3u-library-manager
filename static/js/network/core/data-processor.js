// static/js/network/core/data-processor.js

import { NetworkTheme } from './themes.js';

export class DataProcessor {
    constructor() {
        this.theme = NetworkTheme.defaultTheme;
        this.nodeDegrees = new Map();  // Store node degrees
    }

    processData(nodes, edges) {
        console.log(`Processing ${nodes.length} nodes and ${edges.length} edges`);

        // Calculate node degrees first
        this._calculateNodeDegrees(edges);
        const processedNodes = this._processNodes(nodes);
        const processedEdges = this._processEdges(edges, processedNodes);

        return { processedNodes, processedEdges };
    }

    _processNodes(nodes) {
        return nodes.map(node => {
            const baseSize = this._calculateNodeSize(node.value || 1, nodes);
            const degree = this.nodeDegrees.get(node.id) || 0;
            
            // Calculate importance factor based on both size and degree
            const importance = this._calculateImportance(baseSize, degree);
            
            return {
                ...node,
                size: baseSize,
                collisionRadius: this._calculateCollisionRadius(baseSize, degree),
                color: node.color || NetworkTheme.generateRandomColor(),
                // Initialize with random positions if not set
                x: node.x || Math.random() * 1000,
                y: node.y || Math.random() * 1000,
                // Store metadata for debugging/visualization
                metadata: {
                    degree,
                    importance
                }
            };
        });
    }

    _calculateCollisionRadius(baseSize, degree) {
        // Base collision radius is 1.5x the visual size
        const baseRadius = baseSize * 1.5;
        
        // Additional spacing based on degree
        const degreeBonus = Math.pow(degree, 0.7) * 2;  // Non-linear scaling
        
        // Combine with importance-based multiplier
        const importance = this._calculateImportance(baseSize, degree);
        const importanceMultiplier = 1 + (importance * 2);  // Up to 3x spacing for important nodes
        
        return Math.max(baseRadius * importanceMultiplier + degreeBonus, baseRadius);
    }

    _calculateNodeSize(value, allNodes) {
        try {
            // Ensure valid numeric value
            const nodeValue = parseFloat(value);
            if (isNaN(nodeValue)) {
                console.warn(`Invalid node value: ${value}, using default size`);
                return 12; // Default minimum size
            }

            // Set min/max sizes
            const minSize = 12;
            const maxSize = 48;

            // For single node or when all values are the same
            if (allNodes.length === 1) {
                return minSize;
            }

            // Get valid node values for max calculation
            const validValues = allNodes
                .map(d => parseFloat(d.value))
                .filter(v => !isNaN(v));

            if (validValues.length === 0) {
                console.warn('No valid node values found for size calculation');
                return minSize;
            }

            const maxValue = Math.max(...validValues);
            const minValue = Math.min(...validValues);

            // If all values are the same, return middle size
            if (maxValue === minValue) {
                return (minSize + maxSize) / 2;
            }

            // Linear scale between min and max sizes
            const scale = d3.scaleLinear()
                .domain([minValue, maxValue])
                .range([minSize, maxSize])
                .clamp(true);

            return scale(nodeValue);

        } catch (error) {
            console.error('Error calculating node size:', error);
            return 12; // Fallback size
        }
    }

    _calculateNodeDegrees(edges) {
        // Reset degree map
        this.nodeDegrees.clear();

        // Count connections for each node
        edges.forEach(edge => {
            this.nodeDegrees.set(edge.from, (this.nodeDegrees.get(edge.from) || 0) + 1);
            this.nodeDegrees.set(edge.to, (this.nodeDegrees.get(edge.to) || 0) + 1);
        });

        // Log high-degree nodes for debugging
        const highDegreeNodes = Array.from(this.nodeDegrees.entries())
            .filter(([_, degree]) => degree > 5)
            .sort((a, b) => b[1] - a[1]);
        if (highDegreeNodes.length > 0) {
            console.log('High degree nodes:', highDegreeNodes);
        }
    }
    
    _calculateImportance(size, degree) {
        // Non-linear scaling that emphasizes nodes that are both large and well-connected
        const normalizedSize = size / 48;  // Normalize by max size
        const normalizedDegree = Math.min(degree / 10, 1);  // Cap at 10 connections
        
        // Combine size and degree with emphasis on high values of both
        return Math.pow(normalizedSize * normalizedDegree, 1.5);
    }

    _calculateNodeColor(value, allNodes) {
        try {
            // Create color scale from theme colors
            const scale = d3.scaleSequential()
                .domain([0, d3.max(allNodes, d => d.value || 0)])
                .interpolator(d3.interpolateBlues);
                
            return scale(value);
            
        } catch (error) {
            console.error('Error calculating node color:', error);
            return this.theme.node.default; // Fallback color
        }
    }

    _processEdges(edges, processedNodes) {
        const nodeMap = new Map(processedNodes.map(node => [node.id, node]));

        return edges.map(edge => {
            const source = nodeMap.get(edge.from);
            const target = nodeMap.get(edge.to);

            if (!source || !target) {
                console.error(`Invalid edge: ${edge.from} -> ${edge.to}`);
                return null;
            }

            const sourceImportance = source.metadata.importance;
            const targetImportance = target.metadata.importance;
            
            // Visual width based on relationship strength
            const visualWidth = this._calculateEdgeWidth(edge.value || 1, edges);
            
            // Edge length for simulation (separate from visual width)
            const baseLength = 200; // Base edge length
            const lengthMultiplier = 1 + Math.max(sourceImportance, targetImportance) * 2;

            return {
                ...edge,
                source,
                target,
                width: visualWidth,
                length: baseLength * lengthMultiplier
            };
        }).filter(edge => edge !== null);
    }

    _calculateEdgeWidth(value, allEdges) {
        try {
            if (!value || value < 1) return 1;
            
            // Linear scale might work better than log for this case
            const scale = d3.scaleLinear()
                .domain([1, d3.max(allEdges, d => d.value || 1)])
                .range([1, 24])  // More conservative range for better visibility
                .clamp(true);
                
            return scale(value);
        } catch (error) {
            console.error('Error calculating edge width:', error);
            return 1;
        }
    }

    validateNode(node) {
        return {
            isValid: Boolean(node && node.id),
            errors: this._getNodeValidationErrors(node)
        };
    }

    validateEdge(edge) {
        return {
            isValid: Boolean(edge && edge.from && edge.to),
            errors: this._getEdgeValidationErrors(edge)
        };
    }

    _getNodeValidationErrors(node) {
        const errors = [];
        
        if (!node) {
            errors.push('Node is undefined');
            return errors;
        }

        if (!node.id) errors.push('Missing node ID');
        if (!node.label) errors.push('Missing node label');
        if (node.value && isNaN(parseFloat(node.value))) {
            errors.push('Invalid node value');
        }

        return errors;
    }

    _getEdgeValidationErrors(edge) {
        const errors = [];
        
        if (!edge) {
            errors.push('Edge is undefined');
            return errors;
        }

        if (!edge.from) errors.push('Missing edge source');
        if (!edge.to) errors.push('Missing edge target');
        if (edge.value && isNaN(parseFloat(edge.value))) {
            errors.push('Invalid edge value');
        }

        return errors;
    }
}