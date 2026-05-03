import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { BASE } from '$lib/api.js';

const STORAGE_KEY = 'univote_branding';
const STORAGE_VERSION = 2; // Bump if DEFAULTS shape changes

export const DEFAULTS = {
	appName: 'UniVote',
	primaryColor: '#0b75fe',
	accentColor: '#5c60f5',
	logoUrl: null
};

/**
 * Very simple hex shade utility.
 * @param {string} hex
 * @param {number} percent
 */
function shadeColor(hex, percent) {
	try {
		const num = parseInt(hex.replace('#', ''), 16);
		const r = Math.min(255, Math.max(0, (num >> 16) + Math.round(255 * percent / 100)));
		const g = Math.min(255, Math.max(0, ((num >> 8) & 0xff) + Math.round(255 * percent / 100)));
		const b = Math.min(255, Math.max(0, (num & 0xff) + Math.round(255 * percent / 100)));
		return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
	} catch {
		return hex;
	}
}

function loadFromStorage() {
	if (!browser) return DEFAULTS;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw) {
			const parsed = JSON.parse(raw);
			// If version matches return it, otherwise use defaults
			if (parsed._v === STORAGE_VERSION) {
				const { _v, ...data } = parsed;
				return { ...DEFAULTS, ...data };
			}
		}
	} catch {
		// ignore
	}
	return DEFAULTS;
}

/**
 * Apply branding CSS variables to :root immediately. This is the single source of truth
 * for all portals. Targeting :root only — dark mode is a CSS class on <html>, not
 * a separate element that needs separate variable injection.
 * @param {{appName: string, primaryColor: string, accentColor: string, logoUrl: string|null}} val
 */
export function applyBrandingCSS(val) {
	if (!browser) return;
	const root = document.documentElement;
	const hex = val.primaryColor;

	// Parse once
	const r = parseInt(hex.slice(1, 3), 16);
	const g = parseInt(hex.slice(3, 5), 16);
	const b = parseInt(hex.slice(5, 7), 16);

	// ── Core brand tokens (used across ALL portals) ──
	root.style.setProperty('--accent', val.primaryColor);
	root.style.setProperty('--accent2', val.accentColor);
	root.style.setProperty('--brand-gradient', `linear-gradient(135deg, ${val.primaryColor}, ${val.accentColor})`);
	root.style.setProperty('--brand-primary', val.primaryColor);
	root.style.setProperty('--brand-primary-hover', shadeColor(val.primaryColor, -12));
	root.style.setProperty('--brand-primary-light', `rgba(${r}, ${g}, ${b}, 0.15)`);
	root.style.setProperty('--brand-secondary', val.accentColor);

	// Glow & focus rings
	root.style.setProperty('--brand-glow', `rgba(${r}, ${g}, ${b}, 0.18)`);
	root.style.setProperty('--focus-ring', `0 0 0 3px rgba(${r}, ${g}, ${b}, 0.25)`);
	root.style.setProperty('--shadow-float', `0 8px 24px -4px rgba(${r}, ${g}, ${b}, 0.2)`);

	// ── Landing page gradient ──
	root.style.setProperty('--landing-bg-start', val.primaryColor);
	root.style.setProperty('--landing-bg-mid', shadeColor(val.primaryColor, -20));
	root.style.setProperty('--landing-bg-end', shadeColor(val.primaryColor, -40));
}

// Initialise with cached data immediately (no flash on load)
const initial = loadFromStorage();

/** @type {import('svelte/store').Writable<{appName: string, primaryColor: string, accentColor: string, logoUrl: string|null}>} */
export const branding = writable(initial);

// Apply CSS and persist on every store change
if (browser) {
	// Apply immediately from cached data (eliminates FOUC)
	applyBrandingCSS(initial);

	branding.subscribe((val) => {
		applyBrandingCSS(val);
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify({ _v: STORAGE_VERSION, ...val }));
		} catch {
			// ignore storage errors
		}
	});
}

/**
 * Fetch branding from the API and update the store.
 * Safe to call from any layout — unauthenticated.
 * Uses stale-while-revalidate: cached values applied instantly, API updates quietly in bg.
 */
export async function loadBranding() {
	try {
		const res = await fetch(`${BASE}/api/admin/settings`);
		if (!res.ok) return;
		const json = await res.json();
		const d = json.data || {};
		branding.set({
			appName: d.app_name || DEFAULTS.appName,
			primaryColor: d.primary_color || DEFAULTS.primaryColor,
			accentColor: d.accent_color || DEFAULTS.accentColor,
			logoUrl: d.logo_url || null
		});
	} catch {
		// Silently fall back to cached/default values
	}
}
