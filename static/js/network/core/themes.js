// static/js/network/core/themes.js

/**
 * Centralized visual styling configuration for network visualization.
 * Provides consistent theming and color schemes.
 */
export class NetworkTheme {
    static defaultTheme = {
        // Base colors
        background: '#202020',
        text: '#FFFFFF',
        
        // Node colors
        node: {
            default: '#4B0082',          // Base node color
            selected: '#9370DB',         // Selected node
            hover: '#8A2BE2',            // Hovered node
            inactive: '#333333',         // Inactive state
            border: '#2D2D2D',           // Node border
            borderWidth: 2,              // Border width
            borderSelected: 3,           // Selected border width
            label: {
                color: '#FFFFFF',
                size: '24px',
                family: 'Segoe UI',
                offset: 5                // Distance from node
            }
        },
        
        // Edge styling
        edge: {
            default: '#666666',          // Base edge color
            highlighted: '#FFFFFF',       // Highlighted state
            inactive: '#333333',         // Inactive state
            opacity: {
                default: 0.6,            // Normal opacity
                highlighted: 1.0,         // Highlighted opacity
                inactive: 0.3,           // Inactive opacity
                dimmed: 0.2              // New: Dimmed state for non-selected
            },
            gradient: {
                duration: 300,           // New: Duration of gradient transitions
                easingFunction: 'linear'  // New: Easing for color flow
            }
        },
        
        // Animation timings
        animation: {
            duration: 300,              // Standard transition duration
            easingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)', // Standard easing
            colorFlow: {
                duration: 300,          // New: Color flow duration
                stagger: 50            // New: Delay between connected transitions
            }
        },
        
        // Selection states
        selection: {
            preserveOpacity: true,     // New: Keep selected nodes at full opacity
            dimOthers: true,          // New: Dim non-selected/non-connected nodes
            colorFlow: true           // New: Enable color flow animations
        },
        
        // Interaction states
        interaction: {
            hoverScale: 1.1,           // Node hover scale factor
            selectScale: 1.2,          // Node selection scale factor
            transitions: {
                node: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                edge: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
            }
        }
    };

    /**
     * Generate a random pleasing color from the rainbow spectrum.
     * @returns {string} HSL color string
     */
    static generateRandomColor() {
        const h = Math.random() * 360;    // Full hue spectrum
        const s = 60 + Math.random() * 20; // 60-80% saturation
        const l = 45 + Math.random() * 10; // 45-55% lightness
        return `hsl(${h}, ${s}%, ${l}%)`;
    }

    /**
     * Create gradient color steps between two colors.
     * @param {string} startColor - Starting color
     * @param {string} endColor - Ending color
     * @param {number} steps - Number of gradient steps
     * @returns {string[]} Array of color values
     */
    static createGradientColors(startColor, endColor, steps = 10) {
        const scale = d3.scaleLinear()
            .domain([0, steps - 1])
            .range([d3.hsl(startColor), d3.hsl(endColor)]);
            
        return Array.from({length: steps}, (_, i) => scale(i).toString());
    }

    /**
     * Get node styling based on state.
     * @param {Object} node - Node data
     * @param {Object} state - Current state
     * @returns {Object} Style configuration
     */
    static getNodeStyle(node, state = {}) {
        const theme = this.defaultTheme;
        const isSelected = state.selectedNodes?.has(node.id);
        const isHighlighted = state.highlightedNodes?.has(node.id);
        const isDimmed = state.hasDimming && !isHighlighted && !isSelected;
        
        return {
            fill: isSelected ? state.selectionColor || node.color : node.color,
            stroke: isSelected ? theme.node.border : theme.node.border,
            strokeWidth: isSelected ? theme.node.borderSelected : theme.node.borderWidth,
            opacity: isDimmed ? theme.node.opacity.inactive : 1,
            transform: `scale(${isHighlighted ? theme.interaction.hoverScale : 
                             isSelected ? theme.interaction.selectScale : 1})`
        };
    }

    /**
     * Get edge styling based on state.
     * @param {Object} edge - Edge data
     * @param {Object} state - Current state
     * @returns {Object} Style configuration
     */
    static getEdgeStyle(edge, state = {}) {
        const theme = this.defaultTheme;
        const isHighlighted = state.highlightedEdges?.has(`${edge.source.id}-${edge.target.id}`);
        const isDimmed = state.hasDimming && !isHighlighted;
        const hasGradient = state.gradientEdges?.has(`${edge.source.id}-${edge.target.id}`);
        
        return {
            stroke: hasGradient ? `url(#gradient-${edge.source.id}-${edge.target.id})` : 
                    isHighlighted ? theme.edge.highlighted : 
                    edge.color || theme.edge.default,
            strokeOpacity: isDimmed ? theme.edge.opacity.dimmed :
                          isHighlighted ? theme.edge.opacity.highlighted :
                          theme.edge.opacity.default,
            transition: theme.interaction.transitions.edge
        };
    }

    /**
     * Create CSS styles for network components.
     * @returns {string} CSS rules
     */
    static generateCSS() {
        const theme = this.defaultTheme;
        return `
            .network-container {
                background-color: ${theme.background};
            }
            
            .node text {
                fill: ${theme.node.label.color};
                font-family: ${theme.node.label.family};
                font-size: ${theme.node.label.size};
                pointer-events: none;
            }
            
            .node circle {
                transition: ${theme.interaction.transitions.node};
            }
            
            .edge {
                transition: ${theme.interaction.transitions.edge};
            }
        `;
    }

    /**
     * Deep merge utility for theme objects.
     * @private
     */
    static _mergeDeep(target, source) {
        const output = Object.assign({}, target);
        if (this._isObject(target) && this._isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this._isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this._mergeDeep(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    }

    static _isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }
}