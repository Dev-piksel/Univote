<script>
	import { onMount } from 'svelte';
	import { admin, adviser } from '$lib/api.js';
	import { selectedElectionId } from '$lib/stores/election.js';
	import { branding } from '$lib/stores/branding.js';
	import { sortPositions, calculateWinners } from '$lib/constants.js';
	import { BASE } from '$lib/api.js';

	const SSE_BASE = `${BASE}/api/results/adviser/stream`;

	/** @type {any[]} */
	let elections = $state([]);
	/** @type {any[]} */
	let candidates = $state([]);
	/** @type {Record<string, any>} */
	let liveResults = $state({});
	let electionStatus = $state('');
	let sseConnected = $state(false);
	let lastUpdated = $state('');
	let isLoading = $state(false);

	/** @type {EventSource | null} */
	let eventSource = null;
	// Track the ID we are currently connected to so we don't reconnect on other state changes
	let connectedElectionId = '';

	async function loadElections() {
		try {
			const res = await adviser.getElections();
			elections = res.data || [];
		} catch (err) {
			console.error('Failed to load elections:', err);
		}
	}

	/** @param {string} electionId */
	async function loadData(electionId) {
		if (!electionId) return;
		isLoading = true;
		try {
			const [cRes, rRes] = await Promise.all([
				adviser.getCandidates(electionId),
				adviser.getLiveResults(electionId)
			]);
			candidates = cRes.data || [];
			const fetched = rRes.data || {};
			if (fetched.tallies) {
				liveResults = fetched.tallies;
				electionStatus = fetched.status;
			} else if (fetched.status === 'upcoming') {
				liveResults = {};
				electionStatus = fetched.status;
			} else {
				liveResults = fetched;
			}
			lastUpdated = new Date().toLocaleTimeString();
		} catch (err) {
			console.error('Failed to load data:', err);
		} finally {
			isLoading = false;
		}
	}

	function closeSSE() {
		if (eventSource) {
			eventSource.close();
			eventSource = null;
			sseConnected = false;
			connectedElectionId = '';
		}
	}

	/** @param {string} electionId */
	function openSSE(electionId) {
		if (connectedElectionId === electionId) return; // Already connected to this one
		closeSSE();

		connectedElectionId = electionId;
		eventSource = new EventSource(`${SSE_BASE}/${electionId}`);
		eventSource.onopen = () => {
			sseConnected = true;
		};
		eventSource.onmessage = (e) => {
			try {
				const payload = JSON.parse(e.data);
				if (payload.tallies) {
					liveResults = payload.tallies;
					electionStatus = payload.status;
				} else if (payload.status === 'upcoming') {
					liveResults = {};
					electionStatus = payload.status;
				} else {
					liveResults = payload;
				}
				sseConnected = true;
				lastUpdated = new Date().toLocaleTimeString();
			} catch (err) {
				console.error('SSE parse error:', err);
			}
		};
		eventSource.onerror = () => {
			sseConnected = false;
			console.warn('SSE connection lost, retrying...');
		};
	}

	onMount(() => {
		async function init() {
			await loadElections();
			// Note: $effect handles the initial connection once loadElections is done
		}
		init();
		return () => closeSSE();
	});

	$effect(() => {
		const id = $selectedElectionId;
		if (id && id !== connectedElectionId) {
			loadData(id);
			openSSE(id);
		} else if (!id) {
			closeSSE();
			liveResults = {};
		}
	});

	/** @type {string[]} */
	const positions = $derived(sortPositions(Object.keys(liveResults)));
	let isCompleted = $derived(electionStatus === 'completed');
	let winnersData = $derived(isCompleted ? calculateWinners(liveResults, candidates) : {});

	/** @param {string} candidateId */
	function getCandidateInfo(candidateId) {
		const c = candidates.find(/** @param {any} c */ (c) => c.id === candidateId);
		return {
			name: c?.students?.full_name || 'Unknown',
			party: c?.partylists?.name || 'Independent'
		};
	}

	/** @param {string} position */
	function getPositionResults(position) {
		const posVotes = liveResults[position] || {};
		const entries = Object.entries(posVotes).map(([candId, count]) => ({
			id: candId,
			...getCandidateInfo(candId),
			votes: Number(count)
		}));
		entries.sort((a, b) => b.votes - a.votes);
		const totalVotes = entries.reduce((sum, e) => sum + e.votes, 0);
		return { entries, totalVotes };
	}
</script>

<svelte:head><title>Results | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Live Results</p>
			<h1 class="dash-title">
				{elections.find((e) => e.id === $selectedElectionId)?.name || 'Live Results & Tally'}
			</h1>
		</div>
		<div style="display:flex;align-items:center;gap:1rem;">
			<!-- Live Indicator -->
			{#if $selectedElectionId}
				<div class="pill {sseConnected ? 'pill-success' : 'pill-warning'} pill-dot">
					{sseConnected
						? lastUpdated
							? `Live Feed: ${lastUpdated}`
							: 'Connected'
						: 'Connecting...'}
				</div>
			{/if}

			<!-- Election Selector -->
			<div style="display:flex;align-items:center;gap:0.75rem;">
				<label for="election-select" class="field-label" style="margin-bottom:0;line-height:1;"
					>Election</label
				>
				<select
					id="election-select"
					bind:value={$selectedElectionId}
					class="input-base btn-sm"
					style="min-width:200px; width:auto; max-width:450px;"
				>
					<option value="" disabled>Select Session</option>
					{#each elections as election}
						<option value={election.id}>{election.name}</option>
					{/each}
				</select>
			</div>
		</div>
	</div>

	{#if !$selectedElectionId}
		<div class="empty-state">
			<svg
				class="empty-state-icon"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				viewBox="0 0 24 24"
				><path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/></svg
			>
			<h3 class="empty-state-title">Select an Election</h3>
			<p class="empty-state-text">
				Choose an election session from the menu above to view its real-time results.
			</p>
		</div>
	{:else if isLoading}
		<div style="display:flex;flex-direction:column;gap:2rem;">
			<div class="bento-grid bento-2col">
				{#each [1, 2, 3, 4] as i}
					<div class="admin-card skeleton" style="height:250px;opacity:0.5;"></div>
				{/each}
			</div>
		</div>
	{:else if electionStatus === 'upcoming'}
		<div class="empty-state">
			<svg
				class="empty-state-icon"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				viewBox="0 0 24 24"
				><path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
				/></svg
			>
			<h3 class="empty-state-title">Election Not Started</h3>
			<p class="empty-state-text">
				Live results for this election will be available once the voting period officially begins.
			</p>
		</div>
	{:else if positions.length === 0}
		<div class="empty-state">
			<svg
				class="empty-state-icon"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				viewBox="0 0 24 24"
				><path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
				/></svg
			>
			<h3 class="empty-state-title">No Votes Recorded</h3>
			<p class="empty-state-text">
				Live cryptographic tallies will appear here automatically once voters begin submitting their
				ballots.
			</p>
		</div>
	{:else}
		<div style="display:flex;flex-direction:column;gap:2rem;">
			<!-- Certified Winners (if completed) -->
			{#if isCompleted}
				<div>
					<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
						<div class="pill pill-success pill-dot" style="font-size:0.8125rem;">
							Election Certified
						</div>
						<h2 style="font-size:1rem;font-weight:700;color:var(--text-main);">Official Winners</h2>
					</div>
					<div class="bento-grid bento-3col">
						{#each positions as position}
							{#if winnersData[position] && winnersData[position].length > 0}
								<div
									class="admin-card relative overflow-hidden"
									style="padding:1.5rem;display:flex;flex-direction:column;align-items:center;text-align:center;border: 1px solid #10B981;box-shadow: 0 0 16px rgba(16,185,129,0.15), inset 0 0 24px rgba(16,185,129,0.05);"
								>
									<div
										class="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-transparent via-[#10B981] to-transparent opacity-70"
									></div>

									<div class="absolute top-4 right-4 text-[#10B981]">
										<svg
											class="h-6 w-6 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]"
											fill="currentColor"
											viewBox="0 0 24 24"
											><path
												d="M12 2l2.4 7.4h7.6l-6.2 4.5 2.4 7.4-6.2-4.5-6.2 4.5 2.4-7.4-6.2-4.5h7.6z"
											/></svg
										>
									</div>

									<p class="section-label" style="margin-bottom:1rem;">{position} WINNER</p>
									{#each winnersData[position] as winner}
										<div
											class="avatar-initial"
											style="width:64px;height:64px;border-radius:12px;font-size:1.5rem;margin-bottom:0.75rem;color:#10B981;background:rgba(16,185,129,0.1);border-color:transparent;box-shadow: 0 0 12px rgba(16,185,129,0.2);"
										>
											{winner.students?.full_name?.charAt(0) || '?'}
										</div>
										<h3
											style="font-size:1rem;font-weight:900;color:var(--text-main);drop-shadow(0 2px 4px rgba(0,0,0,0.5))"
										>
											{winner.students?.full_name || 'Unknown'}
										</h3>
										<p
											style="font-size:0.6875rem;color:var(--text-muted);margin-top:0.25rem;font-weight:700;"
										>
											{winner.partylists?.name || 'Independent'}
										</p>
										<div
											class="pill pill-success"
											style="margin-top:0.75rem;box-shadow: 0 0 8px rgba(16,185,129,0.3);"
										>
											{(liveResults[position] || {})[winner.id] || 0} Votes Certified
										</div>
									{/each}
								</div>
							{/if}
						{/each}
					</div>
				</div>
				<hr />
			{/if}

			<!-- Detailed Tally -->
			<div>
				<h2 style="font-size:1rem;font-weight:700;color:var(--text-main);margin-bottom:1rem;">
					Detailed Tally Returns
				</h2>

				<div class="bento-grid bento-2col">
					{#each positions as position, idx}
						{@const { entries, totalVotes } = getPositionResults(position)}
						<div class="admin-card" style="padding:1.5rem;">
							<!-- Header -->
							<div
								style="display:flex;align-items:flex-start;justify-content:space-between;border-bottom:1px solid var(--border-main);padding-bottom:1rem;margin-bottom:1.25rem;"
							>
								<div style="display:flex;align-items:center;gap:0.75rem;">
									<div
										class="avatar-initial"
										style="width:24px;height:24px;border-radius:6px;font-size:0.6875rem;"
									>
										{idx + 1}
									</div>
									<h2 style="font-size:0.875rem;font-weight:700;color:var(--text-main);">
										{position}
									</h2>
								</div>
								<div style="text-align:right;">
									<span class="section-label">{totalVotes} Total Votes</span>
								</div>
							</div>

							<!-- Bars -->
							<div style="display:flex;flex-direction:column;gap:1.25rem;">
								{#each entries as candidate, ci}
									{@const pct =
										totalVotes > 0 ? Math.round((candidate.votes / totalVotes) * 100) : 0}
									{@const isLeading = ci === 0 && candidate.votes > 0}
									<div>
										<div
											style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;"
										>
											<div style="display:flex;align-items:center;gap:0.75rem;">
												<div
													class="avatar-initial"
													style="width:28px;height:28px;border-radius:6px;font-size:0.6875rem;{isLeading
														? 'background-color:var(--status-success-bg);color:var(--status-success-fg);border-color:var(--status-success-bg);'
														: ''}"
												>
													{candidate.name.charAt(0)}
												</div>
												<div>
													<p
														style="font-size:0.8125rem;font-weight:700;color:var(--text-main);line-height:1.2;"
													>
														{candidate.name}
													</p>
													<p
														style="font-size:0.6875rem;color:var(--text-muted);margin-top:0.125rem;"
													>
														{candidate.party}
													</p>
												</div>
											</div>
											<div style="text-align:right;">
												<span
													style="display:block;font-size:0.875rem;font-weight:700;color:var(--text-main);line-height:1.2;"
													>{candidate.votes}</span
												>
												<span
													style="display:block;font-size:0.6875rem;color:var(--text-subtle);margin-top:0.125rem;"
													>{pct}%</span
												>
											</div>
										</div>

										<!-- Progress Bar -->
										<div
											style="height:6px;background-color:var(--border-subtle);border-radius:3px;overflow:hidden;"
										>
											<div
												style="height:100%;border-radius:3px;background-color:{isLeading
													? 'var(--status-success-fg)'
													: 'var(--text-muted)'};width:{pct}%;transition:width 1s ease-out;"
											></div>
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>
