/**
 * Lightweight in-memory TTL cache for API GET responses.
 * Lives at module scope so it persists across client-side navigations.
 *
 * Usage:
 *   getCached(key)           → data or null
 *   setCached(key, data)     → void
 *   invalidate('/api/admin') → clears all keys starting with that prefix
 *   invalidateAll()          → nuke everything (e.g. on logout)
 */

/** @type {Map<string, { data: any, expiresAt: number }>} */
const _store = new Map();

const DEFAULT_TTL_MS = 45_000; // 45 seconds – instant re-nav, still reasonably fresh

/**
 * @param {string} key
 * @returns {any | null}
 */
export function getCached(key) {
	const entry = _store.get(key);
	if (!entry) return null;
	if (Date.now() > entry.expiresAt) {
		_store.delete(key);
		return null;
	}
	return entry.data;
}

/**
 * @param {string} key
 * @param {any} data
 * @param {number} [ttl] milliseconds
 */
export function setCached(key, data, ttl = DEFAULT_TTL_MS) {
	_store.set(key, { data, expiresAt: Date.now() + ttl });
}

/**
 * Remove all cached entries whose key starts with `prefix`.
 * Call this after any mutation so related GETs are re-fetched.
 * @param {string} prefix
 */
export function invalidate(prefix) {
	for (const key of _store.keys()) {
		if (key.startsWith(prefix)) _store.delete(key);
	}
}

/** Clear everything — use on logout / role switch. */
export function invalidateAll() {
	_store.clear();
}
