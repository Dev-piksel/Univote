<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { page } from '$app/state';
	import { fade, fly, scale } from 'svelte/transition';
	import { elasticOut } from 'svelte/easing';
	import { sortPositions } from '$lib/constants.js';

	let isSubmitting = $state(false);
	let hasSubmitted = $state(false);
	let isLoading = $state(true); 
	let errorMessage = $state('');
	let showConfirm = $state(false);
	let alreadyVoted = $state(false);
	let electionId = $state('');
	let receiptId = $state('');

	let isAuthorized = $state(false);
	let adviserPin = $state(''); // Layer 1 Entry PIN
	let passcodeId = $state(''); // Linked record ID
	let adviserId = $state(''); // Adviser UID for persistent session tracking
	let sessionPasscode = $state(''); // Layer 2 Session Passcode
	let isVerifyingPasscode = $state(false);

	/** @type {Record<string, any[]>} */
	let candidatesGrouped = $state({});
	/** @type {Record<string, string | null>} */
	let selectedVotes = $state({});

	let voterName = $derived($voterSession?.full_name || 'Voter');
	let electionName = $state('');

	/** @type {string[]} */
	const positionOrder = $derived(sortPositions(Object.keys(candidatesGrouped)));
	const selectedCount = $derived(Object.values(selectedVotes).filter((v) => v).length);
	const totalPositions = $derived(positionOrder.length);
	const allSelected = $derived(selectedCount === totalPositions && totalPositions > 0);
	/** Tracks which positions are collapsed (after selecting a candidate) */
	/** @type {Record<string, boolean>} */
	let collapsed = $state({});

	/** @param {string} position @param {string} candidateId */
	function selectCandidate(position, candidateId) {
		selectedVotes[position] = candidateId;
		// Auto-collapse after selection (slight delay so user sees the selected state)
		setTimeout(() => { collapsed[position] = true; }, 350);
	}

	/** @param {string} name */
	function getMonogram(name) {
		return name
			.split(' ')
			.slice(0, 2)
			.map((w) => w[0]?.toUpperCase() || '')
			.join('');
	}

	function getReviewList() {
		return positionOrder
			.filter((pos) => selectedVotes[pos])
			.map((pos) => ({
				position: pos,
				candidate: (candidatesGrouped[pos] || []).find((c) => c.id === selectedVotes[pos])
			}))
			.filter((r) => r.candidate);
	}

	onMount(() => {
		if (!$voterSession) {
			goto('/student/validate');
		}
	});

	$effect(() => {
		const session = $voterSession;
		if (!session) return;

		const id = page.url.searchParams.get('election') || '';
		electionId = id;

		if (!id) {
			isLoading = false;
			alreadyVoted = false;
			candidatesGrouped = {};
			selectedVotes = {};
			return;
		}

		isLoading = true;
		alreadyVoted = false;
		hasSubmitted = false;
		errorMessage = '';

		const electionInfo = (session.elections || []).find((e) => e.id === id);
		electionName = electionInfo?.name || 'Election';

		if (electionInfo?.status === 'upcoming') {
			errorMessage = 'This election has not started yet. Please check back later.';
			isLoading = false;
			return;
		}

		if (electionInfo?.has_voted) {
			alreadyVoted = true;
			isLoading = false;
			return;
		}

		studentApi
			.getCandidates(id)
			.then((res) => {
				const data = res.data || [];
				/** @type {Record<string, any[]>} */
				const grouped = {};
				data.forEach((/** @type {any} */ c) => {
					if (!grouped[c.position]) grouped[c.position] = [];
					grouped[c.position].push({
						id: c.id,
						name: c.students?.full_name || 'Unknown',
						party: c.partylists?.name || 'Independent'
					});
				});
				candidatesGrouped = grouped;
				/** @type {Record<string, string | null>} */
				const initialVotes = {};
				Object.keys(grouped).forEach((pos) => {
					initialVotes[pos] = null;
				});
				selectedVotes = initialVotes;
			})
			.catch((/** @type {any} */ err) => {
				errorMessage = err.message || 'Failed to load ballot data.';
			})
			.finally(() => {
				isLoading = false;
			});
	});

	async function verifyPasscode() {
		if (!adviserPin) return;
		isVerifyingPasscode = true;
		try {
			const res = await studentApi.verifyPasscode(electionId, adviserPin);
			passcodeId = res.passcode_id;
			adviserId = res.adviser_id;
			isAuthorized = true;
			isLoading = false;
		} catch (/** @type {any} */ err) {
			errorMessage = err.message || 'Invalid Adviser Passcode.';
		} finally {
			isVerifyingPasscode = false;
		}
	}


	async function submitVote() {
		const session = $voterSession;
		if (!session) return;

		isSubmitting = true;
		errorMessage = '';
		const votes = Object.entries(selectedVotes)
			.filter(([_, id]) => id !== null)
			.map(([position, candidate_id]) => ({ 
				candidate_id: /** @type {string} */ (candidate_id), 
				position 
			}));

		try {
			const resp = await studentApi.vote(session.student_id ?? '', electionId, passcodeId, adviserId, votes, sessionPasscode);
			if (resp && resp.receipt_id) receiptId = resp.receipt_id;
			voterSession.markVoted(electionId);
			showConfirm = false;
			hasSubmitted = true;
		} catch (/** @type {any} */ err) {
			errorMessage = err.message || 'Failed to cast ballot.';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<svelte:head><title>Cast Vote | {$branding.appName}</title></svelte:head>

<div class="page-header">
	<div class="breadcrumb-row">
		<div class="live-dot"></div>
		<span class="breadcrumb">PAGES / VOTING BOOTH</span>
	</div>
	<h1 class="page-title">Voting Room</h1>
</div>

{#if isLoading}
	<div class="loader-area" in:fade>
		<div class="spinner"></div>
		<p>Initializing secure protocol…</p>
		<div style="display:flex;flex-direction:column;gap:2rem;width:100%;max-width:800px;margin-top:2rem;">
			{#each [1, 2] as i}
				<div class="skeleton" style="height:40px;width:200px;border-radius:8px;"></div>
				<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;">
					{#each [1, 2] as j}
						<div class="skeleton" style="height:200px;border-radius:24px;opacity:0.3;"></div>
					{/each}
				</div>
			{/each}
		</div>
	</div>
{:else if hasSubmitted || alreadyVoted}
	<div class="completed-wrapper" in:fade>
		<div class="completed-card">
			<div class="check-ring">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
			</div>
			<div class="completed-title">All Done, {voterName.split(' ')[0]}!</div>
			<div class="completed-body">
				<p>You've completed all active election sessions.</p>
				<p class="bold">Thank you for participating in the democratic process.</p>
				<p class="muted">Your vote has been securely recorded.</p>
			</div>
			<div class="action-row">
				<a href="/student/results?election={electionId}" class="btn btn-green" aria-label="View Election Results">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
					View Results
				</a>
				<a href="/student" class="btn btn-white" aria-label="Return to Dashboard">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
					Back to Dashboard
				</a>
			</div>
			<div class="receipt-note">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
				A voting receipt has been saved to your dashboard
			</div>
		</div>
	</div>
{:else if electionId && !isAuthorized}
	<!-- Gatekeeper -->
	<div class="gatekeeper-area" in:fade>
		<div class="gatekeeper-card">
			<div class="lock-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
			</div>
			<h2 class="gk-title">Voting Room Access</h2>
			<p class="gk-body">Ask your room adviser for the <strong>6-digit Entry PIN</strong> to unlock and enter this voting session.</p>
			<div class="gk-steps">
				<div class="gk-step">
					<span class="gk-step-num">1</span>
					<span>Enter the 6-digit Entry PIN below to access the ballot</span>
				</div>
				<div class="gk-step">
					<span class="gk-step-num">2</span>
					<span>Select your candidates, then request the 8-character Session Code from your adviser to finalize your vote</span>
				</div>
			</div>

			<div class="gk-form">
				<label class="gk-pin-label" for="entry-pin-input">Entry PIN</label>
				<input
					id="entry-pin-input"
					type="password"
					inputmode="numeric"
					bind:value={adviserPin}
					placeholder="••••••"
					maxlength="6"
					class="passcode-input"
					onkeydown={(e) => e.key === 'Enter' && adviserPin.length === 6 && verifyPasscode()}
				>
				{#if errorMessage}
					<p class="err-msg">{errorMessage}</p>
				{/if}
				<button
					class="btn-primary"
					disabled={isVerifyingPasscode || adviserPin.length < 6 || (voterSession.getElectionStatus && voterSession.getElectionStatus(electionId) === 'upcoming')}
					onclick={verifyPasscode}
				>
					{#if isVerifyingPasscode}
						Verifying…
					{:else if voterSession.getElectionStatus && voterSession.getElectionStatus(electionId) === 'upcoming'}
						Voting Not Started
					{:else}
						Enter Voting Room
					{/if}
				</button>
				<a href="/student" class="gk-abort">← Return to Dashboard</a>
			</div>
		</div>
	</div>
{:else if electionId}
	<!-- Ballot -->
	<div class="ballot-container" in:fade>
		<div class="ballot-header">
			<div class="ballot-h-left">
				<h2 class="ballot-name">{electionName}</h2>
				<p class="ballot-subtitle">Authenticated Session: Welcome {voterName.split(' ')[0]}</p>
			</div>
			<div class="progress-pill">
				<span class="count">{selectedCount} / {totalPositions}</span>
				<span class="label">Positions</span>
			</div>
		</div>

		{#if errorMessage}
			<div class="err-banner" in:fly={{ y: -10 }}>{errorMessage}</div>
		{/if}

		<div class="positions-stack">
			{#each positionOrder as position, idx}
				{@const isCollapsed = collapsed[position] && !!selectedVotes[position]}
				{@const selectedCand = (candidatesGrouped[position] || []).find(c => c.id === selectedVotes[position])}
				<div class="position-section" in:fly={{ y: 20, delay: idx * 100 }}>
					<!-- Position header (always visible) -->
					<div class="pos-header" role="button" tabindex="0" style="cursor:{selectedVotes[position] ? 'pointer' : 'default'}" onclick={() => { if (selectedVotes[position]) collapsed[position] = !collapsed[position]; }} onkeydown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && selectedVotes[position]) collapsed[position] = !collapsed[position]; }}>
						<div class="pos-num" class:done={selectedVotes[position]}>{idx + 1}</div>
						<div class="pos-text">
							<h3 class="pos-title">{position}</h3>
							<p class="pos-meta">{selectedVotes[position] ? 'Selection Recorded ▾ click to change' : 'Select Candidate'}</p>
						</div>
						<!-- Collapsed summary row -->
						{#if isCollapsed && selectedCand}
							<div style="display:flex;align-items:center;gap:10px;margin-left:auto;" in:fade>
								{#if selectedCand.id}
									{@const photoUrl = studentApi.getCandidatePhotoUrl ? studentApi.getCandidatePhotoUrl(selectedCand.id) : `/api/common/candidates/${selectedCand.id}/photo`}
									<img src={photoUrl} alt={selectedCand.name} style="width:32px;height:32px;border-radius:50%;object-fit:cover;border:2px solid var(--green);" />
								{:else}
									<div class="cand-avatar" style="width:32px;height:32px;font-size:11px;background:var(--accent);color:white;">{getMonogram(selectedCand.name)}</div>
								{/if}
								<span style="font-size:13px;font-weight:700;color:var(--green);">{selectedCand.name}</span>
								<button onclick={(e) => { e.stopPropagation(); collapsed[position] = false; }} style="font-size:11px;font-weight:700;color:var(--accent);background:none;border:none;cursor:pointer;">Change</button>
							</div>
						{/if}
					</div>

					<!-- Candidates grid (collapsible) -->
					{#if !isCollapsed}
						<div class="candidates-grid" in:fly={{ y: -8, duration: 250 }}>
							{#each candidatesGrouped[position] as cand}
								<button
									class="cand-card"
									class:active={selectedVotes[position] === cand.id}
									onclick={() => selectCandidate(position, cand.id)}
								>
									{#if cand.id}
										{@const photoUrl = studentApi.getCandidatePhotoUrl ? studentApi.getCandidatePhotoUrl(cand.id) : `/api/common/candidates/${cand.id}/photo`}
										<img 
											src={photoUrl} 
											alt={cand.name} 
											class="cand-photo" 
											loading="lazy"
											onerror={(e) => { 
												const target = /** @type {HTMLImageElement} */ (e.currentTarget);
												const next = /** @type {HTMLElement} */ (target.nextElementSibling);
												target.style.display = 'none'; 
												if (next) next.style.display = 'flex'; 
											}}
										/>
										<div class="cand-avatar" style="display:none;">{getMonogram(cand.name)}</div>
									{:else}
										<div class="cand-avatar">{getMonogram(cand.name)}</div>
									{/if}
									<div class="cand-name">{cand.name}</div>
									<div class="cand-party">{cand.party}</div>
									<div class="cand-check">
										<div class="check-dot"></div>
										<span>{selectedVotes[position] === cand.id ? 'SELECTED' : 'CHOOSE'}</span>
									</div>
								</button>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		</div>

		<div class="footer-action">
			<div class="footer-info">
				<h3 class="f-title">{allSelected ? 'Protocol Complete' : 'Protocol Pending'}</h3>
				<p class="f-body">{allSelected ? 'Ballot ready for final encryption.' : `Designate candidates for all ${totalPositions} positions.`}</p>
			</div>
			<button class="btn btn-primary lg" disabled={!allSelected} onclick={() => showConfirm = true}>
				Certify Ballot
			</button>
		</div>
	</div>

	<!-- Confirmation Modal -->
	{#if showConfirm}
		<div 
			class="modal-overlay" 
			in:fade 
			role="button"
			tabindex="-1"
			onclick={() => showConfirm = false}
			onkeydown={e => e.key === 'Escape' && (showConfirm = false)}
		>
			<div class="modal-card" role="dialog" aria-modal="true" tabindex="-1" onclick={e => e.stopPropagation()} onkeydown={e => e.stopPropagation()} in:scale={{ start: 0.9 }}>
				<h3 class="modal-title">Confirm Ballot</h3>
				<p class="modal-subtitle">Your vote is anonymous and final. Secure encryption is about to engage.</p>
				
				<div class="review-box">
					{#each getReviewList() as item}
						<div class="review-item">
							<span class="r-pos">{item.position}</span>
							<span class="r-name">{item.candidate.name}</span>
						</div>
					{/each}
				</div>

				<div class="pin-section" style="margin-top:20px;">
					<div class="pin-header">
						<span class="p-label">🎲 Adviser Session Code</span>
					</div>
					<p style="font-size:11px;color:var(--muted);margin-bottom:12px;">Ask your room monitoring adviser for their <strong>8-character Session Code</strong>. This code is tied to the same adviser whose Entry PIN you used.</p>
					<input type="text" maxlength="8" bind:value={sessionPasscode} placeholder="e.g. 1234567G" class="pin-input" style="text-transform:uppercase;letter-spacing:0.2em;font-family:monospace;">
				</div>

				<div class="modal-buttons">
					<button class="btn btn-ghost flex-1" onclick={() => showConfirm = false}>Cancel</button>
					<button class="btn btn-primary flex-1" disabled={isSubmitting || sessionPasscode.length < 8} onclick={submitVote}>
						{isSubmitting ? 'Casting…' : 'Cast Vote'}
					</button>
				</div>
			</div>
		</div>
	{/if}
{:else}
	<!-- Election Selection (Rare if coming from home, but fallback) -->
	{#if Array.isArray($voterSession?.elections)}
		{@const pElections = ($voterSession?.elections || []).filter(e => !e.has_voted)}
		{#if pElections.length > 0}
			<div class="selection-grid" in:fade>
				{#each pElections as e}
					<a href="/student/ballot?election={e.id}" class="e-select-card">
						<div class="e-icon">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
						</div>
						<div class="e-info">
							<span class="e-name">{e.name}</span>
							<span class="e-meta">Session active until {new Date(e.end_date || Date.now()).toLocaleDateString()}</span>
						</div>
						<span class="e-btn">Start Voting</span>
					</a>
				{/each}
			</div>
		{:else}
			<div class="empty-ballot-hero" in:scale={{ start: 0.95, duration: 400 }}>
				<div class="hero-icon-ring">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
				</div>
				<h2 class="hero-title">All Secured</h2>
				<p class="hero-body">You have no pending election sessions at this time. All your ballots are encrypted and stored.</p>
				<a href="/student" class="btn btn-primary lg">Return to Dashboard</a>
			</div>
		{/if}
	{/if}
{/if}

<style>
	.page-header { margin-bottom: 24px; }
	.breadcrumb-row { display: flex; align-items: center; gap: 7px; margin-bottom: 6px; }
	.live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 2s ease infinite; }
	@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.5); } }
	.breadcrumb { font-size: 11px; text-transform: uppercase; letter-spacing: 1.4px; color: var(--accent); font-weight: 700; }
	.page-title { font-size: 26px; font-weight: 800; letter-spacing: -0.8px; color: var(--text); }

	.loader-area { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1rem; color: var(--muted); padding: 40px 0; }
	.spinner { width: 40px; height: 40px; border: 3px solid var(--surface2); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }

	/* COMPLETED CARD */
	.completed-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 0; }
	.completed-card {
		background: var(--surface); border: 1px solid var(--border); border-radius: 28px;
		padding: 64px 40px; text-align: center; width: 100%; max-width: 740px;
		box-shadow: 0 4px 30px rgba(0,0,0,.03); position: relative;
	}
	.check-ring {
		width: 84px; height: 84px; border-radius: 50%;
		background: #ecfdf5; border: 1px solid rgba(16,185,129,.2);
		display: grid; place-items: center; margin: 0 auto 32px;
	}
	.check-ring svg { width: 32px; height: 32px; color: #10b981; }
	.completed-title { font-size: 30px; font-weight: 800; letter-spacing: -1.2px; color: var(--text); margin-bottom: 20px; }
	.completed-body { font-size: 15px; color: var(--muted); line-height: 1.8; margin-bottom: 36px; }
	.completed-body .bold { font-weight: 800; color: var(--text2); }
	.completed-body .muted { font-size: 14px; opacity: 0.8; }
	
	.action-row { display: flex; gap: 16px; justify-content: center; margin-bottom: 32px; }
	
	.btn-green { background: #10b981; color: white; box-shadow: 0 4px 14px rgba(16,185,129,0.25); }
	.btn-green:hover { filter: brightness(1.1); transform: translateY(-1.5px); }
	.btn-white { background: white; border: 1.5px solid var(--border); color: var(--text2); }
	.btn-white:hover { background: var(--surface2); transform: translateY(-1.5px); }

	.receipt-note { font-size: 12px; color: var(--muted); display: flex; align-items: center; justify-content: center; gap: 8px; font-weight: 600; opacity: 0.7; }
	.receipt-note svg { width: 14px; height: 14px; color: var(--accent); }

	/* GATEKEEPER */
	.gatekeeper-area { display: flex; justify-content: center; padding: 40px 0; }
	.gatekeeper-card { background: var(--surface); border: 1px solid var(--border); border-radius: 24px; padding: 32px; width: 100%; max-width: 420px; text-align: center; box-shadow: var(--shadow-card); }
	.lock-icon { width: 64px; height: 64px; border-radius: 18px; background: var(--amber-bg); color: var(--amber); display: grid; place-items: center; margin: 0 auto 20px; }
	.lock-icon svg { width: 28px; height: 28px; }
	.gk-title { font-size: 20px; font-weight: 800; color: var(--text); margin-bottom: 8px; }
	.gk-body { font-size: 13px; color: var(--muted); margin-bottom: 24px; line-height: 1.6; font-weight: 500; }
	.passcode-input { width: 100%; padding: 16px; border-radius: 12px; border: 1.5px solid var(--border); font-family: monospace; text-align: center; letter-spacing: 2px; font-size: 16px; margin-bottom: 20px; outline: none; transition: border-color 0.2s; }
	.passcode-input:focus { border-color: var(--accent); }
	.gk-abort { display: block; margin-top: 16px; font-size: 12px; font-weight: 700; color: var(--muted); text-decoration: none; text-transform: uppercase; letter-spacing: 1px; }
	.gk-abort:hover { color: var(--text); }
	.err-msg { color: var(--red); font-size: 12px; font-weight: 700; margin-bottom: 16px; }
	.gk-steps { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; text-align: left; }
	.gk-step { display: flex; align-items: flex-start; gap: 10px; font-size: 12px; color: var(--muted); line-height: 1.5; }
	.gk-step-num { min-width: 20px; height: 20px; border-radius: 50%; background: var(--accent); color: white; font-size: 11px; font-weight: 800; display: grid; place-items: center; flex-shrink: 0; margin-top: 1px; }
	.gk-pin-label { display: block; font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; text-align: left; }

	/* BALLOT */
	.ballot-container { width: 100%; max-width: 1800px; padding-bottom: 60px; }
	.ballot-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 32px; flex-wrap: wrap; }
	.ballot-name { font-size: 42px; font-weight: 800; color: var(--text); letter-spacing: -1.5px; }
	.ballot-subtitle { font-size: 13px; color: var(--muted); font-weight: 500; margin-top: 2px; }
	.progress-pill { background: var(--surface); border: 1.5px solid var(--border); border-radius: 14px; padding: 10px 16px; display: flex; flex-direction: column; align-items: flex-end; }
	.progress-pill .count { font-size: 16px; font-weight: 800; color: var(--text); line-height: 1; }
	.progress-pill .label { font-size: 9px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

	.err-banner { background: #fef2f2; border: 1px solid rgba(239, 68, 68, 0.2); color: var(--red); padding: 12px 16px; border-radius: 12px; font-size: 13px; font-weight: 700; margin-bottom: 24px; }

	.positions-stack { display: flex; flex-direction: column; gap: 48px; margin-bottom: 60px; }
	.pos-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
	.pos-num { width: 40px; height: 40px; border-radius: 12px; background: var(--surface2); border: 1px solid var(--border); display: grid; place-items: center; font-size: 15px; font-weight: 800; color: var(--muted); transition: all 0.2s; }
	.pos-num.done { background: var(--green-bg); border-color: rgba(18,183,106,0.3); color: var(--green); }
	.pos-title { font-size: 16px; font-weight: 800; color: var(--text); text-transform: uppercase; letter-spacing: 0.5px; }
	.pos-meta { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 1px; }

	.candidates-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
	.cand-card { background: var(--surface); border: 2px solid var(--border); border-radius: 24px; padding: 32px; text-align: center; cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); background: var(--surface); position: relative; overflow: hidden; }
	.cand-card:hover { transform: translateY(-3px); border-color: var(--accent); }
	.cand-card.active { border-color: var(--green); background: var(--green-bg); border-width: 2px; }
	.cand-avatar { width: 60px; height: 60px; border-radius: 50%; background: var(--surface2); color: var(--muted); font-size: 18px; font-weight: 800; display: grid; place-items: center; margin: 0 auto 16px; transition: all 0.2s; }
	.cand-photo { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin: 0 auto 16px; display: block; border: 2px solid var(--border); transition: all 0.2s; }
	.cand-card.active .cand-photo { border-color: var(--green); box-shadow: 0 0 0 3px rgba(16,185,129,0.2); }
	.cand-card.active .cand-avatar { background: var(--accent); color: white; }
	.cand-name { font-size: 20px; font-weight: 800; color: var(--text); margin-bottom: 6px; }
	.cand-party { font-size: 12px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; }
	.cand-check { display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
	.check-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--border); }
	.cand-card.active .check-dot { background: var(--green); }
	.cand-card.active .cand-check span { color: var(--green); }

	.footer-action { background: var(--surface2); border: 1px solid var(--border); border-radius: 24px; padding: 32px; text-align: center; }
	.footer-info { margin-bottom: 24px; }
	.f-title { font-size: 18px; font-weight: 800; color: var(--text); margin-bottom: 4px; }
	.f-body { font-size: 13px; color: var(--muted); font-weight: 500; }

	/* MODAL */
	.modal-overlay { position: fixed; inset: 0; z-index: 1000; background: rgba(19, 25, 38, 0.4); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); display: grid; place-items: center; padding: 20px; }
	.modal-card { background: var(--surface); border: 1px solid var(--border); border-radius: 28px; width: 100%; max-width: 440px; padding: 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.15); }
	.modal-title { font-size: 20px; font-weight: 800; color: var(--text); margin-bottom: 8px; }
	.modal-subtitle { font-size: 13px; color: var(--muted); margin-bottom: 24px; font-weight: 500; line-height: 1.5; }
	.review-box { background: var(--surface2); border: 1px solid var(--border); border-radius: 16px; padding: 8px; margin-bottom: 24px; max-height: 200px; overflow-y: auto; }
	.review-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid var(--border); }
	.review-item:last-child { border: none; }
	.r-pos { font-size: 9px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
	.r-name { font-size: 13px; font-weight: 800; color: var(--text); }
	.pin-section { margin-bottom: 28px; }
	.pin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
	.p-label { font-size: 10px; font-weight: 800; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
	.pin-reveal { background: var(--green-bg); border: 1px solid rgba(18,183,106,0.3); border-radius: 12px; padding: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
	.pr-label { font-size: 9px; font-weight: 700; color: var(--green); text-transform: uppercase; letter-spacing: 1px; }
	.pr-val { font-family: monospace; font-size: 18px; font-weight: 800; color: var(--green); letter-spacing: 4px; }
	.pin-input { width: 100%; padding: 16px; border-radius: 12px; border: 1.5px solid var(--border); text-align: center; font-size: 18px; font-weight: 800; font-family: monospace; letter-spacing: 4px; outline: none; transition: border-color 0.2s; }
	.pin-input:focus { border-color: var(--accent); }
	.modal-buttons { display: flex; gap: 12px; }

	/* SELECTION */
	.selection-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(540px, 1fr)); gap: 32px; padding: 20px 0; }
	.e-select-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: 32px; padding: 40px; text-decoration: none; display: flex; align-items: center; gap: 32px; transition: all 0.28s; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
	.e-select-card:hover { transform: translateY(-6px); border-color: var(--accent); box-shadow: 0 20px 40px rgba(92, 96, 245, 0.12); }
	.e-icon { width: 72px; height: 72px; border-radius: 24px; background: var(--accent-bg); color: var(--accent); display: grid; place-items: center; flex-shrink: 0; }
	.e-icon svg { width: 32px; height: 32px; }
	.e-info { flex: 1; min-width: 0; }
	.e-name { display: block; font-size: 26px; font-weight: 800; color: var(--text); margin-bottom: 14px; line-height: 1.25; letter-spacing: -0.8px; }
	.e-meta { display: block; font-size: 13px; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; }
	.e-btn { background: var(--surface2); color: var(--text2); font-size: 12px; font-weight: 800; padding: 12px 20px; border-radius: 14px; text-transform: uppercase; letter-spacing: 1.5px; white-space: nowrap; transition: all 0.2s; }
	.e-select-card:hover .e-btn { background: var(--accent); color: white; transform: scale(1.05); }

	/* EMPTY HERO */
	.empty-ballot-hero { background: var(--surface); border: 1.5px solid var(--border); border-radius: 32px; padding: 80px 40px; text-align: center; max-width: 600px; margin-top: 40px; }
	.hero-icon-ring { width: 80px; height: 80px; border-radius: 50%; background: var(--accent-bg); color: var(--accent); border: 1px solid rgba(92, 96, 245, 0.2); display: grid; place-items: center; margin: 0 auto 32px; }
	.hero-icon-ring svg { width: 32px; height: 32px; }
	.hero-title { font-size: 28px; font-weight: 800; color: var(--text); margin-bottom: 16px; letter-spacing: -1px; }
	.hero-body { font-size: 15px; color: var(--muted); line-height: 1.7; margin-bottom: 40px; }

	/* GENERAL BUTTONS */
	.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 20px; border-radius: 14px; font-size: 14px; font-weight: 700; cursor: pointer; transition: all .18s; border: none; font-family: inherit; text-decoration: none; }
	.btn-primary { background: var(--green); color: #fff; box-shadow: 0 4px 12px rgba(18,183,106,.2); }
	.btn-primary:not(:disabled):hover { filter: brightness(1.1); transform: translateY(-1.5px); }
	.btn-ghost { background: transparent; border: 1.5px solid var(--border); color: var(--text2); }
	.btn-ghost:hover { background: var(--surface2); }
	.btn.lg { padding: 16px 32px; font-size: 15px; }
	.btn:disabled { opacity: 0.5; cursor: not-allowed; }

	@media (max-width: 768px) {
		.page-title { font-size: 24px; }
		.completed-card { padding: 40px 20px; }
		.completed-title { font-size: 24px; }
		.action-row { flex-direction: column; gap: 12px; }
		.action-row .btn { width: 100%; }
		.completed-wrapper { padding: 20px 0; }
	}
</style>
