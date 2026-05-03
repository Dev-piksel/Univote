import { writable } from 'svelte/store';

const SESSION_KEY = 'univote_voter_session';

/**
 * @typedef {Object} StudentSession
 * @property {string} id - Database UUID
 * @property {string} student_id - Human readable ID
 * @property {string} full_name
 * @property {string} access_token - JWT for voting
 * @property {string} program
 * @property {number} year_level
 * @property {string} [photo_url] - Student profile picture (base64)
 * @property {Array<{id: string, name: string, has_voted: boolean, status: string, start_date?: string, end_date?: string}>} [elections]
 */

/**
 * @typedef {Object} VoterSessionStore
 * @property {(this: void, run: import('svelte/store').Subscriber<StudentSession | null>, invalidate?: (() => void) | undefined) => import('svelte/store').Unsubscriber} subscribe
 * @property {(data: any) => void} login
 * @property {(electionId: string) => void} markVoted
 * @property {(fn: (session: StudentSession | null) => StudentSession | null) => void} update
 * @property {() => void} logout
 * @property {(studentId: string) => Promise<any>} sync
 * @property {(electionId: string) => string} getElectionStatus
 */

function createSessionStore() {
	/** @type {StudentSession | null} */
	let initial = null;
	try {
		const stored = typeof window !== 'undefined' ? localStorage.getItem(SESSION_KEY) : null;
		initial = stored && stored !== 'undefined' ? JSON.parse(stored) : null;
	} catch {
		initial = null;
	}

	const { subscribe, set, update } = writable(initial);

	return {
		subscribe,
		/** @param {any} data */
		login(data) {
			const student = data.student || data;
			const flattened = {
				access_token: data.access_token || student.access_token,
				student_id: student.student_id,
				full_name: student.full_name,
				id: student.id,
				program: student.program,
				year_level: student.year_level,
				photo_url: student.photo_url || null,
				elections: data.active_elections || data.elections || []
			};
			if (typeof window !== 'undefined') {
				localStorage.setItem(SESSION_KEY, JSON.stringify(flattened));
			}
			set(flattened);
		},
		/** Mark a specific election as voted in the session */
		/** @param {string} electionId */
		markVoted(electionId) {
			update((session) => {
				if (!session) return session;
				const updated = {
					...session,
					elections: (session.elections || []).map((e) =>
						e.id === electionId ? { ...e, has_voted: true } : e
					)
				};
				if (typeof window !== 'undefined') {
					localStorage.setItem(SESSION_KEY, JSON.stringify(updated));
				}
				return updated;
			});
		},
		/** @param {(session: StudentSession | null) => StudentSession | null} fn */
		update(fn) {
			update((session) => {
				const next = fn(session);
				if (typeof window !== 'undefined' && next) {
					localStorage.setItem(SESSION_KEY, JSON.stringify(next));
				}
				return next;
			});
		},
		logout() {
			if (typeof window !== 'undefined') {
				localStorage.removeItem(SESSION_KEY);
			}
			set(null);
		},
		/** @param {string} studentId */
		async sync(studentId) {
			try {
				const { student: studentApi } = await import('$lib/api.js');
				const data = await studentApi.validate(studentId);
				// data looks like { student: {...}, active_elections: [...], access_token: "..." }
				this.login(data);
				return data;
			} catch (err) {
				console.error('Session sync failed:', err);
				throw err;
			}
		},
		/** @param {string} electionId */
		getElectionStatus(electionId) {
			let status = 'unknown';
			subscribe((session) => {
				if (!session || !session.elections) return;
				const e = session.elections.find((el) => el.id === electionId);
				if (e) status = e.status;
			})();
			return status;
		}
	};
}


/** @type {VoterSessionStore} */
export const voterSession = createSessionStore();
