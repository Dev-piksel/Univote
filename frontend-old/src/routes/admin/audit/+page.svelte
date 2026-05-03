<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';

	/** @type {Array<any>} */
	let auditLogs = $state([]);
	let isLoading = $state(true);
	let pageHistory = $state([/** @type {string | null} */ (null)]);
	let currentPage = $state(0);
	let nextPageToken = $state(/** @type {string | null} */ (null));
	let searchQuery = $state('');
	let roleFilter = $state('all');
	let sortOrder = $state('desc'); // 'asc' | 'desc'
	let sortKey = $state('created_at');

	onMount(async () => {
		await loadLogs();
	});

	/** @param {string | null} token */
	async function loadLogs(token = null) {
		try {
			isLoading = true;
			const res = await adminApi.getAuditLog(50, token); // Load more for better local filtering
			auditLogs = res.data ?? [];
			nextPageToken = res.next_page_token ?? null;
		} catch (err) {
			console.error('Failed to load audit log:', err);
		} finally {
			isLoading = false;
		}
	}

	async function goNext() {
		if (!nextPageToken || isLoading) return;
		pageHistory.push(nextPageToken);
		currentPage++;
		await loadLogs(nextPageToken);
	}

	async function goPrev() {
		if (currentPage === 0 || isLoading) return;
		currentPage--;
		pageHistory.pop();
		const prevToken = pageHistory[currentPage];
		await loadLogs(prevToken);
	}

	function toggleSort(key) {
		if (sortKey === key) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortOrder = 'desc';
		}
	}

	const filteredLogs = $derived(() => {
		let logs = [...auditLogs];

		// Role filter
		if (roleFilter !== 'all') {
			logs = logs.filter((l) => l.actor_role === roleFilter);
		}

		// Text search
		if (searchQuery) {
			const q = searchQuery.toLowerCase();
			logs = logs.filter(
				(log) =>
					log.action?.toLowerCase().includes(q) ||
					log.target_type?.toLowerCase().includes(q) ||
					log.actor_role?.toLowerCase().includes(q)
			);
		}

		// Sorting
		logs.sort((a, b) => {
			let valA = a[sortKey];
			let valB = b[sortKey];
			
			if (sortKey === 'created_at') {
				valA = new Date(valA).getTime();
				valB = new Date(valB).getTime();
			}

			if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
			if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
			return 0;
		});

		return logs;
	});
</script>

<svelte:head><title>Audit Logs | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> System Administrator</p>
			<h1 class="dash-title">Audit Logs</h1>
		</div>
		<div style="display:flex;align-items:center;gap:0.75rem;">
			<!-- Role Filter -->
			<select bind:value={roleFilter} class="input-base" style="width:140px;height:2.25rem;font-size:0.75rem;padding:0 0.75rem;">
				<option value="all">All Roles</option>
				<option value="admin">Admins</option>
				<option value="adviser">Advisers</option>
				<option value="student">Students</option>
			</select>

			<!-- Search -->
			<div style="position:relative;">
				<svg
					style="position:absolute;left:0.75rem;top:50%;transform:translateY(-50%);width:0.875rem;height:0.875rem;color:var(--text-subtle);opacity:0.6;"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2.5"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/></svg
				>
				<input
					bind:value={searchQuery}
					placeholder="Search events…"
					class="input-base"
					style="padding-left:2.5rem;width:240px;height:2.25rem;font-size:0.75rem;font-family:sans-serif;"
				/>
			</div>
		</div>
	</div>

	<!-- Log Table -->
	<div class="admin-card" style="overflow:hidden;">
		<div style="padding:0.75rem 1rem;border-bottom:1px solid var(--border-main);display:flex;align-items:center;justify-content:space-between;">
			<p class="section-label">
				Listing {filteredLogs().length} operational events
			</p>
			<button onclick={() => loadLogs()} class="btn-icon" title="Refresh logs">
				<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/></svg>
			</button>
		</div>

		{#if isLoading}
			<div style="padding:1.5rem;display:flex;flex-direction:column;gap:0.5rem;">
				{#each Array(8) as _}
					<div class="skeleton" style="height:3rem;"></div>
				{/each}
			</div>
		{:else if filteredLogs().length === 0}
			<div class="empty-state">
				{searchQuery || roleFilter !== 'all' ? 'No logs match your current filters.' : 'No protocol data recorded.'}
			</div>
		{:else}
			<div style="overflow-x:auto;">
				<table class="data-table" style="width:100%;text-align:left;border-collapse:collapse;">
					<thead>
						<tr>
							<th onclick={() => toggleSort('created_at')} style="cursor:pointer;user-select:none;">
								Timestamp {sortKey === 'created_at' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
							</th>
							<th onclick={() => toggleSort('action')} style="cursor:pointer;user-select:none;">
								Event {sortKey === 'action' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
							</th>
							<th>Role</th>
							<th>Context</th>
							<th style="text-align:right;">Status</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredLogs() as log (log.id || Math.random())}
							<tr>
								<td style="padding:1rem;font-size:0.8125rem;color:var(--text-subtle);white-space:nowrap;">
									<span style="font-family:monospace;font-weight:600;color:var(--text-main);">
										{new Date(log.created_at).toLocaleTimeString()}
									</span>
									<div style="font-size:0.6875rem;">{new Date(log.created_at).toLocaleDateString()}</div>
								</td>
								<td style="padding:1rem;">
									<span style="font-size:0.6875rem;font-weight:800;color:var(--brand-primary);background:var(--brand-glow);padding:0.25rem 0.5rem;border-radius:4px;letter-spacing:0.02em;">
										{log.action}
									</span>
								</td>
								<td style="padding:1rem;">
									<span class="pill pill-dot {log.actor_role === 'admin' ? 'pill-warning' : log.actor_role === 'adviser' ? 'pill-info' : 'pill-neutral'}">
										{log.actor_role}
									</span>
								</td>
								<td style="padding:1rem;">
									<div style="font-size:0.8125rem;font-weight:600;color:var(--text-main);">
										{log.target_type ? log.target_type.charAt(0).toUpperCase() + log.target_type.slice(1) : 'System Routine'}
									</div>
									{#if log.target_id}
										<div style="font-size:0.625rem;color:var(--text-subtle);font-family:monospace;">ID: {log.target_id}</div>
									{/if}
								</td>
								<td style="padding:1rem;text-align:right;">
									<span class="pill pill-success" style="font-size:0.625rem;">PROCESSED</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}

		<div style="padding:1rem;display:flex;align-items:center;justify-content:space-between;border-top:1px solid var(--border-main);">
			<button onclick={goPrev} disabled={currentPage === 0 || isLoading} class="btn-secondary btn-sm">Previous</button>
			<span style="font-size:0.75rem;font-weight:600;color:var(--text-muted);">Page {currentPage + 1}</span>
			<button onclick={goNext} disabled={!nextPageToken || isLoading} class="btn-primary btn-sm">Next</button>
		</div>
	</div>
</div>
