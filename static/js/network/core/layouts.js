// static/js/network/core/layouts.js

/**
 * Layout configurations optimized for graphs under 100 nodes and 250 edges.
 * Provides force simulation settings for different visualization scenarios.
 */
export class NetworkLayout {
    static defaultConfig = {
        // Core forces
        charge: {
            strength: d => {
                // Base repulsion for low-degree nodes
                const baseCharge = -5000;
                
                // Get degree from metadata
                const degree = d.metadata?.degree || 0;
                
                if (degree < 10) {
                    return baseCharge;  // Keep base charge for low-degree nodes
                }
                
                // Non-linear scaling for high-degree nodes
                // More dramatic repulsion as degree increases
                const scaleFactor = Math.pow(degree, 15);
                return baseCharge * (1 + (scaleFactor / 10));
            },
            minDistance: 0,        // Minimum repulsion distance
            maxDistance: 5000       // Maximum repulsion distance
        },
        link: {
            distance: d => {
                // Base distance
                const baseDistance = d.length || 200;
                
                // Get degrees of connected nodes
                const sourceDegree = d.source.metadata?.degree || 0;
                const targetDegree = d.target.metadata?.degree || 0;
                const maxDegree = Math.max(sourceDegree, targetDegree);
                
                if (maxDegree < 10) {
                    return baseDistance;  // Keep base distance for low-degree connections
                }
                
                // Scale distance based on highest degree node
                const degreeScale = Math.pow(maxDegree, 0.5);  // Less aggressive than charge scaling
                return baseDistance * (1 + (degreeScale / 10));
            },
            strength: d => {
                // Weaker links for high-degree nodes
                const maxDegree = Math.max(
                    d.source.metadata?.degree || 0,
                    d.target.metadata?.degree || 0
                );
                return maxDegree > 10 ? 0.1 : 0.2;
            },
            iterations: 4
        },
        collision: {
            strength: 0.95,
            radiusScale: d => {
                // Base collision radius
                const baseRadius = d.size + 10;
                const degree = d.metadata?.degree || 0;
                
                if (degree < 10) {
                    return baseRadius;  // Keep base radius for low-degree nodes
                }
                
                // Non-linear scaling for high-degree nodes
                const scaleFactor = Math.pow(degree, 5);  // Slightly less aggressive than charge
                return baseRadius * (1 + (scaleFactor / 20));
            }
        },
        positioning: {
            alpha: 1,
            alphaDecay: 0.01,      // Slower decay for better settling
            alphaMin: 0.001,
            velocityDecay: 0.3     // Reduced for more natural movement
        }
    };

    /**
     * Creates a force simulation with optimized settings.
     * @param {number} width - Container width
     * @param {number} height - Container height
     * @param {Object} options - Optional configuration overrides
     * @returns {d3.ForceSimulation} Configured force simulation
     */
    static createSimulation(width, height, options = {}) {
        const config = { ...NetworkLayout.defaultConfig, ...options };

        return d3.forceSimulation()
            // Core positioning force
            .force('center', d3.forceCenter(width / 2, height / 2))
            
            // Node repulsion force with degree-based scaling
            .force('charge', d3.forceManyBody()
                .strength(config.charge.strength)
                .distanceMin(config.charge.minDistance)
                .distanceMax(config.charge.maxDistance))
            
            // Node collision force with degree-based radius
            .force('collision', d3.forceCollide()
                .strength(config.collision.strength)
                .radius(config.collision.radiusScale))
            
            // Additional stabilizing force
            .force('x', d3.forceX(width / 2).strength(0.1))
            .force('y', d3.forceY(height / 2).strength(0.1))
            
            // Simulation parameters
            .alpha(config.positioning.alpha)
            .alphaDecay(config.positioning.alphaDecay)
            .alphaMin(config.positioning.alphaMin)
            .velocityDecay(config.positioning.velocityDecay);
    }

    /**
     * Configures link force for the simulation.
     * @param {d3.ForceSimulation} simulation - Force simulation instance
     * @param {Array} links - Array of link data
     * @param {Object} options - Optional configuration overrides
     */
    static configureLinks(simulation, links, options = {}) {
        const config = { ...NetworkLayout.defaultConfig, ...options };

        const linkForce = d3.forceLink(links)
            .id(d => d.id)
            .distance(config.link.distance)
            .strength(config.link.strength)
            .iterations(config.link.iterations);

        simulation.force('link', linkForce);
    }

    /**
     * Creates layout configuration for specific graph characteristics.
     * @param {Object} graphStats - Graph statistics
     * @returns {Object} Optimized configuration
     */
    static getOptimizedConfig(graphStats) {
        const baseConfig = { ...NetworkLayout.defaultConfig };

        // Adjust force strengths based on graph density
        const density = (2 * graphStats.edgeCount) / 
                       (graphStats.nodeCount * (graphStats.nodeCount - 1));

        if (density > 0.3) {
            // Dense graph adjustments
            return {
                ...baseConfig,
                charge: {
                    ...baseConfig.charge,
                    strength: d => {
                        const baseStrength = baseConfig.charge.strength(d);
                        return baseStrength * 1.3;  // Increase repulsion for dense graphs
                    },
                    maxDistance: 200
                },
                link: {
                    ...baseConfig.link,
                    strength: d => {
                        const baseStrength = baseConfig.link.strength(d);
                        return baseStrength * 1.2;  // Slightly stronger links for stability
                    }
                }
            };
        }

        // Sparse graph (default config works well)
        return baseConfig;
    }

    /**
     * Adjusts simulation parameters for specific interactions.
     * @param {d3.ForceSimulation} simulation - Force simulation instance
     * @param {string} interaction - Type of interaction
     */
    static adjustForInteraction(simulation, interaction) {
        switch (interaction) {
            case 'drag':
                // Stronger forces during drag
                simulation
                    .alpha(0.5)
                    .alphaTarget(0.3)
                    .velocityDecay(0.6);
                break;

            case 'select':
                // Gentle force adjustment for selection
                simulation
                    .alpha(0.3)
                    .alphaTarget(0)
                    .velocityDecay(0.4);
                break;

            case 'reset':
                // Reset to default parameters
                simulation
                    .alpha(1)
                    .alphaTarget(0)
                    .velocityDecay(NetworkLayout.defaultConfig.positioning.velocityDecay);
                break;
        }
    }
}