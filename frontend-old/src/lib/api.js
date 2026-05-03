import { authSession } from './stores/auth.js';
import { voterSession } from './stores/session.js';

export const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Tokens are now resolved dynamically per-request to avoid cross-role collisions

/**
 * Internal helper: fetch JSON and throw on non-2xx
 * @param {string} path
 * @param {RequestInit} [options]
 */
async function request(path, options = {}) {
	const headers = new Headers(options.headers || {});

	// Resolve the appropriate token based on the path
	let token = null;
	if (path.startsWith('/api/student')) {
		voterSession.subscribe((s) => (token = s?.access_token))();
	} else {
		authSession.subscribe((s) => (token = s?.access_token))();
	}

	if (token && !headers.has('Authorization')) {
		headers.set('Authorization', `Bearer ${token}`);
	}

	const mergedOptions = { ...options, headers };
	const res = await fetch(`${BASE}${path}`, mergedOptions);
	const data = await res.json().catch(() => null);

	if (!res.ok) {
		let message = data?.message ?? `Request failed: ${res.status}`;
		if (data?.detail) {
			if (typeof data.detail === 'string') {
				message = data.detail;
			} else if (Array.isArray(data.detail)) {
				message = data.detail
					.map((/** @type {any} */ err) => err.msg || JSON.stringify(err))
					.join(', ');
			}
		}
		const error = new Error(message);
		// @ts-ignore
		if (data?.retry_after) error.retryAfter = data.retry_after;
		throw error;
	}
	return data;
}

/** @param {object} body */
function json(body) {
	return {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	};
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------
export const auth = {
	/**
	 * @param {string} id
	 * @param {string} password
	 */
	login: (id, password) => request('/api/auth/login', json({ username: id, password })),

	/**
	 * @param {object} payload
	 * @param {string} payload.id
	 * @param {string} payload.password
	 * @param {string} payload.full_name
	 * @param {string} payload.role
	 * @param {string} [payload.department]
	 */
	register: (payload) => {
		const { id, ...rest } = payload;
		return request('/api/auth/register', json({ username: id, ...rest }));
	}
};

// ---------------------------------------------------------------------------
// Student endpoints
// ---------------------------------------------------------------------------
export const student = {
	/** @param {string} student_id */
	validate: (student_id) => request('/api/student/validate', json({ student_id })),

	/**
	 * @param {string} student_id
	 * @param {string} election_id
	 * @param {string} passcode_id
	 * @param {string} adviser_id
	 * @param {Array<{candidate_id: string, position: string}>} votes
	 * @param {string} voting_pin
	 * @param {string} session_passcode
	 */
	vote: (student_id, election_id, passcode_id, adviser_id, votes, session_passcode) =>
		request('/api/student/vote', {
			...json({ student_id, election_id, passcode_id, adviser_id, votes, session_passcode }),
			method: 'POST'
		}),

	/**
	 * @param {string} election_id
	 * @param {string} passcode
	 */
	verifyPasscode: (election_id, passcode) =>
		request('/api/student/verify-passcode', json({ election_id, passcode })),

	/**
	 * @param {string} student_id
	 */
	getVotingPin: (student_id) => request(`/api/student/voting-pin?student_id=${student_id}`),

	/** @param {string} election_id */
	getCandidates: (election_id) => request(`/api/student/candidates?election_id=${election_id}`),

	/**
	 * @param {string} student_id
	 * @param {string} election_id
	 */
	getVoteSummary: (student_id, election_id) =>
		request(`/api/student/vote-summary?student_id=${student_id}&election_id=${election_id}`),

	/** @param {string} election_id */
	getResults: (election_id) => request(`/api/student/results?election_id=${election_id}`),

	/** @param {string} photo_url base64 data URL */
	uploadProfilePhoto: (photo_url) =>
		request('/api/student/profile-photo', {
			...json({ photo_url }),
			method: 'PUT'
		}),

	getProfilePhoto: () => request('/api/student/profile-photo'),

	/** 
	 * Helper to get the absolute URL for a candidate's photo
	 * @param {string} candidate_id
	 */
	getCandidatePhotoUrl: (candidate_id) => `${BASE}/api/common/candidates/${candidate_id}/photo`
};

// ---------------------------------------------------------------------------
// Admin endpoints
// ---------------------------------------------------------------------------
export const admin = {
	getElections: () => request('/api/admin/elections'),

	/**
	 * @param {object} payload
	 * @param {string} payload.name
	 * @param {string} payload.start_date
	 * @param {string} payload.end_date
	 * @param {string} [payload.description]
	 */
	createElection: (payload) => request('/api/admin/elections', json(payload)),
 
	/**
	 * @param {string} election_id
	 * @param {object} payload
	 */
	updateElection: (election_id, payload) =>
		request(`/api/admin/elections/${election_id}`, { ...json(payload), method: 'PUT' }),

	/**
	 * @param {string} election_id
	 * @param {'upcoming' | 'active' | 'completed'} status
	 */
	toggleElection: (election_id, status) =>
		request(`/api/admin/elections/${election_id}/status`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ status })
		}),

	/** @param {FormData} formData */
	uploadStudents: (formData) =>
		request('/api/admin/students/upload', { method: 'POST', body: formData }),

	/**
	 * @param {object} payload
	 * @param {string} payload.student_id
	 * @param {string} payload.full_name
	 * @param {string} [payload.program]
	 * @param {number} [payload.year_level]
	 */
	addStudent: (payload) => request('/api/admin/students', json(payload)),

	/**
	 * @param {number} [page_size]
	 * @param {string | null} [page_token]
	 */
	getAuditLog: (page_size = 15, page_token = null) => {
		const params = new URLSearchParams({ page_size: String(page_size) });
		if (page_token) params.set('page_token', page_token);
		return request(`/api/admin/audit-log?${params}`);
	},

	/** @param {string} election_id */
	deleteElection: (election_id) =>
		request(`/api/admin/elections/${election_id}`, { method: 'DELETE' }),

	/**
	 * @param {number} [page_size]
	 * @param {string | null} [page_token]
	 */
	getStudents: (page_size = 50, page_token = null) => {
		const params = new URLSearchParams({ page_size: String(page_size) });
		if (page_token) params.set('page_token', page_token);
		return request(`/api/admin/students?${params}`);
	},

	/**
	 * @param {string} student_id
	 * @param {object} payload
	 */
	updateStudent: (student_id, payload) =>
		request(`/api/admin/students/${student_id}`, { ...json(payload), method: 'PUT' }),

	/** @param {string} student_id */
	deleteStudent: (student_id) => request(`/api/admin/students/${student_id}`, { method: 'DELETE' }),

	/**
	 * @param {number} [page_size]
	 * @param {string | null} [page_token]
	 */
	getAdvisers: (page_size = 50, page_token = null) => {
		const params = new URLSearchParams({ page_size: String(page_size) });
		if (page_token) params.set('page_token', page_token);
		return request(`/api/admin/advisers?${params}`);
	},

	/** @param {object} payload */
	createAdviser: (payload) => request('/api/admin/advisers', json(payload)),

	/** @param {string} adviser_id */
	deleteAdviser: (adviser_id) => request(`/api/admin/advisers/${adviser_id}`, { method: 'DELETE' }),

	/** Fetch app branding/settings (public, no auth required) */
	getSettings: () => request('/api/admin/settings'),

	/**
	 * @param {{ app_name?: string, primary_color?: string, accent_color?: string, logo_url?: string }} payload
	 */
	saveSettings: (payload) => request('/api/admin/settings', { ...json(payload), method: 'PUT' }),

	/** @param {FormData} formData */
	uploadLogo: (formData) => request('/api/admin/settings/logo', { method: 'POST', body: formData }),

	/** @param {FormData} formData */
	importAdvisers: (formData) => request('/api/admin/advisers/import', { method: 'POST', body: formData }),

	downloadAdviserTemplate: () => `${BASE}/api/admin/advisers/import-template`
};

// ---------------------------------------------------------------------------
// Adviser endpoints
// ---------------------------------------------------------------------------
export const adviser = {
	/** Fetch all elections (adviser-scoped, no admin token needed) */
	getElections: () => request('/api/adviser/elections'),

	/** @param {string} [election_id] */
	getPartylists: (election_id) =>
		request(`/api/adviser/partylists${election_id ? `?election_id=${election_id}` : ''}`),

	/**
	 * @param {string} election_id
	 * @param {string} name
	 */
	createPartylist: (election_id, name) =>
		request(`/api/adviser/partylists?election_id=${election_id}`, json({ name })),

	/**
	 * @param {string} partylist_id
	 * @param {string} name
	 */
	updatePartylist: (partylist_id, name) =>
		request(`/api/adviser/partylists/${partylist_id}`, { ...json({ name }), method: 'PUT' }),

	/**
	 * @param {string} partylist_id
	 */
	deletePartylist: (partylist_id) =>
		request(`/api/adviser/partylists/${partylist_id}`, { method: 'DELETE' }),

	/** @param {string} [election_id] */
	getCandidates: (election_id) =>
		request(`/api/adviser/candidates${election_id ? `?election_id=${election_id}` : ''}`),

	/**
	 * @param {string} election_id
	 * @param {object} payload
	 */
	createCandidate: (election_id, payload) =>
		request(`/api/adviser/candidates?election_id=${election_id}`, json(payload)),

	/** @param {string} election_id */
	getLiveResults: (election_id) => request(`/api/adviser/live-results/${election_id}`),

	/** @param {string} candidate_id */
	deleteCandidate: (candidate_id) =>
		request(`/api/adviser/candidates/${candidate_id}`, { method: 'DELETE' }),

	/** @param {string} election_id */
	refreshPasscode: (election_id) =>
		request(`/api/adviser/elections/${election_id}/refresh-passcode`, { method: 'POST' }),

	/** @param {string} election_id */
	getPasscode: (election_id) => request(`/api/adviser/elections/${election_id}/passcode`),

	/**
	 * @param {string} candidate_id
	 * @param {string} photo_url - base64 data URL
	 */
	uploadCandidatePhoto: (candidate_id, photo_url) =>
		request(`/api/adviser/candidates/${candidate_id}/photo`, {
			...json({ photo_url }),
			method: 'PUT'
		}),

	/** @param {string} candidate_id */
	deleteCandidatePhoto: (candidate_id) =>
		request(`/api/adviser/candidates/${candidate_id}/photo`, { method: 'DELETE' }),

	/**
	 * @param {number} [page_size]
	 * @param {string | null} [page_token]
	 */
	getAuditLog: (page_size = 15, page_token = null) => {
		const params = new URLSearchParams({ page_size: String(page_size) });
		if (page_token) params.set('page_token', page_token);
		return request(`/api/adviser/audit-log?${params}`);
	},

	/**
	 * @param {{ current_password: string, new_password: string }} payload
	 */
	changePassword: (payload) =>
		request('/api/adviser/change-password', { ...json(payload), method: 'PUT' }),

	/**
	 * @param {string} election_id
	 * @param {string} pin  - exactly 6 digits
	 */
	setEntryPin: (election_id, pin) =>
		request(`/api/adviser/elections/${election_id}/set-entry-pin`, {
			...json({ election_id, pin }),
			method: 'POST'
		}),

	/** @param {string} election_id */
	getEntryPin: (election_id) => request(`/api/adviser/elections/${election_id}/entry-pin`),

	/** @param {string} query */
	searchStudents: (query) => request(`/api/adviser/students/search?query=${encodeURIComponent(query)}`),

	/** 
	 * Helper to get the absolute URL for a candidate's photo 
	 * @param {string} candidate_id
	 */
	getCandidatePhotoUrl: (candidate_id) => `${BASE}/api/common/candidates/${candidate_id}/photo`
};
