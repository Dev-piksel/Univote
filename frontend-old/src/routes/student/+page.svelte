<script>
	import { onMount } from 'svelte';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { fade } from 'svelte/transition';

	let isLoading = $state(!$voterSession?.student_id);
	/** @type {Array<{id: string, name: string, start_date?: string, end_date?: string, has_voted: boolean, status: string}>} */
	let elections = $derived($voterSession?.elections || []);
	let activeElections = $derived(elections.filter((e) => e.status === 'active'));
	let upcomingElections = $derived(elections.filter((e) => e.status === 'upcoming'));
	let voterName = $derived($voterSession?.full_name || 'Student');

	const stats = $derived({
		total: elections.length,
		voted: elections.filter((e) => e.has_voted).length,
		pending: activeElections.filter((e) => !e.has_voted).length
	});

	/** @param {string} name */
	function getGreeting(name) {
		const hour = new Date().getHours();
		let text = '';
		if (hour < 12) text = `Good Morning, ${name} ☀️`;
		else if (hour < 18) text = `Good Afternoon, ${name} 👋`;
		else text = `Good Evening, ${name} 🌙`;
		return text;
	}

	// Receipt Drawer Logic
	let selectedSummaryId = $state(/** @type {string | null} */ (null));
	/** @type {any} */
	let receiptData = $state(null);
	let receiptLoading = $state(false);

	/** @param {string} electionId */
	async function toggleReceipt(electionId) {
		if (selectedSummaryId === electionId) {
			selectedSummaryId = null;
			receiptData = null;
			return;
		}

		receiptLoading = true;
		selectedSummaryId = electionId;
		try {
			// Using the correct API method from lib/api.js
			const res = await studentApi.getVoteSummary($voterSession?.student_id || '', electionId);
			receiptData = res;
		} catch (err) {
			console.error('Failed to load receipt:', err);
		} finally {
			receiptLoading = false;
		}
	}

	onMount(async () => {
		try {
			if ($voterSession?.student_id) {
				await voterSession.sync($voterSession.student_id);
			}
		} catch (err) {
			console.error('Failed to sync session:', err);
		} finally {
			// Ensure we clear the loader even if sync fails, 
			// as derived data might already be present from store.
			isLoading = false;
		}
	});
</script>

<svelte:head><title>Dashboard | {$branding.appName}</title></svelte:head>

{#if isLoading}
	<div class="loader-container">
		<div class="spinner"></div>
		<p>Synchronizing your secure session…</p>
	</div>
{:else}
	<div class="page-header">
		<div class="greeting-container">
			<div class="breadcrumb">PAGES / STUDENT DASHBOARD</div>
			<h1 class="greeting">{getGreeting(voterName.split(' ')[0])}</h1>
		</div>
	</div>

	<div class="stats-grid">
		<!-- Total -->
		<div class="stat-card">
			<div class="stat-content">
				<div class="stat-label">Total Elections</div>
				<div class="stat-value-row">
					<div class="stat-glyph total">{stats.total}</div>
					<div class="stat-icon-wrapper blue">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
					</div>
				</div>
			</div>
		</div>

		<!-- Voted -->
		<div class="stat-card">
			<div class="stat-content">
				<div class="stat-label">Votes Cast</div>
				<div class="stat-value-row">
					<div class="stat-glyph voted">{stats.voted}</div>
					<div class="stat-icon-wrapper green">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
					</div>
				</div>
			</div>
		</div>

		<!-- Pending -->
		<div class="stat-card">
			<div class="stat-content">
				<div class="stat-label">Pending</div>
				<div class="stat-value-row">
					<div class="stat-glyph pending">{stats.pending}</div>
					<div class="stat-icon-wrapper amber">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="section-row">
		<h2 class="section-title">Active Elections</h2>
		<span class="active-pill">{activeElections.length} Active</span>
	</div>

	<div class="elections-list">
		{#if activeElections.length === 0}
			<div class="empty-state-mini">No active elections at the moment.</div>
		{:else}
			{#each activeElections as election, idx}
				<div class="election-item" in:fade={{ duration: 300, delay: idx * 80 }}>
					<div class="election-main">
						<div class="election-icon-bg" class:is-voted={election.has_voted}>
							{#if election.has_voted}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
							{:else}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
							{/if}
						</div>
						<div class="election-info">
							<div class="election-name-row">
								<h3 class="election-name">{election.name}</h3>
								{#if election.has_voted}
									<div class="voted-tag"><div class="dot"></div>Voted</div>
								{/if}
							</div>
							<div class="election-meta">Ends {new Date(election.end_date || Date.now()).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</div>
						</div>
					</div>

					<div class="election-actions">
						{#if election.has_voted}
							<button class="btn-action btn-blue" onclick={() => toggleReceipt(election.id)}>
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
								{selectedSummaryId === election.id ? 'Hide Receipt' : 'View Receipt'}
							</button>
						{:else}
							<a href="/student/ballot?election={election.id}" class="btn-action btn-blue" style="background:var(--accent);">
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
								Cast Vote
							</a>
						{/if}
						<a href="/student/results?election={election.id}" class="btn-action btn-ghost">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
							View Results
						</a>
					</div>

					{#if selectedSummaryId === election.id}
						<div class="receipt-area" in:fade>
							{#if receiptLoading}
								<div class="receipt-loading">
									<div class="mini-spinner"></div>
									<span>Retrieving encrypted receipt…</span>
								</div>
							{:else if receiptData}
								<div class="receipt-card" id="receipt-{election.id}">
									<div class="receipt-header">
										<div class="receipt-id-box">
											<p class="label">Official Receipt ID</p>
											<code class="val">{receiptData.receipt_id}</code>
										</div>
										<div class="receipt-actions">
											<button class="receipt-icon-btn" onclick={() => navigator.clipboard.writeText(receiptData.receipt_id)} title="Copy ID">
												<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
											</button>
											<button class="receipt-icon-btn" onclick={() => window.print()} title="Download PDF">
												<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
											</button>
										</div>
									</div>
									
									<div class="receipt-votes-grid">
										{#each receiptData.votes || [] as vote}
											<div class="receipt-vote-item">
												<span class="p-pos">{vote.position}</span>
												<div class="p-cand">
													<span class="p-name">{vote.candidates?.students?.full_name}</span>
													<span class="p-party">{vote.candidates?.partylists?.name || 'Independent'}</span>
												</div>
											</div>
										{/each}
									</div>

									<div class="receipt-footer-meta">
										<p>Voter: {voterName}</p>
										<p>Certified on {new Date(receiptData.voted_at).toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short' })}</p>
									</div>
								</div>

								<!-- Hidden Print-Only Version -->
								<div class="print-only-receipt">
									<div class="print-header">
										<img src="/Messenger_creation_1261776042047231.jpeg" alt="UniVote" class="print-logo" />
										<h1>OFFICIAL VOTING RECEIPT</h1>
										<p class="print-sub">UNIVOTE DIGITAL ELECTION SYSTEM</p>
									</div>
									<div class="print-divider"></div>
									<div class="print-meta-grid">
										<div>
											<span class="p-label">STUDENT NAME</span>
											<p>{voterName}</p>
										</div>
										<div>
											<span class="p-label">ELECTION</span>
											<p>{election.name}</p>
										</div>
										<div>
											<span class="p-label">RECEIPT ID</span>
											<p class="mono">{receiptData.receipt_id}</p>
										</div>
										<div>
											<span class="p-label">DATE CERTIFIED</span>
											<p>{new Date(receiptData.voted_at).toLocaleString()}</p>
										</div>
									</div>
									<div class="print-divider"></div>
									<table class="print-table">
										<thead>
											<tr>
												<th>POSITION</th>
												<th>CANDIDATE</th>
												<th>PARTYLIST</th>
											</tr>
										</thead>
										<tbody>
											{#each receiptData.votes || [] as vote}
												<tr>
													<td>{vote.position}</td>
													<td>{vote.candidates?.students?.full_name}</td>
													<td>{vote.candidates?.partylists?.name || 'Independent'}</td>
												</tr>
											{/each}
										</tbody>
									</table>
									<div class="print-footer">
										<p>This is a computer-generated document. No signature required.</p>
										<p>© {new Date().getFullYear()} UniVote Student Council Election Services</p>
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		{/if}
	</div>

	{#if upcomingElections.length > 0}
		<div class="section-row" style="margin-top: 40px;">
			<h2 class="section-title">Upcoming Elections</h2>
			<span class="active-pill" style="background:var(--amber-bg);color:var(--amber);opacity:0.8;">{upcomingElections.length} Scheduled</span>
		</div>

		<div class="elections-list">
			{#each upcomingElections as election, idx}
				<div class="election-item" in:fade={{ duration: 300, delay: idx * 80 }}>
					<div class="election-main">
						<div class="election-icon-bg" style="background:var(--amber-bg);color:var(--amber);">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
						</div>
						<div class="election-info">
							<div class="election-name-row">
								<h3 class="election-name">{election.name}</h3>
								<div class="voted-tag" style="background:var(--amber-bg);color:var(--amber);border-color:rgba(245,158,11,0.2);"><div class="dot" style="background:var(--amber);"></div>Upcoming</div>
							</div>
							<div class="election-meta">Starts {new Date(election.start_date || Date.now()).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</div>
						</div>
					</div>

					<div class="election-actions">
						<button class="btn-action btn-ghost" disabled style="opacity:0.6; cursor:not-allowed;">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
							Coming Soon
						</button>
						<a href="/student/results?election={election.id}" class="btn-action btn-ghost">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
							Candidates Info
						</a>
					</div>
				</div>
			{/each}
		</div>
	{/if}
{/if}

<style>
	.empty-state-mini { padding: 40px; text-align: center; background: var(--surface2); border: 1.5px dashed var(--border); border-radius: 20px; color: var(--muted); font-size: 14px; font-weight: 600; grid-column: 1 / -1; }
	.loader-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 1rem; color: var(--muted); }
	.spinner { width: 40px; height: 40px; border: 3px solid var(--surface2); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }

	.page-header { margin-bottom: 30px; }
	@media (max-width: 768px) {
		.page-header { gap: 0 !important; margin-bottom: 20px; }
		.greeting { font-size: 32px !important; }
	}
	.breadcrumb { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent); font-weight: 800; margin-bottom: 8px; }
	.greeting { font-size: 44px; font-weight: 800; color: var(--text); letter-spacing: -2px; line-height: 1.1; }

	.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 36px; }
	.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 24px; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
	.stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
	.stat-card:hover { transform: translateY(-2px); border-color: var(--accent); }
	.stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); font-weight: 600; margin-bottom: 16px; }
	.stat-value-row { display: flex; align-items: center; justify-content: space-between; }
	.stat-glyph { font-size: 52px; font-weight: 800; line-height: 1; letter-spacing: -2px; }
	.stat-glyph.total { color: var(--accent); }
	.stat-glyph.voted { color: var(--green); }
	.stat-glyph.pending { color: var(--amber); }
	.stat-icon-wrapper { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; }
	.stat-icon-wrapper.blue { background: var(--accent-bg); color: var(--accent); }
	.stat-icon-wrapper.green { background: var(--green-bg); color: var(--green); }
	.stat-icon-wrapper.amber { background: var(--amber-bg); color: var(--amber); }
	.stat-icon-wrapper svg { width: 22px; height: 22px; }

	.section-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
	.section-title { font-size: 18px; font-weight: 800; color: var(--text); letter-spacing: -0.5px; }
	.active-pill { background: var(--accent-bg); color: var(--accent); font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(92, 96, 245, 0.2); }

	.elections-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(540px, 1fr)); gap: 30px; }
	@media (max-width: 768px) {
		.elections-list { grid-template-columns: 1fr; }
	}
	.election-item { background: var(--surface); border: 1.5px solid var(--border); border-radius: 24px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
	.election-main { display: flex; align-items: center; gap: 20px; margin-bottom: 24px; }
	.election-icon-bg { width: 52px; height: 52px; border-radius: 16px; background: var(--accent-bg); border: 1px solid var(--border); color: var(--accent); display: grid; place-items: center; flex-shrink: 0; }
	.election-icon-bg.is-voted { background: var(--green-bg); color: var(--green); border-color: rgba(18,183,106,0.2); }
	.election-icon-bg svg { width: 24px; height: 24px; }
	.election-info { flex: 1; }
	.election-name-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }
	.election-name { font-size: 20px; font-weight: 800; color: var(--text); margin: 0; letter-spacing: -0.5px; }
	.voted-tag { display: flex; align-items: center; gap: 6px; background: var(--green-bg); border: 1px solid rgba(18,183,106,0.25); color: var(--green); font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px; }
@keyframes pulse { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.5); opacity: 0.5; } 100% { transform: scale(1); opacity: 1; } }
	.election-meta { font-size: 13px; color: var(--muted); margin-top: 4px; font-weight: 600; }

	.election-actions { display: flex; gap: 10px; flex-wrap: wrap; }
	.btn-action { display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 12px; font-size: 13px; font-weight: 600; text-decoration: none; transition: all 0.2s; cursor: pointer; border: none; }
	.btn-blue { background: var(--accent); color: white; box-shadow: 0 4px 12px rgba(59,110,245,0.2); }
	.btn-blue:hover { transform: translateY(-1.5px); filter: brightness(1.1); }
	.btn-ghost { background: transparent; border: 1.5px solid var(--border); color: var(--text2); }
	.btn-ghost:hover { background: var(--surface2); }
	.btn-action svg { width: 14px; height: 14px; }

	.receipt-area { margin-top: 20px; border-top: 1.5px dashed var(--border); padding-top: 24px; }
	.receipt-card { background: var(--surface2); border: 1.5px solid var(--border); border-radius: 20px; padding: 20px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }
	.receipt-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
	.receipt-id-box .label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); font-weight: 800; margin-bottom: 6px; }
	.receipt-id-box .val { font-family: 'Geist Mono', monospace; font-size: 14px; color: var(--text); font-weight: 700; letter-spacing: 1px; }
	
	.receipt-actions { display: flex; gap: 8px; }
	.receipt-icon-btn { width: 36px; height: 36px; border-radius: 10px; background: var(--surface); border: 1.5px solid var(--border); display: grid; place-items: center; cursor: pointer; color: var(--text2); transition: all 0.2s; }
	.receipt-icon-btn:hover { color: var(--accent); border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(92,96,245,0.15); }

	.receipt-votes-grid { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }
	.receipt-vote-item { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 12px 16px; display: flex; align-items: center; gap: 16px; transition: border-color 0.2s; }
	.receipt-vote-item:hover { border-color: var(--accent-subtle); }
	.p-pos { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); font-weight: 800; width: 120px; flex-shrink: 0; }
	.p-cand { flex: 1; display: flex; flex-direction: column; }
	.p-name { font-size: 15px; font-weight: 800; color: var(--text); letter-spacing: -0.3px; }
	.p-party { font-size: 11px; font-weight: 600; color: var(--muted); }

	.receipt-footer-meta { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border-top: 1px solid var(--border); padding-top: 16px; }

	/* ── PRINT-ONLY RECEIPT (OFFICIAL DOCUMENT) ── */
	.print-only-receipt { display: none; }
	
	@media print {
		:global(body *) { visibility: hidden; }
		.print-only-receipt, .print-only-receipt * { visibility: visible; }
		.print-only-receipt { 
			display: block !important; 
			position: absolute; 
			left: 0; 
			top: 0; 
			width: 100%; 
			padding: 40px; 
			background: white !important; 
			color: black !important;
			font-family: 'Geist Mono', monospace !important;
		}
		.print-header { text-align: center; margin-bottom: 30px; }
		.print-logo { width: 60px; height: 60px; margin: 0 auto 15px; border-radius: 12px; }
		.print-header h1 { font-size: 24px; font-weight: 800; margin: 0; letter-spacing: 2px; }
		.print-sub { font-size: 12px; opacity: 0.7; margin-top: 4px; }
		.print-divider { height: 2px; background: black; margin: 20px 0; }
		.print-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
		.print-meta-grid .p-label { font-size: 10px; font-weight: 800; display: block; margin-bottom: 4px; }
		.print-meta-grid p { font-size: 14px; margin: 0; font-weight: 600; }
		.print-meta-grid .mono { font-family: 'Geist Mono', monospace; font-weight: 800; letter-spacing: 1px; }
		.print-table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
		.print-table th { text-align: left; font-size: 11px; border-bottom: 2px solid black; padding: 10px; }
		.print-table td { padding: 12px 10px; border-bottom: 1px solid #eee; font-size: 13px; }
		.print-footer { text-align: center; border-top: 1px solid #eee; padding-top: 20px; font-size: 10px; opacity: 0.6; }
	}

	@media (max-width: 768px) {
		.greeting { font-size: 28px; }
		.stat-glyph { font-size: 44px; }
		.receipt-vote-item { flex-direction: column; align-items: flex-start; gap: 4px; }
		.p-pos { width: auto; font-size: 9px; }
		.receipt-footer-meta { flex-direction: column; gap: 8px; align-items: flex-start; }
	}
</style>
