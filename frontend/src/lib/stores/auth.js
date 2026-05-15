import { writable } from 'svelte/store';
import { browser } from '$app/environment';

/**
 * @typedef {Object} AdminAdviserSession
 * @property {string} access_token
 * @property {string} role
 * @property {string} full_name  - Computed display name (first [M.] last)
 * @property {string} first_name
 * @property {string} last_name
 * @property {string} [middle_initial]
 * @property {string} [email]
 * @property {string} user_id
 * @property {string} id_number
 * @property {string} [photo_url]
 * @property {string} [department_id]
 * @property {string} [department_name]
 * @property {boolean} [must_change_password]
 */

function createAuthStore() {
	const isBrowser = typeof window !== 'undefined';

	// Read initial state from sessionStorage if available (clears on tab/browser close)
	const initialData = isBrowser ? sessionStorage.getItem('univote_admin_session') : null;
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
				sessionStorage.setItem('univote_admin_session', JSON.stringify(sessionData));
			}
		},
		/**
		 * @param {(s: AdminAdviserSession | null) => AdminAdviserSession} fn
		 */
		update: (fn) => {
			update(fn);
			if (isBrowser) {
				// subscribe() is synchronous — immediately yields the current value
				let current = null;
				const unsub = subscribe(s => (current = s));
				unsub();
				if (current) sessionStorage.setItem('univote_admin_session', JSON.stringify(current));
			}
		},
		logout: () => {
			set(null);
			if (isBrowser) {
				sessionStorage.removeItem('univote_admin_session');
			}
		}
	};
}

export const authSession = createAuthStore();
