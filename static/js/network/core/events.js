// static/js/network/core/events.js

export class EventManager {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, callback) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }
        this.listeners.get(eventName).add(callback);
        console.log(`Added listener for event: ${eventName}`);
    }

    off(eventName, callback) {
        const callbacks = this.listeners.get(eventName);
        if (callbacks) {
            callbacks.delete(callback);
            console.log(`Removed listener for event: ${eventName}`);
        }
    }

    emit(eventName, data) {
        const callbacks = this.listeners.get(eventName);
        if (callbacks) {
            //console.log(`Emitting event: ${eventName}`, data);
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event callback (${eventName}):`, error);
                }
            });
        }
    }

    cleanup() {
        this.listeners.clear();
    }
}