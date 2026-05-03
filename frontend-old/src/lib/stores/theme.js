import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const initialTheme = browser ? localStorage.getItem('univote_theme') || 'light' : 'light';
export const theme = writable(initialTheme);

if (browser) {
	theme.subscribe((val) => {
		localStorage.setItem('univote_theme', val);
		if (val === 'dark') {
			document.documentElement.classList.add('dark');
		} else {
			document.documentElement.classList.remove('dark');
		}
	});
}

export function toggleTheme() {
	theme.update((current) => (current === 'light' ? 'dark' : 'light'));
}

/**
 * Imperatively set the theme (used by role-based layouts).
 * Calling setTheme('dark') from admin/adviser layouts enforces the
 * premium dark dashboard. Calling setTheme('light') from student
 * layout enforces the paper-ballot light voter UI.
 * @param {'light'|'dark'} val
 */
export function setTheme(val) {
	theme.set(val);
}
