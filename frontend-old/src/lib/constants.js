export const POSITION_ORDER = [
	'President',
	'Vice President',
	'Secretary',
	'Treasurer',
	'Auditor',
	'Public Information Officer (PIO)',
	'Protocol Officer'
];

/**
 * Helper to sort positions based on the predefined order.
 * @param {string[]} positions
 * @returns {string[]}
 */
export function sortPositions(positions) {
	return [...positions].sort((a, b) => {
		const indexA = POSITION_ORDER.indexOf(a);
		const indexB = POSITION_ORDER.indexOf(b);

		if (indexA === -1 && indexB === -1) return a.localeCompare(b);
		if (indexA === -1) return 1;
		if (indexB === -1) return -1;

		return indexA - indexB;
	});
}

/**
 * Helper to calculate winners for each position from the raw results.
 * Returns an object mapping positions to arrays of winning candidate objects.
 * Handles exactly matching ties automatically.
 * @param {Record<string, Record<string, number>>} results
 * @param {any[]} candidates
 * @returns {Record<string, any[]>}
 */
export function calculateWinners(results, candidates) {
	if (!results || !candidates || candidates.length === 0) return {};
	/** @type {Record<string, any[]>} */
	const winners = {};

	Object.keys(results).forEach((position) => {
		const positionCandidates = candidates.filter((c) => c.position === position);
		if (positionCandidates.length === 0) return;

		let maxVotes = 0;
		positionCandidates.forEach((c) => {
			const votes = Number(results[position][c.id]) || 0;
			if (votes > maxVotes) maxVotes = votes;
		});

		if (maxVotes > 0) {
			winners[position] = positionCandidates.filter(
				(c) => (Number(results[position][c.id]) || 0) === maxVotes
			);
		}
	});

	return winners;
}
