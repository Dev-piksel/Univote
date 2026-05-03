<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { branding } from '$lib/stores/branding.js';
	import StatusBadge from '$lib/components/StatusBadge.svelte';

	/** @type {any[]} */
	let elections = $state([]);
	/** @type {any[]} */
	let students = $state([]);
	/** @type {any[]} */
	let advisers = $state([]);
	/** @type {any[]} */
	let auditLogs = $state([]);
	let isLoading = $state(true);

	// Overlay state
	let activeReport = $state(/** @type {string|null} */ (null)); // 'elections', 'voters', 'advisers', 'turnout'
	let showOverlay = $state(false);

	/** @type {any} */
	let reportData = $state(null);

	onMount(async () => {
		try {
			const [eRes, sRes, aRes, lRes] = await Promise.all([
				adminApi.getElections(),
				adminApi.getStudents(),
				adminApi.getAdvisers(),
				adminApi.getAuditLog()
			]);
			elections = eRes.data ?? [];
			students = sRes.data ?? [];
			advisers = aRes.data ?? [];
			auditLogs = lRes.data ?? [];
		} catch (err) {
			console.error('Dashboard load error:', err);
		} finally {
			isLoading = false;
		}
	});

	const activeElections = $derived(elections.filter((e) => e.status === 'active'));
	const closedElections = $derived(
		elections.filter((e) => e.status === 'ended' || e.status === 'closed' || e.status === 'completed')
	);
	const votedCount = $derived(students.filter((s) => s.has_voted).length);
	const notVotedCount = $derived(students.length - votedCount);
	const turnoutPct = $derived(
		students.length ? Math.round((votedCount / students.length) * 100) : 0
	);

	// SVG donut math — r=40, circumference ≈ 251
	const CIRC = 251;
	const voterDash = $derived(Math.round((turnoutPct / 100) * CIRC));
	const activeShare = $derived(
		elections.length ? Math.round((activeElections.length / elections.length) * 100) : 0
	);
	const activeDash = $derived(Math.round((activeShare / 100) * CIRC));

	// Bar chart: last 7 stats based on audit log activity by day
	const barData = $derived.by(() => {
		const days = Array.from({ length: 7 }, (_, i) => {
			const d = new Date();
			d.setDate(d.getDate() - (6 - i));
			return d.toDateString();
		});
		return days.map((day) => ({
			label: new Date(day).toLocaleDateString('en', { weekday: 'short' }),
			value: auditLogs.filter((l) => new Date(l.created_at).toDateString() === day).length
		}));
	});

	const barMax = $derived(Math.max(...barData.map((b) => b.value), 1));

	// Sparkline for elections (simple horizontal line + value)
	const recentLogs = $derived(auditLogs.slice(0, 6));
	const adminName = $derived($authSession?.full_name?.split(' ')[0] ?? 'Admin');

	// Report Handlers
	/** @param {'elections' | 'voters' | 'advisers' | 'turnout'} type */
	function openReport(type) {
		activeReport = type;
		showOverlay = true;
		
		if (type === 'elections') {
			reportData = {
				title: 'Elections Report',
				metrics: [
					{ label: 'Pending Elections', value: elections.filter(e => e.status === 'upcoming').length, color: '#fda085' },
					{ label: 'Active Elections', value: activeElections.length, color: '#68d391' },
					{ label: 'Completed Elections', value: closedElections.length, color: '#a0aec0' }
				]
			};
		} else if (type === 'voters' || type === 'turnout') {
			// For voter status/turnout, the user wants "active election data"
			const activeCount = activeElections.length;
			if (activeCount === 0) {
				reportData = {
					title: type === 'voters' ? 'Voter Status Report' : 'Voter Turnout Report',
					message: 'No active elections currently running.',
					metrics: []
				};
			} else {
				// Aggregate or show primary active election
				// For now, use the global stats but contextually labeled
				reportData = {
					title: type === 'voters' ? 'Voter Status Report' : 'Voter Turnout Report',
					subtitle: `Based on ${activeCount} active election(s)`,
					metrics: [
						{ label: 'Total Registered', value: students.length, color: '#4facfe' },
						{ label: 'Voted', value: votedCount, color: '#68d391' },
						{ label: 'Pending', value: notVotedCount, color: '#fda085' },
						{ label: 'Turnout Percentage', value: turnoutPct + '%', color: '#0B75FE' }
					]
				};
			}
		} else if (type === 'advisers') {
			reportData = {
				title: 'Advisers Report',
				metrics: [
					{ label: 'Total Advisers', value: advisers.length, color: '#4facfe' },
					{ label: 'Active Accounts', value: advisers.length, color: '#68d391' }
				]
			};
		}
	}

	function closeOverlay() {
		showOverlay = false;
		setTimeout(() => { activeReport = null; reportData = null; }, 300);
	}
</script>

<svelte:head><title>Dashboard | {$branding.appName} Admin</title></svelte:head>

<div class="dash">
	<!-- ── PAGE HEADER ── -->
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Dashboard</p>
			<h1 class="dash-title">Dashboard</h1>
		</div>
		<div class="dash-search">
			<svg
				style="width:14px;height:14px;color:#a0aec0;"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				viewBox="0 0 24 24"
				><path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
				/></svg
			>
			<input
				placeholder="Type here..."
				style="border:none;outline:none;background:transparent;font-size:0.8125rem;color:var(--text-muted);width:140px;"
			/>
		</div>
	</div>

	<!-- ── TOP KPI CARDS ── -->
	<div class="kpi-row">
		<!-- Total Elections card with mini bar -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Total Elections</p>
					{#if isLoading}
						<div class="skeleton" style="width:3rem;height:2rem;"></div>
					{:else}
						<p class="kpi-num">{elections.length}</p>
					{/if}
					<p class="kpi-delta" style="color:#68d391;">
						<span>▲</span>
						{activeElections.length} active
					</p>
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
							d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
						/></svg
					>
				</div>
			</div>
			<!-- Mini sparkline bars -->
			<div class="kpi-sparkbars">
				{#each [3, 5, 4, 7, 6, 8, activeElections.length + 1] as v}
					<div
						class="spark-bar"
						style="height:{Math.round((v / 9) * 100)}%;background:#00D2FF;"
					></div>
				{/each}
			</div>
			<button onclick={() => openReport('elections')} class="kpi-sub">View report →</button>
		</div>

		<!-- Registered Voters card -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Registered Voters</p>
					{#if isLoading}
						<div class="skeleton" style="width:3rem;height:2rem;"></div>
					{:else}
						<p class="kpi-num">{students.length.toLocaleString()}</p>
					{/if}
					<p class="kpi-delta" style="color:#68d391;"><span>▲</span> {turnoutPct}% voted</p>
				</div>
				<div class="kpi-icon-box" style="background:linear-gradient(135deg,#f6d365,#fda085);">
					<svg
						style="width:20px;height:20px;color:#fff;"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
						/></svg
					>
				</div>
			</div>
			<div class="kpi-sparkbars">
				{#each [20, 35, 28, 45, 38, 55, votedCount || 5] as v}
					<div
						class="spark-bar"
						style="height:{Math.round((v / 60) * 100)}%;background:#fbd38d;"
					></div>
				{/each}
			</div>
			<button onclick={() => openReport('voters')} class="kpi-sub">View report →</button>
		</div>

		<!-- Advisers card -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Advisers</p>
					{#if isLoading}
						<div class="skeleton" style="width:3rem;height:2rem;"></div>
					{:else}
						<p class="kpi-num">{advisers.length}</p>
					{/if}
					<p class="kpi-delta" style="color:#fc8181;"><span>●</span> Active accounts</p>
				</div>
				<div class="kpi-icon-box" style="background:linear-gradient(135deg,#4facfe,#00f2fe);">
					<svg
						style="width:20px;height:20px;color:#fff;"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
						/></svg
					>
				</div>
			</div>
			<div class="kpi-sparkbars">
				{#each [1, 2, 2, 3, 3, advisers.length || 1, advisers.length || 1] as v}
					<div
						class="spark-bar"
						style="height:{Math.round(
							(v / Math.max(advisers.length + 1, 4)) * 100
						)}%;background:#9ae6b4;"
					></div>
				{/each}
			</div>
			<button onclick={() => openReport('advisers')} class="kpi-sub">View report →</button>
		</div>

		<!-- Turnout card -->
		<div class="kpi-card">
			<div class="kpi-top">
				<div>
					<p class="kpi-eyebrow">Turnout</p>
					{#if isLoading}
						<div class="skeleton" style="width:3rem;height:2rem;"></div>
					{:else}
						<p class="kpi-num">{turnoutPct}%</p>
					{/if}
					<p class="kpi-delta" style="color:#68d391;"><span>▲</span> {votedCount} voted</p>
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
							d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
						/></svg
					>
				</div>
			</div>
			<div class="kpi-sparkbars">
				{#each [5, 12, 8, 18, 14, 22, turnoutPct || 10] as v}
					<div
						class="spark-bar"
						style="height:{Math.round((v / 25) * 100)}%;background:#76e4f7;"
					></div>
				{/each}
			</div>
			<button onclick={() => openReport('turnout')} class="kpi-sub">View report →</button>
		</div>
	</div>

	<!-- ── MIDDLE: Bar Chart + Donut Charts ── -->
	<div class="mid-row">
		<!-- Weekly Activity Bar Chart -->
		<div class="dash-card bar-card">
			<div class="card-header">
				<p class="card-title">Weekly Activity</p>
				<div style="display:flex;align-items:center;gap:1rem;">
					<span class="legend-dot" style="background:var(--brand-primary, #0B75FE);"></span><span class="legend-label"
						>This Week</span
					>
					<span class="legend-dot" style="background:#e2e8f0;"></span><span class="legend-label"
						>Last Week</span
					>
				</div>
			</div>
			<div class="bar-chart-area">
				{#each barData as bar}
					<div class="bc-col">
						<div class="bc-track">
							<div class="bc-bg-bar"></div>
							<div class="bc-fill" style="height:{Math.round((bar.value / barMax) * 100)}%;"></div>
						</div>
						<span class="bc-label">{bar.label}</span>
					</div>
				{/each}
			</div>
		</div>

		<!-- Donut Chart — Voter Turnout -->
		<div class="dash-card donut-card">
			<p class="card-title">Voter Status</p>
			<div class="donut-wrap">
				<svg viewBox="0 0 100 100" class="donut-svg">
					<!-- background ring -->
					<circle cx="50" cy="50" r="40" fill="none" stroke="#E2E8F0" stroke-width="12" />
					<!-- voted -->
					<circle
						cx="50"
						cy="50"
						r="40"
						fill="none"
						stroke="var(--brand-primary, #0B75FE)"
						stroke-width="12"
						stroke-dasharray="{voterDash} {CIRC - voterDash}"
						stroke-dashoffset="63"
						stroke-linecap="round"
						transform="rotate(-90 50 50)"
					/>
				</svg>
				<div class="donut-center">
					<p class="donut-pct">{turnoutPct}%</p>
					<p class="donut-sub">Voted</p>
				</div>
			</div>
			<div class="donut-legend">
				<div class="dl-item">
					<span class="dl-dot" style="background:var(--brand-primary, #0B75FE);"></span><span class="dl-label">Voted</span>
					<span class="dl-val">{votedCount}</span>
				</div>
				<div class="dl-item">
					<span class="dl-dot" style="background:#e2e8f0;"></span><span class="dl-label"
						>Pending</span
					><span class="dl-val">{notVotedCount}</span>
				</div>
			</div>
		</div>

		<!-- Donut Chart — Elections -->
		<div class="dash-card donut-card">
			<p class="card-title">Election Status</p>
			<div class="donut-wrap">
				<svg viewBox="0 0 100 100" class="donut-svg">
					<circle cx="50" cy="50" r="40" fill="none" stroke="#E2E8F0" stroke-width="12" />
					<circle
						cx="50"
						cy="50"
						r="40"
						fill="none"
						stroke="#11998e"
						stroke-width="12"
						stroke-dasharray="{activeDash} {CIRC - activeDash}"
						stroke-dashoffset="63"
						stroke-linecap="round"
						transform="rotate(-90 50 50)"
					/>
				</svg>
				<div class="donut-center">
					<p class="donut-pct">{activeElections.length}</p>
					<p class="donut-sub">Active</p>
				</div>
			</div>
			<div class="donut-legend">
				<div class="dl-item">
					<span class="dl-dot" style="background:#11998e;"></span><span class="dl-label"
						>Active</span
					><span class="dl-val">{activeElections.length}</span>
				</div>
				<div class="dl-item">
					<span class="dl-dot" style="background:#fda085;"></span><span class="dl-label">Ended</span
					><span class="dl-val">{closedElections.length}</span>
				</div>
				<div class="dl-item">
					<span class="dl-dot" style="background:#e2e8f0;"></span><span class="dl-label">Draft</span
					><span class="dl-val"
						>{elections.length - activeElections.length - closedElections.length}</span
					>
				</div>
			</div>
		</div>
	</div>

	<!-- ── BOTTOM: Activity log + Quick Nav ── -->
	<div class="btm-row">
		<!-- Recent Activity table -->
		<div class="dash-card activity-card">
			<div class="card-header">
				<p class="card-title">Recent Activity</p>
				<button onclick={() => goto('/admin/audit')} class="view-btn">View all →</button>
			</div>
			<table class="act-table">
				<thead>
					<tr>
						<th>User</th>
						<th>Action</th>
						<th>Time</th>
						<th>Role</th>
					</tr>
				</thead>
				<tbody>
					{#if isLoading}
						{#each Array(5) as _}
							<tr
								><td colspan="4"
									><div class="skeleton" style="height:1.5rem;border-radius:4px;"></div></td
								></tr
							>
						{/each}
					{:else if recentLogs.length === 0}
						<tr
							><td colspan="4" style="text-align:center;color:var(--text-subtle);padding:2rem;"
								>No activity yet</td
							></tr
						>
					{:else}
						{#each recentLogs as log}
							<tr>
								<td>
									<div class="act-user">
										<div
											class="act-avatar {log.actor_role === 'admin' ? 'av-admin' : 'av-adviser'}"
										>
											{log.actor_role?.[0]?.toUpperCase()}
										</div>
										<span class="act-name"
											>{log.actor_role === 'admin' ? adminName : 'Adviser'}</span
										>
									</div>
								</td>
								<td class="act-action">{log.action?.replace(/_/g, ' ')}</td>
								<td class="act-time"
									>{new Date(log.created_at).toLocaleTimeString([], {
										hour: '2-digit',
										minute: '2-digit'
									})}</td
								>
								<td>
									<span class="role-tag {log.actor_role === 'admin' ? 'rt-admin' : 'rt-adviser'}"
										>{log.actor_role}</span
									>
								</td>
							</tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>

		<!-- Quick navigation -->
		<div class="dash-card quick-nav-card">
			<p class="card-title" style="margin-bottom:1rem;">Quick Access</p>
			{#each [{ label: 'Elections', sub: elections.length + ' total', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z', grad: 'var(--brand-gradient)', path: '/admin/elections' }, { label: 'Voters', sub: students.length + ' registered', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z', grad: 'linear-gradient(135deg,#f6d365,#fda085)', path: '/admin/voters' }, { label: 'Advisers', sub: advisers.length + ' accounts', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z', grad: 'linear-gradient(135deg,#4facfe,#00f2fe)', path: '/admin/advisers' }, { label: 'Audit Logs', sub: auditLogs.length + ' events', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4', grad: 'linear-gradient(135deg,#11998e,#38ef7d)', path: '/admin/audit' }] as nav}
				<button onclick={() => goto(nav.path)} class="qn-item">
					<div class="qn-icon" style="background:{nav.grad};">
						<svg
							style="width:16px;height:16px;color:#fff;"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d={nav.icon} />
						</svg>
					</div>
					<div class="qn-text">
						<p class="qn-label">{nav.label}</p>
						<p class="qn-sub">{nav.sub}</p>
					</div>
					<svg
						style="width:16px;height:16px;color:#a0aec0;margin-left:auto;"
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

	<!-- ── REPORT OVERLAY ── -->
	{#if showOverlay}
		<div
			class="overlay-backdrop"
			onclick={closeOverlay}
			onkeydown={(e) => e.key === 'Escape' && closeOverlay()}
			role="button"
			tabindex="0"
		>
			<div class="report-card" onclick={(e) => e.stopPropagation()} role="presentation">
				<div class="rc-header">
					<div>
						<h2 class="rc-title">{reportData?.title}</h2>
						{#if reportData?.subtitle}
							<p class="rc-subtitle">{reportData.subtitle}</p>
						{/if}
					</div>
					<button class="rc-close" onclick={closeOverlay}>×</button>
				</div>

				<div class="rc-content">
					{#if reportData?.message}
						<p class="rc-msg">{reportData.message}</p>
					{:else}
						<div class="rc-grid">
							{#each reportData?.metrics ?? [] as m}
								<div class="rc-item">
									<p class="rc-label">{m.label}</p>
									<p class="rc-value" style="color:{m.color};">{m.value}</p>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				<div class="rc-footer">
					<button class="rc-btn" onclick={closeOverlay}>Close Report</button>
				</div>
			</div>
		</div>
	{/if}
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
		align-items: center;
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
	.dash-search {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 20px;
		padding: 0.375rem 0.875rem;
		box-shadow: 0 1px 4px rgba(80, 70, 229, 0.07);
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
		box-shadow: 0 2px 12px rgba(80, 70, 229, 0.06);
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease;
		cursor: default;
	}
	.kpi-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 24px rgba(80, 70, 229, 0.12);
	}
	.kpi-top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: 0.75rem;
	}
	.kpi-eyebrow {
		font-size: 0.6875rem;
		font-weight: 600;
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
	.kpi-sub {
		background: none;
		border: none;
		padding: 0;
		text-align: left;
		font-family: inherit;
		font-size: 0.6875rem;
		font-weight: 600;
		color: var(--brand-primary);
		cursor: pointer;
		margin: 0;
	}

	/* ── Overlay Styles ── */
	.overlay-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.4);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		animation: fadeIn 0.3s ease;
	}

	.report-card {
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 24px;
		width: 90%;
		max-width: 500px;
		box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
		padding: 2rem;
		animation: slideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
		position: relative;
	}

	.rc-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}
	.rc-title {
		font-size: 1.5rem;
		font-weight: 800;
		color: var(--text-main);
		margin: 0;
		letter-spacing: -0.02em;
	}
	.rc-subtitle {
		font-size: 0.8125rem;
		color: var(--text-subtle);
		margin: 0.25rem 0 0;
	}
	.rc-close {
		background: var(--bg-elevated);
		border: none;
		color: var(--text-main);
		width: 32px;
		height: 32px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.25rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	.rc-close:hover {
		background: #ff4d4d;
		color: #fff;
	}

	.rc-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.25rem;
	}
	.rc-item {
		background: var(--bg-elevated);
		padding: 1.25rem;
		border-radius: 16px;
		border: 1px solid var(--border-subtle);
	}
	.rc-label {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--text-subtle);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 0.5rem;
	}
	.rc-value {
		font-size: 1.5rem;
		font-weight: 800;
		margin: 0;
	}
	.rc-msg {
		text-align: center;
		color: var(--text-subtle);
		padding: 2rem 0;
	}

	.rc-footer {
		margin-top: 2rem;
		display: flex;
		justify-content: flex-end;
	}
	.rc-btn {
		background: var(--brand-gradient);
		color: #fff;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 12px;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(11, 117, 254, 0.3);
		transition: transform 0.2s;
	}
	.rc-btn:hover {
		transform: translateY(-2px);
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
	@keyframes slideUp {
		from { opacity: 0; transform: translateY(20px) scale(0.95); }
		to { opacity: 1; transform: translateY(0) scale(1); }
	}

	/* ── Middle Row ── */
	.mid-row {
		display: grid;
		grid-template-columns: 1.6fr 1fr 1fr;
		gap: 1rem;
	}

	/* ── Base Card ── */
	.dash-card {
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 16px;
		padding: 1.25rem;
		box-shadow: 0 2px 8px rgba(80, 70, 229, 0.05);
	}
	.card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}
	.card-title {
		font-size: 0.9375rem;
		font-weight: 700;
		color: var(--text-main);
		margin: 0;
	}
	.view-btn {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--brand-primary);
		background: none;
		border: none;
		cursor: pointer;
	}
	.legend-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		display: inline-block;
	}
	.legend-label {
		font-size: 0.6875rem;
		color: var(--text-subtle);
	}

	/* ── Bar Chart ── */
	.bar-chart-area {
		display: flex;
		align-items: flex-end;
		gap: 0.5rem;
		height: 140px;
	}
	.bc-col {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.375rem;
		height: 100%;
	}
	.bc-track {
		flex: 1;
		width: 100%;
		position: relative;
		border-radius: 6px 6px 0 0;
		overflow: visible;
		display: flex;
		align-items: flex-end;
	}
	.bc-bg-bar {
		position: absolute;
		inset: 0;
		background: var(--bg-elevated);
		border-radius: 6px;
	}
	.bc-fill {
		position: relative;
		width: 100%;
		border-radius: 6px;
		background: linear-gradient(to top, var(--brand-primary, #0b75fe), var(--brand-secondary, #00d2ff));
		transition: height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
		min-height: 6px;
		box-shadow: 0 -2px 12px var(--brand-glow, rgba(11, 117, 254, 0.3));
	}
	.bc-label {
		font-size: 0.625rem;
		font-weight: 600;
		color: var(--text-subtle);
	}

	/* ── Donut Chart ── */
	.donut-card {
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	.donut-wrap {
		position: relative;
		width: 130px;
		height: 130px;
		margin: 0.75rem 0;
	}
	.donut-svg {
		width: 100%;
		height: 100%;
	}
	.donut-center {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}
	.donut-pct {
		font-size: 1.5rem;
		font-weight: 800;
		color: var(--text-main);
		margin: 0;
		letter-spacing: -0.03em;
	}
	.donut-sub {
		font-size: 0.625rem;
		font-weight: 600;
		color: var(--text-subtle);
		margin: 0;
	}
	.donut-legend {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		margin-top: 0.5rem;
	}
	.dl-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.dl-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.dl-label {
		font-size: 0.75rem;
		color: var(--text-muted);
		flex: 1;
	}
	.dl-val {
		font-size: 0.75rem;
		font-weight: 700;
		color: var(--text-main);
	}

	/* ── Bottom Row ── */
	.btm-row {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 1rem;
	}

	/* ── Activity Table ── */
	.act-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8125rem;
	}
	.act-table th {
		font-size: 0.625rem;
		font-weight: 700;
		color: var(--text-subtle);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		padding: 0 0.5rem 0.625rem;
		text-align: left;
		border-bottom: 1px solid var(--border-subtle);
	}
	.act-table td {
		padding: 0.625rem 0.5rem;
		border-bottom: 1px solid var(--border-subtle);
		vertical-align: middle;
		color: var(--text-main);
	}
	.act-table tr:last-child td {
		border-bottom: none;
	}
	.act-user {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.act-avatar {
		width: 28px;
		height: 28px;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.6875rem;
		font-weight: 700;
		flex-shrink: 0;
	}
	.av-admin {
		background: #fef3c7;
		color: #d97706;
	}
	.av-adviser {
		background: var(--brand-primary-light, #e6f0ff);
		color: var(--brand-primary, #0b75fe);
	}
	.act-name {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--text-main);
	}
	.act-action {
		font-size: 0.75rem;
		color: var(--text-muted);
		text-transform: capitalize;
	}
	.act-time {
		font-size: 0.6875rem;
		color: var(--text-subtle);
		white-space: nowrap;
	}
	.role-tag {
		font-size: 0.625rem;
		font-weight: 700;
		padding: 0.2rem 0.5rem;
		border-radius: 999px;
		text-transform: capitalize;
	}
	.rt-admin {
		background: #fef3c7;
		color: #d97706;
	}
	.rt-adviser {
		background: var(--brand-primary-light, #e6f0ff);
		color: var(--brand-primary, #0b75fe);
	}

	/* ── Quick Nav ── */
	.quick-nav-card {
		display: flex;
		flex-direction: column;
	}
	.qn-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.6rem 0.5rem;
		border-radius: 10px;
		background: none;
		border: none;
		cursor: pointer;
		text-align: left;
		width: 100%;
		transition: background-color 0.12s;
	}
	.qn-item:hover {
		background: var(--bg-elevated);
	}
	.qn-icon {
		width: 36px;
		height: 36px;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
	}
	.qn-text {
		flex: 1;
		min-width: 0;
	}
	.qn-label {
		font-size: 0.8125rem;
		font-weight: 600;
		color: var(--text-main);
		margin: 0;
	}
	.qn-sub {
		font-size: 0.6875rem;
		color: var(--text-subtle);
		margin: 0.1rem 0 0;
	}

	/* ── Responsive ── */
	@media (max-width: 1100px) {
		.kpi-row {
			grid-template-columns: repeat(2, 1fr);
		}
		.mid-row {
			grid-template-columns: 1fr 1fr;
		}
		.btm-row {
			grid-template-columns: 1fr;
		}
	}
	@media (max-width: 600px) {
		.kpi-row {
			grid-template-columns: 1fr;
		}
		.mid-row {
			grid-template-columns: 1fr;
		}
	}
</style>
