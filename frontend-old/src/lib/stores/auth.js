import { writable } from 'svelte/store';
import { browser } from '$app/environment';

/**
 * @typedef {Object} AdminAdviserSession
 * @property {string} access_token
 * @property {string} role
 * @property {string} full_name
 * @property {string} user_id
 * @property {string} [photo_url]
 * @property {boolean} [must_change_password]
 */

function createAuthStore() {
	const isBrowser = typeof window !== 'undefined';

	// Read initial state from localStorage if available
	const initialData = isBrowser ? localStorage.getItem('univote_admin_session') : null;
	/** @type {AdminAdviserSession | null} */
	let parsed = null;
	try {
		parsed = initialData && initialData !== 'undefined' ? JSON.parse(initialData) : null;
	} catch {
		parsed = null;
	}

	const { subscribe, set, update } = writable(parsed);

	return {
		subscribe,
		/**
		 * @param {AdminAdviserSession} sessionData
		 */
		login: (sessionData) => {
			set(sessionData);
			if (isBrowser) {
				localStorage.setItem('univote_admin_session', JSON.stringify(sessionData));
			}
		},
		logout: () => {
			set(null);
			if (isBrowser) {
				localStorage.removeItem('univote_admin_session');
			}
		}
	};
}

export const authSession = createAuthStore();
