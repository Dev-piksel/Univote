<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import Notification from '$lib/components/Notification.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import ConfirmModal from '$lib/components/ConfirmModal.svelte';
	import { slide } from 'svelte/transition';

	/** @type {Array<any>} */
	let elections = $state([]);
	let isLoading = $state(true);
	let electionSearch = $state('');
	let newElection = $state({ name: '', start_date: '', end_date: '', description: '' });
	let isCreating = $state(false);
	let showForm = $state(false);
	let editingElectionId = $state(/** @type {string|null} */ (null));

	// Confirmation Modal State
	let confirmState = $state({
		show: false,
		title: '',
		message: '',
		onConfirm: () => {},
		id: ''
	});

	/** @type {{ text: string, type: 'info' | 'success' | 'error' }} */
	let notification = $state({ text: '', type: 'info' });

	onMount(async () => {
		await loadElections();
	});

	async function loadElections() {
		try {
			const res = await adminApi.getElections();
			elections = res.data ?? [];
		} catch (err) {
			console.error('Failed to load elections:', err);
		} finally {
			isLoading = false;
		}
	}

	const filteredElections = $derived(
		electionSearch
			? elections.filter((e) => e.name.toLowerCase().includes(electionSearch.toLowerCase()))
			: elections
	);

	function notify(text = '', type = /** @type {'info' | 'success' | 'error'} */ ('info')) {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3500);
	}

	async function handleSubmit(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!newElection.name || !newElection.start_date || !newElection.end_date) {
			notify('Please fill in all required fields.', 'error');
			return;
		}
		if (new Date(newElection.end_date) <= new Date(newElection.start_date)) {
			notify('End date must be after start date.', 'error');
			return;
		}
		isCreating = true;
		try {
			const payload = {
				...newElection,
				start_date: new Date(newElection.start_date).toISOString(),
				end_date: new Date(newElection.end_date).toISOString()
			};

			if (editingElectionId) {
				await adminApi.updateElection(editingElectionId, payload);
				notify('Election updated successfully', 'success');
			} else {
				await adminApi.createElection(payload);
				notify('Election created successfully', 'success');
			}

			await loadElections();
			resetForm();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Operation failed', 'error');
		} finally {
			isCreating = false;
		}
	}

	function resetForm() {
		newElection = { name: '', start_date: '', end_date: '', description: '' };
		editingElectionId = null;
		showForm = false;
	}

	function openEdit(/** @type {any} */ election) {
		// Convert ISO to local datetime-local format (YYYY-MM-DDTHH:MM)
		const start = new Date(election.start_date);
		const end = new Date(election.end_date);

		// Helper to format for datetime-local
		const fmt = (/** @type {Date} */ d) => {
			const pad = (/** @type {number} */ n) => String(n).padStart(2, '0');
			return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
		};

		newElection = {
			name: election.name,
			start_date: fmt(start),
			end_date: fmt(end),
			description: election.description || ''
		};
		editingElectionId = election.id;
		showForm = true;
		// Scroll to form
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	async function toggleElection(/** @type {string} */ id, /** @type {string} */ current_status) {
		let nextStatus = 'upcoming';
		if (current_status === 'upcoming') nextStatus = 'active';
		else if (current_status === 'active') nextStatus = 'completed';
		try {
			await adminApi.toggleElection(id, /** @type {any} */ (nextStatus));
			const res = await adminApi.getElections();
			elections = res.data ?? [];
			notify('Election status updated', 'success');
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Error updating status', 'error');
		}
	}

	function promptDelete(/** @type {any} */ election) {
		confirmState = {
			show: true,
			title: 'Delete Election',
			message: `Are you sure you want to delete "${election.name}"? This will permanently remove all associated candidates and votes.`,
			id: election.id,
			onConfirm: async () => {
				try {
					await adminApi.deleteElection(confirmState.id);
					elections = elections.filter((e) => e.id !== confirmState.id);
					notify('Election deleted', 'success');
				} catch (/** @type {any} */ err) {
					notify(err.message ?? 'Failed to delete election', 'error');
				} finally {
					confirmState.show = false;
				}
			}
		};
	}

	function toggleLabel(/** @type {string} */ status) {
		if (status === 'upcoming') return 'Activate';
		if (status === 'active') return 'Complete';
		return '';
	}
	function toggleVariant(/** @type {string} */ status) {
		if (status === 'upcoming') return 'btn-success btn-sm';
		if (status === 'active') return 'btn-danger btn-sm';
		return '';
	}
</script>

<svelte:head><title>Elections | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Administrator</p>
			<h1 class="dash-title">Election Management</h1>
		</div>
		<div style="display:flex;gap:0.5rem;align-items:center;">
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
					bind:value={electionSearch}
					placeholder="Search elections…"
					class="input-base"
					style="padding-left:2.5rem;width:240px;height:2rem;font-size:0.75rem;font-family:sans-serif;"
				/>
			</div>
			<button onclick={loadElections} class="btn-secondary btn-sm">
				<svg
					class="h-3.5 w-3.5"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
					/></svg
				>
				Refresh
			</button>
			<button onclick={() => (showForm = !showForm)} class="btn-primary btn-sm">
				<svg
					class="h-3.5 w-3.5"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
					><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg
				>
				New Election
			</button>
		</div>
	</div>

	<!-- Create Election Form -->
	{#if showForm}
		<div transition:slide={{ duration: 400 }}>
			<div class="w-full bg-white/[0.04] backdrop-blur-3xl border border-white/10 p-8 rounded-[2rem] relative overflow-hidden shadow-2xl" style="margin-bottom:1.5rem;">
				<header class="mb-8 flex items-start justify-between">
					<div>
						<h2 class="text-xl font-black text-white tracking-tighter uppercase mb-1">{editingElectionId ? 'Edit Election' : 'New Election'}</h2>
						<p class="text-[10px] font-bold text-white/30 uppercase tracking-widest">{editingElectionId ? 'Update election details' : 'Create a new election event'}</p>
					</div>
					<button onclick={() => (showForm = false)} class="p-2 bg-white/5 border border-white/10 rounded-xl text-white/30 hover:text-white hover:bg-white/10 transition-all" aria-label="Close form">
						<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
					</button>
				</header>

				<form onsubmit={handleSubmit} class="space-y-6">
					<!-- Election Name -->
					<div class="relative group">
						<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
						<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
							<input id="election-name" type="text" bind:value={newElection.name} required placeholder=" " class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0" />
							<label for="election-name" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">Election Name</label>
						</div>
					</div>

					<div class="grid md:grid-cols-2 gap-6">
						<!-- Start Date -->
						<div class="relative group">
							<label class="block text-[9px] font-black text-white/40 uppercase tracking-widest mb-2 px-1">Start Date & Time</label>
							<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none" style="top:1.5rem;"></div>
							<input id="start-date" type="datetime-local" bind:value={newElection.start_date} required class="relative w-full px-4 py-3 bg-white/[0.04] border border-white/10 rounded-2xl text-white outline-none font-semibold text-sm focus:border-primary-400 transition-all duration-300 [color-scheme:dark]" />
						</div>
						<!-- End Date -->
						<div class="relative group">
							<label class="block text-[9px] font-black text-white/40 uppercase tracking-widest mb-2 px-1">End Date & Time</label>
							<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none" style="top:1.5rem;"></div>
							<input id="end-date" type="datetime-local" bind:value={newElection.end_date} required class="relative w-full px-4 py-3 bg-white/[0.04] border border-white/10 rounded-2xl text-white outline-none font-semibold text-sm focus:border-primary-400 transition-all duration-300 [color-scheme:dark]" />
						</div>
					</div>

					<!-- Description -->
					<div class="relative group">
						<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
						<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
							<input id="election-desc" type="text" bind:value={newElection.description} placeholder=" " class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0" />
							<label for="election-desc" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">Description (Optional)</label>
						</div>
					</div>

					<div class="flex justify-end gap-3 pt-4 border-t border-white/5">
						<button type="button" onclick={() => (showForm = false)} class="px-6 py-2.5 rounded-xl font-black text-[10px] tracking-widest uppercase bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 transition-all">Cancel</button>
						<button type="submit" disabled={isCreating} class="px-8 py-2.5 rounded-xl font-black text-[10px] tracking-widest uppercase bg-primary-600 text-white hover:bg-primary-500 transition-all shadow-xl disabled:opacity-50 flex items-center gap-2">
							{#if isCreating}
								<span class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
								Saving…
							{:else}
								{editingElectionId ? 'Update Election' : 'Create Election'}
							{/if}
						</button>
					</div>
				</form>
			</div>
		</div>
	{/if}

	<!-- Elections Table -->
	<div class="bento-card" style="overflow:hidden; border-radius: 16px;">
		<div
			style="padding:0.75rem 1rem;border-bottom:1px solid var(--border-main);display:flex;align-items:center;justify-content:space-between;"
		>
			<p class="section-label">{filteredElections.length} Election{filteredElections.length !== 1 ? 's' : ''}</p>
		</div>

		{#if isLoading}
			<div style="padding:1.5rem;display:flex;flex-direction:column;gap:0.5rem;">
				{#each Array(4) as _}
					<div class="skeleton" style="height:3rem;"></div>
				{/each}
			</div>
		{:else if filteredElections.length === 0}
			<div class="empty-state">
				{electionSearch ? 'No elections match your search.' : 'No elections yet. Click "New Election" to create one.'}
			</div>
		{:else}
			<div style="overflow-x:auto;">
				<table class="data-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>Status</th>
							<th>Start Date</th>
							<th>End Date</th>
							<th>Voters</th>
							<th>Turnout</th>
							<th style="text-align:right;">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredElections as election (election.id)}
							<tr>
								<td
									style="font-weight:600;color:var(--text-main);max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
									>{election.name}</td
								>
								<td><StatusBadge status={election.status} /></td>
								<td style="color:var(--text-muted);white-space:nowrap;"
									>{new Date(election.start_date).toLocaleDateString()}</td
								>
								<td style="color:var(--text-muted);white-space:nowrap;"
									>{new Date(election.end_date).toLocaleDateString()}</td
								>
								<td style="color:var(--text-muted);">{election.voters_count ?? 0}</td>
								<td>
									{#if election.voters_count}
										<span style="font-weight:600;color:var(--text-main);"
											>{Math.round((election.votes_cast / election.voters_count) * 100)}%</span
										>
									{:else}
										<span style="color:var(--text-subtle);">—</span>
									{/if}
								</td>
								<td style="text-align:right;white-space:nowrap;">
									{#if election.status !== 'completed'}
										<button
											onclick={() => toggleElection(election.id, election.status)}
											class={toggleVariant(election.status)}>{toggleLabel(election.status)}</button
										>
										{#if election.status === 'upcoming'}
											<button
												onclick={() => openEdit(election)}
												class="btn-icon-edit"
												title="Edit election"
												style="margin-left:0.25rem;"
											>
												<svg
													class="h-4 w-4"
													fill="none"
													stroke="currentColor"
													stroke-width="2"
													viewBox="0 0 24 24"
													><path
														stroke-linecap="round"
														stroke-linejoin="round"
														d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125"
													/></svg
												>
											</button>
										{/if}
									{/if}
									<button
										onclick={() => promptDelete(election)}
										class="btn-icon-danger"
										title="Delete election"
										style="margin-left:0.25rem;"
									>
										<svg
											class="h-4 w-4"
											fill="none"
											stroke="currentColor"
											stroke-width="2"
											viewBox="0 0 24 24"
											><path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
											/></svg
										>
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<div style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:110;">
	<Notification text={notification.text} type={notification.type} />
</div>

<ConfirmModal
	show={confirmState.show}
	title={confirmState.title}
	message={confirmState.message}
	onConfirm={confirmState.onConfirm}
	onCancel={() => (confirmState.show = false)}
/>

<style>
	.data-table thead th {
		position: sticky;
		top: 0;
		background: var(--bg-card);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		z-index: 10;
		border-bottom: 1px solid var(--border-main);
		padding: 1rem;
		font-size: 0.75rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--text-subtle);
		transition: color 0.2s;
	}
	.data-table thead th:hover {
		color: var(--text-main);
	}
	.data-table tbody td {
		padding: 1rem;
		vertical-align: middle;
	}
	.data-table tbody tr {
		transition: all 0.2s ease;
		border-bottom: 1px solid var(--border-subtle);
	}
	.data-table tbody tr:last-child {
		border-bottom: none;
	}
	.data-table tbody tr:hover {
		background: rgba(128, 128, 128, 0.05);
	}
</style>
