// static/js/network/core/simulation.js

export class NetworkSimulation {
    constructor(width, height) {
        this.width = width;
        this.height = height;
        this.simulation = null;
        this.isRunning = false;
        this.tickCount = 0;
        this.maxTicks = 300;
        
        this.callbacks = {
            tick: null,
            progress: null,
            complete: null
        };
        
        this._initialize();
    }

    _initialize() {
        console.log('Initializing force simulation');
        this.simulation = d3.forceSimulation()
            // Repulsion between nodes
            .force('charge', d3.forceManyBody()
                .strength(d => {
                    // Much weaker base repulsion
                    const baseCharge = -5000;
                    const degree = d.metadata?.degree || 0;
                    // Scale based on degree but keep forces small
                    return degree < 5 ? baseCharge : baseCharge * (1 + (Math.pow(degree, 2)/100));
                })
                .distanceMin(10)    // Smaller minimum distance
                .distanceMax(500))   // Much smaller maximum distance
            
            // Center force to keep nodes in middle
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            
            // Collision prevention
            .force('collision', d3.forceCollide()
                .strength(1)  // Full strength collision
                .radius(d => d.size * 1.2))  // Just slightly larger than node
                       
            // Slower simulation for more stable layout
            .alpha(0.5)
            .alphaDecay(0.02)
            .alphaMin(0.001)
            .velocityDecay(0.4)
            
            .on('tick', () => this._onTick())
            .on('end', () => this._onSimulationEnd());
            
        this.simulation.stop();
        console.log('Force simulation initialized and ready');
    }

    setData(nodes, edges) {
        console.log('Setting simulation data:', { nodes: nodes.length, edges: edges.length });
        
        // Initialize nodes with positions spread around center
        nodes.forEach((node, i) => {
            const angle = (i / nodes.length) * 2 * Math.PI;
            const radius = Math.min(this.width, this.height) / 4;
            node.x = this.width/2 + radius * Math.cos(angle);
            node.y = this.height/2 + radius * Math.sin(angle);
        });
        
        this.simulation.nodes(nodes);
        
        // Weaker link force
        const linkForce = d3.forceLink(edges)
            .id(d => d.id)
            .distance(100)  // Fixed short distance
            .strength(0.3);  // Weak links

        this.simulation.force('link', linkForce);
        this.tickCount = 0;
        console.log('Simulation data set with initial positions');
    }

    on(eventName, callback) {
        console.log(`Registering simulation ${eventName} callback`);
        switch (eventName) {
            case 'tick':
                this.callbacks.tick = callback;
                break;
            case 'stabilizationProgress':
                this.callbacks.progress = callback;
                break;
            case 'stabilizationComplete':
                this.callbacks.complete = callback;
                break;
            default:
                console.warn(`Unknown event: ${eventName}`);
        }
    }

    restart() {
        console.log('Restarting simulation');
        this.isRunning = true;
        this.tickCount = 0;
        this.simulation.alpha(1).restart();
    }

    stop() {
        console.log('Stopping simulation');
        this.isRunning = false;
        this.simulation.stop();
    }

    _onTick() {
        if (!this.isRunning) return;

        this.tickCount++;
        
        if (this.callbacks.tick) {
            this.callbacks.tick();
        }
        
        if (this.callbacks.progress) {
            const progress = Math.min(100, Math.round((this.tickCount / this.maxTicks) * 100));
            this.callbacks.progress(progress);
        }
        
        if (this.tickCount >= this.maxTicks) {
            this._onSimulationEnd();
        }
    }

    _onSimulationEnd() {
        console.log('Simulation ended');
        this.isRunning = false;
        if (this.callbacks.complete) {
            this.callbacks.complete();
        }
    }

    onTick(callback) {
        this.callbacks.tick = callback;
    }

    onStabilizationProgress(callback) {
        this.callbacks.progress = callback;
    }

    onStabilizationComplete(callback) {
        this.callbacks.complete = callback;
    }
}