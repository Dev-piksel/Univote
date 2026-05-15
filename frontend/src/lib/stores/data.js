import { writable } from 'svelte/store';

/**
 * @typedef {Object} DataCache
 * @property {Array<any>} elections
 * @property {Array<any>} departments
 * @property {Array<any>} advisers
 * @property {Array<any>} voters
 * @property {Date|null} lastUpdated
 */

const initialState = {
	elections: [],
	departments: [],
	advisers: [],
	voters: [],
	lastUpdated: null
};

function createDataStore() {
	const { subscribe, set, update } = writable(/** @type {DataCache} */ (initialState));

	return {
		subscribe,
		/** @param {Array<any>} data */
		setElections: (data) => update(s => ({ ...s, elections: data, lastUpdated: new Date() })),
		/** @param {Array<any>} data */
		setDepartments: (data) => update(s => ({ ...s, departments: data, lastUpdated: new Date() })),
		/** @param {Array<any>} data */
		setAdvisers: (data) => update(s => ({ ...s, advisers: data, lastUpdated: new Date() })),
		/** @param {Array<any>} data */
		setVoters: (data) => update(s => ({ ...s, voters: data, lastUpdated: new Date() })),
		clear: () => set(initialState)
	};
}

export const dataCache = createDataStore();
