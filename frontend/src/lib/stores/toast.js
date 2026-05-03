import { writable } from 'svelte/store';

/**
 * @typedef {Object} Toast
 * @property {string} id
 * @property {string} message
 * @property {'success' | 'error' | 'info' | 'warning'} type
 * @property {number} [duration]
 */

function createToastStore() {
    const { subscribe, update } = writable(/** @type {Toast[]} */ ([]));

    /**
     * @param {string} message
     * @param {'success' | 'error' | 'info' | 'warning'} type
     * @param {number} [duration]
     */
    function show(message, type = 'info', duration = 3000) {
        const id = Math.random().toString(36).substring(2, 9);
        update(all => [{ id, message, type, duration }, ...all]);

        if (duration > 0) {
            setTimeout(() => {
                dismiss(id);
            }, duration);
        }
    }

    /** @param {string} id */
    function dismiss(id) {
        update(all => all.filter(t => t.id !== id));
    }

    return {
        subscribe,
        success: (/** @type {string} */ msg, dur = 3000) => show(msg, 'success', dur),
        error: (/** @type {string} */ msg, dur = 5000) => show(msg, 'error', dur),
        info: (/** @type {string} */ msg, dur = 3000) => show(msg, 'info', dur),
        warning: (/** @type {string} */ msg, dur = 4000) => show(msg, 'warning', dur),
        dismiss
    };
}

export const toast = createToastStore();
