<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { page } from '$app/state';
	import { fade, fly, scale } from 'svelte/transition';
	import { sortPositions, calculateWinners } from '$lib/constants.js';
	import { BASE } from '$lib/api.js';

	const SSE_BASE = `${BASE}/api/results/adviser/stream`;

	let isLoading = $state(true);
	/** @type {Record<string, Record<string, number>>} */
	let results = $state({});
	/** @type {any[]} */
	let candidates = $state([]);
	let electionId = $state('');
	let lastUpdated = $state('');
	let statusMessage = $state('');
	let currentTime = $state(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));

	/** @type {any[]} */
	let availableElections = $state([]);
	/** @type {EventSource | null} */
	let eventSource = null;

	const positions = $derived(sortPositions(Object.keys(results)));
	const winnersData = $derived(calculateWinners(results, candidates));

	onMount(() => {
		const session = $voterSession;
		if (!session) {
			goto('/student/validate');
			return;
		}
		availableElections = session.elections || [];

		const urlId = page.url.searchParams.get('election');
		const defaultId = session.elections?.[0]?.id ?? '';
		const targetId = urlId || defaultId;

		if (targetId) {
			// If we already have results for this ID, don't show full loader
			if (Object.keys(results).length > 0 && targetId === electionId) {
				isLoading = false;
			}
			loadResults(targetId);
		} else {
			isLoading = false;
		}

		const timer = setInterval(() => {
			currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		}, 60000);

		return () => {
			closeSSE();
			clearInterval(timer);
		};
	});

	function closeSSE() {
		if (eventSource) {
			eventSource.close();
			eventSource = null;
		}
	}

	/** @param {string} targetId */
	function openSSE(targetId) {
		closeSSE();
		eventSource = new EventSource(`${SSE_BASE}/${targetId}`);
		eventSource.onmessage = (e) => {
			try {
				const payload = JSON.parse(e.data);
				if (payload.tallies) {
					results = payload.tallies;
				} else {
					results = payload;
				}
				lastUpdated = new Date().toLocaleTimeString();
			} catch (err) {
				console.error('SSE parse error:', err);
			}
		};
	}

	/** @param {string} targetId */
	async function loadResults(targetId) {
		if (!targetId) return;
		electionId = targetId;
		try {
			const [resData, candData] = await Promise.all([
				studentApi.getResults(targetId),
				studentApi.getCandidates(targetId)
			]);
			const fetched = resData.data || {};
			results = fetched.tallies || fetched;
			statusMessage = fetched.message || '';
			candidates = candData.data || [];
			lastUpdated = new Date().toLocaleTimeString();
		} catch (err) {
			console.error('Failed to load results:', err);
		} finally {
			isLoading = false;
			openSSE(targetId);
		}
	}

	/** @param {any} e */
	function handleElectionChange(e) {
		const newId = e.target.value;
		if (!newId) return;
		isLoading = true;
		loadResults(newId);
	}

	/** @param {string} position */
	function getPositionResults(position) {
		const posVotes = results[position] || {};
		const entries = Object.entries(posVotes).map(([candId, count]) => {
			const c = candidates.find((can) => can.id === candId);
			return {
				id: candId,
				name: c?.students?.full_name || 'Unknown',
				party: c?.partylists?.name || 'Independent',
				votes: Number(count)
			};
		});
		entries.sort((a, b) => b.votes - a.votes);
		const totalVotes = entries.reduce((sum, e) => sum + e.votes, 0);
		return { entries, totalVotes };
	}

	/** @param {string} name */
	function getMonogram(name) {
		if (!name) return '??';
		return name
			.split(' ')
			.slice(0, 2)
			.map((w) => w[0]?.toUpperCase())
			.join('');
	}
</script>

<svelte:head><title>Election Results | {$branding.appName}</title></svelte:head>

<div class="results-container">
	<div class="page-header">
		<div class="breadcrumb">PAGES / ELECTION RESULTS</div>
		
		<div class="header-row">
			<h1 class="page-title">Election Outcomes</h1>
			
			<div class="header-pills">
				<div class="session-pill">
					<span class="s-label">Session</span>
					<select bind:value={electionId} onchange={handleElectionChange} aria-label="Select Election Session">
						{#each availableElections as e}
							<option value={e.id}>{e.name}</option>
						{/each}
					</select>
				</div>

				<div class="live-pill">
					<div class="live-indicator"></div>
					<span class="live-time">{currentTime.toLowerCase()}</span>
				</div>
			</div>
		</div>
	</div>

	{#if isLoading}
		<div class="loader-area">
			<div class="spinner"></div>
			<p>Syncing Cryptographic Data…</p>
		</div>
	{:else if electionId && (positions.length === 0 || statusMessage)}
		<div class="empty-results-hero" in:scale={{ start: 0.95, duration: 400 }}>
			<div class="hero-icon-ring" style="color: {statusMessage ? 'var(--amber)' : 'var(--accent)'};">
				{#if statusMessage}
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
				{:else}
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
				{/if}
			</div>
			<h2 class="hero-title">{statusMessage ? 'Access Restricted' : 'Awaiting Live Feed'}</h2>
			<p class="hero-body">{statusMessage || 'Cryptographic tallies will appear here automatically as verifyable ballots are submitted. No data available for this session yet.'}</p>
		</div>
	{:else if !electionId}
		<div class="empty-results-hero" in:scale={{ start: 0.95, duration: 400 }}>
			<div class="hero-icon-ring">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
			</div>
			<h2 class="hero-title">Select Session</h2>
			<p class="hero-body">Please designate an active election session from the dropdown above to engage the live results monitor.</p>
		</div>
	{:else}
		<div class="results-grid">
			{#each positions as position, idx}
				{@const { entries, totalVotes } = getPositionResults(position)}
				{@const positionWinners = winnersData[position] || []}
				<div class="result-card" in:fade={{ duration: 300, delay: idx * 80 }}>
					<div class="card-header">
						<div class="header-left">
							<div class="pos-num">{idx + 1}</div>
							<h3 class="pos-title">{position}</h3>
						</div>
						<div class="total-pill">{totalVotes} total votes</div>
					</div>

					<div class="candidates-list">
						{#each entries as cand}
							{@const pct = totalVotes > 0 ? Math.round((cand.votes / totalVotes) * 100) : 0}
							{@const isWinner = positionWinners.some(w => w.id === cand.id)}
							<div class="cand-row">
								<div class="cand-info">
									<div class="cand-avatar" class:winner={isWinner}>
										{getMonogram(cand.name)}
									</div>
									<div class="cand-text">
										<div class="cand-name">{cand.name}</div>
										<div class="cand-party">{cand.party}</div>
									</div>
									<div class="cand-stats">
										<span class="v-count">{cand.votes}</span>
										<span class="v-perc">{pct}%</span>
										{#if isWinner}
											<span class="winner-crown">👑</span>
										{/if}
									</div>
								</div>
								<div class="progress-container">
									<div class="progress-bar" class:winner={isWinner} style="width: {pct}%"></div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.results-container { width: 100%; max-width: 1600px; padding-bottom: 60px; text-align: left; }
	.page-header { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; margin-bottom: 40px; width: 100%; }
	.header-row { display: flex; align-items: center; justify-content: flex-start; gap: 40px; flex-wrap: wrap; width: 100%; }
	.header-pills { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
	
	.breadcrumb { font-size: 10px; font-weight: 800; color: var(--accent); letter-spacing: 1.5px; opacity: 0.8; text-transform: uppercase; }
	.page-title { font-size: 42px; font-weight: 800; color: var(--text); letter-spacing: -2px; white-space: nowrap; margin: 0; }
	@media (max-width: 768px) {
		.page-title { font-size: 32px; white-space: normal; }
	}
	
	.session-pill { display: flex; align-items: center; gap: 10px; background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 6px 14px; width: fit-content; flex-shrink: 0; }
	.s-label { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
	.session-pill select { border: none; background: transparent; font-size: 13px; font-weight: 800; color: var(--text2); outline: none; cursor: pointer; padding-right: 8px; }

	.live-pill { background: var(--green-bg); border: 1px solid rgba(16, 185, 129, 0.2); padding: 7px 16px; border-radius: 20px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
	.live-indicator { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
	@keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.4); } 100% { opacity: 1; transform: scale(1); } }
	.live-time { font-size: 13px; font-weight: 800; color: var(--status-success-fg); }

	/* EMPTY HERO */
	.empty-results-hero { background: var(--surface); border: 1.5px solid var(--border); border-radius: 32px; padding: 100px 40px; text-align: center; max-width: 600px; margin-top: 40px; }
	.hero-icon-ring { width: 80px; height: 80px; border-radius: 50%; background: var(--accent-bg); color: var(--accent); border: 1px solid rgba(92, 96, 245, 0.2); display: grid; place-items: center; margin: 0 auto 32px; }
	.hero-icon-ring svg { width: 32px; height: 32px; }
	.hero-title { font-size: 28px; font-weight: 800; color: var(--text); margin-bottom: 16px; letter-spacing: -1px; }
	.hero-body { font-size: 15px; color: var(--muted); line-height: 1.7; margin: 0 auto; max-width: 440px; }

	.loader-area { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 100px 0; gap: 1rem; color: var(--muted); }
	.spinner { width: 40px; height: 40px; border: 3px solid var(--surface2); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }

	.results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 24px; }
	@media (max-width: 768px) {
		.results-grid { grid-template-columns: 1fr; }
	}
	.result-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: 32px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); transition: all 0.2s; }
	.result-card:hover { border-color: var(--accent); transform: translateY(-4.5px); }
	.card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 32px; }
	.header-left { display: flex; align-items: center; gap: 16px; }
	.pos-num { width: 36px; height: 36px; border-radius: 10px; background: var(--bg); border: 1px solid var(--border); display: grid; place-items: center; font-size: 14px; font-weight: 800; color: var(--muted); }
	.pos-title { font-size: 22px; font-weight: 800; color: var(--text); font-family: 'Syne', sans-serif; letter-spacing: -0.5px; }
	.total-pill { font-size: 11px; font-weight: 700; color: var(--muted); background: var(--bg); padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); text-transform: uppercase; letter-spacing: 0.5px; }

	.candidates-list { display: flex; flex-direction: column; gap: 20px; }
	.cand-row { display: flex; flex-direction: column; gap: 8px; }
	.cand-info { display: flex; align-items: center; gap: 14px; }
	.cand-avatar { width: 44px; height: 44px; border-radius: 50%; background: #475569; color: white; display: grid; place-items: center; font-size: 14px; font-weight: 800; flex-shrink: 0; }
	.cand-avatar.winner { background: var(--brand-primary, var(--accent)); }
	.cand-text { flex: 1; min-width: 0; }
	.cand-name { font-size: 16px; font-weight: 800; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.cand-party { font-size: 10px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }

	.cand-stats { display: flex; align-items: center; gap: 8px; }
	.v-count { font-size: 18px; font-weight: 900; color: var(--text); }
	.v-perc { font-size: 11px; font-weight: 700; color: var(--muted); }
	.winner-crown { font-size: 16px; margin-left: 4px; }

	.progress-container { width: 100%; height: 6px; background: var(--bg); border-radius: 10px; overflow: hidden; }
	.progress-bar { height: 100%; border-radius: 10px; background: #94a3b8; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }
	.progress-bar.winner { background: var(--brand-primary, var(--accent)); }


	@media (max-width: 768px) {
		.results-grid { grid-template-columns: 1fr; }
		.page-header { gap: 12px; }
		.page-title { font-size: 28px; }
		.session-pill select { font-size: 11px; }
		.result-card { padding: 20px; }
	}
</style>
