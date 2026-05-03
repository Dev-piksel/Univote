import { writable } from 'svelte/store';

// Helper to get initial value from localStorage
/** @param {string} key @param {string} defaultValue */
const getStoredValue = (key, defaultValue) => {
	if (typeof window !== 'undefined') {
		return localStorage.getItem(key) || defaultValue;
	}
	return defaultValue;
};

// Persistent store for the selected election ID
export const selectedElectionId = writable(getStoredValue('selectedElectionId', ''));

// Subscribe to changes and persist to localStorage
if (typeof window !== 'undefined') {
	selectedElectionId.subscribe((value) => {
		localStorage.setItem('selectedElectionId', value);
	});
}
