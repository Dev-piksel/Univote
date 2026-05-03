<script>
	import { onMount } from 'svelte';
	import { adviser as adviserApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import { selectedElectionId } from '$lib/stores/election.js';
	import { fly } from 'svelte/transition';

	/** @type {any[]} */
	let logs = $state([]);
	let isLoading = $state(true);
	let pageHistory = $state([/** @type {string | null} */ (null)]);
	let currentPage = $state(0);
	let nextPageToken = $state(/** @type {string | null} */ (null));

	async function loadLogs(/** @type {string | null} */ token = null) {
		isLoading = true;
		try {
			const res = await adviserApi.getAuditLog(15, token);
			logs = res.data || [];
			nextPageToken = res.next_page_token || null;
		} catch (err) {
			console.error('Failed to load audit logs:', err);
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

	onMount(() => {
		loadLogs();
	});

	function formatAction(/** @type {string} */ action) {
		return action.replace(/_/g, ' ').toLowerCase();
	}
</script>

<svelte:head><title>Audit Logs | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Audit Logs</p>
			<h1 class="dash-title">Operational History</h1>
		</div>
		<button
			onclick={() => { currentPage = 0; pageHistory = [null]; loadLogs(); }}
			class="btn-primary mt-4 rounded-2xl px-6 py-3 text-[10px] uppercase shadow-xl lg:mt-0"
		>
			Refresh Protocol
		</button>
	</div>

	<div class="rounded-[2.5rem] border border-line-subtle bg-surface-elevated p-8" in:fly={{ y: 20, duration: 800 }}>
		<div class="scrollbar-hide overflow-x-auto">
			<table class="w-full min-w-[800px] border-collapse text-left">
				<thead>
					<tr style="border-bottom:1px solid var(--border-main);">
						<th style="padding:1rem;font-size:0.6875rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;">Timestamp</th>
						<th style="padding:1rem;font-size:0.6875rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;">Event</th>
						<th style="padding:1rem;font-size:0.6875rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;">Subject Context</th>
						<th style="padding:1rem;font-size:0.6875rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;text-align:right;">Status</th>
					</tr>
				</thead>
				<tbody>
					{#if isLoading}
						{#each Array(6) as _}
							<tr class="animate-pulse" style="border-bottom:1px solid var(--border-subtle);">
								<td style="padding:1rem;"><div style="height:0.75rem;background:var(--bg-elevated);border-radius:99px;width:8rem;"></div></td>
								<td style="padding:1rem;"><div style="height:0.75rem;background:var(--bg-elevated);border-radius:99px;width:6rem;"></div></td>
								<td style="padding:1rem;"><div style="height:0.75rem;background:var(--bg-elevated);border-radius:99px;width:12rem;"></div></td>
								<td style="padding:1rem;"><div style="height:0.75rem;background:var(--bg-elevated);border-radius:99px;width:4rem;margin-left:auto;"></div></td>
							</tr>
						{/each}
					{:else}
						{#each logs as log}
							<tr style="border-bottom:1px solid var(--border-subtle);transition:background-color 0.2s;" class="hover:bg-[var(--bg-hover)]">
								<td style="padding:1rem;font-size:0.8125rem;color:var(--text-subtle);white-space:nowrap;">
									<span style="font-family:monospace;font-weight:600;color:var(--text-main);">{new Date(log.created_at).toLocaleTimeString()}</span>
									<div style="font-size:0.6875rem;">{new Date(log.created_at).toLocaleDateString()}</div>
								</td>
								<td style="padding:1rem;">
									<span style="font-size:0.75rem;font-weight:700;color:var(--brand-primary);background:var(--brand-glow);padding:0.25rem 0.5rem;border-radius:4px;">
										{formatAction(log.action)}
									</span>
								</td>
								<td style="padding:1rem;max-width:300px;">
									<div style="font-size:0.8125rem;font-weight:600;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
										{log.target_type ? `Target: ${log.target_type.toUpperCase()}` : 'SYSTEM ROUTINE'}
									</div>
								</td>
								<td style="padding:1rem;text-align:right;">
									<span style="font-size:0.75rem;font-weight:700;color:var(--status-success-fg);">OK</span>
								</td>
							</tr>
						{:else}
							<tr><td colspan="4" style="padding:4rem 1rem;text-align:center;color:var(--text-subtle);">Protocol Log Vacant</td></tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>

		<div style="padding:1rem;display:flex;align-items:center;justify-content:space-between;border-top:1px solid var(--border-main);margin-top:2rem;">
			<button onclick={goPrev} disabled={currentPage === 0 || isLoading} class="btn-secondary btn-sm">Previous</button>
			<span style="font-size:0.75rem;font-weight:600;color:var(--text-muted);">Page {currentPage + 1}</span>
			<button onclick={goNext} disabled={!nextPageToken || isLoading} class="btn-primary btn-sm">Next</button>
		</div>
	</div>
</div>
