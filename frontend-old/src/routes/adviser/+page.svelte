<script>
	import { onMount } from 'svelte';
	import { admin, adviser } from '$lib/api.js';
	import { selectedElectionId } from '$lib/stores/election.js';
	import { authSession } from '$lib/stores/auth.js';
	import { branding } from '$lib/stores/branding.js';
	import GlassCard from '$lib/components/GlassCard.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import { goto } from '$app/navigation';

	/** @type {any[]} */
	let elections = $state([]);
	let summary = $state({ 
		candidates: 0, 
		partylists: 0, 
		totalVotes: 0, 
		votedCount: 0, 
		notVotedCount: 0, 
		totalVoters: 0,
		turnoutPercentage: 0,
		lastVoteAt: null
	});
	let isRefreshing = $state(false);
	let activePasscode = $state({ code: '—', expires_at: null });
	let entryPin = $state('');
	let entryPinInput = $state('');
	let isSavingPin = $state(false);
	let pinMsg = $state('');

	async function loadSummary() {
		if (!$selectedElectionId) return;
		try {
			const [pRes, cRes, lRes, passRes] = await Promise.all([
				adviser.getPartylists($selectedElectionId),
				adviser.getCandidates($selectedElectionId),
				adviser.getLiveResults($selectedElectionId),
				adviser.getPasscode($selectedElectionId)
			]);
			const res = lRes.data || {};
			// Handle both {tallies: ...} and direct tallies
			const liveResults = res.tallies || res;
			let voteCount = 0;
			Object.values(liveResults).forEach((posVotes) => {
				if (typeof posVotes === 'object' && posVotes !== null) {
					Object.values(posVotes).forEach((count) => {
						voteCount += Number(count);
					});
				}
			});
			summary = {
				partylists: (pRes.data || []).length,
				candidates: (cRes.data || []).length,
				totalVotes: voteCount,
				votedCount: res.voted_count || 0,
				notVotedCount: res.not_voted_count || 0,
				totalVoters: res.total_voters || 0,
				turnoutPercentage: res.turnout_percentage || 0,
				lastVoteAt: res.last_vote_at
			};

			const pData = passRes.data;
			activePasscode = pData
				? { code: pData.passcode, expires_at: pData.expires_at }
				: { code: '—', expires_at: null };

			// Load entry PIN
			try {
				const pinRes = await adviser.getEntryPin($selectedElectionId);
				entryPin = pinRes.entry_pin || '';
				entryPinInput = entryPin;
			} catch { /* ignore */ }
		} catch (err) {
			console.error('Failed to load dashboard summary:', err);
		}
	}

	async function loadElections() {
		try {
			const res = await adviser.getElections();
			elections = res.data || [];
			if (elections.length > 0 && !$selectedElectionId) {
				$selectedElectionId = elections[0].id;
			}
		} catch (err) {
			console.error('Failed to load elections:', err);
		}
	}

	async function refreshPasscode() {
		if (!$selectedElectionId) return;
		isRefreshing = true;
		try {
			const res = await adviser.refreshPasscode($selectedElectionId);
			activePasscode = { code: res.adviser_passcode, expires_at: res.expires_at };
		} catch (err) {
			console.error('Failed to refresh passcode:', err);
		} finally {
			isRefreshing = false;
		}
	}

	async function saveEntryPin() {
		if (!$selectedElectionId) return;
		if (!/^\d{6}$/.test(entryPinInput)) {
			pinMsg = 'Must be exactly 6 digits.';
			setTimeout(() => (pinMsg = ''), 2500);
			return;
		}
		isSavingPin = true;
		try {
			await adviser.setEntryPin($selectedElectionId, entryPinInput);
			entryPin = entryPinInput;
			pinMsg = 'PIN saved!';
			setTimeout(() => (pinMsg = ''), 2500);
		} catch (err) {
			console.error('Failed to save PIN:', err);
			pinMsg = 'Failed to save.';
			setTimeout(() => (pinMsg = ''), 2500);
		} finally {
			isSavingPin = false;
		}
	}

	async function checkPasscode() {
		if (!$selectedElectionId) return;
		try {
			const passRes = await adviser.getPasscode($selectedElectionId);
			const pData = passRes.data;
			if (pData) {
				activePasscode = { code: pData.passcode, expires_at: pData.expires_at };
			}
		} catch (err) {
			console.error('Failed to poll passcode:', err);
		}
	}

	onMount(() => {
		loadElections().then(() => {
			if ($selectedElectionId) loadSummary();
		});

		// Auto-refresh passcode every 30s to catch auto-regenerations
		const interval = setInterval(() => {
			if ($selectedElectionId) checkPasscode();
		}, 30000);

		return () => clearInterval(interval);
	});

	$effect(() => {
		if ($selectedElectionId) {
			loadSummary();
		}
	});

	const currentElection = $derived(elections.find((e) => e.id === $selectedElectionId));

	const navCards = [
		{
			name: 'Candidates',
			path: '/adviser/candidates',
			desc: 'Manage election participants',
			icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
		},
		{
			name: 'Partylists',
			path: '/adviser/partylists',
			desc: 'Manage political organizations',
			icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'
		},
		{
			name: 'Results',
			path: '/adviser/results',
			desc: 'Monitor live ballot tallies',
			icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
		},
		{
			name: 'Audit Logs',
			path: '/adviser/audit',
			desc: 'Review administrative actions',
			icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'
		}
	];
</script>

<svelte:head><title>Adviser Dashboard | {$branding.appName}</title></svelte:head>

<div class="dash">
	<!-- ── PAGE HEADER ── -->
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Adviser Dashboard</p>
			<h1 class="dash-title">Dashboard</h1>
		</div>
		<div style="display:flex;align-items:center;gap:0.5rem;">
			<label
				class="field-label"
				for="election-select"
				style="margin-bottom:0;color:var(--text-subtle);font-weight:600;font-size:0.75rem;text-transform:uppercase;"
				>Context:</label
			>
			<select id="election-select" bind:value={$selectedElectionId} class="dash-select">
				<option value="" disabled>Select election</option>
				{#each elections as election}
					<option value={election.id}>{election.name}</option>
				{/each}
			</select>
		</div>
	</div>

	<!-- ── TOP KPI CARDS ── -->
	<div class="kpi-row">
		<!-- Candidates Card -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Candidates</p>
					<p class="kpi-num">{summary.candidates}</p>
					<p class="kpi-delta" style="color:var(--brand-primary);"><span>●</span> Approved</p>
				</div>
				<div class="kpi-icon-box" style="background:linear-gradient(135deg,#00D2FF,#0B75FE);">
					<svg
						style="width:20px;height:20px;color:#fff;"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
						/></svg
					>
				</div>
			</div>
			<!-- Mini sparkline bars -->
			<div class="kpi-sparkbars">
				{#each [2, 3, 4, 4, 5, 7, summary.candidates || 1] as v}
					<div
						class="spark-bar"
						style="height:{Math.round(
							(v / Math.max(summary.candidates + 2, 10)) * 100
						)}%;background:#00D2FF;"
					></div>
				{/each}
			</div>
			<button class="kpi-sub-btn" onclick={() => goto('/adviser/candidates')}>Manage candidates →</button>
		</div>

		<!-- Partylists Card -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Partylists</p>
					<p class="kpi-num">{summary.partylists}</p>
					<p class="kpi-delta" style="color:#68d391;"><span>▲</span> Registered</p>
				</div>
				<div class="kpi-icon-box" style="background:var(--brand-gradient);">
					<svg
						style="width:20px;height:20px;color:#fff;"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
						/></svg
					>
				</div>
			</div>
			<div class="kpi-sparkbars">
				{#each [1, 2, 1, 3, 2, 4, summary.partylists || 1] as v}
					<div
						class="spark-bar"
						style="height:{Math.round(
							(v / Math.max(summary.partylists + 2, 6)) * 100
						)}%;background:#0B75FE;"
					></div>
				{/each}
			</div>
			<button class="kpi-sub-btn" onclick={() => goto('/adviser/partylists')}>Manage partylists →</button>
		</div>

		<!-- Voted Card -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Voted Students</p>
					<p class="kpi-num">{summary.votedCount.toLocaleString()}</p>
					<p class="kpi-delta" style="color:#68d391;"><span>▲</span> {summary.turnoutPercentage}% Turnout</p>
				</div>
				<div class="kpi-icon-box" style="background:linear-gradient(135deg,#11998e,#38ef7d);">
					<svg
						style="width:20px;height:20px;color:#fff;"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
						/></svg
					>
				</div>
			</div>
			<div class="kpi-sparkbars">
				{#each [2, 5, 8, 12, 10, 15, summary.votedCount || 1] as v}
					<div
						class="spark-bar"
						style="height:{Math.round(
							(v / Math.max(summary.totalVoters, 20)) * 100
						)}%;background:#76e4f7;"
					></div>
				{/each}
			</div>
			<button class="kpi-sub-btn" onclick={() => goto('/adviser/results')}>View participation →</button>
		</div>

		<!-- Not Voted Card -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Pending</p>
					<p class="kpi-num">{summary.notVotedCount.toLocaleString()}</p>
					<p class="kpi-delta" style="color:var(--status-warning-fg);"><span>●</span> Not Yet Voted</p>
				</div>
				<div class="kpi-icon-box" style="background:linear-gradient(135deg,#f093fb,#f5576c);">
					<svg
						style="width:20px;height:20px;color:#fff;"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
						/></svg
					>
				</div>
			</div>
			<div class="kpi-sparkbars">
				{#each [20, 18, 15, 12, 10, 8, summary.notVotedCount || 1] as v}
					<div
						class="spark-bar"
						style="height:{Math.round(
							(v / Math.max(summary.totalVoters, 20)) * 100
						)}%;background:#f5576c;"
					></div>
				{/each}
			</div>
			<p class="kpi-sub" style="color:var(--text-subtle); display:flex; justify-content:space-between;">
				<span>Total registered: {summary.totalVoters}</span>
				{#if summary.lastVoteAt}
					<span style="color:var(--brand-primary);">Last activity: {new Date(summary.lastVoteAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
				{/if}
			</p>
		</div>
	</div>

	<div class="mid-row">
		<div class="mid-left-col">
		<!-- Passcode Panel -->
		<div class="dash-card passcode-card">
			{#if currentElection}
				<div style="display:flex;flex-direction:column;gap:1rem;">
					<!-- Title -->
					<div style="display:flex;align-items:center;gap:0.75rem;">
						<div style="width:36px;height:36px;background:linear-gradient(135deg,rgba(0,210,255,0.15),rgba(11,117,254,0.15));color:var(--brand-primary);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
							<svg style="width:18px;height:18px;" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
								><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg
							>
						</div>
						<div>
							<p class="card-title" style="margin-bottom:0.1rem;">Voting Access Controls</p>
							<p style="font-size:0.75rem;color:var(--text-subtle);margin:0;">Manage entry PIN and session passcode for <strong>{currentElection.name}</strong>.</p>
						</div>
					</div>

					<!-- Two panels side by side -->
					<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.875rem;">

						<!-- Panel 1: Adviser Entry PIN (6-digit, adviser sets) -->
						<div style="background:var(--bg-elevated);border-radius:12px;padding:1rem;border:1px solid var(--border-main);display:flex;flex-direction:column;gap:0.75rem;">
							<div>
								<p style="font-size:0.6875rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-subtle);margin:0 0 0.2rem;">🔑 Entry PIN</p>
								<p style="font-size:0.7rem;color:var(--text-subtle);margin:0;">6-digit PIN you choose. Shared with students before they can access the voting page.</p>
							</div>
							{#if entryPin}
								<code style="font-size:1.5rem;font-weight:900;color:var(--brand-primary);letter-spacing:0.25em;display:block;text-align:center;padding:0.5rem 0;">{entryPin}</code>
							{/if}
							<div style="display:flex;gap:0.5rem;align-items:center;">
								<input
									type="text"
									inputmode="numeric"
									maxlength="6"
									placeholder="000000"
									bind:value={entryPinInput}
									style="flex:1;background:var(--bg-card);border:1.5px solid var(--border-main);border-radius:8px;padding:0.5rem 0.75rem;color:var(--text-main);font-family:monospace;font-size:1rem;font-weight:700;letter-spacing:0.18em;text-align:center;outline:none;"
								/>
								<button
									onclick={saveEntryPin}
									disabled={isSavingPin}
									class="btn-primary"
									style="padding:0.5rem 0.75rem;font-size:0.75rem;white-space:nowrap;"
								>Set PIN</button>
							</div>
							{#if pinMsg}
								<p style="font-size:0.7rem;font-weight:600;color:{pinMsg === 'PIN saved!' ? 'var(--status-success-fg)' : 'var(--status-danger-fg)'};margin:0;">{pinMsg}</p>
							{/if}
						</div>

						<!-- Panel 2: Session Passcode (8-char auto-generated) -->
						<div style="background:var(--bg-elevated);border-radius:12px;padding:1rem;border:1px solid var(--border-main);display:flex;flex-direction:column;gap:0.75rem;">
							<div>
								<p style="font-size:0.6875rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-subtle);margin:0 0 0.2rem;">🎲 Session Passcode</p>
								<p style="font-size:0.7rem;color:var(--text-subtle);margin:0;">8-char code auto-generated per adviser. Students enter this before casting their vote.</p>
							</div>
							<code style="font-size:1.25rem;font-weight:900;color:var(--brand-primary);letter-spacing:0.2em;display:block;text-align:center;padding:0.5rem 0;">{activePasscode.code}</code>
							{#if activePasscode.expires_at}
								<p style="font-size:0.6875rem;color:var(--status-warning-fg);font-weight:600;margin:0;text-align:center;">Expires {new Date(activePasscode.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
							{/if}
							<button
								onclick={refreshPasscode}
								disabled={isRefreshing}
								class="btn-primary"
								style="font-size:0.75rem;white-space:nowrap;"
							>
								{isRefreshing ? 'Generating…' : '↻ Generate New Passcode'}
							</button>
						</div>
					</div>
				</div>
			{:else}
				<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem;color:var(--text-subtle);">
					<p>Please select an active election to manage passcodes.</p>
				</div>
			{/if}
		</div>

		<!-- Election Details Card -->
		{#if currentElection}
			<div class="dash-card election-info-card">
				<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
					<div style="width:36px;height:36px;background:linear-gradient(135deg,rgba(104,211,145,0.15),rgba(56,239,125,0.1));color:#68d391;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
						<svg style="width:18px;height:18px;" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
							><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg
						>
					</div>
					<div>
						<p class="card-title" style="margin-bottom:0.1rem;">Election Details</p>
						<p style="font-size:0.75rem;color:var(--text-subtle);margin:0;">Current election summary</p>
					</div>
				</div>
				<div class="election-info-grid">
					<div class="info-item">
						<span class="info-label">Name</span>
						<span class="info-value">{currentElection.name}</span>
					</div>
					<div class="info-item">
						<span class="info-label">Status</span>
						<span class="info-value">
							<StatusBadge status={currentElection.status} />
						</span>
					</div>
					<div class="info-item">
						<span class="info-label">Start Date</span>
						<span class="info-value">
							{currentElection.start_date
								? new Date(currentElection.start_date).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })
								: '—'}
						</span>
					</div>
					<div class="info-item">
						<span class="info-label">End Date</span>
						<span class="info-value">
							{currentElection.end_date
								? new Date(currentElection.end_date).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })
								: '—'}
						</span>
					</div>
					{#if currentElection.description}
						<div class="info-item" style="grid-column:1/-1;">
							<span class="info-label">Description</span>
							<span class="info-value" style="color:var(--text-subtle);font-size:0.8rem;">{currentElection.description}</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}
		</div>

		<!-- Quick Navigation -->
		<div class="dash-card quick-nav-card">
			<p class="card-title" style="margin-bottom:1.25rem;">System Navigation</p>
			{#each navCards as nav}
				<button onclick={() => goto(nav.path)} class="qn-item">
					<div class="qn-icon" style="background:var(--bg-elevated);color:var(--brand-primary);">
						<svg
							style="width:18px;height:18px;"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d={nav.icon} />
						</svg>
					</div>
					<div class="qn-text">
						<p class="qn-label">{nav.name}</p>
						<p class="qn-sub">{nav.desc}</p>
					</div>
					<svg
						style="width:16px;height:16px;color:var(--text-subtle);margin-left:auto;"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg
					>
				</button>
			{/each}
		</div>
	</div>
</div>

<style>
	/* ── Shell ── */
	.dash {
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		max-width: 1400px;
		margin: 0 auto;
	}

	/* ── Header ── */
	.dash-header {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
	}
	.dash-eyebrow {
		font-size: 0.6875rem;
		color: var(--text-subtle);
		margin: 0;
	}
	.dash-title {
		font-size: 1.375rem;
		font-weight: 800;
		color: var(--text-main);
		margin: 0.125rem 0 0;
		letter-spacing: -0.02em;
	}

	.dash-select {
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		color: var(--text-main);
		border-radius: 8px;
		padding: 0.5rem 2rem 0.5rem 0.75rem;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
		min-width: 200px;
		max-width: 450px;
	}

	/* ── KPI Row ── */
	.kpi-row {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}
	.kpi-card {
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 16px;
		padding: 1.25rem;
		box-shadow: 0 2px 12px rgba(11, 117, 254, 0.06);
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease;
	}
	.kpi-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 24px rgba(11, 117, 254, 0.12);
	}
	.kpi-top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: 0.75rem;
	}
	.kpi-eyebrow {
		font-size: 0.6875rem;
		font-weight: 700;
		color: var(--text-subtle);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		margin: 0 0 0.375rem;
	}
	.kpi-num {
		font-size: 1.75rem;
		font-weight: 800;
		color: var(--text-main);
		margin: 0;
		letter-spacing: -0.03em;
		line-height: 1;
	}
	.kpi-delta {
		font-size: 0.6875rem;
		font-weight: 600;
		margin: 0.3rem 0 0;
	}
	.kpi-icon-box {
		width: 44px;
		height: 44px;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
	}
	.kpi-sparkbars {
		display: flex;
		align-items: flex-end;
		gap: 3px;
		height: 36px;
		margin-bottom: 0.5rem;
	}
	.spark-bar {
		flex: 1;
		border-radius: 2px 2px 0 0;
		min-height: 4px;
		transition: height 0.4s ease;
	}
	.kpi-sub, .kpi-sub-btn {
		font-size: 0.6875rem;
		font-weight: 600;
		color: var(--brand-primary);
		cursor: pointer;
		margin: 0;
		background: none;
		border: none;
		padding: 0;
		text-align: left;
		font-family: inherit;
	}

	/* ── Middle Row ── */
	.mid-row {
		display: grid;
		grid-template-columns: 2.2fr 1fr;
		gap: 1rem;
	}

	/* ── Base Card ── */
	.dash-card {
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 2px 12px rgba(11, 117, 254, 0.05);
	}
	.card-title {
		font-size: 1rem;
		font-weight: 800;
		color: var(--text-main);
		margin: 0;
	}

	.passcode-card {
		display: flex;
		flex-direction: column;
		padding: 1rem;
	}

	/* ── Left Column ── */
	.mid-left-col {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	/* ── Election Info Card ── */
	.election-info-card {
		padding: 1rem;
	}
	.election-info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.625rem;
	}
	.info-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}
	.info-label {
		font-size: 0.6rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--text-subtle);
	}
	.info-value {
		font-size: 0.8125rem;
		font-weight: 600;
		color: var(--text-main);
	}

	/* ── Quick Nav ── */
	.quick-nav-card {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.qn-item {
		display: flex;
		align-items: center;
		gap: 0.875rem;
		padding: 0.75rem 0.5rem;
		border-radius: 10px;
		background: none;
		border: none;
		cursor: pointer;
		text-align: left;
		width: 100%;
		transition: background-color 0.15s;
	}
	.qn-item:hover {
		background: var(--bg-hover);
	}
	.qn-item:hover .qn-icon {
		background: var(--brand-primary) !important;
		color: white !important;
	}
	.qn-icon {
		width: 40px;
		height: 40px;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		transition: all 0.2s;
	}
	.qn-text {
		flex: 1;
		min-width: 0;
	}
	.qn-label {
		font-size: 0.875rem;
		font-weight: 700;
		color: var(--text-main);
		margin: 0;
	}
	.qn-sub {
		font-size: 0.75rem;
		color: var(--text-subtle);
		margin: 0.125rem 0 0;
	}

	/* ── Responsive ── */
	@media (max-width: 1024px) {
		.mid-row {
			grid-template-columns: 1fr;
		}
	}
	@media (max-width: 768px) {
		.kpi-row {
			grid-template-columns: 1fr;
		}
		.dash-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 1rem;
		}
	}
</style>
